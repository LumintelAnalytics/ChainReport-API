# Error Messages Specification

## Purpose
The `errorMessages` field in the ChainReport API response is designed to provide a centralized mechanism for capturing and communicating any non-fatal errors or warnings that occur during the report generation process, particularly those originating from individual data agents.

## Structure
The `errorMessages` field is a top-level property within the main report object. It is an array of strings.

```json
{
  "errorMessages": [
    "AgentX failed to retrieve data for price information: Connection timed out.",
    "SocialSentimentAgent encountered an issue processing Twitter data: API rate limit exceeded."
  ],
  "metadata": { ... },
  "tokenomics": { ... },
  // ... other report sections
}
```

## Usage
- **Agent Failures**: When an individual agent (e.g., `PriceAgent`, `SocialSentimentAgent`, `OnchainAgent`) encounters an error that prevents it from fully contributing its section to the report, it should add a descriptive error message to this list.
- **Non-blocking Errors**: This field is intended for errors that do not halt the entire report generation process but indicate partial data or issues with specific components.
- **Informational**: The messages should be informative enough for developers or support staff to understand the nature of the issue without needing to consult extensive logs.
- **Format**: Each error message should be a clear, concise string describing the agent involved (if applicable) and the specific problem encountered.

## Examples
- `"PriceAgent: Could not fetch real-time price data due to external API error."`
- `"TeamDocAgent: Failed to parse documentation from provided URL: Invalid content format."`
- `"OnchainAgent: Insufficient permissions to access historical transaction data."`