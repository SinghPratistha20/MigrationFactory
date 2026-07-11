# Copyright © 2025-2026 -- Hackathon submission: Agentic AI Migration Factory
"""
coded_tools/hackathon/agentic_migrator/migration_tool.py
CodedTool wrapper for the Migration Execution Agent.
"""
import json
import logging
from typing import Any, Dict, Union

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.hackathon.agentic_migrator import agent_logic, db

logger = logging.getLogger(__name__)


class MigrationTool(CodedTool):
    """
    Simulates the ETL run (Extract, Transform, Clean, Map, Load, Verify)
    and writes S/4-shaped target files.
    """

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        logger.debug(">>>>>>>>>>>>>>>>>> Migration Agent >>>>>>>>>>>>>>>>>>")
        if "run_id" not in sly_data:
            sly_data["run_id"] = db.new_run()

        fixed_data = sly_data.get("fixed_data") or sly_data.get("raw_data") or agent_logic.load_source_data(agent_logic.DATA_DIR)
        mapping_dict = (sly_data.get("mapping") or {}).get("mapping_dict", {})
        output_dir = args.get("output_dir") or agent_logic.OUTPUT_DIR

        report = agent_logic.run_migration(fixed_data, mapping_dict, output_dir)
        sly_data["migration"] = report

        db.log_agent(sly_data["run_id"], "Migration", json.dumps({k: v for k, v in report.items() if k != "output_files"}))
        logger.debug(">>>>>>>>>>>>>>>>>> Migration Agent DONE >>>>>>>>>>>>>>>>>>")
        return json.dumps({k: v for k, v in report.items() if k != "output_files"})

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        return self.invoke(args, sly_data)
