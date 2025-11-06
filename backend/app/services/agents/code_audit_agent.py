import os
from typing import Dict, Any, List
import httpx
from pydantic import BaseModel, Field

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
            # Fetch commits count
            commits_resp = await self.client.get(f"{base_url}/commits?per_page=1", headers=headers)
            commits_resp.raise_for_status()
            link_header = commits_resp.headers.get('link') or commits_resp.headers.get('Link') # Try both cases
            if link_header:
                last_page_link = link_header.split(',')[-1] # Corrected index to -1
                commits_count = int(last_page_link.split('&page=')[1].split('>')[0])
            else:
                commits_count = len(commits_resp.json()) # Fallback for small repos
            repo_data['commits_count'] = commits_count

            # Fetch contributors count
            contributors_resp = await self.client.get(f"{base_url}/contributors?per_page=1", headers=headers)
            contributors_resp.raise_for_status()
            if 'link' in contributors_resp.headers:
                last_page_link = contributors_resp.headers['link'].split(',')[-1] # Corrected index to -1
                contributors_count = int(last_page_link.split('&page=')[1].split('>')[0])
            else:
                contributors_count = len(contributors_resp.json()) # Fallback for small repos
            repo_data['contributors_count'] = contributors_count

            # Fetch latest release
            releases_resp = await self.client.get(f"{base_url}/releases/latest", headers=headers)
            if releases_resp.status_code == 200:
                repo_data['latest_release'] = releases_resp.json().get('tag_name', 'N/A')
            else:
                repo_data['latest_release'] = 'N/A'

            # Fetch issues count
            issues_resp = await self.client.get(f"{base_url}/issues?state=all&per_page=1", headers=headers)
            issues_resp.raise_for_status()
            if 'link' in issues_resp.headers:
                last_page_link = issues_resp.headers['link'].split(',')[-1] # Corrected index to -1
                issues_count = int(last_page_link.split('&page=')[1].split('>')[0])
            else:
                issues_count = len(issues_resp.json())
            repo_data['issues_count'] = issues_count

            # Fetch pull requests count
            pulls_resp = await self.client.get(f"{base_url}/pulls?state=all&per_page=1", headers=headers)
            pulls_resp.raise_for_status()
            if 'link' in pulls_resp.headers:
                last_page_link = pulls_resp.headers['link'].split(',')[-1] # Corrected index to -1
                pulls_count = int(last_page_link.split('&page=')[1].split('>')[0])
            else:
                pulls_count = len(pulls_resp.json())
            repo_data['pull_requests_count'] = pulls_count

        except httpx.HTTPStatusError as e:
            print(f"GitHub API error: {e}")
        except httpx.RequestError as e:
            print(f"GitHub network error: {e}")
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
            print(f"GitLab API error: {e}")
        except httpx.RequestError as e:
            print(f"GitLab network error: {e}")
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

        if "github.com" in repo_url:
            parts = repo_url.split("/")
            owner = parts[-2]
            repo = parts[-1].replace(".git", "")
            github_data = await self._fetch_github_repo_data(owner, repo)
            metrics_data.update(github_data)
        elif "gitlab.com" in repo_url:
            # For GitLab, we need the project ID. This is a simplification.
            # A more robust solution would involve searching for the project by path.
            # For now, assume the URL contains the project ID or path that can be converted.
            # Example: https://gitlab.com/group/subgroup/project -> project_id can be derived or passed.
            # For simplicity, let's assume the last part of the path is the project path with owner.
            parts = repo_url.split("/")
            project_path_with_namespace = "/".join(parts[-2:])
            # This is a significant simplification. GitLab API needs project ID or URL-encoded path.
            # For a real implementation, you'd need to resolve project_path_with_namespace to an ID.
            # For now, I'll use a placeholder for project_id.
            # A better approach would be to use the search API or require the user to provide the project ID.
            print("GitLab integration requires project ID or full path. Using placeholder for now.")
            # Placeholder for project_id. In a real scenario, this would need to be resolved.
            # For example, if the URL is https://gitlab.com/gitlab-org/gitlab, project_id could be 'gitlab-org%2Fgitlab'
            # For now, I'll use a dummy ID or try to infer from URL if possible.
            # Let's assume the user provides the full path in the URL for now.
            # Example: https://gitlab.com/gitlab-org/gitlab-foss -> project_id = gitlab-org%2Fgitlab-foss
            project_id = project_path_with_namespace.replace("/", "%2F")
            gitlab_data = await self._fetch_gitlab_repo_data(project_id)
            metrics_data.update(gitlab_data)
        else:
            print(f"Unsupported repository URL: {repo_url}")

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

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

