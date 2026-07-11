# Copyright © 2025-2026 -- Hackathon submission: Agentic AI Migration Factory
"""
coded_tools/hackathon/agentic_migrator/discovery_tool.py
CodedTool wrapper for the Discovery Agent.
"""
import json
import logging
from typing import Any, Dict, Union

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.hackathon.agentic_migrator import agent_logic, db

logger = logging.getLogger(__name__)


class DiscoveryTool(CodedTool):
    """
    Analyzes uploaded ECC datasets: table/record counts, master vs
    transaction data, duplicate entities, and a complexity score.
    """

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        :param args: Optional key "data_dir" overriding the default sample-data folder.
        :param sly_data: Shared run state. Populates "run_id", "raw_data", "discovery".
        :return: JSON string with the discovery report.
        """
        logger.debug(">>>>>>>>>>>>>>>>>> Discovery Agent >>>>>>>>>>>>>>>>>>")
        if "run_id" not in sly_data:
            sly_data["run_id"] = db.new_run()

        data_dir = args.get("data_dir") or agent_logic.DATA_DIR
        raw_data = agent_logic.load_source_data(data_dir)
        sly_data["raw_data"] = raw_data

        report = agent_logic.run_discovery(raw_data)
        sly_data["discovery"] = report
        db.log_agent(sly_data["run_id"], "Discovery", json.dumps(report))
        logger.debug(">>>>>>>>>>>>>>>>>> Discovery Agent DONE >>>>>>>>>>>>>>>>>>")
        return json.dumps(report)

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        return self.invoke(args, sly_data)
