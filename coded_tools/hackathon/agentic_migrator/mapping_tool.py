# Copyright © 2025-2026 -- Hackathon submission: Agentic AI Migration Factory
"""
coded_tools/hackathon/agentic_migrator/mapping_tool.py
CodedTool wrapper for the Mapping Agent.
"""
import json
import logging
from typing import Any, Dict, Union

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.hackathon.agentic_migrator import agent_logic, db

logger = logging.getLogger(__name__)


class MappingTool(CodedTool):
    """
    Maps ECC fields to S/4HANA fields using the mapping table and returns
    a mapping confidence score.
    """

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        logger.debug(">>>>>>>>>>>>>>>>>> Mapping Agent >>>>>>>>>>>>>>>>>>")
        if "run_id" not in sly_data:
            sly_data["run_id"] = db.new_run()

        fixed_data = sly_data.get("fixed_data") or sly_data.get("raw_data") or agent_logic.load_source_data(agent_logic.DATA_DIR)
        mapping_csv = args.get("mapping_csv")
        report = agent_logic.run_mapping(fixed_data, mapping_csv)
        sly_data["mapping"] = report

        db.log_agent(sly_data["run_id"], "Mapping", json.dumps({k: v for k, v in report.items() if k != "mapping_dict"}))
        logger.debug(">>>>>>>>>>>>>>>>>> Mapping Agent DONE >>>>>>>>>>>>>>>>>>")
        return json.dumps({k: v for k, v in report.items() if k != "mapping_dict"})

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        return self.invoke(args, sly_data)
