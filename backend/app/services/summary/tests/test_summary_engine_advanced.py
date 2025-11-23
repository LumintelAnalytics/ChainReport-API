import pytest
from backend.app.services.summary.report_summary_engine import ReportSummaryEngine

@pytest.fixture
def summary_engine():
    return ReportSummaryEngine()

# Test cases for generate_scores
def test_generate_scores_partial_data(summary_engine):
    # Test with partial data for some agents
    data = {
        "tokenomics_data": {"distribution_score": 0.6}, # Missing utility_score
        "sentiment_data": {"positive_sentiment_ratio": 0.8, "negative_sentiment_ratio": 0.1},
        "code_audit_data": {"test_coverage": 0.8}, # Missing lines_of_code, bug_density
    }
    scores = summary_engine.generate_scores(data)

    # Expected calculations with default placeholders for missing values
    assert scores["tokenomics_strength"] == (0.6 + 0.5) / 2 * 10 # 0.5 is default for utility_score
    assert scores["sentiment_health"] == (0.8 - 0.1 + 1) / 2 * 10
    assert scores["code_maturity"] == (0.8 * 0.6 + (1 - 0.1) * 0.4) * 10 # 0.1 is default for bug_density

def test_generate_scores_boundary_values(summary_engine):
    # Test with boundary values for scores (0 or 1 for ratios, etc.)
    data = {
        "tokenomics_data": {"distribution_score": 0.0, "utility_score": 1.0},
        "sentiment_data": {"positive_sentiment_ratio": 1.0, "negative_sentiment_ratio": 0.0},
        "code_audit_data": {"lines_of_code": 100, "test_coverage": 0.0, "bug_density": 1.0},
        "audit_data": {"num_audits": 0, "critical_findings_resolved": 0.0},
        "team_data": {"team_experience_score": 0.0, "transparency_score": 1.0},
    }
    scores = summary_engine.generate_scores(data)

    assert scores["tokenomics_strength"] == (0.0 + 1.0) / 2 * 10
    assert scores["sentiment_health"] == (1.0 - 0.0 + 1) / 2 * 10
    assert scores["code_maturity"] == (0.0 * 0.6 + (1 - 1.0) * 0.4) * 10
    assert scores["audit_confidence"] == min(0 * 2, 5) + 0.0 * 5
    assert scores["team_credibility"] == (0.0 * 0.5 + 1.0 * 0.5) * 10

# Test cases for build_final_summary
def test_build_final_summary_all_strengths(summary_engine):
    nlg_outputs = {
        "tokenomics": "Strong tokenomics.",
        "sentiment": "Very positive sentiment.",
    }
    scores = {
        "tokenomics_strength": 9.0,
        "sentiment_health": 8.0,
        "code_maturity": 7.0,
        "audit_confidence": 7.5,
        "team_credibility": 9.5,
    }
    summary = summary_engine.build_final_summary(nlg_outputs, scores)

    assert isinstance(summary, dict)
    assert "overall_summary" in summary
    assert "scores" in summary
    assert "weaknesses" in summary
    assert "strengths" in summary

    assert len(summary["weaknesses"]) == 0
    assert len(summary["strengths"]) == 5
    assert "Tokenomics Strength" in summary["strengths"]
    assert "Sentiment Health" in summary["strengths"]
    assert "Code Maturity" in summary["strengths"]
    assert "Audit Confidence" in summary["strengths"]
    assert "Team Credibility" in summary["strengths"]

def test_build_final_summary_all_weaknesses(summary_engine):
    nlg_outputs = {
        "tokenomics": "Weak tokenomics.",
        "sentiment": "Very negative sentiment.",
    }
    scores = {
        "tokenomics_strength": 3.0,
        "sentiment_health": 2.0,
        "code_maturity": 4.0,
        "audit_confidence": 1.5,
        "team_credibility": 4.5,
    }
    summary = summary_engine.build_final_summary(nlg_outputs, scores)

    assert isinstance(summary, dict)
    assert "overall_summary" in summary
    assert "scores" in summary
    assert "weaknesses" in summary
    assert "strengths" in summary

    assert len(summary["strengths"]) == 0
    assert len(summary["weaknesses"]) == 5
    assert "Tokenomics Strength" in summary["weaknesses"]
    assert "Sentiment Health" in summary["weaknesses"]
    assert "Code Maturity" in summary["weaknesses"]
    assert "Audit Confidence" in summary["weaknesses"]
    assert "Team Credibility" in summary["weaknesses"]

def test_build_final_summary_mixed_scores(summary_engine):
    nlg_outputs = {
        "tokenomics": "Mixed tokenomics.",
        "sentiment": "Neutral sentiment.",
        "code_audit": "Code audit findings.",
    }
    scores = {
        "tokenomics_strength": 8.0, # Strength
        "sentiment_health": 4.0,    # Weakness
        "code_maturity": 6.0,       # Neutral
        "audit_confidence": 2.0,    # Weakness
        "team_credibility": 7.0,    # Strength
    }
    summary = summary_engine.build_final_summary(nlg_outputs, scores)

    assert isinstance(summary, dict)
    assert "overall_summary" in summary
    assert "scores" in summary
    assert "weaknesses" in summary
    assert "strengths" in summary

    assert len(summary["strengths"]) == 2
    assert "Tokenomics Strength" in summary["strengths"]
    assert "Team Credibility" in summary["strengths"]

    assert len(summary["weaknesses"]) == 2
    assert "Sentiment Health" in summary["weaknesses"]
    assert "Audit Confidence" in summary["weaknesses"]

    assert "Code Maturity" not in summary["strengths"]
    assert "Code Maturity" not in summary["weaknesses"]

    # Verify overall_summary content
    assert "Tokenomics Insights: Mixed tokenomics." in summary["overall_summary"]
    assert "Sentiment Insights: Neutral sentiment." in summary["overall_summary"]
    assert "Code Audit Insights: Code audit findings." in summary["overall_summary"]

    # Verify scores content and rounding
    assert summary["scores"] == {
        "Tokenomics Strength": 8.0,
        "Sentiment Health": 4.0,
        "Code Maturity": 6.0,
        "Audit Confidence": 2.0,
        "Team Credibility": 7.0,
    }
