import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict, Any
from backend.app.core.logger import services_logger
from backend.app.services.nlg.llm_client import LLMClient
from backend.app.services.nlg.prompt_templates import get_template, fill_template
from backend.app.security.rate_limiter import rate_limiter

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
        services_logger.info("TeamDocAgent: Starting generate_team_doc_text. Analyzing team and documentation data.")
        summary_parts = []

        async with LLMClient() as client:
            # Summarize Team Roles
            team_roles_prompt = fill_template(
                get_template("team_roles_summary"),
                team_data=json.dumps(team_data, indent=2)
            )
            services_logger.debug("TeamDocAgent: Calling LLM for team roles summary.")
            try:
                team_roles_response = await client.generate_text(team_roles_prompt)
                choices = team_roles_response.get("choices") or []
                content = choices[0].get("message", {}).get("content", "N/A") if choices else "N/A"
                services_logger.info(f"TeamDocAgent: LLM generated team roles summary. Response size: {len(str(team_roles_response))} bytes")
                summary_parts.append("### Team Roles and Responsibilities\n")
                summary_parts.append(content)
            except Exception as e:
                services_logger.error(f"TeamDocAgent: Error generating team roles summary: {e}")
                summary_parts.append("### Team Roles and Responsibilities\n")
                summary_parts.append("N/A (Failed to generate team roles summary)")
            summary_parts.append("\n\n")

            # Summarize Team Experience
            team_experience_prompt = fill_template(
                get_template("team_experience_summary"),
                team_data=json.dumps(team_data, indent=2)
            )
            services_logger.debug("TeamDocAgent: Calling LLM for team experience summary.")
            try:
                team_experience_response = await client.generate_text(team_experience_prompt)
                choices = team_experience_response.get("choices") or []
                content = choices[0].get("message", {}).get("content", "N/A") if choices else "N/A"
                services_logger.info(f"TeamDocAgent: LLM generated team experience summary. Response size: {len(str(team_experience_response))} bytes")
                summary_parts.append("### Team Experience and Expertise\n")
                summary_parts.append(content)
            except Exception as e:
                services_logger.error(f"TeamDocAgent: Error generating team experience summary: {e}")
                summary_parts.append("### Team Experience and Expertise\n")
                summary_parts.append("N/A (Failed to generate team experience summary)")
            summary_parts.append("\n\n")

            # Summarize Team Credibility
            team_credibility_prompt = fill_template(
                get_template("team_credibility_summary"),
                team_data=json.dumps(team_data, indent=2)
            )
            services_logger.debug("TeamDocAgent: Calling LLM for team credibility summary.")
            try:
                team_credibility_response = await client.generate_text(team_credibility_prompt)
                choices = team_credibility_response.get("choices") or []
                content = choices[0].get("message", {}).get("content", "N/A") if choices else "N/A"
                services_logger.info(f"TeamDocAgent: LLM generated team credibility summary. Response size: {len(str(team_credibility_response))} bytes")
                summary_parts.append("### Team Credibility\n")
                summary_parts.append(content)
            except Exception as e:
                services_logger.error(f"TeamDocAgent: Error generating team credibility summary: {e}")
                summary_parts.append("### Team Credibility\n")
                summary_parts.append("N/A (Failed to generate team credibility summary)")
            summary_parts.append("\n\n")

            # Summarize Documentation Strength
            doc_strength_prompt = fill_template(
                get_template("documentation_strength_summary"),
                doc_data=json.dumps(doc_data, indent=2)
            )
            services_logger.debug("TeamDocAgent: Calling LLM for documentation strength summary.")
            try:
                doc_strength_response = await client.generate_text(doc_strength_prompt)
                choices = doc_strength_response.get("choices") or []
                content = choices[0].get("message", {}).get("content", "N/A") if choices else "N/A"
                services_logger.info(f"TeamDocAgent: LLM generated documentation strength summary. Response size: {len(str(doc_strength_response))} bytes")
                summary_parts.append("### Documentation Strength\n")
                summary_parts.append(content)
            except Exception as e:
                services_logger.error(f"TeamDocAgent: Error generating documentation strength summary: {e}")
                summary_parts.append("### Documentation Strength\n")
                summary_parts.append("N/A (Failed to generate documentation strength summary)")
            summary_parts.append("\n\n")
        
        services_logger.info("TeamDocAgent: Completed generate_team_doc_text.")
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
        services_logger.info(f"TeamDocAgent: Starting scrape_team_profiles. URLs: {urls}")
        team_profiles = []
        for url in urls:
            services_logger.debug(f"TeamDocAgent: Checking rate limit for URL: {url}")
            if not rate_limiter.check_rate_limit("team_doc_agent"):
                services_logger.warning(f"TeamDocAgent: Rate limit exceeded for team_doc_agent for URL: {url}. Skipping.")
                team_profiles.append({"url": url, "error": "Rate limit exceeded", "source": url})
                continue
            try:
                services_logger.debug(f"TeamDocAgent: Attempting to scrape URL: {url}")
                response = requests.get(url, timeout=10)
                response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
                services_logger.info(f"TeamDocAgent: Successfully scraped URL: {url}. Response size: {len(response.text)} bytes")
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
                services_logger.error("TeamDocAgent: Error scraping %s: %s", url, e)
                team_profiles.append({
                    "url": url,
                    "error": str(e),
                    "source": url
                })
            except Exception as e:
                services_logger.error("TeamDocAgent: An unexpected error occurred while processing %s: %s", url, e)
                team_profiles.append({
                    "url": url,
                    "error": f"Unexpected error: {e}",
                    "source": url
                })
        services_logger.info("TeamDocAgent: Completed scrape_team_profiles.")
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
        services_logger.info("TeamDocAgent: Starting analyze_whitepaper.")
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
                services_logger.debug("TeamDocAgent: Identified 'Q1 2026' in whitepaper text.")
            if "mainnet launch" in text.lower():
                extracted_data["roadmap_items"].append("Mainnet Launch")
                services_logger.debug("TeamDocAgent: Identified 'mainnet launch' in whitepaper text.")
            if "our vision is" in text.lower():
                start = text.lower().find("our vision is")
                end = text.lower().find(".", start)
                if start != -1 and end != -1:
                    extracted_data["public_statements"].append(text[start:end+1].strip())
                    services_logger.debug("TeamDocAgent: Identified 'our vision is' statement in whitepaper text.")
            services_logger.info("TeamDocAgent: Completed analyze_whitepaper successfully.")
            return extracted_data
        except Exception as e:
            services_logger.error("TeamDocAgent: Error analyzing whitepaper: %s", e)
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