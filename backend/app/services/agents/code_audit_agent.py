import os
import re
import logging
from typing import Dict, Any, List
import httpx
from pydantic import BaseModel, Field
import urllib.parse

logger = logging.getLogger(__name__)

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
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.gitlab_token = os.getenv("GITLAB_TOKEN")
        self.client = httpx.AsyncClient()

    async def _fetch_github_repo_data(self, owner: str, repo: str) -> Dict[str, Any]:
        headers = {"Authorization": f"token {self.github_token}"} if self.github_token else {}
        base_url = f"https://api.github.com/repos/{owner}/{repo}"
        
        repo_data = {}
        
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
            commits_resp = await self.client.get(f"{base_url}/commits?per_page=1", headers=headers)
            commits_resp.raise_for_status()
            link_header = commits_resp.headers.get('link') or commits_resp.headers.get('Link')
            repo_data['commits_count'] = parse_link_header(link_header, len(commits_resp.json()))

            # Fetch contributors count
            contributors_resp = await self.client.get(f"{base_url}/contributors?per_page=1", headers=headers)
            contributors_resp.raise_for_status()
            link_header = contributors_resp.headers.get('link') or contributors_resp.headers.get('Link')
            repo_data['contributors_count'] = parse_link_header(link_header, len(contributors_resp.json()))

            # Fetch latest release
            releases_resp = await self.client.get(f"{base_url}/releases/latest", headers=headers)
            if releases_resp.status_code == 200:
                repo_data['latest_release'] = releases_resp.json().get('tag_name', 'N/A')
            else:
                repo_data['latest_release'] = 'N/A'

            # Fetch issues count using GitHub Search API to avoid double-counting PRs
            search_query = urllib.parse.quote_plus(f"repo:{owner}/{repo}+type:issue")
            search_issues_url = f"https://api.github.com/search/issues?q={search_query}&per_page=1"
            issues_search_resp = await self.client.get(search_issues_url, headers=headers)
            issues_search_resp.raise_for_status()
            issues_search_data = issues_search_resp.json()
            repo_data['issues_count'] = issues_search_data.get('total_count', 0)

            # Fetch pull requests count
            pulls_resp = await self.client.get(f"{base_url}/pulls?state=all&per_page=1", headers=headers)
            pulls_resp.raise_for_status()
            link_header = pulls_resp.headers.get('link') or pulls_resp.headers.get('Link')
            repo_data['pull_requests_count'] = parse_link_header(link_header, len(pulls_resp.json()))

        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API error for {owner}/{repo}: {e}")
        except httpx.RequestError as e:
            logger.error(f"GitHub network error for {owner}/{repo}: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching GitHub data for {owner}/{repo}: {e}")
        return repo_data

    async def _fetch_gitlab_repo_data(self, project_id: str) -> Dict[str, Any]:
        headers = {"Private-Token": self.gitlab_token} if self.gitlab_token else {}
        base_url = f"https://gitlab.com/api/v4/projects/{project_id}"
        
        repo_data = {}

        try:
            # Fetch commits count
            commits_resp = await self.client.get(f"{base_url}/repository/commits?per_page=1", headers=headers)
            commits_resp.raise_for_status()
            repo_data['commits_count'] = int(commits_resp.headers.get('x-total', 0))

            # Fetch contributors count
            contributors_resp = await self.client.get(f"{base_url}/repository/contributors?per_page=1", headers=headers)
            contributors_resp.raise_for_status()
            repo_data['contributors_count'] = int(contributors_resp.headers.get('x-total', 0))

            # Fetch latest release (tags in GitLab)
            tags_resp = await self.client.get(f"{base_url}/repository/tags?per_page=1", headers=headers)
            if tags_resp.status_code == 200 and tags_resp.json():
                repo_data['latest_release'] = tags_resp.json()[0].get('name', 'N/A')
            else:
                repo_data['latest_release'] = 'N/A'

            # Fetch issues count
            issues_resp = await self.client.get(f"{base_url}/issues?scope=all&per_page=1", headers=headers)
            issues_resp.raise_for_status()
            repo_data['issues_count'] = int(issues_resp.headers.get('x-total', 0))

            # Fetch merge requests count
            merge_requests_resp = await self.client.get(f"{base_url}/merge_requests?scope=all&per_page=1", headers=headers)
            merge_requests_resp.raise_for_status()
            repo_data['pull_requests_count'] = int(merge_requests_resp.headers.get('x-total', 0))

        except httpx.HTTPStatusError as e:
            logger.error(f"GitLab API error for project ID {project_id}: {e}")
        except httpx.RequestError as e:
            logger.error(f"GitLab network error for project ID {project_id}: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching GitLab data for project ID {project_id}: {e}")
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

        if "github.com" in parsed_url.netloc:
            path_segments = [s for s in parsed_url.path.split('/') if s]
            if len(path_segments) >= 2:
                owner = path_segments[0]
                repo = path_segments[1].replace(".git", "")
                github_data = await self._fetch_github_repo_data(owner, repo)
                metrics_data.update(github_data)
            else:
                logger.error(f"Invalid GitHub repository URL format: {repo_url}")
        elif "gitlab.com" in parsed_url.netloc:
            # For GitLab, we need the project ID. This is a simplification.
            # A more robust solution would involve searching for the project by path.
            # For now, assume the URL contains the project ID or path that can be converted.
            # Example: https://gitlab.com/group/subgroup/project -> project_id can be derived or passed.
            # For simplicity, let's assume the last part of the path is the project path with owner.
            path_segments = [s for s in parsed_url.path.split('/') if s]
            if len(path_segments) >= 2:
                project_path_with_namespace = "/".join(path_segments)
                project_id = urllib.parse.quote_plus(project_path_with_namespace)
                gitlab_data = await self._fetch_gitlab_repo_data(project_id)
                metrics_data.update(gitlab_data)
            else:
                logger.error(f"Invalid GitLab repository URL format: {repo_url}")
        else:
            logger.error(f"Unsupported repository URL: {repo_url}")

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

    async def audit_codebase(self, repo_url: str, project_name: str) -> CodeAuditResult:
        code_metrics = await self.fetch_repo_metrics(repo_url)
        # code_activity_analysis = await self.analyze_code_activity(code_metrics) # Not directly used in final output, but can be for internal logic
        audit_summaries = await self.search_and_summarize_audit_reports(project_name)

        return CodeAuditResult(
            code_metrics=code_metrics,
            audit_summaries=audit_summaries
        )

    async def close(self):
        await self.client.aclose()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

