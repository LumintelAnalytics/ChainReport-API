import pytest
from backend.app.services.summary.report_summary_engine import ReportSummaryEngine

@pytest.fixture
def summary_engine():
    return ReportSummaryEngine()

def test_generate_scores_empty_data(summary_engine):
    data = {}
    scores = summary_engine.generate_scores(data)
    assert isinstance(scores, dict)
    assert "tokenomics_strength" in scores
    assert "sentiment_health" in scores
    assert "code_maturity" in scores
    assert "audit_confidence" in scores
    assert "team_credibility" in scores
    # Check default placeholder values (0.5 for ratios, 1 for num_audits, etc.)
    assert scores["tokenomics_strength"] == 5.0
    assert scores["sentiment_health"] == 5.0
    assert scores["code_maturity"] == (0.7 * 0.6 + (1 - 0.1) * 0.4) * 10
    assert scores["audit_confidence"] == min(1 * 2, 5) + 1.0 * 5
    assert scores["team_credibility"] == (0.7 * 0.5 + 0.8 * 0.5) * 10

def test_generate_scores_with_data(summary_engine):
    data = {
        "tokenomics_data": {"distribution_score": 0.8, "utility_score": 0.9},
        "sentiment_data": {"positive_sentiment_ratio": 0.7, "negative_sentiment_ratio": 0.2},
        "code_audit_data": {"lines_of_code": 5000, "test_coverage": 0.9, "bug_density": 0.05},
        "audit_data": {"num_audits": 3, "critical_findings_resolved": 0.95},
        "team_data": {"team_experience_score": 0.9, "transparency_score": 0.95},
    }
    scores = summary_engine.generate_scores(data)

    assert scores["tokenomics_strength"] == (0.8 + 0.9) / 2 * 10
    assert scores["sentiment_health"] == (0.7 - 0.2 + 1) / 2 * 10
    assert scores["code_maturity"] == (0.9 * 0.6 + (1 - 0.05) * 0.4) * 10
    assert scores["audit_confidence"] == min(3 * 2, 5) + 0.95 * 5
    assert scores["team_credibility"] == (0.9 * 0.5 + 0.95 * 0.5) * 10

def test_build_final_summary(summary_engine):
    nlg_outputs = {
        "tokenomics": "Tokenomics insights text.",
        "social_sentiment": "Social sentiment insights text.",
    }
    scores = {
        "tokenomics_strength": 7.5,
        "sentiment_health": 8.2,
    }
    summary = summary_engine.build_final_summary(nlg_outputs, scores)

    assert "--- Comprehensive Report Summary ---" in summary
    assert "Tokenomics Insights:" in summary
    assert "Tokenomics insights text." in summary
    assert "Social Sentiment Insights:" in summary
    assert "Social sentiment insights text." in summary
    assert "--- Overall Scores (out of 10) ---" in summary
    assert "Tokenomics Strength: 7.50/10" in summary
    assert "Sentiment Health: 8.20/10" in summary
    assert "--- End of Report ---" in summary
