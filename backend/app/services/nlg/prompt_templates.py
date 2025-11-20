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
        "social_sentiment": """
        Analyze the following social sentiment data, including sentiment scores and community perception.
        Generate a concise written summary that highlights overall trends, key community directions,
        and any significant shifts in public opinion. Emphasize both positive and negative aspects,
        and their potential implications for the project.

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
        """,
        "team_roles_summary": """
        Based on the following team member data, summarize the key roles and responsibilities
        identified within the team. Highlight the diversity of roles and how they contribute
        to the project's overall structure and execution.

        Team Member Data:
        {team_data}
        """,
        "team_experience_summary": """
        Analyze the provided team member data to summarize the collective experience and expertise
        within the team. Focus on relevant industry experience, technical skills, and past project
        successes. Discuss how this experience strengthens the team's ability to deliver.

        Team Member Data:
        {team_data}
        """,
        "team_credibility_summary": """
        From the given team member data, assess and summarize the team's credibility.
        Consider factors like verified credentials, significant past achievements,
        and public recognition. Explain why the team is credible and trustworthy.

        Team Member Data:
        {team_data}
        """,
        "documentation_strength_summary": """
        Evaluate the strength and comprehensiveness of the project documentation
        based on the provided documentation data. Highlight well-documented areas,
        clarity, and accessibility. Discuss how strong documentation supports
        user adoption and developer engagement.

        Documentation Data:
        {doc_data}
        """
    }
    return templates.get(section_id, "No template found for this section ID.")

def fill_template(template: str, **kwargs) -> str:
    """
    Fills a given template with the provided data using keyword arguments.
    This allows for flexible placeholder names in the template.
    """
    return template.format(**kwargs)
