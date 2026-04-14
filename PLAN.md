Below is a concrete product and implementation plan for **Atlas**.

## What Atlas is

**Atlas** is an AI layer on top of Gmail that gives users two things:

1. **Inbox organization by user-defined intent**
   Users define labels and plain-English descriptions of what those labels mean, and Atlas classifies incoming and historical email into those labels.

2. **Scoped research and retrieval over the mailbox**
   Users can ask natural-language questions over a mailbox scope they control, such as Primary only, Primary + Updates, or everything except Promotions. Gmail already exposes system labels such as `INBOX`, `CATEGORY_PERSONAL`, `CATEGORY_SOCIAL`, and `CATEGORY_PROMOTIONS`, and its API supports search through `q` plus label filtering through `labelIds[]`, which is the right base primitive for Atlas’s scope model. ([Google for Developers][1])

A good one-line description is:

**Atlas is a user-configurable AI control layer for Gmail that organizes email into user-defined labels and answers research questions over a user-defined mailbox scope.**

---

## The 2 main objectives

### Objective 1: Intelligent inbox organization

Atlas should let users define labels like:

* Recruiting
* Finance/Bills
* Travel
* Personal Important
* Newsletters to Read Later

Each label should have:

* a name
* a description
* optional inclusions
* optional exclusions
* examples over time
* confidence threshold
* default action, for v1 this should be label-only

The product value here is not just “AI labels email.”
It is: **the user defines the meaning, Atlas operationalizes it consistently.**

This is feasible because Gmail supports both custom user labels and system labels, and labels can be applied and managed programmatically. Gmail’s docs also clarify an important detail: labels exist on messages, while thread label views reflect labels found on any message in that thread. ([Google for Developers][1])

### Objective 2: Natural-language research over the inbox

Atlas should answer questions such as:

* “How many recruiters contacted me in the last two months?”
* “Summarize all discussion related to my France postdoc.”
* “Find every invoice due this month.”
* “Compile all travel bookings from Updates and Primary, excluding Promotions.”

This is not just semantic search. It is a combination of:

* mailbox scoping
* Gmail retrieval
* classification
* extraction
* de-duplication
* aggregation
* answer synthesis

Gmail gives the initial retrieval layer through `messages.list` and `threads.list`, but there are key constraints Atlas must handle itself. The Gmail API supports most of Gmail’s advanced search syntax, but the API does not do thread-wide search the same way the Gmail UI does. Also, `messages.list` returns only message IDs and thread IDs plus a `resultSizeEstimate`, so Atlas must fetch message details separately for exact answers. ([Google for Developers][2])

---

## Project scope for v1

Atlas v1 should do exactly these things:

* Connect a Gmail account with OAuth
* Let the user define mailbox scope
* Let the user create labels and label descriptions
* Classify historical and new emails into those labels
* Preview proposed label actions before applying them
* Support natural-language querying over selected mailbox scope
* Return answers with evidence, counts, threads, and source emails

Atlas v1 should **not** do these yet:

* autonomous replies
* silent archiving at scale
* deletion
* meeting scheduling
* multi-provider email support
* complex cross-app workflows

That keeps the first version focused and lowers trust risk.

---

## Core product design

Atlas should be built around four first-class objects.

### 1. Mailbox Scope

A saved scope object that defines what Atlas can search.

Example:

* Include: `INBOX`, `CATEGORY_PERSONAL`, `CATEGORY_UPDATES`
* Exclude: `CATEGORY_PROMOTIONS`, `CATEGORY_SOCIAL`
* Date default: last 180 days

This maps cleanly to Gmail system labels and label filtering. ([Google for Developers][1])

### 2. Label Policy

A user-defined policy object.

Example:

* Label: Recruiting
* Meaning: recruiter outreach, interview scheduling, hiring discussions
* Exclude: job board newsletters and promotional job blasts
* Confidence threshold: 0.85
* Action: apply label only

### 3. Query Plan

Atlas should convert every natural-language question into a structured internal plan.

Example:

* task type: count
* entity: recruiter
* time window: last 60 days
* scope: Primary + Updates, exclude Promotions
* aggregation: unique recruiter identities

### 4. Evidence Bundle

Every answer should point to the actual underlying messages or threads used.

This is critical for trust.

---

## Recommended technical architecture

I would split the system into six services or layers.

### 1. OAuth and account connection layer

Purpose:

* connect Gmail
* request minimal scopes
* store tokens securely
* refresh tokens
* support incremental permission upgrades later

Important platform constraint:

* `gmail.labels` is non-sensitive and only covers label management
* `gmail.readonly`, `gmail.modify`, and `gmail.metadata` are restricted scopes
* if you store or transmit restricted Gmail data on servers, Google requires verification and potentially a security assessment ([Google for Developers][3])

Practical implication:

* For a public SaaS, compliance is part of the product plan, not a later detail.
* A local-first or single-tenant architecture is strategically easier for an early version.

### 2. Gmail sync and ingestion layer

Purpose:

* initial mailbox sync
* incremental sync for new mail and label changes
* hydrate metadata first
* fetch body only when needed

Use:

* `messages.list`
* `messages.get`
* `threads.get` where needed
* `watch` plus `history.list` for ongoing updates

Gmail push notifications are viable here, but mailbox watches must be renewed at least every 7 days, and Google recommends renewing daily. ([Google for Developers][4])

### 3. Mail understanding layer

Purpose:

* classify email type
* extract entities
* normalize senders and companies
* score label policy matches

This layer should produce structured facts such as:

* sender identity
* company
* topic
* due date
* recruiting / invoice / travel / newsletter class
* confidence
* explanation

### 4. Query planner

Purpose:

* parse natural language into structured query plans

For example, “How many recruiters have contacted me within the last two months?” becomes:

* retrieve candidate emails in time window
* apply mailbox scope
* filter to inbound mail
* classify recruiter outreach
* resolve unique recruiter identities
* count distinct recruiters
* return evidence

### 5. Answer synthesis layer

Purpose:

* compile retrieved evidence
* generate summaries and counts
* produce user-facing answers with citations back to emails

### 6. Action engine

Purpose:

* create labels
* apply labels
* later possibly archive or mark read

For v1, keep actions limited to labels only.

---

## Data model

A simple but durable schema would look like this.

### Users

* id
* email
* auth_provider
* encrypted_token_ref
* created_at

### MailboxConnections

* user_id
* provider = gmail
* granted_scopes
* sync_cursor
* watch_expiration
* status

### Scopes

* id
* user_id
* name
* include_system_labels[]
* exclude_system_labels[]
* include_user_labels[]
* exclude_user_labels[]
* default_date_window

### Labels

* id
* user_id
* gmail_label_id
* name
* description
* status

### LabelPolicies

* id
* label_id
* description
* inclusions
* exclusions
* confidence_threshold
* apply_mode

### Messages

* gmail_message_id
* thread_id
* internal_date
* from_header
* to_header
* subject
* snippet
* label_ids[]
* body_ref
* raw_ref

### Threads

* gmail_thread_id
* subject_canonical
* participants[]
* first_message_at
* last_message_at

### Extractions

* message_id
* classifier_outputs
* entities_json
* dates_json
* confidence

### QueryRuns

* id
* user_id
* raw_question
* structured_plan_json
* scope_id
* status
* answer_json
* evidence_refs[]

### ActionRuns

* id
* user_id
* action_type
* target_refs[]
* preview_only
* status

---

## Detailed implementation plan

## Phase 0: Product boundary and trust model

Before coding, lock these decisions:

1. **First provider**: Gmail only
2. **First actions**: labels only
3. **First trust model**: preview first, then apply
4. **First deployment choice**: decide between:

   * local-first/private
   * hosted SaaS

I strongly recommend:

* **local-first or single-tenant private beta first**
* **hosted public SaaS later**

Reason: Gmail restricted-scope verification and security assessment become much heavier if you store or transmit restricted mailbox data on servers. ([Google for Developers][3])

---

## Phase 1: Gmail connection and mailbox sync

Build:

* OAuth connect flow
* scope management
* token storage
* initial sync job
* incremental sync job
* watch renewal job

Recommended access pattern:

* use `gmail.readonly` for read/search product paths
* add `gmail.modify` only when label application is enabled
* use `gmail.labels` for label management where possible, since it is non-sensitive, though mailbox reading still requires restricted scopes for Atlas’s main value proposition ([Google for Developers][3])

Sync strategy:

* first sync recent mailbox range, for example last 90 or 180 days
* store metadata first
* fetch full body lazily or selectively
* keep a history cursor for incremental updates

Important API behavior:

* `messages.list` supports `q` and `labelIds[]`
* it returns only IDs and thread IDs, not full content
* for exact processing, follow up with `messages.get`
* `messages.get` supports `format=METADATA` and `metadataHeaders[]` so you can avoid fetching full bodies initially ([Google for Developers][5])

---

## Phase 2: Scope engine

Build the user-facing concept of scope.

The user should be able to save scopes like:

* Primary only
* Primary + Updates
* Everything except Promotions
* Unlabeled mail only
* Last 30 days + Primary
* Work scope: include certain domains, exclude newsletters

Implementation:

* compile scope to Gmail `labelIds[]` plus query fragments
* support date ranges using `after:` and `before:`
* use epoch seconds internally for precise timezone behavior, since Gmail interprets date strings at midnight PST if plain dates are used in search queries ([Google for Developers][2])

---

## Phase 3: Label policy engine

This is the first major user-value feature.

Build:

* create label UI
* label description editor
* policy preview
* confidence scoring
* approval workflow
* batch apply

Classification pipeline:

1. Retrieve emails within selected scope
2. Run cheap heuristics first
3. Run semantic classifier second
4. Produce match confidence and reason
5. Show preview to user
6. Apply labels after approval

The important design choice:

* **understand at thread level**
* **write labels at message level first**

This avoids Gmail thread-label confusion, because labels technically live on messages, and a thread’s labels reflect labels present on any message in that thread. ([Google for Developers][1])

v1 UX:

* “Atlas found 84 likely Travel emails”
* confidence buckets: high, medium, low
* user approves high first
* user can correct mistakes
* those corrections become future examples

---

## Phase 4: Natural-language query engine

This is the second major feature.

Atlas should not answer user questions directly from the LLM. It should build an internal plan.

### Query types to support first

1. **Find**
   “Find all emails about ACAC 2026.”

2. **Count**
   “How many recruiters contacted me in the last 2 months?”

3. **Summarize**
   “Summarize all discussion with CNRS.”

4. **Extract**
   “List invoice due dates this month.”

5. **Compile timeline**
   “Show the sequence of travel approval emails.”

### Execution flow

1. Parse the question
2. Resolve scope
3. Build Gmail query
4. Retrieve candidate messages
5. Fetch metadata or bodies as needed
6. Classify and extract
7. Group and de-duplicate
8. Aggregate if required
9. Synthesize the answer with evidence

Important Gmail-specific constraint:

* the Gmail API supports most advanced search syntax, but does not support thread-wide search the way the Gmail UI does, so Atlas must do its own thread expansion and reasoning when needed. ([Google for Developers][2])

---

## Phase 5: Research answer layer

This is where Atlas becomes more than a filter tool.

For every answer, Atlas should return:

* direct answer
* concise explanation
* evidence summary
* source emails or threads
* ambiguity notes if needed

Example output:

* “12 recruiters contacted you in the last 60 days.”
* “This is based on 18 inbound messages across 15 threads.”
* “I counted unique recruiter identities, not raw emails.”
* “3 cases were borderline and excluded.”

That level of transparency is what makes the system usable.

---

## Phase 6: Monitoring new mail

Once historical sync and query work, add real-time or near-real-time classification.

Implementation:

* subscribe to Gmail mailbox changes through `watch`
* store `historyId`
* process deltas using `history.list`
* refresh watch daily

This enables:

* label suggestion on new mail
* updated counts
* continuous organization without full rescans

Gmail’s push documentation explicitly requires watch renewal at least every 7 days and recommends daily renewal. ([Google for Developers][4])

---

## Phase 7: Security, privacy, and compliance

This is a major workstream, not a footnote.

### Security requirements

* encrypt tokens at rest
* strict data retention
* audit logs
* no permanent raw-body storage unless necessary
* body fetch on demand where possible
* role-based admin access internally
* revocation and disconnect flow

### Privacy requirements

* explain exactly what Atlas reads
* explain scope in user terms
* let user choose included mailbox categories
* allow “metadata-only mode” for lightweight use cases

### Compliance reality

Google classifies `gmail.readonly`, `gmail.modify`, and `gmail.metadata` as restricted scopes, and apps that store or transmit restricted data on servers may need a security assessment. ([Google for Developers][3])

So your go-to-market path should be one of these:

1. **Local-first desktop app**

   * easier early trust story
   * fewer backend data custody issues

2. **Private beta, single-tenant**

   * controlled rollout
   * easier security review posture

3. **Public multi-tenant SaaS**

   * strongest distribution upside
   * hardest compliance path

My recommendation is option 1 or 2 first.

---

## Suggested milestone breakdown

## Milestone 1: Inbox foundation

Deliver:

* Gmail connect
* token storage
* initial sync
* mailbox scope model
* raw message metadata store

Success:

* user connects Gmail
* Atlas can retrieve scoped candidate messages correctly

## Milestone 2: Label-driven organization MVP

Deliver:

* create user labels
* define label descriptions
* preview matched emails
* apply labels to approved emails
* feedback loop for corrections

Success:

* user can meaningfully organize mailbox with custom labels

## Milestone 3: Query and research MVP

Deliver:

* natural-language query input
* query planner
* count/find/summarize question types
* evidence-backed answers

Success:

* Atlas can answer scoped inbox questions accurately enough to be trusted

## Milestone 4: Continuous monitoring

Deliver:

* Gmail watch setup
* incremental sync
* auto-suggestion on new mail

Success:

* Atlas moves from one-time tool to continuous inbox layer

## Milestone 5: Hardening

Deliver:

* privacy controls
* audit logging
* scope upgrade flow
* quality metrics
* compliance preparation

Success:

* ready for external users

---

## Recommended MVP stack

This is a sensible technical direction, not a rigid requirement.

### Backend

* FastAPI or similar API service
* Postgres for relational state
* Redis for jobs and short-lived caching
* background worker for sync and classification
* object storage only if you choose to persist bodies/raw MIME

### ML / intelligence

* rules + LLM hybrid
* classifier layer for message type
* extraction layer for entities and dates
* optional embeddings for semantic retrieval over selected content

### Frontend

* web app first
* three main views:

  * Connect and scopes
  * Labels and preview
  * Query and evidence

### Deployment

* local-first if you want fastest path to a real usable alpha
* otherwise private cloud deployment with minimal retention

---

## Biggest product risks

1. **Trust risk**
   Users will stop using Atlas if it silently mislabels important mail.

2. **Overlapping labels**
   Without guidance, users will create ambiguous categories.

3. **Query ambiguity**
   Natural-language mailbox questions often require an internal structured plan, not just search.

4. **Compliance drag**
   A public hosted product can get slowed down substantially by Gmail restricted-scope requirements. ([Google for Developers][3])

---

## Final recommendation

Build Atlas around this sequence:

**Connect mailbox → define scope → define labels → preview categorization → apply labels → ask research questions → inspect evidence**

That is the right first product.

If you want, the next useful step is for us to turn this into a **v1 product spec** with:

* user stories
* API surface
* database schema
* service boundaries
* first 3 screens
* milestone-by-milestone engineering tasks

[1]: https://developers.google.com/workspace/gmail/api/guides/labels "Manage labels  |  Gmail  |  Google for Developers"
[2]: https://developers.google.com/workspace/gmail/api/guides/filtering "Search and filter messages  |  Gmail  |  Google for Developers"
[3]: https://developers.google.com/workspace/gmail/api/auth/scopes "Choose Gmail API scopes  |  Google for Developers"
[4]: https://developers.google.com/workspace/gmail/api/guides/push "Configure push notifications in Gmail API  |  Google for Developers"
[5]: https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/list "Method: users.messages.list  |  Gmail  |  Google for Developers"