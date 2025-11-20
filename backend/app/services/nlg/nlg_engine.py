import json
from abc import ABC, abstractmethod

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
