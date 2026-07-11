"""
coded_tools/hackathon/agentic_migrator/run_standalone.py
----------------------------------------------------------------
Optional sanity-check script. Runs the same 9-stage pipeline that the
"MigrationFactory" agent network calls, but directly -- no neuro-san
server, no LLM API key required. Useful to quickly confirm the logic
and sample data work before wiring up the full agent network.

Usage (from the repo root):
    python coded_tools/hackathon/agentic_migrator/run_standalone.py
----------------------------------------------------------------
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from coded_tools.hackathon.agentic_migrator import agent_logic


def main():
    raw_data = agent_logic.load_source_data()

    discovery = agent_logic.run_discovery(raw_data)
    print("\n=== Discovery Agent ===")
    print(json.dumps(discovery, indent=2))

    quality_before = agent_logic.run_quality(raw_data)
    print("\n=== Data Quality Agent (before) ===")
    print(json.dumps(quality_before, indent=2))

    fixed_data, autofix_summary = agent_logic.run_autofix(raw_data)
    print("\n=== Auto Fix Agent ===")
    print(json.dumps(autofix_summary, indent=2))

    quality_after = agent_logic.run_quality(fixed_data)
    print("\n=== Data Quality Agent (after) ===")
    print(json.dumps(quality_after, indent=2))

    mapping = agent_logic.run_mapping(fixed_data)
    print("\n=== Mapping Agent ===")
    print(json.dumps({k: v for k, v in mapping.items() if k != "mapping_dict"}, indent=2))

    risk = agent_logic.run_risk(quality_after, mapping, discovery)
    print("\n=== Risk Assessment Agent ===")
    print(json.dumps(risk, indent=2))

    migration = agent_logic.run_migration(fixed_data, mapping["mapping_dict"])
    print("\n=== Migration Execution Agent ===")
    print(json.dumps({k: v for k, v in migration.items() if k != "output_files"}, indent=2))
    print(f"(target files written to {agent_logic.OUTPUT_DIR})")

    validation = agent_logic.run_validation(fixed_data, migration)
    print("\n=== Validation Agent ===")
    print(json.dumps(validation, indent=2))

    monitoring = agent_logic.run_monitoring(migration, validation)
    print("\n=== Monitoring Agent ===")
    print(json.dumps(monitoring["primary_event"], indent=2))

    reporting = agent_logic.run_reporting(quality_before, quality_after, migration, autofix_summary)
    print("\n=== Reporting Agent (Executive Summary) ===")
    print(json.dumps(reporting, indent=2))


if __name__ == "__main__":
    main()
