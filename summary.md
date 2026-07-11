# Project Summary — Agentic AI Migration Factory

## The problem

Enterprise ERP migrations (e.g. SAP ECC to S/4HANA) are notoriously
expensive and risky, largely because data quality, field mapping, and
migration readiness are usually assessed manually, in silos, by different
teams working from spreadsheets and tribal knowledge. Nobody has a single,
living view of "how clean is our data, how confident are we in the field
mapping, and how risky is this cutover" until very late in the project,
when problems are expensive to fix.

## What we built

**Agentic AI Migration Factory** is a working simulation of an
ECC-to-S/4HANA migration control tower, built as a **neuro-san agent
network** of nine specialist agents coordinated by a single front-man
agent, `MigrationFactory`. A user (or downstream system) simply asks the
front man to run the migration, or asks a targeted question about any
stage, and the front man delegates to the right specialist agents, in the
right order, and synthesizes their findings into a plain-language answer.

The nine agents mirror the real phases of an ERP migration project:

1. **Discovery** — profiles the source data (tables, records, master vs.
   transaction objects, duplicate entities) and produces a complexity
   score.
2. **Data Quality** — finds duplicate vendors/customers, missing GST
   numbers, missing emails, invalid GL accounts, and missing cost centers.
3. **Auto-Fix** — automatically remediates what it safely can: merging
   near-duplicate vendor names using fuzzy string matching, filling
   missing values from context, correcting invalid GL/cost-center data —
   and flags what still needs a human.
4. **Mapping** — maps ECC fields to their S/4HANA equivalents using a
   configurable mapping table, and reports a coverage-based confidence
   score.
5. **Risk** — combines data quality, mapping confidence, and data volume
   into a single migration-readiness risk score and level (Low/Medium/
   High).
6. **Migration Execution** — simulates the actual ETL run (Extract,
   Transform, Clean, Map, Load, Verify) and writes S/4-shaped target CSV
   files.
7. **Validation** — reconciles record counts and financial totals between
   source and target, reporting PASS/FAIL.
8. **Monitoring** — watches the execution for load failures or mismatches
   and recommends retry or rollback.
9. **Reporting** — rolls everything up into an executive summary,
   including a quality-improvement measure (before vs. after Auto-Fix) and
   an illustrative ROI figure.

Every number produced is computed from the actual sample data at run time
— duplicate vendor detection uses real fuzzy string matching, GL account
validity is checked against SAP's numeric-account convention, mapping
confidence is a genuine field-coverage calculation, and risk/ROI are
transparent weighted formulas defined in `agent_logic.py`. Nothing is a
hardcoded demo value; feeding the agents different CSVs produces different,
correct results.

## How the agentic system works

This is not a Python script wearing an "agent" label. It's a real
`neuro-san` agent network (`registries/agentic_migrator.hocon`):

- `MigrationFactory` is the **front man** — the only agent the user talks
  to. Its `instructions` tell it the required call order for a full run,
  but it can also answer a narrower question ("what are the current data
  quality issues?") by calling only the agents needed to answer it.
- Each specialist is a genuine **down-chain tool agent** with its own
  `function` description (so the LLM understands what it's for and what
  arguments it takes) and its own `CodedTool` Python implementation
  (`coded_tools/agentic_migrator/*_tool.py`).
- Agents **hand off context through neuro-san's shared `sly_data`**
  bulletin board rather than calling each other's code directly — the
  same loosely-coupled handoff pattern a real cross-functional team uses.
- Every tool is **defensive by design**: if it's invoked without the
  context an earlier agent would normally have produced, it safely loads
  or recomputes what it needs instead of failing, and if it's ever handed
  a malformed argument (including one an LLM might hallucinate, like a
  nonexistent file path), it falls back to safe defaults instead of
  crashing the whole conversation.

## Why this approach

We deliberately chose a **multi-agent, LLM-orchestrated** design over a
single script for three reasons:

1. **Delegation mirrors the real organization.** Real migration projects
   already split this work across a Data Quality team, a Basis/Migration
   team, a Risk/Governance function, and Reporting — modeling that as
   separate agents makes the system's reasoning legible and each stage
   independently auditable, testable, and improvable.
2. **Conversational flexibility.** Because the front man reasons about
   which agents to call, the same network answers both "run the full
   migration" and narrower questions like "why is the risk medium?"
   without needing separate code paths.
3. **Extensibility.** Each agent is an independent unit with its own
   `CodedTool`. Swapping in a real SAP connector for the Discovery agent,
   or a real Postgres/production data store, requires touching only that
   one agent — the rest of the network, and the front man's reasoning,
   are unaffected.

## What's included

- The full agent network definition and nine `CodedTool` implementations.
- The exact sample ECC extract files (vendor, customer, finance) and the
  ECC→S/4 field mapping table used to develop and test every agent.
- A local SQLite-backed run/agent-log store (upgradeable to real Postgres
  via one environment variable), with the equivalent Postgres DDL included.
- A dependency-free `run_standalone.py` script that exercises the full
  nine-agent pipeline with no LLM key or server required, for a fast
  sanity check before wiring up the live agent network.
- Setup instructions in `README.md` and this project's dependencies in
  `requirements.txt`.

## Status and possible next steps

This is a working, fully tested simulation intended to demonstrate the
agentic architecture and the migration domain logic end-to-end over
representative sample data. Natural next steps would be: connecting the
Discovery agent to a real SAP ECC extract or OData service instead of
static CSVs, adding a persistent audit trail suitable for compliance sign-
off, and giving the Auto-Fix agent a human-in-the-loop approval step for
changes it currently flags as "manual review" rather than applying
automatically.
