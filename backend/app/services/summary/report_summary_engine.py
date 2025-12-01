from typing import Any, Dict
from backend.app.services.summary.summary_engine import SummaryEngine

class ReportSummaryEngine(SummaryEngine):
    def generate_scores(self, data: Dict[str, Any]) -> Dict[str, float]:
        scores = {}

        # Tokenomics Strength Score
        # Assuming 'tokenomics_data' contains a 'distribution_score' and 'utility_score'
        tokenomics_data = data.get("tokenomics_data", {})
        distribution_score = tokenomics_data.get("distribution_score", 0.5) # Placeholder
        utility_score = tokenomics_data.get("utility_score", 0.5) # Placeholder
        scores["tokenomics_strength"] = (distribution_score + utility_score) / 2 * 10 # Scale to 1-10

        # Sentiment Health Score
        # Assuming 'sentiment_data' contains a 'positive_sentiment_ratio' and 'negative_sentiment_ratio'
        sentiment_data = data.get("sentiment_data", {})
        positive_ratio = sentiment_data.get("positive_sentiment_ratio", 0.5) # Placeholder
        negative_ratio = sentiment_data.get("negative_sentiment_ratio", 0.5) # Placeholder
        scores["sentiment_health"] = (positive_ratio - negative_ratio + 1) / 2 * 10 # Scale to 1-10

        # Code Maturity Score
        # Assuming 'code_audit_data' contains 'lines_of_code', 'test_coverage', 'bug_density'
        code_audit_data = data.get("code_audit_data", {})

        test_coverage = code_audit_data.get("test_coverage", 0.7) # Placeholder
        bug_density = code_audit_data.get("bug_density", 0.1) # Placeholder
        # Simple rule: higher coverage, lower bug density, reasonable LOC
        scores["code_maturity"] = (test_coverage * 0.6 + (1 - bug_density) * 0.4) * 10 # Scale to 1-10

        # Audit Confidence Score
        # Assuming 'audit_data' contains 'num_audits', 'critical_findings_resolved'
        audit_data = data.get("audit_data", {})
        num_audits = audit_data.get("num_audits", 1) # Placeholder
        critical_resolved = audit_data.get("critical_findings_resolved", 1.0) # Placeholder (1.0 means all resolved)
        # Simple rule: more audits, all critical findings resolved
        scores["audit_confidence"] = min(num_audits * 2, 5) + critical_resolved * 5 # Scale to 1-10

        # Team Credibility Score
        # Assuming 'team_data' contains 'team_experience_score', 'transparency_score'
        team_data = data.get("team_data", {})
        experience_score = team_data.get("team_experience_score", 0.7) # Placeholder
        transparency_score = team_data.get("transparency_score", 0.8) # Placeholder
        scores["team_credibility"] = (experience_score * 0.5 + transparency_score * 0.5) * 10 # Scale to 1-10

        return scores

    def build_final_summary(self, nlg_outputs: Dict[str, str], scores: Dict[str, float], agent_errors: Dict[str, Any]) -> Dict[str, Any]:
        overall_summary_parts = []
        for agent, output in nlg_outputs.items():
            overall_summary_parts.append(f"{agent.replace('_', ' ').title()} Insights: {output}")
        overall_summary = "\n\n".join(overall_summary_parts)

        weaknesses = [
            score_name.replace('_', ' ').title()
            for score_name, score_value in scores.items()
            if score_value < 5.0
        ]

        strengths = [
            score_name.replace('_', ' ').title()
            for score_name, score_value in scores.items()
            if score_value >= 7.0
        ]

        error_report = []
        for agent_name, error_details in agent_errors.items():
            error_report.append({
                "agent_name": agent_name.replace('_', ' ').title(),
                "timestamp": error_details.get("timestamp"),
                "error_message": error_details.get("error_message")
            })

        final_summary = {
            "overall_summary": overall_summary,
            "scores": {score_name.replace('_', ' ').title(): round(score_value, 2) for score_name, score_value in scores.items()},
            "weaknesses": weaknesses,
            "strengths": strengths,
            "error_report": error_report
        }
        return final_summary
