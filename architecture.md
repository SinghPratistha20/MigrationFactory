# Architecture — Agentic AI Migration Factory

## What this project does

**Agentic AI Migration Factory** simulates an end-to-end **SAP ECC → S/4HANA
data migration** using a team of nine specialist AI agents instead of a
single monolithic script. It takes raw, messy "ECC extract" CSVs (vendor
master, customer master, finance transactions), profiles them, cleans them,
maps them to the target S/4HANA data model, assesses migration risk,
executes a simulated ETL load, validates the result, watches for
operational issues, and produces an executive report — all without needing
a real SAP system, entirely from CSVs and a lightweight local database.

The goal is to show what an **ERP migration control tower** could look like
if every stage of the migration playbook were delegated to its own
accountable agent, coordinated by an orchestrating front-man agent, rather
than one opaque batch job.

## Why this is agentic, not just a pipeline script

It would be easy to write this as nine Python functions called in sequence.
Instead, this project is built as a **real neuro-san agent network**
(`registries/agentic_migrator.hocon`), where:

- **`MigrationFactory`** is the front-man agent. It is the only agent the
  user talks to. It receives natural-language requests ("run the
  migration", "why is the risk medium?", "what data quality issues did you
  find?"), decides which of its nine down-chain agents to call and in what
  order, and synthesizes their structured output back into a plain-language
  answer. This is genuine agentic delegation, not a fixed script: the front
  man can answer a narrow question by calling only the agents needed to
  answer it, or run the full pipeline for a complete request.

- Each of the nine down-chain agents — **Discovery, Data Quality, Auto-Fix,
  Mapping, Risk, Migration Execution, Validation, Monitoring, and
  Reporting** — is a first-class agent in the network with its own
  `function` description, its own reasoning `instructions`, and its own
  `CodedTool` implementation. The front man treats them as tools it can
  invoke, exactly the way a project manager would delegate to specialists,
  each of whom reports back a structured result rather than raw data.

- Agents **share state through neuro-san's `sly_data` bulletin board**,
  not through direct function calls. Each agent reads what it needs from
  earlier stages (e.g. the Risk agent reads the Quality and Mapping
  agents' scores) and writes its own result for downstream agents — the
  same pattern a real cross-functional migration team would use to hand
  off work, while staying decoupled from each other's internals.

- Every agent is independently **defensive**: if an upstream agent's
  output is missing (e.g. a user asks the Risk agent to run in isolation),
  the agent recomputes or safely defaults what it needs rather than
  failing — mirroring how a competent specialist would ask "let me pull
  that data myself" rather than blocking the whole team.

## Agent network diagram

```
                     ┌─────────────────────┐
        User  ─────► │   MigrationFactory   │   (front-man agent)
                     └──────────┬───────────┘
                                │ delegates, in order, based on the request
        ┌───────────┬──────────┼──────────┬───────────┬────────────┐
        ▼           ▼          ▼          ▼           ▼            ▼
  discovery_    quality_   autofix_   mapping_     risk_      migration_
   agent         agent      agent      agent       agent        agent
        │           │          │          │           │            │
        └─────┬─────┴────┬─────┴────┬─────┴─────┬─────┴─────┬──────┘
              ▼          ▼          ▼           ▼           ▼
                              validation_agent
                                    │
                              monitoring_agent
                                    │
                              reporting_agent
                                    │
                                    ▼
                      Executive summary back to the user
```

(Strictly, `MigrationFactory` calls all nine directly as its down-chain
tools — the diagram groups them by pipeline stage for readability. The
order in which they must be called is enforced in `MigrationFactory`'s
`instructions`, not by hard-coded control flow.)

## Agent responsibilities

| Agent | Responsibility | Key output |
|---|---|---|
| **Discovery** | Profiles the uploaded ECC datasets: table/record counts, master vs. transaction objects, duplicate entities | `complexity_score` (0–100) |
| **Data Quality** | Scans for duplicate vendors/customers, missing GST, missing emails, invalid GL accounts, missing cost centers | `quality_score` |
| **Auto-Fix** | Merges near-duplicate vendor names (fuzzy matching), fills missing values, corrects invalid GL/cost-center data | `fixed_records`, `remaining_manual_review` |
| **Mapping** | Maps ECC fields to S/4HANA fields using a configurable mapping table, computes field-coverage confidence | `mapping_confidence` |
| **Risk** | Blends quality, mapping confidence, and data volume into a migration readiness score | `risk_score`, `risk` (Low/Medium/High) |
| **Migration Execution** | Simulates Extract → Transform → Clean → Map → Load → Verify and writes `s4_*.csv` target files | `processed`, `success_rate` |
| **Validation** | Reconciles record counts and financial totals between source and target | `validation_status` (PASS/FAIL) |
| **Monitoring** | Detects load failures / mismatches during execution, recommends retry or rollback | `primary_event` |
| **Reporting** | Aggregates the full run into an executive summary with an illustrative ROI estimate | `quality_before`/`after`, `roi` |

## Technical implementation

- **Framework:** [neuro-san](https://github.com/cognizant-ai-lab/neuro-san) /
  neuro-san-studio, via `registries/agentic_migrator.hocon` (the agent
  network definition) and `coded_tools/agentic_migrator/*.py` (the
  `CodedTool` implementations).
- **Agent logic:** `coded_tools/agentic_migrator/agent_logic.py` holds all
  nine agents' actual computation — real fuzzy-matching deduplication
  (`difflib`), null/format validation, coverage-based mapping confidence,
  and a weighted risk formula. Nothing is hardcoded or mocked; re-running
  against different sample CSVs produces different, correct numbers.
- **Persistence:** `coded_tools/agentic_migrator/db.py` logs every run and
  every agent's activity to a local SQLite file by default, or to real
  PostgreSQL if `DATABASE_URL` is set (`schema.sql` documents the
  equivalent DDL).
- **LLM:** `config/llm_config.hocon` defines a provider fallback chain
  (Mistral → OpenAI → Anthropic → Google), so the project runs with
  whichever key is available.
- **Sample data:** `coded_tools/agentic_migrator/data/` — the exact
  vendor/customer/finance/mapping CSVs used to develop and test the agents,
  swappable for any real-world extract with the same column headers.

## Design choices worth calling out

- **No hardcoded outcomes.** Every score (complexity, quality, mapping
  confidence, risk, ROI) is computed from the data at run time. This was a
  deliberate choice so the agents demonstrably *reason over data*, not
  replay a canned demo.
- **Defensive, stateless-where-possible tools.** Any agent can be invoked
  standalone (e.g. "just check data quality") and will load or recompute
  whatever upstream context it needs, rather than assuming a fixed call
  order — this makes the front man's delegation genuinely flexible instead
  of a disguised linear script.
- **Graceful degradation on bad input.** If the front man (or its LLM)
  passes a malformed or hallucinated file path, the affected tool falls
  back to the bundled sample data rather than crashing the whole
  conversation — an explicit lesson learned from hardening this project
  against LLM-generated tool arguments.
