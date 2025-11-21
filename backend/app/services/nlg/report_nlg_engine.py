import asyncio
import json
import logging
from typing import Dict, Any

from backend.app.services.nlg.llm_client import LLMClient
from backend.app.services.nlg.prompt_templates import get_template, fill_template
from backend.app.services.nlg.nlg_engine import NLGEngine as BaseNLGEngine # Alias to avoid name collision

logger = logging.getLogger(__name__)

class ReportNLGEngine(BaseNLGEngine):
    """
    Concrete implementation of the NLGEngine for generating report sections.
    """

    def generate_section_text(self, section_id: str, raw_data: dict) -> str:
        """
        Generates natural language text for a specific report section based on raw data.
        This method is abstract in the base class and needs to be implemented.
        For simplicity, it will delegate to the async _generate_section_with_llm.
        """
        # This method is synchronous, but _generate_section_with_llm is async.
        # In a real application, you might want to refactor generate_section_text
        # to be async or handle the async call differently if it's called from a sync context.
        # For now, we'll assume it's called in an async context or can be awaited.
        # However, the orchestrator expects an async method for generate_nlg_outputs.
        # So, we'll make generate_nlg_outputs the primary entry point.
        raise NotImplementedError("generate_section_text should not be called directly. Use generate_nlg_outputs.")

    async def generate_nlg_outputs(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generates natural language outputs for various sections of the report.
        This method will call the specific section generation methods and return
        a dictionary of section_id to generated text.
        """
        nlg_outputs = {}

        # Define sections and their corresponding data keys and generator methods
        sections_to_generate = [
            {"section_id": "tokenomics", "data_key": "tokenomics", "generator": self.generate_tokenomics_text},
            {"section_id": "onchain_metrics", "data_key": "onchain_metrics", "generator": self.generate_onchain_text},
            {"section_id": "social_sentiment", "data_key": "social_sentiment", "generator": self.generate_sentiment_text},
            {"section_id": "code_audit_summary", "data_key": ["code_audit", "audit_summary"], "generator": self.generate_code_audit_text}, # code_audit_text takes two args
            {"section_id": "team_documentation", "data_key": "team_documentation", "generator": self.generate_team_documentation_text},
        ]

        tasks = []
        for section_info in sections_to_generate:
            section_id = section_info["section_id"]
            data_key = section_info["data_key"]
            generator = section_info["generator"]

            if isinstance(data_key, list): # For methods that take multiple data arguments
                # Assuming data_key[0] maps to code_audit.code_metrics and data_key[1] maps to code_audit.audit_summary
                code_data = data.get(data_key[0], {}).get("code_metrics", {})
                audit_data = data.get(data_key[0], {}).get(data_key[1], [])
                tasks.append(asyncio.create_task(generator(code_data, audit_data)))
            else:
                section_data = data.get(data_key, {})
                tasks.append(asyncio.create_task(generator(section_data)))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            section_id = sections_to_generate[i]["section_id"]
            if isinstance(result, Exception):
                logger.error(f"Error generating {section_id} section: {result}", exc_info=True)
                nlg_outputs[section_id] = f"Failed to generate {section_id} summary due to an internal error."
            else:
                try:
                    # Assuming the generator methods return a JSON string with "text" key
                    parsed_result = json.loads(result)
                    nlg_outputs[section_id] = parsed_result.get("text", f"No text generated for {section_id}.")
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decoding error for {section_id} section: {e}. Raw result: {result}", exc_info=True)
                    nlg_outputs[section_id] = f"Failed to parse {section_id} summary due to an internal error."

        return nlg_outputs

    # The following methods are copied from the base NLGEngine,
    # as they are concrete implementations that use _generate_section_with_llm.
    # In a more complex scenario, these might be moved to a utility or a mixin.

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

    async def generate_team_documentation_text(self, raw_data: Dict[str, Any]) -> str:
        """
        Generates natural language text for team and documentation based on raw data.
        """
        if not raw_data:
            return self._format_output({
                "section_id": "team_documentation",
                "text": "Team and documentation data is not available at this time. Please check back later for updates."
            })

        # Assuming raw_data contains 'team_analysis' and 'whitepaper_summary'
        team_analysis = raw_data.get("team_analysis", [])
        whitepaper_summary = raw_data.get("whitepaper_summary", {})

        combined_data = {
            "team_analysis": json.dumps(team_analysis, indent=2) if team_analysis else "N/A",
            "whitepaper_summary": json.dumps(whitepaper_summary, indent=2) if whitepaper_summary else "N/A",
        }

        template = get_template("team_documentation")
        prompt = fill_template(template, **combined_data)

        async with LLMClient() as llm_client:
            try:
                response = await llm_client.generate_text(prompt)
                generated_text = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if not generated_text:
                    raise ValueError("LLM returned empty content for team_documentation.")
                return self._format_output({"section_id": "team_documentation", "text": generated_text})
            except Exception as e:
                logger.error(f"Error generating team_documentation text with LLM: {e}", exc_info=True)
                return self._format_output({
                    "section_id": "team_documentation",
                    "text": "Failed to generate team and documentation summary due to an internal error. Please try again later."
                })
