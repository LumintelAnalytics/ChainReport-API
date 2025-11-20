import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

from backend.app.services.nlg.llm_client import LLMClient
from backend.app.services.nlg.prompt_templates import get_template, fill_template

logger = logging.getLogger(__name__)

class NLGEngine(ABC):
    """
    Base class for Natural Language Generation (NLG) engines.
    Defines the interface for generating text sections and full reports,
    with a structure prepared for plugging in various LLM providers.
    """

    @abstractmethod
    def generate_section_text(self, section_id: str, raw_data: dict) -> str:
        """
        Generates natural language text for a specific report section based on raw data.

        Args:
            section_id (str): The identifier for the report section (e.g., "executive_summary", "market_trends").
            raw_data (dict): The raw data pertinent to the section, used as context for generation.

        Returns:
            str: A JSON-formatted string containing the generated text and metadata.
                  Example: `return self._format_output({"section_id": "executive_summary", "text": "Generated summary text."})`
        """
        pass

    @abstractmethod
    def generate_full_report(self, data: dict) -> str:
        """
        Generates a complete natural language report based on a comprehensive data structure.

        Args:
            data (dict): A dictionary containing all necessary data for generating the full report.

        Returns:
            str: A JSON-formatted string representing the full generated report,
                  structured with sections and their respective texts.
                  Example: `return self._format_output({"report_title": "...", "sections": [{"section_id": "...", "text": "..."}]})`
        """
        pass

    def _format_output(self, content: dict) -> str:
        """
        Helper method to ensure all outputs are structured as JSON.
        """
        return json.dumps(content)

    async def _generate_section_with_llm(self, section_id: str, data: Dict[str, Any], not_available_msg: str, error_msg: str) -> str:
        if not data:
            return self._format_output({
                "section_id": section_id,
                "text": not_available_msg
            })

        template = get_template(section_id)
        prompt = fill_template(template, data=json.dumps(data, indent=2))

        async with LLMClient() as llm_client:
            try:
                response = await llm_client.generate_text(prompt)
                generated_text = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if not generated_text:
                    raise ValueError(f"LLM returned empty content for {section_id}.")
                return self._format_output({"section_id": section_id, "text": generated_text})
            except Exception as e:
                logger.error(f"Error generating {section_id} text with LLM: {e}", exc_info=True)
                return self._format_output({
                    "section_id": section_id,
                    "text": error_msg
                })

    async def generate_tokenomics_text(self, raw_data: Dict[str, Any]) -> str:
        """
        Generates natural language text for tokenomics based on raw data.
        Includes fallback logic for missing data.
        """
        if not raw_data:
            return self._format_output({
                "section_id": "tokenomics",
                "text": "Tokenomics data is not available at this time. Please check back later for updates."
            })
        return await self._generate_section_with_llm(
            section_id="tokenomics",
            data=raw_data,
            not_available_msg="Tokenomics data is not available at this time. Please check back later for updates.",
            error_msg="Failed to generate tokenomics summary due to an internal error. Please try again later."
        )

    async def generate_onchain_text(self, raw_data: Dict[str, Any]) -> str:
        """
        Generates natural language text for on-chain metrics based on raw data.
        Collects metrics like active addresses, holders, transaction flows, and liquidity
        and converts them into narrative form using the LLM. Handles incomplete fields safely.
        """
        if not raw_data:
            return self._format_output({
                "section_id": "onchain_metrics",
                "text": "On-chain metrics data is not available at this time. Please check back later for updates."
            })

        # Extract relevant metrics, handling potential missing fields safely
        onchain_metrics_data = {
            "active_addresses": raw_data.get("active_addresses", "N/A"),
            "holders": raw_data.get("holders", "N/A"),
            "transaction_flows": raw_data.get("transaction_flows", "N/A"),
            "liquidity": raw_data.get("liquidity", "N/A"),
        }

        return await self._generate_section_with_llm(
            section_id="onchain_metrics",
            data=onchain_metrics_data,
            not_available_msg="On-chain metrics data is not available at this time. Please check back later for updates.",
            error_msg="Failed to generate on-chain metrics summary due to an internal error. Please try again later."
        )

