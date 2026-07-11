# Copyright © 2025-2026 -- Hackathon submission: Agentic AI Migration Factory
"""
coded_tools/hackathon/agentic_migrator/monitoring_tool.py
CodedTool wrapper for the Monitoring Agent.
"""
import json
import logging
from typing import Any, Dict, Union

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.hackathon.agentic_migrator import agent_logic, db

logger = logging.getLogger(__name__)


class MonitoringTool(CodedTool):
    """
    Watches migration execution for timeouts, API failures, load
    failures, and data mismatches; recommends retry or rollback.
    """

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        logger.debug(">>>>>>>>>>>>>>>>>> Monitoring Agent >>>>>>>>>>>>>>>>>>")
        if "run_id" not in sly_data:
            sly_data["run_id"] = db.new_run()

        migration = sly_data.get("migration") or {}
        validation = sly_data.get("validation") or {}

        report = agent_logic.run_monitoring(migration, validation)
        sly_data["monitoring"] = report

        db.log_agent(sly_data["run_id"], "Monitoring", json.dumps(report["primary_event"]))
        logger.debug(">>>>>>>>>>>>>>>>>> Monitoring Agent DONE >>>>>>>>>>>>>>>>>>")
        return json.dumps(report)

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        return self.invoke(args, sly_data)
