import asyncio
import logging
from typing import List, Dict, Any
from textblob import TextBlob
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Define a retry decorator for API calls at the module level
api_retry_decorator = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(Exception), # Can be refined to specific API rate limit exceptions
    reraise=True
)

class SocialSentimentAgent:
    def __init__(self):
        # Placeholder for API key management. In a real application, use a secure method
        # to load API keys (e.g., environment variables, a secrets manager).
        self.twitter_api_key = "YOUR_TWITTER_API_KEY"
        self.reddit_api_key = "YOUR_REDDIT_API_KEY"
        self.news_api_key = "YOUR_NEWS_API_KEY"

    @api_retry_decorator
    async def _fetch_twitter_data(self, token_id: str) -> List[Dict[str, Any]]:
        logger.info(f"Attempting to fetch Twitter data for {token_id}...")
        await asyncio.sleep(1) # Simulate network delay
        twitter_data = [{"source": "twitter", "text": f"Great news about {token_id}!", "id": "1"},
                        {"source": "twitter", "text": f"{token_id} is a scam.", "id": "2"}]
        logger.info(f"Successfully fetched Twitter data for {token_id}.")
        return twitter_data

    @api_retry_decorator
    async def _fetch_reddit_data(self, token_id: str) -> List[Dict[str, Any]]:
        logger.info(f"Attempting to fetch Reddit data for {token_id}...")
        await asyncio.sleep(1) # Simulate network delay
        reddit_data = [{"source": "reddit", "text": f"Loving the community around {token_id}.", "id": "3"},
                       {"source": "reddit", "text": f"Is {token_id} going to zero?", "id": "4"}]
        logger.info(f"Successfully fetched Reddit data for {token_id}.")
        return reddit_data

    @api_retry_decorator
    async def _fetch_news_data(self, token_id: str) -> List[Dict[str, Any]]:
        logger.info(f"Attempting to fetch News data for {token_id}...")
        await asyncio.sleep(1) # Simulate network delay
        news_data = [{"source": "news", "text": f"Analyst predicts bright future for {token_id}.", "id": "5"},
                     {"source": "news", "text": f"Concerns raised over {token_id} security.", "id": "6"}]
        logger.info(f"Successfully fetched News data for {token_id}.")
        return news_data

    async def fetch_social_data(self, token_id: str) -> List[Dict[str, Any]]:
        """
        Fetches social media data (posts, tweets, comments) for a given token_id.
        Includes rate-limit handling and error logging.
        """
        all_data = []
        
        # --- Twitter API integration ---
        try:
            twitter_data = await self._fetch_twitter_data(token_id)
            all_data.extend(twitter_data)
        except Exception as e:
            logger.error(f"Failed to fetch Twitter data for {token_id} after multiple retries: {e}")

        # --- Reddit API integration ---
        try:
            reddit_data = await self._fetch_reddit_data(token_id)
            all_data.extend(reddit_data)
        except Exception as e:
            logger.error(f"Failed to fetch Reddit data for {token_id} after multiple retries: {e}")

        # --- News Aggregator API integration ---
        try:
            news_data = await self._fetch_news_data(token_id)
            all_data.extend(news_data)
        except Exception as e:
            logger.error(f"Failed to fetch News data for {token_id} after multiple retries: {e}")

        return all_data

    async def analyze_sentiment(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Performs sentiment analysis on the collected data and summarizes community perception.
        Returns a sentiment score (positive, neutral, negative).
        """
        if not data:
            logger.warning("No data provided for sentiment analysis.")
            return {"overall_sentiment": "neutral", "score": 0.0, "details": []}

        sentiments = []
        details = []

        for item in data:
            text = item.get("text", "")
            if text:
                analysis = TextBlob(text)
                polarity = analysis.sentiment.polarity # -1.0 to +1.0
                
                sentiment_label = "neutral"
                if polarity > 0.1: # Threshold for positive sentiment
                    sentiment_label = "positive"
                elif polarity < -0.1: # Threshold for negative sentiment
                    sentiment_label = "negative"
                
                sentiments.append(polarity)
                details.append({
                    "source": item.get("source", "unknown"),
                    "text": text,
                    "sentiment": sentiment_label,
                    "polarity_score": polarity
                })
            else:
                details.append({
                    "source": item.get("source", "unknown"),
                    "text": "No text available",
                    "sentiment": "neutral",
                    "polarity_score": 0.0
                })

        if not sentiments:
            return {"overall_sentiment": "neutral", "score": 0.0, "details": details}

        average_polarity = sum(sentiments) / len(sentiments)

        overall_sentiment_label = "neutral"
        if average_polarity > 0.1:
            overall_sentiment_label = "positive"
        elif average_polarity < -0.1:
            overall_sentiment_label = "negative"

        logger.info(f"Sentiment analysis complete. Overall sentiment: {overall_sentiment_label} (Score: {average_polarity:.2f})")
        return {
            "overall_sentiment": overall_sentiment_label,
            "score": round(average_polarity, 4),
            "details": details
        }

if __name__ == "__main__":
    async def main():
        agent = SocialSentimentAgent()
        token = "ExampleToken"
        
        print(f"--- Fetching social data for {token} ---")
        social_data = await agent.fetch_social_data(token)
        print("\n--- Analyzing sentiment ---")
        sentiment_report = await agent.analyze_sentiment(social_data)
        
        import json
        print(json.dumps(sentiment_report, indent=2))

    asyncio.run(main())
