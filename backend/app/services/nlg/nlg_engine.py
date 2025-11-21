import asyncio
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

    async def generate_full_report(self, data: dict) -> str:
        """
        Generates a complete natural language report based on a comprehensive data structure.
        Gathers text outputs from all section generators and merges them into a final multi-section narrative.

        Args:
            data (dict): A dictionary containing all necessary data for generating the full report.

        Returns:
            str: A JSON-formatted string representing the full generated report,
                  structured with sections and their respective texts.
                  Example: `return self._format_output({"report_title": "...", "sections": [{"section_id": "...", "text": "..."}]})`
        """
        sections_to_generate = [
            {
                "section_id": "tokenomics",
                "generator": self.generate_tokenomics_text,
                "data": data.get("tokenomics_data", {}),
                "fallback": {"section_id": "tokenomics", "text": "Failed to generate tokenomics summary due to an internal error."}
            },
            {
                "section_id": "onchain_metrics",
                "generator": self.generate_onchain_text,
                "data": data.get("onchain_data", {}),
                "fallback": {"section_id": "onchain_metrics", "text": "Failed to generate on-chain metrics summary due to an internal error."}
            },
            {
                "section_id": "social_sentiment",
                "generator": self.generate_sentiment_text,
                "data": data.get("sentiment_data", {}),
                "fallback": {"section_id": "social_sentiment", "text": "Failed to generate social sentiment summary due to an internal error."}
            },
            {
                "section_id": "code_audit_summary",
                "generator": self.generate_code_audit_text,
                "data": (data.get("code_data", {}), data.get("audit_data", {})), # Pass as tuple for multiple args
                "fallback": {"section_id": "code_audit_summary", "text": "Failed to generate code audit summary due to an internal error."}
            },
        ]

        tasks = []
        for section_info in sections_to_generate:
            if section_info["section_id"] == "code_audit_summary":
                # Handle code_audit_summary with two arguments
                tasks.append(asyncio.create_task(section_info["generator"](*section_info["data"])))
            else:
                tasks.append(asyncio.create_task(section_info["generator"](section_info["data"])))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        sections = []
        for i, result in enumerate(results):
            section_info = sections_to_generate[i]
            section_id = section_info["section_id"]
            fallback_dict = section_info["fallback"]

            if isinstance(result, Exception):
                logger.error(f"Error generating {section_id} section: {result}", exc_info=True)
                sections.append(fallback_dict)
            else:
                try:
                    sections.append(json.loads(result))
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decoding error for {section_id} section: {e}. Raw result: {result}", exc_info=True)
                    sections.append(fallback_dict)

        return self._format_output({"sections": sections})

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
        if not raw_data or raw_data.get("status") == "failed":
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

    async def generate_sentiment_text(self, raw_data: Dict[str, Any]) -> str:
        """
        Generates natural language text for social sentiment based on raw data.
        Converts sentiment scores and community perception into a written summary,
        highlighting trends and community direction.
        """
        return await self._generate_section_with_llm(
            section_id="social_sentiment",
            data=raw_data,
            not_available_msg="Social sentiment data is not available at this time. Please check back later for updates.",
            error_msg="Failed to generate social sentiment summary due to an internal error. Please try again later."
        )

    async def generate_code_audit_text(self, code_data: Dict[str, Any], audit_data: Dict[str, Any]) -> str:
        """
        Generates a comprehensive code audit summary using LLM prompts.
        Includes clarity points, risk highlights, code activity, and repository quality indicators.
        Handles missing audit information gracefully.
        """
        if not code_data and not audit_data:
            return self._format_output({
                "section_id": "code_audit_summary",
                "text": "Code audit and repository data are not available at this time. Please check back later for updates."
            })

        # Combine data for the prompt, handling potentially missing parts
        combined_data = {
            "code_data": json.dumps(code_data, indent=2) if code_data else "N/A",
            "audit_data": json.dumps(audit_data, indent=2) if audit_data else "N/A",
        }

        template = get_template("code_audit_summary")
        prompt = fill_template(template, **combined_data)

        async with LLMClient() as llm_client:
            try:
                response = await llm_client.generate_text(prompt)
                generated_text = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if not generated_text:
                    raise ValueError("LLM returned empty content for code_audit_summary.")
                return self._format_output({"section_id": "code_audit_summary", "text": generated_text})
            except Exception as e:
                logger.error(f"Error generating code_audit_summary text with LLM: {e}", exc_info=True)
                return self._format_output({
                    "section_id": "code_audit_summary",
                    "text": "Failed to generate code audit summary due to an internal error. Please try again later."
                })

