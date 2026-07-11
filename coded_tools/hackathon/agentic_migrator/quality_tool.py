# Copyright © 2025-2026 -- Hackathon submission: Agentic AI Migration Factory
"""
coded_tools/hackathon/agentic_migrator/quality_tool.py
CodedTool wrapper for the Data Quality Agent.
"""
import json
import logging
from typing import Any, Dict, Union

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.hackathon.agentic_migrator import agent_logic, db

logger = logging.getLogger(__name__)


class QualityTool(CodedTool):
    """
    Reviews ECC data for duplicate vendors/customers, missing GST/emails,
    invalid GL accounts, and missing cost centers. Produces a quality score.
    """

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        logger.debug(">>>>>>>>>>>>>>>>>> Quality Agent >>>>>>>>>>>>>>>>>>")
        if "run_id" not in sly_data:
            sly_data["run_id"] = db.new_run()

        raw_data = sly_data.get("raw_data") or agent_logic.load_source_data(args.get("data_dir") or agent_logic.DATA_DIR)
        sly_data["raw_data"] = raw_data

        report = agent_logic.run_quality(raw_data)
        sly_data["quality_before"] = report
        db.log_agent(sly_data["run_id"], "Quality", json.dumps(report))
        logger.debug(">>>>>>>>>>>>>>>>>> Quality Agent DONE >>>>>>>>>>>>>>>>>>")
        return json.dumps(report)

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        return self.invoke(args, sly_data)
