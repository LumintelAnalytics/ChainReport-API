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
        "code_audit_summary": """
        Based on the provided code audit and repository data, generate a comprehensive audit summary.
        The summary should include:
        1.  **Clarity Points**: Highlight aspects of the codebase that are well-structured,
            easy to understand, and follow best practices.
        2.  **Risk Highlights**: Identify potential security vulnerabilities, performance bottlenecks,
            or maintainability issues.
        3.  **Code Activity**: Summarize recent development activity, such as commit frequency,
            contributor engagement, and major feature implementations.
        4.  **Repository Quality Indicators**: Comment on aspects like test coverage,
            documentation quality, and adherence to coding standards.

        Handle cases where specific audit information might be missing by stating
        that the information is not available or could not be assessed.

        Code Audit Data:
        {code_data}

        Audit Data:
        {audit_data}
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
        """,
        "team_documentation": """
        Based on the provided team analysis and whitepaper summary, generate a comprehensive overview of the project's team and documentation.
        The summary should include:
        1.  **Team Analysis**: Summarize the team's background, experience, and contributions.
        2.  **Whitepaper Summary**: Provide a concise summary of the project's whitepaper, highlighting key aspects and technical details.

        Handle cases where specific information might be missing by stating that the information is not available or could not be assessed.

        Team Analysis Data:
        {team_analysis}

        Whitepaper Summary Data:
        {whitepaper_summary}
        """
    }
    return templates.get(section_id, "No template found for this section ID.")

def fill_template(template: str, **kwargs) -> str:
    """
    Fills a given template with the provided data using keyword arguments.
    This allows for flexible placeholder names in the template.
    """
    return template.format(**kwargs)
