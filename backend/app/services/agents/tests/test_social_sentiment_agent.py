import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from backend.app.services.agents.social_sentiment_agent import SocialSentimentAgent

@pytest.mark.asyncio
async def test_fetch_social_data_success():
    agent = SocialSentimentAgent()
    token_id = "TestToken"

    with patch('asyncio.sleep', new=AsyncMock()): # Mock asyncio.sleep to speed up tests
        data = await agent.fetch_social_data(token_id)

        assert isinstance(data, list)
        assert len(data) == 6 # 2 from Twitter, 2 from Reddit, 2 from News
        
        # Verify content from Twitter
        twitter_data = [item for item in data if item.get("source") == "twitter"]
        assert len(twitter_data) == 2
        assert any(f"Great news about {token_id}!" in item.get("text", "") for item in twitter_data)
        assert any(f"{token_id} is a scam." in item.get("text", "") for item in twitter_data)

        # Verify content from Reddit
        reddit_data = [item for item in data if item.get("source") == "reddit"]
        assert len(reddit_data) == 2
        assert any(f"Loving the community around {token_id}." in item.get("text", "") for item in reddit_data)
        assert any(f"Is {token_id} going to zero?" in item.get("text", "") for item in reddit_data)

        # Verify content from News
        news_data = [item for item in data if item.get("source") == "news"]
        assert len(news_data) == 2
        assert any(f"Analyst predicts bright future for {token_id}." in item.get("text", "") for item in news_data)
        assert any(f"Concerns raised over {token_id} security." in item.get("text", "") for item in news_data)

@pytest.mark.asyncio
async def test_fetch_social_data_api_failure_one_source():
    agent = SocialSentimentAgent()
    token_id = "TestToken"

    # Create a mock for asyncio.sleep that raises an exception on its first call
    mock_sleep = AsyncMock(side_effect=[Exception("Simulated Twitter API error"), None, None])

    with patch('asyncio.sleep', new=mock_sleep), \
         patch('backend.app.services.agents.social_sentiment_agent.logger.error') as mock_logger_error:
        data = await agent.fetch_social_data(token_id)

        # Verify error was logged for Twitter
        mock_logger_error.assert_called_with(f"Error fetching Twitter data for {token_id}: Simulated Twitter API error")
        
        # Verify data from other sources is still present
        assert isinstance(data, list)
        assert len(data) == 4 # Only Reddit and News data should be present (2 each)
        assert not any(item.get("source") == "twitter" for item in data)
        assert any(item.get("source") == "reddit" for item in data)
        assert any(item.get("source") == "news" for item in data)

@pytest.mark.asyncio
async def test_fetch_social_data_all_api_failures():
    agent = SocialSentimentAgent()
    token_id = "TestToken"

    # Create a mock for asyncio.sleep that raises an exception on all calls
    mock_sleep = AsyncMock(side_effect=[Exception("Twitter error"), Exception("Reddit error"), Exception("News error")])

    with patch('asyncio.sleep', new=mock_sleep), \
         patch('backend.app.services.agents.social_sentiment_agent.logger.error') as mock_logger_error:
        data = await agent.fetch_social_data(token_id)
        
        assert isinstance(data, list)
        assert len(data) == 0 # No data should be returned if all APIs fail
        assert mock_logger_error.call_count == 3 # Verify errors logged for all three sources

@pytest.mark.asyncio
async def test_analyze_sentiment_positive():
    agent = SocialSentimentAgent()
    positive_data = [
        {"source": "twitter", "text": "This token is absolutely fantastic and will skyrocket!"},
        {"source": "reddit", "text": "This project is incredibly promising and has immense potential."},
        {"source": "news", "text": "Leading analysts predict unprecedented growth and success for the token."}
    ]
    sentiment_report = await agent.analyze_sentiment(positive_data)

    assert sentiment_report["overall_sentiment"] == "positive"
    assert sentiment_report["score"] > 0.1
    assert len(sentiment_report["details"]) == 3
    for item in sentiment_report["details"]:
        assert item["polarity_score"] > 0 # Individual items should have positive polarity
        assert item["sentiment"] == "positive" or item["sentiment"] == "neutral" # Allow for neutral if polarity is between 0 and 0.1

@pytest.mark.asyncio
async def test_analyze_sentiment_negative():
    agent = SocialSentimentAgent()
    negative_data = [
        {"source": "twitter", "text": "This token is an absolute catastrophe, a complete and utter disaster. It is worthless."},
        {"source": "reddit", "text": "The project is a total scam, utterly doomed to fail. Price will crash to zero."},
        {"source": "news", "text": "Devastating reports of severe security breaches and an imminent, irreversible collapse."}
    ]
    sentiment_report = await agent.analyze_sentiment(negative_data)

    assert sentiment_report["overall_sentiment"] == "negative"
    assert sentiment_report["score"] < -0.1
    assert len(sentiment_report["details"]) == 3
    for item in sentiment_report["details"]:
        assert item["polarity_score"] < 0 # Individual items should have negative polarity
        assert item["sentiment"] == "negative" or item["sentiment"] == "neutral" # Allow for neutral if polarity is between -0.1 and 0

@pytest.mark.asyncio
async def test_analyze_sentiment_neutral():
    agent = SocialSentimentAgent()
    neutral_data = [
        {"source": "twitter", "text": "The token price is currently 1.5 USD."},
        {"source": "reddit", "text": "I just acquired some tokens for my portfolio."},
        {"source": "news", "text": "The token's market capitalization is 100 million dollars."}
    ]
    sentiment_report = await agent.analyze_sentiment(neutral_data)

    assert sentiment_report["overall_sentiment"] == "neutral"
    assert -0.1 <= sentiment_report["score"] <= 0.1
    assert len(sentiment_report["details"]) == 3
    for item in sentiment_report["details"]:
        assert -0.1 <= item["polarity_score"] <= 0.1 # Individual items should have neutral polarity
        assert item["sentiment"] == "neutral"

@pytest.mark.asyncio
async def test_analyze_sentiment_mixed():
    agent = SocialSentimentAgent()
    mixed_data = [
        {"source": "twitter", "text": "This token is absolutely fantastic!"}, # Positive (0.5)
        {"source": "reddit", "text": "This is a very bad project, avoid it."},
        {"source": "news", "text": "A neutral report on the token's recent performance."}
    ]
    sentiment_report = await agent.analyze_sentiment(mixed_data)

    assert sentiment_report["overall_sentiment"] in {"neutral", "negative"}
    assert sentiment_report["score"] <= 0.0
    assert len(sentiment_report["details"]) == 3
    
    # Verify individual sentiments
    assert sentiment_report["details"][0]["sentiment"] == "positive"
    assert sentiment_report["details"][1]["sentiment"] == "negative"
    assert sentiment_report["details"][2]["sentiment"] == "neutral"

@pytest.mark.asyncio
async def test_analyze_sentiment_empty_data():
    agent = SocialSentimentAgent()
    empty_data = []
    sentiment_report = await agent.analyze_sentiment(empty_data)

    assert sentiment_report["overall_sentiment"] == "neutral"
    assert sentiment_report["score"] == 0.0
    assert sentiment_report["details"] == []

@pytest.mark.asyncio
async def test_analyze_sentiment_data_no_text_field():
    agent = SocialSentimentAgent()
    data_no_text = [
        {"source": "twitter", "id": "1"},
        {"source": "reddit", "id": "2", "text": "This is a moderately positive statement."},
        {"source": "news", "id": "3"}
    ]
    sentiment_report = await agent.analyze_sentiment(data_no_text)

    # With one moderately positive and two neutral (no text), the overall should be slightly positive or neutral
    assert sentiment_report["overall_sentiment"] == "neutral" or sentiment_report["overall_sentiment"] == "positive"
    assert sentiment_report["score"] >= 0.0 # Should be non-negative due to one positive statement
    assert len(sentiment_report["details"]) == 3
    
    # Verify handling of items without text
    assert sentiment_report["details"][0]["text"] == "No text available"
    assert sentiment_report["details"][0]["sentiment"] == "neutral"
    assert sentiment_report["details"][0]["polarity_score"] == 0.0

    assert sentiment_report["details"][1]["text"] == "This is a moderately positive statement."
    assert sentiment_report["details"][1]["sentiment"] == "positive"
    assert sentiment_report["details"][1]["polarity_score"] > 0.0

    assert sentiment_report["details"][2]["text"] == "No text available"
    assert sentiment_report["details"][2]["sentiment"] == "neutral"
    assert sentiment_report["details"][2]["polarity_score"] == 0.0

@pytest.mark.asyncio
async def test_analyze_sentiment_json_output_structure():
    agent = SocialSentimentAgent()
    sample_data = [
        {"source": "twitter", "text": "Positive tweet."},
        {"source": "reddit", "text": "Negative comment."}
    ]
    sentiment_report = await agent.analyze_sentiment(sample_data)

    assert isinstance(sentiment_report, dict)
    assert "overall_sentiment" in sentiment_report
    assert "score" in sentiment_report
    assert "details" in sentiment_report

    assert isinstance(sentiment_report["overall_sentiment"], str)
    assert isinstance(sentiment_report["score"], float)
    assert isinstance(sentiment_report["details"], list)

    for detail in sentiment_report["details"]:
        assert isinstance(detail, dict)
        assert "source" in detail
        assert "text" in detail
        assert "sentiment" in detail
        assert "polarity_score" in detail
        assert isinstance(detail["source"], str)
        assert isinstance(detail["text"], str)
        assert isinstance(detail["sentiment"], str)
        assert isinstance(detail["polarity_score"], float)
