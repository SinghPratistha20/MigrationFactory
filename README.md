# Agentic AI Migration Factory

A 9-agent SAP ECC → S/4HANA data migration simulation, built as a real
[neuro-san](https://github.com/cognizant-ai-lab/neuro-san) agent network.

See [`architecture.md`](architecture.md) for how the agentic system is
designed, and [`summary.md`](summary.md) for a project overview.

```
MigrationFactory (front man)
   │
   ├─ discovery_agent    ─ profiles the ECC extract, produces a complexity score
   ├─ quality_agent      ─ finds duplicates, missing GST/emails, invalid GL accounts
   ├─ autofix_agent       ─ auto-remediates what it safely can
   ├─ mapping_agent       ─ maps ECC fields to S/4HANA fields, confidence score
   ├─ risk_agent          ─ predicts migration readiness risk
   ├─ migration_agent     ─ simulates the ETL run, writes S/4-shaped target files
   ├─ validation_agent    ─ reconciles record counts and financial totals
   ├─ monitoring_agent    ─ flags load failures / mismatches, recommends retry/rollback
   └─ reporting_agent     ─ produces the final executive summary + ROI
```

## Requirements

- Python 3.10+
- An API key for at least one LLM provider: Mistral (default), OpenAI,
  Anthropic, or Google Gemini.

## Setup

```bash
# 1. (Recommended) create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your LLM API key
cp .env.example .env
# then edit .env and fill in MISTRAL_API_KEY (or another provider's key)
```

## Run it

### Option A — full agent network (neuro-san server + UI)

```bash
ns run
```

The neuro-san server listens on `localhost:8080`; the nsflow chat UI opens
at [http://localhost:4173/](http://localhost:4173/). Select
**MigrationFactory** from the list of agent networks and try:

> Run the full ECC to S/4HANA migration and give me the executive summary.

### Option B — command-line chat (no browser needed)

```bash
ns chat MigrationFactory
```

### Option C — fastest sanity check (no LLM key, no server)

Runs the same nine agents directly, printing every stage's JSON output —
useful to confirm the logic and sample data work before touching the LLM
or the server at all:

```bash
python coded_tools/agentic_migrator/run_standalone.py
```

## Project structure

```
.
├── README.md
├── architecture.md              # agentic system design write-up
├── summary.md                   # project summary
├── requirements.txt
├── .env.example
├── config/
│   └── llm_config.hocon         # LLM provider fallback chain (Mistral → OpenAI → Anthropic → Google)
├── registries/
│   ├── manifest.hocon            # registers the agent network below
│   └── agentic_migrator.hocon    # the agent network: MigrationFactory + 9 agents
└── coded_tools/
    └── agentic_migrator/
        ├── agent_logic.py        # the actual computation for all 9 agents
        ├── discovery_tool.py ... reporting_tool.py   # 9 CodedTool wrappers
        ├── db.py + schema.sql    # SQLite (default) / Postgres run logging
        ├── data/                 # sample vendor/customer/finance/mapping CSVs
        └── run_standalone.py     # dependency-free sanity check
```

## Using your own data

Drop your own CSVs into `coded_tools/agentic_migrator/data/` with the same
column headers as the samples (`vendor.csv`, `customer.csv`,
`finance.csv`, `mapping.csv`), or point `discovery_agent`/`mapping_agent`
at a different folder/file via their optional `data_dir` / `mapping_csv`
arguments when chatting. Every score is computed from the data at run time
— nothing is hardcoded.

## Persistence

Run metadata and per-agent log lines are written to a local SQLite file at
`coded_tools/agentic_migrator/migration_runs.db` (auto-created). To use
real PostgreSQL instead, set `DATABASE_URL` in `.env` and install
`psycopg2-binary` — see `coded_tools/agentic_migrator/schema.sql` for the
equivalent DDL. `db.py` switches automatically; no code changes needed.

## Troubleshooting

- **No agents showing up in the UI:** confirm you're running `ns run` from
  this project's root directory, and that `pandas` installed correctly
  (`pip show pandas`) — the agents' tools depend on it.
- **"Function needs at least one argument" errors:** already handled —
  every tool's parameter schema in `registries/agentic_migrator.hocon` has
  at least one declared property.
- **A tool fails on a bad/hallucinated file path:** already handled — every
  tool that accepts a path argument validates it and falls back to the
  bundled sample data rather than crashing.
