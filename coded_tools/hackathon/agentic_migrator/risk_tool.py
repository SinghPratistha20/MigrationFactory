# Copyright © 2025-2026 -- Hackathon submission: Agentic AI Migration Factory
"""
coded_tools/hackathon/agentic_migrator/risk_tool.py
CodedTool wrapper for the Risk Assessment Agent.
"""
import json
import logging
from typing import Any, Dict, Union

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.hackathon.agentic_migrator import agent_logic, db

logger = logging.getLogger(__name__)


class RiskTool(CodedTool):
    """
    Analyzes migration readiness (data quality, unmapped fields, data
    volume) and predicts a migration risk score and level.
    """

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        logger.debug(">>>>>>>>>>>>>>>>>> Risk Agent >>>>>>>>>>>>>>>>>>")
        if "run_id" not in sly_data:
            sly_data["run_id"] = db.new_run()

        quality_after = sly_data.get("quality_after") or sly_data.get("quality_before") or {}
        mapping = sly_data.get("mapping") or {}
        discovery = sly_data.get("discovery") or {}

        report = agent_logic.run_risk(quality_after, mapping, discovery)
        sly_data["risk"] = report

        db.log_agent(sly_data["run_id"], "Risk", json.dumps(report))
        logger.debug(">>>>>>>>>>>>>>>>>> Risk Agent DONE >>>>>>>>>>>>>>>>>>")
        return json.dumps(report)

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        return self.invoke(args, sly_data)
