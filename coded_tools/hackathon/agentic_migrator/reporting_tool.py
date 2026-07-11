# Copyright © 2025-2026 -- Hackathon submission: Agentic AI Migration Factory
"""
coded_tools/hackathon/agentic_migrator/reporting_tool.py
CodedTool wrapper for the Reporting Agent.
"""
import json
import logging
from typing import Any, Dict, Union

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.hackathon.agentic_migrator import agent_logic, db

logger = logging.getLogger(__name__)


class ReportingTool(CodedTool):
    """
    Aggregates every agent's result into the final executive summary:
    quality before/after, migration success rate, and ROI.
    """

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        logger.debug(">>>>>>>>>>>>>>>>>> Reporting Agent >>>>>>>>>>>>>>>>>>")
        if "run_id" not in sly_data:
            sly_data["run_id"] = db.new_run()

        quality_before = sly_data.get("quality_before") or {}
        quality_after = sly_data.get("quality_after") or quality_before
        migration = sly_data.get("migration") or {}
        autofix = sly_data.get("autofix") or {}

        report = agent_logic.run_reporting(quality_before, quality_after, migration, autofix)
        sly_data["reporting"] = report

        db.log_agent(sly_data["run_id"], "Reporting", json.dumps(report))
        db.finish_run(sly_data["run_id"], "COMPLETED")
        logger.debug(">>>>>>>>>>>>>>>>>> Reporting Agent DONE >>>>>>>>>>>>>>>>>>")
        return json.dumps(report)

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        return self.invoke(args, sly_data)
