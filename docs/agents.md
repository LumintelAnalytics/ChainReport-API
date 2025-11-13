# Data Acquisition Agents Documentation

This document describes the data acquisition agents within the ChainReport-API, detailing their purpose, functions, expected inputs/outputs, error handling, and integration with the orchestrator. Example API calls and JSON outputs are provided for developers to easily understand and extend these agents.

---

## 1. CodeAuditAgent

**Purpose:**
The `CodeAuditAgent` is responsible for auditing codebases, fetching repository metrics (e.g., commit count, contributors, latest releases, issues, pull requests) from platforms like GitHub and GitLab, and summarizing audit reports.

**Functions:**

*   `fetch_repo_metrics(repo_url: str) -> CodeMetrics`:
    *   **Description:** Fetches various repository metrics from the specified `repo_url`. It supports both GitHub and GitLab repositories.
    *   **Inputs:**
        *   `repo_url` (string): The URL of the repository (e.g., "https://github.com/owner/repo" or "https://gitlab.com/owner/repo").
    *   **Outputs:** A `CodeMetrics` object containing:
        *   `repo_url` (str)
        *   `commits_count` (int)
        *   `contributors_count` (int)
        *   `latest_release` (str)
        *   `lines_of_code` (int, currently a placeholder)
        *   `issues_count` (int)
        *   `pull_requests_count` (int)
    *   **Error Handling:** Logs `httpx.HTTPStatusError`, `httpx.RequestError`, and general `Exception` during API calls. In case of an error, it returns a `CodeMetrics` object with default/empty data.

*   `analyze_code_activity(metrics: CodeMetrics) -> Dict[str, Any]`:
    *   **Description:** Analyzes the provided `CodeMetrics` to determine activity levels, contributor engagement, release frequency, and issues/PRs activity.
    *   **Inputs:**
        *   `metrics` (CodeMetrics object): The metrics obtained from `fetch_repo_metrics`.
    *   **Outputs:** A dictionary summarizing the analysis, including:
        *   `activity_level` (str: "low", "medium", "high")
        *   `contributor_engagement` (str: "low", "medium", "high")
        *   `release_frequency` (str: "low", "present")
        *   `code_quality_indicators` (str: "N/A", placeholder)
        *   `issues_and_prs_activity` (str: "low", "medium", "high")
    *   **Error Handling:** Not explicitly shown, but designed to return default values if metrics are insufficient.

*   `search_and_summarize_audit_reports(project_name: str) -> List[AuditSummary]`:
    *   **Description:** (Placeholder) This function is intended to search for and summarize external audit reports related to a given project.
    *   **Inputs:**
        *   `project_name` (string): The name of the project to search for audit reports.
    *   **Outputs:** A list of `AuditSummary` objects, each containing:
        *   `report_title` (str)
        *   `audit_firm` (str)
        *   `date` (str)
        *   `findings_summary` (str)
        *   `severity_breakdown` (Dict[str, int])
    *   **Error Handling:** Logs general `Exception` and returns an empty list in case of an error.

*   `audit_codebase(repo_url: str, project_name: str) -> CodeAuditResult`:
    *   **Description:** Orchestrates the complete codebase audit process by fetching metrics and summarizing audit reports.
    *   **Inputs:**
        *   `repo_url` (string): The URL of the repository.
        *   `project_name` (string): The name of the project.
    *   **Outputs:** A `CodeAuditResult` object containing:
        *   `code_metrics` (CodeMetrics object)
        *   `audit_summaries` (List[AuditSummary])
    *   **Error Handling:** Logs general `Exception` and returns a `CodeAuditResult` with default/empty data.

**Integration with Orchestrator:**
The `CodeAuditAgent` is designed as an asynchronous context manager. The orchestrator would typically instantiate the agent using `async with CodeAuditAgent() as agent:`, then call methods like `audit_codebase` to retrieve comprehensive audit results.

**Example API Call (Conceptual) and JSON Output:**

```python
# Conceptual orchestrator call
async with CodeAuditAgent() as agent:
    result = await agent.audit_codebase(
        repo_url="https://github.com/example/repo",
        project_name="Example Project"
    )
    # result would be a CodeAuditResult object
```

```json
{
  "code_metrics": {
    "repo_url": "https://github.com/example/repo",
    "commits_count": 1500,
    "contributors_count": 25,
    "latest_release": "v1.2.0",
    "lines_of_code": 0,
    "issues_count": 75,
    "pull_requests_count": 40
  },
  "audit_summaries": [
    {
      "report_title": "Example Project Smart Contract Audit by CertiK",
      "audit_firm": "CertiK",
      "date": "2023-10-26",
      "findings_summary": "Initial audit found several medium-severity reentrancy vulnerabilities and one high-severity access control issue. All issues have been addressed in subsequent patches.",
      "severity_breakdown": {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
        "informational": 5
      }
    }
  ]
}
```

---

## 2. OnchainAgent

**Purpose:**
The `OnchainAgent` is responsible for fetching on-chain metrics and tokenomics data from various external blockchain data APIs. It incorporates robust retry mechanisms and comprehensive error handling to ensure data reliability.

**Functions:**

* `fetch_onchain_metrics(url: str, token_id: str, params: dict | None = None) -> dict`:
  * **Description:** Fetches general on-chain metrics from a specified API endpoint.
  * **Inputs:**
    * `url` (string): The API endpoint URL.
    * `token_id` (string): A unique identifier for request tracing and log correlation.
    * `params` (dict, optional): A dictionary of query parameters to be included in the request.
  * **Outputs:** A dictionary containing the fetched on-chain metrics. The structure depends on the external API.
  * **Error Handling:**
    * `OnchainAgentTimeout`: Raised if the request times out.
    * `OnchainAgentNetworkError`: Raised for network-related errors (e.g., connection issues).
    * `OnchainAgentHTTPError`: Raised if the HTTP response status is not in the 2xx range.
    * `OnchainAgentException`: Raised for other unexpected errors.
    * Uses `tenacity` for retries with exponential backoff on various exceptions.

* `fetch_tokenomics(url: str, token_id: str, params: dict | None = None) -> dict`:
  * **Description:** Fetches tokenomics-specific data from a specified API endpoint.
  * **Inputs:** Same as `fetch_onchain_metrics`.
  * **Outputs:** A dictionary containing the fetched tokenomics data. The structure depends on the external API.
  * **Error Handling:** Same as `fetch_onchain_metrics`.

**Integration with Orchestrator:**
The orchestrator directly calls the asynchronous functions `fetch_onchain_metrics` and `fetch_tokenomics`, providing the necessary API URL, a `token_id` for traceability, and any required query parameters.

**Example API Call (Conceptual) and JSON Output:**

```python
# Conceptual orchestrator call for on-chain metrics
metrics_data = await fetch_onchain_metrics(
    url="https://api.example.com/v1/onchain/metrics",
    token_id="ethereum",
    params={"interval": "24h"}
)

# Conceptual orchestrator call for tokenomics
tokenomics_data = await fetch_tokenomics(
    url="https://api.example.com/v1/tokenomics/data",
    token_id="ethereum"
)
```

```json
{
  "total_transactions_24h": 1200000,
  "active_addresses_24h": 500000,
  "average_transaction_fee_usd": 5.23,
  "defi_tvl_usd": 65000000000,
  "token_id": "ethereum"
}
```

```json
{
  "circulating_supply": "120,000,000 ETH",
  "max_supply": "Unlimited",
  "inflation_rate_annual": "0.5%",
  "staking_ratio": "25%",
  "token_distribution": {
    "community": "40%",
    "team": "20%",
    "treasury": "30%",
    "investors": "10%"
  },
  "token_id": "ethereum"
}
```

---

## 3. PriceAgent

**Purpose:**
The `PriceAgent` is a mock agent designed to simulate fetching price data for a given token. It serves as a placeholder for future integration with real-time price data APIs.

**Functions:**

* `run(report_id: str, token_id: str)`:
  * **Description:** Mocks the retrieval of price data for a specified token.
  * **Inputs:**
    * `report_id` (string): An identifier for the report being generated.
    * `token_id` (string): The identifier of the token for which price data is requested.
  * **Outputs:** A dictionary containing a mock price, along with the input `token_id` and `report_id`.
  * **Error Handling:** Not explicitly implemented in this mock.

**Integration with Orchestrator:**
The orchestrator calls the asynchronous `run` function, passing the `report_id` and `token_id` to obtain mock price information.

**Example API Call (Conceptual) and JSON Output:**

```python
# Conceptual orchestrator call
price_data = await run(report_id="report_abc", token_id="mock_token")
```

```json
{
  "price": 123.45,
  "token_id": "mock_token",
  "report_id": "report_abc"
}
```

---

## 4. SocialSentimentAgent

**Purpose:**
The `SocialSentimentAgent` collects social media data (from sources like Twitter, Reddit, and news aggregators) for a specified token and performs sentiment analysis to gauge community perception.

**Functions:**

*   `fetch_social_data(token_id: str) -> List[Dict[str, Any]]`:
    *   **Description:** Orchestrates the fetching of social media data from various sources for a given `token_id`. (Currently uses mock data for Twitter, Reddit, and News).
    *   **Inputs:**
        *   `token_id` (string): The identifier of the token to search for on social media.
    *   **Outputs:** A list of dictionaries, where each dictionary represents a piece of social data (e.g., a tweet, Reddit post, news snippet) with `source`, `text`, and `id`.
    *   **Error Handling:** Catches `RetryError` from underlying fetch functions (which use `tenacity` for retries on `httpx.RequestError`, `httpx.HTTPStatusError`, `asyncio.TimeoutError`) and logs them.

*   `analyze_sentiment(data: List[Dict[str, Any]]) -> Dict[str, Any]`:
    *   **Description:** Performs sentiment analysis on the collected social data using `TextBlob` and provides an overall sentiment score and breakdown.
    *   **Inputs:**
        *   `data` (List[Dict[str, Any]]): A list of social data items, typically the output from `fetch_social_data`.
    *   **Outputs:** A dictionary containing:
        *   `overall_sentiment` (str: "positive", "neutral", "negative")
        *   `score` (float: average polarity, -1.0 to +1.0)
        *   `details` (List[Dict[str, Any]]): Individual sentiment analysis results for each item, including `source`, `text`, `sentiment`, and `polarity_score`.
    *   **Error Handling:** Returns a "neutral" sentiment with a score of 0.0 if no data is provided for analysis.

**Integration with Orchestrator:**
The orchestrator would instantiate `SocialSentimentAgent`, call `fetch_social_data` with a `token_id`, and then pass the resulting data to `analyze_sentiment` to get the sentiment report.

**Example API Call (Conceptual) and JSON Output:**

```python
# Conceptual orchestrator call
agent = SocialSentimentAgent()
social_data = await agent.fetch_social_data(token_id="ExampleToken")
sentiment_report = await agent.analyze_sentiment(social_data)
```

```json
{
  "overall_sentiment": "neutral",
  "score": 0.0,
  "details": [
    {
      "source": "twitter",
      "text": "Great news about ExampleToken!",
      "sentiment": "positive",
      "polarity_score": 0.5
    },
    {
      "source": "twitter",
      "text": "ExampleToken is a scam.",
      "sentiment": "negative",
      "polarity_score": -0.5
    },
    {
      "source": "reddit",
      "text": "Loving the community around ExampleToken.",
      "sentiment": "positive",
      "polarity_score": 0.6
    },
    {
      "source": "reddit",
      "text": "Is ExampleToken going to zero?",
      "sentiment": "negative",
      "polarity_score": -0.25
    },
    {
      "source": "news",
      "text": "Analyst predicts bright future for ExampleToken.",
      "sentiment": "positive",
      "polarity_score": 0.7
    },
    {
      "source": "news",
      "text": "Concerns raised over ExampleToken security.",
      "sentiment": "negative",
      "polarity_score": -0.3
    }
  ]
}
```

---

## 5. TeamDocAgent

**Purpose:**
The `TeamDocAgent` is designed to scrape and analyze information related to project teams, documentation, and whitepapers. This includes extracting team member profiles and key details from whitepaper content.

**Functions:**

*   `scrape_team_profiles(urls: List[str]) -> List[Dict[str, Any]]`:
    *   **Description:** Scrapes team member profiles from a list of provided URLs. It attempts to extract name, title, biography, and simulates credential verification.
    *   **Inputs:**
        *   `urls` (List[str]): A list of URLs pointing to team member profiles (e.g., LinkedIn, company bio pages).
    *   **Outputs:** A list of dictionaries, each representing a team member's profile with:
        *   `url` (str)
        *   `name` (str)
        *   `title` (str)
        *   `biography` (str)
        *   `credentials_verified` (bool, simulated)
        *   `source` (str)
        *   If an error occurs, the dictionary will contain `url` and `error`.
    *   **Error Handling:** Catches `requests.exceptions.RequestException` for network/HTTP errors and general `Exception`. Logs errors and returns a dictionary with error details for failed URLs.

*   `analyze_whitepaper(text: str) -> Dict[str, Any]`:
    *   **Description:** Analyzes the full text content of a whitepaper to extract project timelines, roadmap items, and public statements. (Currently uses keyword-based simulation).
    *   **Inputs:**
        *   `text` (string): The complete text content of the whitepaper.
    *   **Outputs:** A dictionary containing:
        *   `project_timelines` (List[Dict[str, str]])
        *   `roadmap_items` (List[str])
        *   `public_statements` (List[str])
        *   `analysis_summary` (str)
    *   **Error Handling:** Catches general `Exception`, logs it, and returns an error-filled dictionary.

**Integration with Orchestrator:**
The orchestrator would instantiate `TeamDocAgent`, call `scrape_team_profiles` with relevant URLs, and `analyze_whitepaper` with the whitepaper content (which might be obtained from another agent or direct input).

**Example API Call (Conceptual) and JSON Output:**

```python
# Conceptual orchestrator call for scraping team profiles
agent = TeamDocAgent()
team_urls = ["http://example.com/team-member-1", "http://example.com/team-member-2"]
profiles = agent.scrape_team_profiles(team_urls)

# Conceptual orchestrator call for whitepaper analysis
whitepaper_text = "..." # Full text of the whitepaper
whitepaper_analysis = agent.analyze_whitepaper(whitepaper_text)
```

```json
[
  {
    "url": "http://example.com/team-member-1",
    "name": "John Doe",
    "title": "CEO",
    "biography": "Experienced leader in blockchain.",
    "credentials_verified": true,
    "source": "http://example.com/team-member-1"
  },
  {
    "url": "http://example.com/team-member-2",
    "name": "Jane Smith",
    "title": "CTO",
    "biography": "Innovator in smart contract development.",
    "credentials_verified": true,
    "source": "http://example.com/team-member-2"
  }
]
```

```json
{
  "project_timelines": [
    {
      "event": "Phase 1 Completion",
      "date": "Q1 2026"
    }
  ],
  "roadmap_items": [
    "Mainnet Launch",
    "Smart Contract Audits",
    "Community Governance Implementation"
  ],
  "public_statements": [
    "Our vision is to revolutionize decentralized finance."
  ],
  "analysis_summary": "Analysis performed based on keywords."
}
```

---

## 6. TrendAgent

**Purpose:**
The `TrendAgent` is a mock agent designed to simulate fetching trend data for a given token. It serves as a placeholder for future integration with real-time market trend APIs.

**Functions:**

*   `run(report_id: str, token_id: str)`:
    *   **Description:** Mocks the retrieval of trend data for a specified token.
    *   **Inputs:**
        *   `report_id` (string): An identifier for the report being generated.
        *   `token_id` (string): The identifier of the token for which trend data is requested.
    *   **Outputs:** A dictionary containing a mock trend, 24-hour change, and the input `token_id` and `report_id`.
    *   **Error Handling:** Not explicitly implemented in this mock.

**Integration with Orchestrator:**
The orchestrator calls the asynchronous `run` function, passing the `report_id` and `token_id` to obtain mock trend information.

**Example API Call (Conceptual) and JSON Output:**

```python
# Conceptual orchestrator call
trend_data = await run(report_id="report_xyz", token_id="mock_token_trend")
```

```json
{
  "trend": "up",
  "change_24h": 5.67,
  "token_id": "mock_token_trend",
  "report_id": "report_xyz"
}
```

---

## 7. VolumeAgent

**Purpose:**
The `VolumeAgent` is a mock agent designed to simulate fetching trading volume data for a given token. It serves as a placeholder for future integration with real-time exchange volume APIs.

**Functions:**

*   `run(report_id: str, token_id: str)`:
    *   **Description:** Mocks the retrieval of trading volume data for a specified token.
    *   **Inputs:**
        *   `report_id` (string): An identifier for the report being generated.
        *   `token_id` (string): The identifier of the token for which volume data is requested.
    *   **Outputs:** A dictionary containing a mock volume, along with the input `token_id` and `report_id`.
    *   **Error Handling:** Not explicitly implemented in this mock.

**Integration with Orchestrator:**
The orchestrator calls the asynchronous `run` function, passing the `report_id` and `token_id` to obtain mock volume information.

**Example API Call (Conceptual) and JSON Output:**

```python
# Conceptual orchestrator call
volume_data = await run(report_id="report_uvw", token_id="mock_token_volume")
```

```json
{
  "volume": 987654.32,
  "token_id": "mock_token_volume",
  "report_id": "report_uvw"
}
```
