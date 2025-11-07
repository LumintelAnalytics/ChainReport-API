import pytest
from unittest.mock import Mock, patch
from backend.app.services.agents.team_doc_agent import TeamDocAgent
import requests

# Mock response for requests.get
class MockResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"HTTP Error: {self.status_code}")

@pytest.fixture
def team_doc_agent():
    return TeamDocAgent()

def test_analyze_whitepaper_full_content(team_doc_agent):
    sample_whitepaper_text = """
    This is a sample whitepaper. Our vision is to revolutionize decentralized finance.
    The project timeline includes a testnet launch in Q4 2025 and mainnet launch in Q1 2026.
    Roadmap items include smart contract audits and community governance implementation.
    We believe in a future where financial services are accessible to everyone.
    Our vision is also to empower users with financial freedom.
    """
    analysis = team_doc_agent.analyze_whitepaper(sample_whitepaper_text)

    expected_timelines = [{'event': 'Phase 1 Completion', 'date': 'Q1 2026'}]
    expected_roadmap = ['Mainnet Launch']
    expected_statements = [
        'Our vision is to revolutionize decentralized finance.'
    ]

    assert analysis["project_timelines"] == expected_timelines
    assert analysis["roadmap_items"] == expected_roadmap
    assert analysis["public_statements"] == expected_statements
    assert "analysis_summary" in analysis

def test_analyze_whitepaper_partial_content(team_doc_agent):
    sample_whitepaper_text = """
    This whitepaper only mentions a mainnet launch.
    """
    analysis = team_doc_agent.analyze_whitepaper(sample_whitepaper_text)

    assert analysis["project_timelines"] == []
    assert analysis["roadmap_items"] == ['Mainnet Launch']
    assert analysis["public_statements"] == []

def test_analyze_whitepaper_no_content(team_doc_agent):
    sample_whitepaper_text = """
    This is some random text without any keywords.
    """
    analysis = team_doc_agent.analyze_whitepaper(sample_whitepaper_text)

    assert analysis["project_timelines"] == []
    assert analysis["roadmap_items"] == []
    assert analysis["public_statements"] == []

def test_analyze_whitepaper_public_statement_no_period(team_doc_agent):
    sample_whitepaper_text = """
    Our vision is a better world
    """
    analysis = team_doc_agent.analyze_whitepaper(sample_whitepaper_text)

    assert analysis["public_statements"] == [] # Should not extract if no period is found

@patch('backend.app.services.agents.team_doc_agent.requests.get')
def test_scrape_team_profiles_success(mock_get, team_doc_agent):
    mock_html = """
    <html>
        <body>
            <h1 class="profile-name">John Doe</h1>
            <p class="profile-title">Software Engineer</p>
            <div class="profile-bio">John is an experienced engineer.</div>
        </body>
    </html>
    """
    mock_get.return_value = MockResponse(mock_html)

    urls = ["http://example.com/team/john-doe"]
    profiles = team_doc_agent.scrape_team_profiles(urls)

    expected_profiles = [
        {
            "url": "http://example.com/team/john-doe",
            "name": "John Doe",
            "title": "Software Engineer",
            "biography": "John is an experienced engineer.",
            "credentials_verified": True,
            "source": "http://example.com/team/john-doe"
        }
    ]
    assert profiles == expected_profiles
    mock_get.assert_called_once_with(urls[0], timeout=10)

@patch('backend.app.services.agents.team_doc_agent.requests.get')
def test_scrape_team_profiles_missing_elements(mock_get, team_doc_agent):
    mock_html = """
    <html>
        <body>
            <h1>Just a title, no class</h1>
            <div class="profile-bio">A bio without a name or title.</div>
        </body>
    </html>
    """
    mock_get.return_value = MockResponse(mock_html)

    urls = ["http://example.com/team/no-name"]
    profiles = team_doc_agent.scrape_team_profiles(urls)

    expected_profiles = [
        {
            "url": "http://example.com/team/no-name",
            "name": "N/A",
            "title": "N/A",
            "biography": "A bio without a name or title.",
            "credentials_verified": True,
            "source": "http://example.com/team/no-name"
        }
    ]
    assert profiles == expected_profiles

@patch('backend.app.services.agents.team_doc_agent.requests.get')
def test_scrape_team_profiles_http_error(mock_get, team_doc_agent):
    mock_get.return_value = MockResponse("Not Found", status_code=404)

    urls = ["http://example.com/team/404"]
    profiles = team_doc_agent.scrape_team_profiles(urls)

    assert len(profiles) == 1
    assert profiles[0]["url"] == urls[0]
    assert "error" in profiles[0]
    assert "HTTP Error: 404" in profiles[0]["error"]

@patch('backend.app.services.agents.team_doc_agent.requests.get')
def test_scrape_team_profiles_connection_error(mock_get, team_doc_agent):
    mock_get.side_effect = requests.exceptions.ConnectionError("Network is unreachable")

    urls = ["http://example.com/team/network-error"]
    profiles = team_doc_agent.scrape_team_profiles(urls)

    assert len(profiles) == 1
    assert profiles[0]["url"] == urls[0]
    assert "error" in profiles[0]
    assert "Network is unreachable" in profiles[0]["error"]

@patch('backend.app.services.agents.team_doc_agent.requests.get')
def test_scrape_team_profiles_multiple_urls(mock_get, team_doc_agent):
    mock_html_success = """
    <html>
        <body>
            <h1 class="profile-name">Jane Doe</h1>
            <p class="profile-title">Project Manager</p>
            <div class="profile-bio">Jane manages projects.</div>
        </body>
    </html>
    """
    mock_get.side_effect = [
        MockResponse(mock_html_success),
        MockResponse("Not Found", status_code=404),
        requests.exceptions.ConnectionError("Connection refused")
    ]

    urls = [
        "http://example.com/team/jane-doe",
        "http://example.com/team/404",
        "http://example.com/team/connection-refused"
    ]
    profiles = team_doc_agent.scrape_team_profiles(urls)

    assert len(profiles) == 3

    assert profiles[0]["name"] == "Jane Doe"
    assert profiles[0]["title"] == "Project Manager"

    assert "error" in profiles[1]
    assert "HTTP Error: 404" in profiles[1]["error"]

    assert "error" in profiles[2]
    assert "Connection refused" in profiles[2]["error"]
