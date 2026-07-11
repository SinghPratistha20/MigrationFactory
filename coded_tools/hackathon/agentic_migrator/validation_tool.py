# Copyright © 2025-2026 -- Hackathon submission: Agentic AI Migration Factory
"""
coded_tools/hackathon/agentic_migrator/validation_tool.py
CodedTool wrapper for the Validation Agent.
"""
import json
import logging
from typing import Any, Dict, Union

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.hackathon.agentic_migrator import agent_logic, db

logger = logging.getLogger(__name__)


class ValidationTool(CodedTool):
    """
    Reconciles record counts and financial totals between source and
    target to confirm migration correctness.
    """

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        logger.debug(">>>>>>>>>>>>>>>>>> Validation Agent >>>>>>>>>>>>>>>>>>")
        if "run_id" not in sly_data:
            sly_data["run_id"] = db.new_run()

        fixed_data = sly_data.get("fixed_data") or {}
        migration = sly_data.get("migration") or {}

        report = agent_logic.run_validation(fixed_data, migration)
        sly_data["validation"] = report

        db.log_agent(sly_data["run_id"], "Validation", json.dumps(report))
        logger.debug(">>>>>>>>>>>>>>>>>> Validation Agent DONE >>>>>>>>>>>>>>>>>>")
        return json.dumps(report)

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        return self.invoke(args, sly_data)
