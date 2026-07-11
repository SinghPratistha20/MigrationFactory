# Copyright © 2025-2026 -- Hackathon submission: Agentic AI Migration Factory
"""
coded_tools/hackathon/agentic_migrator/autofix_tool.py
CodedTool wrapper for the Auto Fix Agent.
"""
import json
import logging
from typing import Any, Dict, Union

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.hackathon.agentic_migrator import agent_logic, db

logger = logging.getLogger(__name__)


class AutoFixTool(CodedTool):
    """
    Cleans identified quality issues: merges near-duplicate vendor names,
    fills missing values from reference data, corrects invalid GL accounts
    and cost centers.
    """

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        logger.debug(">>>>>>>>>>>>>>>>>> AutoFix Agent >>>>>>>>>>>>>>>>>>")
        if "run_id" not in sly_data:
            sly_data["run_id"] = db.new_run()

        raw_data = sly_data.get("raw_data") or agent_logic.load_source_data(args.get("data_dir") or agent_logic.DATA_DIR)
        sly_data["raw_data"] = raw_data

        fixed_data, summary = agent_logic.run_autofix(raw_data)
        sly_data["fixed_data"] = fixed_data
        sly_data["autofix"] = summary
        sly_data["quality_after"] = agent_logic.run_quality(fixed_data)

        db.log_agent(sly_data["run_id"], "AutoFix", json.dumps(summary))
        logger.debug(">>>>>>>>>>>>>>>>>> AutoFix Agent DONE >>>>>>>>>>>>>>>>>>")
        return json.dumps(summary)

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        return self.invoke(args, sly_data)
