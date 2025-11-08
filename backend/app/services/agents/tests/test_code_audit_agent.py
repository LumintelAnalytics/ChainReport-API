import pytest
import pytest_asyncio
import respx
from httpx import Response, Request, HTTPStatusError, RequestError
from backend.app.services.agents.code_audit_agent import CodeAuditAgent, CodeMetrics, AuditSummary, CodeAuditResult


@pytest_asyncio.fixture
async def code_audit_agent():
    async with CodeAuditAgent() as agent:
        yield agent

@pytest.mark.asyncio
async def test_fetch_github_repo_metrics(code_audit_agent):
    repo_url = "https://github.com/octocat/Spoon-Knife"
    owner = "octocat"
    repo = "Spoon-Knife"

    with respx.mock:
        # Mock commits count
        respx.get(f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=1").mock(return_value=Response(200, headers={'link': '<https://api.github.com/repositories/1296269/commits?per_page=1&page=2>; rel="next", <https://api.github.com/repositories/1296269/commits?per_page=1&page=10>; rel="last"'}, json=[]))
        # Mock contributors count
        respx.get(f"https://api.github.com/repos/{owner}/{repo}/contributors?per_page=1").mock(return_value=Response(200, headers={'link': '<https://api.github.com/repositories/1296269/contributors?per_page=1&page=2>; rel="next", <https://api.github.com/repositories/1296269/contributors?per_page=1&page=5>; rel="last"'}, json=[]))
        # Mock latest release
        respx.get(f"https://api.github.com/repos/{owner}/{repo}/releases/latest").mock(return_value=Response(200, json={'tag_name': 'v1.0.0'}))
        respx.get(f"https://api.github.com/search/issues?q=repo%3A{owner}%2F{repo}%2Btype%3Aissue&per_page=1").mock(return_value=Response(200, json={'total_count': 20}))
        # Mock pull requests count
        respx.get(f"https://api.github.com/repos/{owner}/{repo}/pulls?state=all&per_page=1").mock(return_value=Response(200, headers={'link': '<https://api.github.com/repositories/1296269/pulls?state=all&per_page=1&page=2>; rel="next", <https://api.github.com/repositories/1296269/pulls?state=all&per_page=1&page=15>; rel="last"'}, json=[]))
        metrics = await code_audit_agent.fetch_repo_metrics(repo_url)

        assert metrics.repo_url == repo_url
        assert metrics.commits_count == 10
        assert metrics.contributors_count == 5
        assert metrics.latest_release == "v1.0.0"
        assert metrics.issues_count == 20
        assert metrics.pull_requests_count == 15

@pytest.mark.asyncio
async def test_fetch_gitlab_repo_metrics(code_audit_agent):
    repo_url = "https://gitlab.com/gitlab-org/gitlab-foss"
    project_id = "gitlab-org%2Fgitlab-foss"

    with respx.mock:
        # Mock commits count
        respx.get(f"https://gitlab.com/api/v4/projects/{project_id}/repository/commits?per_page=1").mock(return_value=Response(200, headers={'x-total': '1000'}, json=[]))
        # Mock contributors count
        respx.get(f"https://gitlab.com/api/v4/projects/{project_id}/repository/contributors?per_page=1").mock(return_value=Response(200, headers={'x-total': '50'}, json=[]))
        # Mock latest release (tags)
        respx.get(f"https://gitlab.com/api/v4/projects/{project_id}/repository/tags?per_page=1").mock(return_value=Response(200, json=[{'name': 'v13.0.0'}]))
        # Mock issues count
        respx.get(f"https://gitlab.com/api/v4/projects/{project_id}/issues?scope=all&per_page=1").mock(return_value=Response(200, headers={'x-total': '200'}, json=[]))
        # Mock merge requests count
        respx.get(f"https://gitlab.com/api/v4/projects/{project_id}/merge_requests?scope=all&per_page=1").mock(return_value=Response(200, headers={'x-total': '150'}, json=[]))
        metrics = await code_audit_agent.fetch_repo_metrics(repo_url)

        assert metrics.repo_url == repo_url
        assert metrics.commits_count == 1000
        assert metrics.contributors_count == 50
        assert metrics.latest_release == "v13.0.0"
        assert metrics.issues_count == 200
        assert metrics.pull_requests_count == 150

@pytest.mark.asyncio
async def test_analyze_code_activity(code_audit_agent):
    # Test high activity
    high_metrics = CodeMetrics(repo_url="test", commits_count=1500, contributors_count=25, issues_count=250, pull_requests_count=120)
    high_analysis = await code_audit_agent.analyze_code_activity(high_metrics)
    assert high_analysis["activity_level"] == "high"
    assert high_analysis["contributor_engagement"] == "high"
    assert high_analysis["issues_and_prs_activity"] == "high"

    # Test medium activity
    medium_metrics = CodeMetrics(repo_url="test", commits_count=500, contributors_count=10, issues_count=100, pull_requests_count=50)
    medium_analysis = await code_audit_agent.analyze_code_activity(medium_metrics)
    assert medium_analysis["activity_level"] == "medium"
    assert medium_analysis["contributor_engagement"] == "medium"
    assert medium_analysis["issues_and_prs_activity"] == "medium"

    # Test low activity
    low_metrics = CodeMetrics(repo_url="test", commits_count=50, contributors_count=2, issues_count=10, pull_requests_count=5)
    low_analysis = await code_audit_agent.analyze_code_activity(low_metrics)
    assert low_analysis["activity_level"] == "low"
    assert low_analysis["contributor_engagement"] == "low"
    assert low_analysis["issues_and_prs_activity"] == "low"

@pytest.mark.asyncio
async def test_search_and_summarize_audit_reports(code_audit_agent):
    project_name = "TestProject"
    audit_summaries = await code_audit_agent.search_and_summarize_audit_reports(project_name)

    assert len(audit_summaries) == 2
    assert isinstance(audit_summaries[0], AuditSummary)
    assert project_name in audit_summaries[0].report_title
    assert audit_summaries[0].audit_firm == "CertiK"

@pytest.mark.asyncio
async def test_audit_codebase(code_audit_agent):
    repo_url = "https://github.com/octocat/Spoon-Knife"
    project_name = "Spoon-Knife"
    owner = "octocat"
    repo = "Spoon-Knife"

    with respx.mock:
        # Mock GitHub API calls for fetch_repo_metrics
        respx.get(f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=1").mock(return_value=Response(200, headers={'link': '<https://api.github.com/repositories/1296269/commits?per_page=1&page=2>; rel="next", <https://api.github.com/repositories/1296269/commits?per_page=1&page=10>; rel="last"'}, json=[]))
        respx.get(f"https://api.github.com/repos/{owner}/{repo}/contributors?per_page=1").mock(return_value=Response(200, headers={'link': '<https://api.github.com/repositories/1296269/contributors?per_page=1&page=2>; rel="next", <https://api.github.com/repositories/1296269/contributors?per_page=1&page=5>; rel="last"'}, json=[]))
        respx.get(f"https://api.github.com/repos/{owner}/{repo}/releases/latest").mock(return_value=Response(200, json={'tag_name': 'v1.0.0'}))
        respx.get(f"https://api.github.com/search/issues?q=repo%3A{owner}%2F{repo}%2Btype%3Aissue&per_page=1").mock(return_value=Response(200, json={'total_count': 20}))
        respx.get(f"https://api.github.com/repos/{owner}/{repo}/pulls?state=all&per_page=1").mock(return_value=Response(200, headers={'link': '<https://api.github.com/repositories/1296269/pulls?state=all&per_page=1&page=2>; rel="next", <https://api.github.com/repositories/1296269/pulls?state=all&per_page=1&page=15>; rel="last"'}, json=[]))

        result = await code_audit_agent.audit_codebase(repo_url, project_name)

        assert isinstance(result, CodeAuditResult)
        assert result.code_metrics.repo_url == repo_url
        assert len(result.audit_summaries) == 2
        assert project_name in result.audit_summaries[0].report_title

@pytest.mark.asyncio
async def test_fetch_github_repo_metrics_http_error(code_audit_agent):
    repo_url = "https://github.com/nonexistent/repo"
    owner = "nonexistent"
    repo = "repo"

    with respx.mock:
        # Mock all GitHub API calls to return 404 Not Found
        respx.get(f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=1").mock(return_value=Response(404))
        respx.get(f"https://api.github.com/repos/{owner}/{repo}/contributors?per_page=1").mock(return_value=Response(404))
        respx.get(f"https://api.github.com/repos/{owner}/{repo}/releases/latest").mock(return_value=Response(404))
        respx.get(f"https://api.github.com/search/issues?q=repo%3A{owner}%2F{repo}%2Btype%3Aissue&per_page=1").mock(return_value=Response(404))
        respx.get(f"https://api.github.com/repos/{owner}/{repo}/pulls?state=all&per_page=1").mock(return_value=Response(404))

        metrics = await code_audit_agent.fetch_repo_metrics(repo_url)

        assert metrics.repo_url == repo_url
        assert metrics.commits_count == 0
        assert metrics.contributors_count == 0
        assert metrics.latest_release == "N/A"
        assert metrics.issues_count == 0
        assert metrics.pull_requests_count == 0

@pytest.mark.asyncio
async def test_fetch_github_repo_metrics_network_error(code_audit_agent):
    repo_url = "https://github.com/owner/repo"
    owner = "owner"
    repo = "repo"

    with respx.mock:
        # Mock all GitHub API calls to raise a RequestError
        respx.get(f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=1").mock(side_effect=RequestError("Network error", request=Request("GET", f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=1")))
        respx.get(f"https://api.github.com/repos/{owner}/{repo}/contributors?per_page=1").mock(side_effect=RequestError("Network error", request=Request("GET", f"https://api.github.com/repos/{owner}/{repo}/contributors?per_page=1")))
        respx.get(f"https://api.github.com/repos/{owner}/{repo}/releases/latest").mock(side_effect=RequestError("Network error", request=Request("GET", f"https://api.github.com/repos/{owner}/{repo}/releases/latest")))
        respx.get(f"https://api.github.com/search/issues?q=repo%3A{owner}%2F{repo}%2Btype%3Aissue&per_page=1").mock(side_effect=RequestError("Network error", request=Request("GET", f"https://api.github.com/search/issues?q=repo%3A{owner}%2F{repo}%2Btype%3Aissue&per_page=1")))
        respx.get(f"https://api.github.com/repos/{owner}/{repo}/pulls?state=all&per_page=1").mock(side_effect=RequestError("Network error", request=Request("GET", f"https://api.github.com/repos/{owner}/{repo}/pulls?state=all&per_page=1")))

        metrics = await code_audit_agent.fetch_repo_metrics(repo_url)

        assert metrics.repo_url == repo_url
        assert metrics.commits_count == 0
        assert metrics.contributors_count == 0
        assert metrics.latest_release == "N/A"
        assert metrics.issues_count == 0
        assert metrics.pull_requests_count == 0

@pytest.mark.asyncio
async def test_fetch_gitlab_repo_metrics_http_error(code_audit_agent):
    repo_url = "https://gitlab.com/nonexistent/repo"
    project_id = "nonexistent%2Frepo"

    with respx.mock:
        # Mock all GitLab API calls to return 404 Not Found
        respx.get(f"https://gitlab.com/api/v4/projects/{project_id}/repository/commits?per_page=1").mock(return_value=Response(404))
        respx.get(f"https://gitlab.com/api/v4/projects/{project_id}/repository/contributors?per_page=1").mock(return_value=Response(404))
        respx.get(f"https://gitlab.com/api/v4/projects/{project_id}/repository/tags?per_page=1").mock(return_value=Response(404))
        respx.get(f"https://gitlab.com/api/v4/projects/{project_id}/issues?scope=all&per_page=1").mock(return_value=Response(404))
        respx.get(f"https://gitlab.com/api/v4/projects/{project_id}/merge_requests?scope=all&per_page=1").mock(return_value=Response(404))

        metrics = await code_audit_agent.fetch_repo_metrics(repo_url)

        assert metrics.repo_url == repo_url
        assert metrics.commits_count == 0
        assert metrics.contributors_count == 0
        assert metrics.latest_release == "N/A"
        assert metrics.issues_count == 0
        assert metrics.pull_requests_count == 0

@pytest.mark.asyncio
async def test_fetch_gitlab_repo_metrics_network_error(code_audit_agent):
    repo_url = "https://gitlab.com/group/project"
    project_id = "group%2Fproject"

    with respx.mock:
        # Mock all GitLab API calls to raise a RequestError
        respx.get(f"https://gitlab.com/api/v4/projects/{project_id}/repository/commits?per_page=1").mock(side_effect=RequestError("Network error", request=Request("GET", f"https://gitlab.com/api/v4/projects/{project_id}/repository/commits?per_page=1")))
        respx.get(f"https://gitlab.com/api/v4/projects/{project_id}/repository/contributors?per_page=1").mock(side_effect=RequestError("Network error", request=Request("GET", f"https://gitlab.com/api/v4/projects/{project_id}/repository/contributors?per_page=1")))
        respx.get(f"https://gitlab.com/api/v4/projects/{project_id}/repository/tags?per_page=1").mock(side_effect=RequestError("Network error", request=Request("GET", f"https://gitlab.com/api/v4/projects/{project_id}/repository/tags?per_page=1")))
        respx.get(f"https://gitlab.com/api/v4/projects/{project_id}/issues?scope=all&per_page=1").mock(side_effect=RequestError("Network error", request=Request("GET", f"https://gitlab.com/api/v4/projects/{project_id}/issues?scope=all&per_page=1")))
        respx.get(f"https://gitlab.com/api/v4/projects/{project_id}/merge_requests?scope=all&per_page=1").mock(side_effect=RequestError("Network error", request=Request("GET", f"https://gitlab.com/api/v4/projects/{project_id}/merge_requests?scope=all&per_page=1")))

        metrics = await code_audit_agent.fetch_repo_metrics(repo_url)

        assert metrics.repo_url == repo_url
        assert metrics.commits_count == 0
        assert metrics.contributors_count == 0
        assert metrics.latest_release == "N/A"
        assert metrics.issues_count == 0
        assert metrics.pull_requests_count == 0

@pytest.mark.asyncio
async def test_fetch_repo_metrics_unsupported_url(code_audit_agent):
    repo_url = "https://bitbucket.org/some/repo"
    metrics = await code_audit_agent.fetch_repo_metrics(repo_url)

    assert metrics.repo_url == repo_url
    assert metrics.commits_count == 0
    assert metrics.contributors_count == 0
    assert metrics.latest_release == "N/A"
    assert metrics.issues_count == 0
    assert metrics.pull_requests_count == 0

@pytest.mark.asyncio
async def test_fetch_repo_metrics_invalid_github_url_format(code_audit_agent):
    repo_url = "https://github.com/owner_only"
    metrics = await code_audit_agent.fetch_repo_metrics(repo_url)

    assert metrics.repo_url == repo_url
    assert metrics.commits_count == 0
    assert metrics.contributors_count == 0
    assert metrics.latest_release == "N/A"
    assert metrics.issues_count == 0
    assert metrics.pull_requests_count == 0

@pytest.mark.asyncio
async def test_fetch_repo_metrics_invalid_gitlab_url_format(code_audit_agent):
    repo_url = "https://gitlab.com/group_only"
    metrics = await code_audit_agent.fetch_repo_metrics(repo_url)

    assert metrics.repo_url == repo_url
    assert metrics.commits_count == 0
    assert metrics.contributors_count == 0
    assert metrics.latest_release == "N/A"
    assert metrics.issues_count == 0
    assert metrics.pull_requests_count == 0