# Agentic AI Migration Factory — neuro-san-studio submission

A 9-agent SAP ECC → S/4HANA migration simulation, built as a real
**neuro-san** agent network (not a mock) and dropped into this
neuro-san-studio checkout as a new registry group: `hackathon`.

```
MigrationFactory (front man)
   │
   ├─ discovery_agent    (coded_tools/hackathon/agentic_migrator/discovery_tool.py)
   ├─ quality_agent      (.../quality_tool.py)
   ├─ autofix_agent      (.../autofix_tool.py)
   ├─ mapping_agent      (.../mapping_tool.py)
   ├─ risk_agent         (.../risk_tool.py)
   ├─ migration_agent    (.../migration_tool.py)
   ├─ validation_agent   (.../validation_tool.py)
   ├─ monitoring_agent   (.../monitoring_tool.py)
   └─ reporting_agent    (.../reporting_tool.py)
```

All nine down-chain tools are real `CodedTool` classes wired via
`registries/hackathon/agentic_migrator.hocon`, registered in the top-level
`registries/manifest.hocon` (see the `include "registries/hackathon/manifest.hocon"`
line), so they load automatically with the rest of the studio's agent
networks — **no separate server config needed.**

## 1. Fastest sanity check (no LLM key, no server)

Confirms the underlying agent logic and sample CSVs work before you touch
the neuro-san server at all:

```bash
python coded_tools/hackathon/agentic_migrator/run_standalone.py
```

This prints all nine agents' JSON output in order and writes
`s4_vendor.csv` / `s4_customer.csv` / `s4_finance.csv` to
`coded_tools/hackathon/agentic_migrator/output/`.

## 2. Run for real, as a neuro-san agent network

This repo already has everything wired up. From the repo root:

```bash
# 1. Install deps (only needed once for the whole studio checkout)
pip install -r requirements.txt

# 2. Set your Mistral key (this branch defaults to Mistral -- see hackathon.md)
echo 'MISTRAL_API_KEY=your_key_here' > .env

# 3. Start the server + nsflow UI
python -m neuro_san_studio run
```

Open [http://localhost:4173/](http://localhost:4173/), and you should see
**MigrationFactory** in the list of available agent networks (alongside
the other demos like `music_nerd`). Chat with it, e.g.:

> Run the full ECC to S/4HANA migration and give me the executive summary.

It will call all nine tools in order and summarize the run.

### Command-line chat (no browser needed)

```bash
python -m neuro_san_studio.cli chat MigrationFactory
# or, depending on your installed neuro-san-studio version:
ns chat MigrationFactory
```

## 3. If "no agents are showing up"

That almost always means the manifest include didn't take effect or the
server was started from the wrong directory. Checklist:

1. Run `python -m neuro_san_studio run` **from the repo root** (the folder
   containing `registries/`, `coded_tools/`, `config/`) — relative includes
   in the `.hocon` files are resolved from there.
2. Confirm `registries/manifest.hocon` contains the line:
   `include "registries/hackathon/manifest.hocon",`
3. Confirm `registries/hackathon/manifest.hocon` contains:
   `"hackathon/agentic_migrator.hocon": true`
4. Check `logs/server.log` for a HOCON parse error — a missing comma or
   brace anywhere in an included file will silently drop networks defined
   after it, not just the broken one.
5. Make sure at least one LLM API key your `config/llm_config.hocon`
   fallback chain can use is set (this branch tries `MISTRAL_API_KEY`
   first, then `OPENAI_API_KEY`, then `ANTHROPIC_API_KEY`, then
   `GOOGLE_API_KEY`).

## Sample data & swapping in your own

Bundled at `coded_tools/hackathon/agentic_migrator/data/`:
`vendor.csv`, `customer.csv`, `finance.csv`, `mapping.csv` (the exact files
from the hackathon homework). Drop your own files with the same column
headers into that folder (or pass `data_dir` / `mapping_csv` args when
chatting with `discovery_agent` / `mapping_agent`) and every score
recomputes from real logic — nothing is hardcoded.

## Persistence

Agent run metadata and per-agent log lines are written to a local SQLite
file at `coded_tools/hackathon/agentic_migrator/migration_runs.db`
(auto-created). To point this at real PostgreSQL instead, set
`DATABASE_URL` and install `psycopg2-binary` — see `schema.sql` in the same
folder for the equivalent DDL. `db.py` switches automatically.
