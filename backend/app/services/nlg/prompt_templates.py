"""
This module contains prompt templates for various report sections and a utility function
to dynamically fill these templates with data.
"""

def get_template(section_id: str) -> str:
    """
    Retrieves a prompt template based on the section ID.
    """
    templates = {
        "tokenomics": """
        Analyze the following tokenomics data and provide a comprehensive summary,
        highlighting key aspects such as token distribution, vesting schedules,
        inflation/deflation mechanisms, and any potential risks or advantages.
        Focus on how these factors impact the long-term value and stability of the token.

        Tokenomics Data:
        {data}
        """,
        "onchain_metrics": """
        Examine the provided on-chain metrics and generate an insightful analysis.
        Cover aspects like active addresses, transaction volume, whale activity,
        and network growth. Explain the implications of these metrics for the
        project's health and adoption.

        On-chain Metrics Data:
        {data}
        """,
        "sentiment": """
        Review the social sentiment data and summarize the overall market perception
        of the project. Identify key themes, positive or negative trends, and
        any significant events influencing sentiment. Discuss the potential impact
        of this sentiment on the project's future.

        Sentiment Data:
        {data}
        """,
        "team_analysis": """
        Analyze the team's background, experience, and contributions based on the
        provided data. Assess the team's capability to execute the project roadmap
        and highlight any strengths or weaknesses.

        Team Analysis Data:
        {data}
        """,
        "documentation": """
        Evaluate the quality and completeness of the project's documentation.
        Identify areas of excellence and areas needing improvement. Discuss how
        effective documentation contributes to user adoption and developer engagement.

        Documentation Data:
        {data}
        """,
        "code_audit": """
        Summarize the findings from the code audit report. Highlight critical
        vulnerabilities, security best practices followed, and overall code quality.
        Explain the implications of these findings for the project's security and reliability.

        Code Audit Data:
        {data}
        """,
        "risk_factors": """
        Based on the provided data, identify and elaborate on the key risk factors
        associated with the project. Categorize risks (e.g., technical, market, regulatory)
        and discuss their potential impact and mitigation strategies.

        Risk Factors Data:
        {data}
        """
    }
    return templates.get(section_id, "No template found for this section ID.")

def fill_template(template: str, data: str) -> str:
    """
    Fills a given template with the provided data.
    """
    return template.format(data=data)
