import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict, Any
from backend.app.core.logger import orchestrator_logger
from backend.app.services.nlg.llm_client import LLMClient
from backend.app.services.nlg.prompt_templates import get_template, fill_template
import asyncio

class TeamDocAgent:
    """
    Agent for scraping team information, project documentation, and whitepaper details.
    """

    async def generate_team_doc_text(self, team_data: List[Dict[str, Any]], doc_data: Dict[str, Any]) -> str:
        """
        Summarizes team roles, experience, credibility, and documentation strength
        using LLM prompts to turn scraped text into a readable analysis.

        Args:
            team_data: A list of dictionaries, each representing a team member's profile.
            doc_data: A dictionary containing extracted whitepaper/documentation details.

        Returns:
            A structured string containing the summarized analysis.
        """
        orchestrator_logger.info("Generating team and documentation analysis using LLM.")
        summary_parts = []

        async with LLMClient() as client:
            # Summarize Team Roles
            team_roles_prompt = fill_template(
                get_template("team_roles_summary"),
                team_data=json.dumps(team_data, indent=2)
            )
            team_roles_response = await client.generate_text(team_roles_prompt)
            summary_parts.append("### Team Roles and Responsibilities\n")
            summary_parts.append(team_roles_response.get("choices", [{}])[0].get("message", {}).get("content", "N/A"))
            summary_parts.append("\n\n")

            # Summarize Team Experience
            team_experience_prompt = fill_template(
                get_template("team_experience_summary"),
                team_data=json.dumps(team_data, indent=2)
            )
            team_experience_response = await client.generate_text(team_experience_prompt)
            summary_parts.append("### Team Experience and Expertise\n")
            summary_parts.append(team_experience_response.get("choices", [{}])[0].get("message", {}).get("content", "N/A"))
            summary_parts.append("\n\n")

            # Summarize Team Credibility
            team_credibility_prompt = fill_template(
                get_template("team_credibility_summary"),
                team_data=json.dumps(team_data, indent=2)
            )
            team_credibility_response = await client.generate_text(team_credibility_prompt)
            summary_parts.append("### Team Credibility\n")
            summary_parts.append(team_credibility_response.get("choices", [{}])[0].get("message", {}).get("content", "N/A"))
            summary_parts.append("\n\n")

            # Summarize Documentation Strength
            doc_strength_prompt = fill_template(
                get_template("documentation_strength_summary"),
                doc_data=json.dumps(doc_data, indent=2)
            )
            doc_strength_response = await client.generate_text(doc_strength_prompt)
            summary_parts.append("### Documentation Strength\n")
            summary_parts.append(doc_strength_response.get("choices", [{}])[0].get("message", {}).get("content", "N/A"))
            summary_parts.append("\n\n")

        return "".join(summary_parts)

    def scrape_team_profiles(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Scrapes team profiles from provided URLs (e.g., LinkedIn, company bio pages).
        Extracts name, title, biography, and verifies credentials (simulated).

        Args:
            urls: A list of URLs to scrape for team profiles.

        Returns:
            A list of dictionaries, each representing a team member's profile in JSON format.
        """
        team_profiles = []
        for url in urls:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
                soup = BeautifulSoup(response.text, 'html.parser')

                # Placeholder for actual scraping logic
                # In a real scenario, you would parse the HTML to extract specific data
                name = soup.find('h1', class_='profile-name')
                title = soup.find('p', class_='profile-title')
                bio = soup.find('div', class_='profile-bio')

                team_profiles.append({
                    "url": url,
                    "name": name.text.strip() if name else "N/A",
                    "title": title.text.strip() if title else "N/A",
                    "biography": bio.text.strip() if bio else "No biography found.",
                    "credentials_verified": True,  # Simulated verification
                    "source": url
                })
            except requests.exceptions.RequestException as e:
                orchestrator_logger.error("Error scraping %s: %s", url, e)
                team_profiles.append({
                    "url": url,
                    "error": str(e),
                    "source": url
                })
            except Exception as e:
                orchestrator_logger.error("An unexpected error occurred while processing %s: %s", url, e)
                team_profiles.append({
                    "url": url,
                    "error": f"Unexpected error: {e}",
                    "source": url
                })
        return team_profiles

    def analyze_whitepaper(self, text: str) -> Dict[str, Any]:
        """
        Analyzes the provided whitepaper text to extract project timelines,
        roadmap items, and public statements.

        Args:
            text: The full text content of the whitepaper.

        Returns:
            A dictionary containing extracted whitepaper details in JSON format.
        """
        try:
            # Placeholder for actual NLP/text analysis logic
            # In a real scenario, you would use NLP techniques to extract information
            extracted_data = {
                "project_timelines": [],
                "roadmap_items": [],
                "public_statements": [],
                "analysis_summary": "No specific analysis performed yet. This is a placeholder."
            }

            # Simulate extraction based on keywords or patterns
            if "Q1 2026" in text:
                extracted_data["project_timelines"].append({"event": "Phase 1 Completion", "date": "Q1 2026"})
            if "mainnet launch" in text.lower():
                extracted_data["roadmap_items"].append("Mainnet Launch")
            if "our vision is" in text.lower():
                start = text.lower().find("our vision is")
                end = text.lower().find(".", start)
                if start != -1 and end != -1:
                    extracted_data["public_statements"].append(text[start:end+1].strip())

            return extracted_data
        except Exception as e:
            orchestrator_logger.error("Error analyzing whitepaper: %s", e)
            return {
                "project_timelines": [],
                "roadmap_items": [],
                "public_statements": [],
                "analysis_summary": f"Error during whitepaper analysis: {e}"
            }

if __name__ == "__main__":
    agent = TeamDocAgent()

    # Example Usage for scrape_team_profiles
    print("--- Scraping Team Profiles ---")
    # Using a placeholder URL as actual LinkedIn scraping requires authentication and is complex
    # For demonstration, this will likely return "N/A" for name, title, bio unless the URL
    # points to a simple HTML page with those specific class names.
    team_urls = ["http://example.com/team-member-1", "http://example.com/team-member-2"]
    profiles = agent.scrape_team_profiles(team_urls)
    print(json.dumps(profiles, indent=4))

    print("\n--- Analyzing Whitepaper ---")
    sample_whitepaper_text = """
    This is a sample whitepaper. Our vision is to revolutionize decentralized finance.
    The project timeline includes a testnet launch in Q4 2025 and mainnet launch in Q2 2026.
    Roadmap items include smart contract audits and community governance implementation.
    We believe in a future where financial services are accessible to everyone.
    """
    whitepaper_analysis = agent.analyze_whitepaper(sample_whitepaper_text)
    print(json.dumps(whitepaper_analysis, indent=4))