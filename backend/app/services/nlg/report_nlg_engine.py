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
        Synchronous section generation is intentionally unsupported.
        `generate_nlg_outputs` is the primary entry point for generating report sections.
        """
        raise NotImplementedError("Synchronous section generation is not supported. Use generate_nlg_outputs.")

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
                code_data = (data.get(data_key[0]) or {}).get("code_metrics", {})
                audit_data = (data.get(data_key[0]) or {}).get(data_key[1], [])
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

    def _empty_llm_content_error(self, section_id: str) -> ValueError:
        return ValueError(f"LLM returned empty content for {section_id}.")

    # The following methods are inherited from BaseNLGEngine and use _generate_section_with_llm.
    async def generate_code_audit_text(self, code_data: Dict[str, Any], audit_data: Any) -> str:
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
                    raise self._empty_llm_content_error("code_audit_summary")
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
                    raise self._empty_llm_content_error("team_documentation")
                return self._format_output({"section_id": "team_documentation", "text": generated_text})
            except Exception as e:
                logger.error(f"Error generating team_documentation text with LLM: {e}", exc_info=True)
                return self._format_output({
                    "section_id": "team_documentation",
                    "text": "Failed to generate team and documentation summary due to an internal error. Please try again later."
                })
