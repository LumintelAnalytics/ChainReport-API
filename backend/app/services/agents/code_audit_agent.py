import os
import re
import logging
import json
from typing import Dict, Any, List
import httpx
from pydantic import BaseModel, Field
import urllib.parse
from backend.app.security.rate_limiter import rate_limiter
from backend.app.utils.cache_utils import cache_request

logger = logging.getLogger(__name__)

def serialize_httpx_response(response: httpx.Response) -> str:
    """Serializes an httpx.Response object to a JSON string."""
    return json.dumps({
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "text": response.text,
    })

def deserialize_httpx_response(data_str: str) -> httpx.Response:
    """Deserializes a JSON string back into a mock httpx.Response object."""
    data = json.loads(data_str)

    class MockResponse:
        def __init__(self, status_code, headers, text):
            self.status_code = status_code
            self.headers = headers
            self.text = text

        def json(self):
            # Attempt to parse text as JSON, return empty dict if not valid JSON
            try:
                return json.loads(self.text)
            except json.JSONDecodeError:
                return {}

        def raise_for_status(self):
            if self.status_code >= 400:
                # Create a dummy request for the HTTPStatusError
                request = httpx.Request("GET", "http://mock.url/error")
                raise httpx.HTTPStatusError(
                    f"Bad response: {self.status_code}", request=request, response=self
                )

    return MockResponse(data["status_code"], data["headers"], data["text"])

class CommitActivity(BaseModel):
    total: int
    weeks: List[Dict[str, int]]

class Contributor(BaseModel):
    login: str
    contributions: int

class Release(BaseModel):
    tag_name: str
    published_at: str

class CodeMetrics(BaseModel):
    repo_url: str
    commits_count: int = Field(default=0)
    contributors_count: int = Field(default=0)
    latest_release: str = Field(default="N/A")
    # Placeholder for more advanced metrics
    lines_of_code: int = Field(default=0)
    issues_count: int = Field(default=0)
    pull_requests_count: int = Field(default=0)

class AuditSummary(BaseModel):
    report_title: str
    audit_firm: str
    date: str
    findings_summary: str
    severity_breakdown: Dict[str, int]

class CodeAuditResult(BaseModel):
    code_metrics: CodeMetrics
    audit_summaries: List[AuditSummary]

class CodeAuditAgent:
    """
    Agent for auditing codebases, fetching repository metrics, and summarizing audit reports.
    This class is designed to be used as an async context manager to ensure proper
    management of the underlying httpx.AsyncClient.

    Example usage:
        async with CodeAuditAgent() as agent:
            metrics = await agent.fetch_repo_metrics("https://github.com/owner/repo")
            # ...
    """
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.gitlab_token = os.getenv("GITLAB_TOKEN")
        self.client = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient()
        return self

    async def _fetch_github_repo_data(self, owner: str, repo: str) -> Dict[str, Any]:
        headers = {"Authorization": f"token {self.github_token}"} if self.github_token else {}
        base_url = f"https://api.github.com/repos/{owner}/{repo}"
        
        repo_data = {
            'commits_count': 0,
            'contributors_count': 0,
            'latest_release': 'N/A',
            'issues_count': 0,
            'pull_requests_count': 0,
        }
        
        try:
            # Helper function to parse link header
            def parse_link_header(link_header_str: str, fallback_len: int) -> int:
                if not link_header_str:
                    return fallback_len
                
                last_page_link = None
                for part in link_header_str.split(','):
                    if 'rel="last"' in part:
                        last_page_link = part.strip()
                        break
                
                if last_page_link:
                    try:
                        url_match = re.search(r'<(.*?)>', last_page_link)
                        if url_match:
                            url = url_match.group(1)
                            page_match = re.search(r'[?&]page=(\d+)', url)
                            if page_match:
                                return int(page_match.group(1))
                    except Exception:
                        logger.warning(f"Failed to parse 'rel=\"last\"' link from header: {last_page_link}")
                return fallback_len

            # Fetch commits count
            if not rate_limiter.check_rate_limit("code_audit_agent"):
                logger.warning("Rate limit exceeded for code_audit_agent (GitHub commits).")
                return repo_data
            commits_resp = await cache_request(
                url=f"{base_url}/commits?per_page=1",
                external_api_call=lambda: self.client.get(f"{base_url}/commits?per_page=1", headers=headers),
                serializer=serialize_httpx_response,
                deserializer=deserialize_httpx_response
            )
            commits_resp.raise_for_status()
            link_header = commits_resp.headers.get('link') or commits_resp.headers.get('Link')
            repo_data['commits_count'] = parse_link_header(link_header, len(commits_resp.json()))

            # Fetch contributors count
            if not rate_limiter.check_rate_limit("code_audit_agent"):
                logger.warning("Rate limit exceeded for code_audit_agent (GitHub contributors).")
                return repo_data
            contributors_resp = await cache_request(
                url=f"{base_url}/contributors?per_page=1",
                external_api_call=lambda: self.client.get(f"{base_url}/contributors?per_page=1", headers=headers),
                serializer=serialize_httpx_response,
                deserializer=deserialize_httpx_response
            )
            contributors_resp.raise_for_status()
            link_header = contributors_resp.headers.get('link') or contributors_resp.headers.get('Link')
            repo_data['contributors_count'] = parse_link_header(link_header, len(contributors_resp.json()))

            # Fetch latest release
            if not rate_limiter.check_rate_limit("code_audit_agent"):
                logger.warning("Rate limit exceeded for code_audit_agent (GitHub releases).")
                return repo_data
            releases_resp = await cache_request(
                url=f"{base_url}/releases/latest",
                external_api_call=lambda: self.client.get(f"{base_url}/releases/latest", headers=headers),
                serializer=serialize_httpx_response,
                deserializer=deserialize_httpx_response
            )
            if releases_resp.status_code == 200:
                repo_data['latest_release'] = releases_resp.json().get('tag_name', 'N/A')
            else:
                repo_data['latest_release'] = 'N/A'

            # Fetch issues count using GitHub Search API to avoid double-counting PRs
            if not rate_limiter.check_rate_limit("code_audit_agent"):
                logger.warning("Rate limit exceeded for code_audit_agent (GitHub issues search).")
                return repo_data
            search_query = urllib.parse.quote_plus(f"repo:{owner}/{repo}+type:issue")
            search_issues_url = f"https://api.github.com/search/issues?q={search_query}&per_page=1"
            issues_search_resp = await cache_request(
                url=search_issues_url,
                external_api_call=lambda: self.client.get(search_issues_url, headers=headers),
                serializer=serialize_httpx_response,
                deserializer=deserialize_httpx_response
            )
            issues_search_resp.raise_for_status()
            issues_search_data = issues_search_resp.json()
            repo_data['issues_count'] = issues_search_data.get('total_count', 0)

            # Fetch pull requests count
            if not rate_limiter.check_rate_limit("code_audit_agent"):
                logger.warning("Rate limit exceeded for code_audit_agent (GitHub pull requests).")
                return repo_data
            pulls_resp = await cache_request(
                url=f"{base_url}/pulls?state=all&per_page=1",
                external_api_call=lambda: self.client.get(f"{base_url}/pulls?state=all&per_page=1", headers=headers),
                serializer=serialize_httpx_response,
                deserializer=deserialize_httpx_response
            )
            pulls_resp.raise_for_status()
            link_header = pulls_resp.headers.get('link') or pulls_resp.headers.get('Link')
            repo_data['pull_requests_count'] = parse_link_header(link_header, len(pulls_resp.json()))

        except httpx.HTTPStatusError as e:
            logger.exception(f"GitHub API error for {owner}/{repo}: {e}")
            return repo_data # Return default empty data on error
        except httpx.RequestError as e:
            logger.exception(f"GitHub network error for {owner}/{repo}: {e}")
            return repo_data # Return default empty data on error
        except Exception as e:
            logger.exception(f"An unexpected error occurred while fetching GitHub data for {owner}/{repo}: {e}")
            return repo_data # Return default empty data on error
        return repo_data

    async def _fetch_gitlab_repo_data(self, project_id: str) -> Dict[str, Any]:
        headers = {"Private-Token": self.gitlab_token} if self.gitlab_token else {}
        base_url = f"https://gitlab.com/api/v4/projects/{project_id}"
        
        repo_data = {
            'commits_count': 0,
            'contributors_count': 0,
            'latest_release': 'N/A',
            'issues_count': 0,
            'pull_requests_count': 0,
        }

        try:
            # Fetch commits count
            if not rate_limiter.check_rate_limit("code_audit_agent"):
                logger.warning("Rate limit exceeded for code_audit_agent (GitLab commits).")
                return repo_data
            commits_resp = await cache_request(
                url=f"{base_url}/repository/commits?per_page=1",
                external_api_call=lambda: self.client.get(f"{base_url}/repository/commits?per_page=1", headers=headers),
                serializer=serialize_httpx_response,
                deserializer=deserialize_httpx_response
            )
            commits_resp.raise_for_status()
            repo_data['commits_count'] = int(commits_resp.headers.get('x-total', 0))

            # Fetch contributors count
            if not rate_limiter.check_rate_limit("code_audit_agent"):
                logger.warning("Rate limit exceeded for code_audit_agent (GitLab contributors).")
                return repo_data
            contributors_resp = await cache_request(
                url=f"{base_url}/repository/contributors?per_page=1",
                external_api_call=lambda: self.client.get(f"{base_url}/repository/contributors?per_page=1", headers=headers),
                serializer=serialize_httpx_response,
                deserializer=deserialize_httpx_response
            )
            contributors_resp.raise_for_status()
            repo_data['contributors_count'] = int(contributors_resp.headers.get('x-total', 0))

            # Fetch latest release (tags in GitLab)
            if not rate_limiter.check_rate_limit("code_audit_agent"):
                logger.warning("Rate limit exceeded for code_audit_agent (GitLab tags).")
                return repo_data
            tags_resp = await cache_request(
                url=f"{base_url}/repository/tags?per_page=1",
                external_api_call=lambda: self.client.get(f"{base_url}/repository/tags?per_page=1", headers=headers),
                serializer=serialize_httpx_response,
                deserializer=deserialize_httpx_response
            )
            if tags_resp.status_code == 200 and tags_resp.json():
                repo_data['latest_release'] = tags_resp.json()[0].get('name', 'N/A')
            else:
                repo_data['latest_release'] = 'N/A'

            # Fetch issues count
            if not rate_limiter.check_rate_limit("code_audit_agent"):
                logger.warning("Rate limit exceeded for code_audit_agent (GitLab issues).")
                return repo_data
            issues_resp = await cache_request(
                url=f"{base_url}/issues?scope=all&per_page=1",
                external_api_call=lambda: self.client.get(f"{base_url}/issues?scope=all&per_page=1", headers=headers),
                serializer=serialize_httpx_response,
                deserializer=deserialize_httpx_response
            )
            issues_resp.raise_for_status()
            repo_data['issues_count'] = int(issues_resp.headers.get('x-total', 0))

            # Fetch merge requests count
            if not rate_limiter.check_rate_limit("code_audit_agent"):
                logger.warning("Rate limit exceeded for code_audit_agent (GitLab merge requests).")
                return repo_data
            merge_requests_resp = await cache_request(
                url=f"{base_url}/merge_requests?scope=all&per_page=1",
                external_api_call=lambda: self.client.get(f"{base_url}/merge_requests?scope=all&per_page=1", headers=headers),
                serializer=serialize_httpx_response,
                deserializer=deserialize_httpx_response
            )
            merge_requests_resp.raise_for_status()
            repo_data['pull_requests_count'] = int(merge_requests_resp.headers.get('x-total', 0))

        except httpx.HTTPStatusError as e:
            logger.exception(f"GitLab API error for project ID {project_id}: {e}")
            return repo_data # Return default empty data on error
        except httpx.RequestError as e:
            logger.exception(f"GitLab network error for project ID {project_id}: {e}")
            return repo_data # Return default empty data on error
        except Exception as e:
            logger.exception(f"An unexpected error occurred while fetching GitLab data for project ID {project_id}: {e}")
            return repo_data # Return default empty data on error
        return repo_data

    async def fetch_repo_metrics(self, repo_url: str) -> CodeMetrics:
        metrics_data = {
            "repo_url": repo_url,
            "commits_count": 0,
            "contributors_count": 0,
            "latest_release": "N/A",
            "lines_of_code": 0, # Placeholder
            "issues_count": 0,
            "pull_requests_count": 0,
        }

        parsed_url = urllib.parse.urlparse(repo_url)
        try:
            if "github.com" in parsed_url.netloc:
                path_segments = [s for s in parsed_url.path.split('/') if s]
                if len(path_segments) >= 2:
                    owner = path_segments[0]
                    repo = path_segments[1]
                    if repo.endswith(".git"):
                        repo = repo[:-4]
                    github_data = await self._fetch_github_repo_data(owner, repo)
                    metrics_data.update(github_data)
                else:
                    logger.error(f"Invalid GitHub repository URL format: {repo_url}")
            elif "gitlab.com" in parsed_url.netloc:
                path_segments = [s for s in parsed_url.path.split('/') if s]
                if len(path_segments) >= 2:
                    if path_segments[-1].endswith('.git'):
                        path_segments[-1] = path_segments[-1][:-4]

                    project_path_with_namespace = "/".join(path_segments)
                    project_id = urllib.parse.quote_plus(project_path_with_namespace)
                    gitlab_data = await self._fetch_gitlab_repo_data(project_id)
                    metrics_data.update(gitlab_data)
                else:
                    logger.error(f"Invalid GitLab repository URL format: {repo_url}")
            else:
                logger.error(f"Unsupported repository URL: {repo_url}")
        except Exception as e:
            logger.exception(f"An unexpected error occurred while fetching repository metrics for {repo_url}: {e}")

        return CodeMetrics(**metrics_data)

    async def analyze_code_activity(self, metrics: CodeMetrics) -> Dict[str, Any]:
        analysis_results = {
            "activity_level": "low",
            "contributor_engagement": "low",
            "release_frequency": "low",
            "code_quality_indicators": "N/A",
            "issues_and_prs_activity": "low"
        }

        if metrics.commits_count > 100:
            analysis_results["activity_level"] = "medium"
        if metrics.commits_count > 1000:
            analysis_results["activity_level"] = "high"

        if metrics.contributors_count > 5:
            analysis_results["contributor_engagement"] = "medium"
        if metrics.contributors_count > 20:
            analysis_results["contributor_engagement"] = "high"

        if metrics.latest_release != "N/A":
            # Simple check for release activity, could be more sophisticated
            analysis_results["release_frequency"] = "present"

        if metrics.issues_count > 50 and metrics.pull_requests_count > 20:
            analysis_results["issues_and_prs_activity"] = "medium"
        if metrics.issues_count > 200 and metrics.pull_requests_count > 100:
            analysis_results["issues_and_prs_activity"] = "high"

        return analysis_results

    async def search_and_summarize_audit_reports(self, project_name: str) -> List[AuditSummary]:
        # This is a placeholder for actual searching and summarization.
        # In a real scenario, this would involve:
        # 1. Web scraping audit firm websites (e.g., CertiK, Trail of Bits, ConsenSys Diligence)
        # 2. Searching internal audit databases
        # 3. Using an LLM to summarize findings from retrieved reports.

        print(f"Searching for audit reports for project: {project_name} (using mock data)")
        try:
            mock_audit_summaries = [
                AuditSummary(
                    report_title=f"{project_name} Smart Contract Audit by CertiK",
                    audit_firm="CertiK",
                    date="2023-10-26",
                    findings_summary="Initial audit found several medium-severity reentrancy vulnerabilities and one high-severity access control issue. All issues have been addressed in subsequent patches.",
                    severity_breakdown={"critical": 0, "high": 1, "medium": 2, "low": 3, "informational": 5}
                ),
                AuditSummary(
                    report_title=f"{project_name} Security Review by Trail of Bits",
                    audit_firm="Trail of Bits",
                    date="2024-01-15",
                    findings_summary="A follow-up review identified minor gas optimization opportunities and confirmed the remediation of all critical findings from the previous audit.",
                    severity_breakdown={"critical": 0, "high": 0, "medium": 0, "low": 2, "informational": 7}
                )
            ]
            return mock_audit_summaries
        except Exception as e:
            logger.exception(f"An unexpected error occurred while searching and summarizing audit reports for {project_name}: {e}")
            return [] # Return empty list on error

    async def fetch_data(self, token_id: str, project_name: str | None = None) -> dict:
        """
        Fetches code metrics and audit summaries for a given token_id, which is used as the repository URL.

        Args:
            token_id (str): The identifier used as the repository URL for CodeAuditAgent (e.g., "https://github.com/owner/repo").
            project_name (str | None): The name of the project. If None, it will be derived from the token_id.

        Returns:
            dict: A dictionary containing CodeMetrics and a list of AuditSummary objects.
        """
        if not token_id:
            raise ValueError("token_id must be provided for CodeAuditAgent.")

        if project_name is None:
            # Attempt to derive project_name from token_id
            parsed_url = urllib.parse.urlparse(token_id)
            path_segments = [s for s in parsed_url.path.split('/') if s]
            if path_segments:
                project_name = path_segments[-1].replace(".git", "")
            else:
                project_name = "unknown_project" # Fallback

        code_metrics = CodeMetrics(repo_url=token_id)
        audit_summaries = []
        try:
            code_metrics = await self.fetch_repo_metrics(token_id)
            audit_summaries = await self.search_and_summarize_audit_reports(project_name)
        except Exception as e:
            logger.exception(f"An unexpected error occurred during codebase audit for {token_id} (project: {project_name}): {e}")

        return CodeAuditResult(
            code_metrics=code_metrics,
            audit_summaries=audit_summaries
        ).model_dump()


    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

