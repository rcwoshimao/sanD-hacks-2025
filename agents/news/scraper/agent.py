# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
Moltbook News Scraper Agent

This agent fetches top posts from Moltbook communities using the Moltbook API
and generates summaries using LLM analysis.

Workflow:
1. Extract submolt name from URL
2. Fetch top posts from Moltbook API
3. Analyze posts with LLM
4. Generate 1-2 paragraph summary

API Documentation: https://www.moltbook.com/skill.md
"""

import logging
import re
import os
import requests
from datetime import datetime
from typing import List, Dict, Any

from llama_index.llms.litellm import LiteLLM
from llama_index.llms.azure_openai import AzureOpenAI
from config.config import LLM_MODEL
from ioa_observe.sdk.decorators import tool

logger = logging.getLogger("lungo.news_scraper.agent")

# --- Moltbook API Configuration ---
MOLTBOOK_API_BASE = "https://www.moltbook.com/api/v1"
MOLTBOOK_API_KEY = os.getenv("MOLTBOOK_API_KEY")

if not MOLTBOOK_API_KEY:
    logger.warning("MOLTBOOK_API_KEY not set. API calls will fail. Set this environment variable to enable Moltbook access.")

# --- LLM Configuration ---
litellm_proxy_base_url = os.getenv("LITELLM_PROXY_BASE_URL")
litellm_proxy_api_key = os.getenv("LITELLM_PROXY_API_KEY")

if not LLM_MODEL:
    raise ValueError("LLM_MODEL is not configured. Please set LLM_MODEL in your .env file.")

if litellm_proxy_base_url and litellm_proxy_api_key:
    logger.info(f"Using LLM via LiteLLM proxy: {litellm_proxy_base_url}")
    llm = AzureOpenAI(
        engine=LLM_MODEL,
        azure_endpoint=litellm_proxy_base_url,
        api_key=litellm_proxy_api_key
    )
else:
    logger.info(f"Using LiteLLM with model: {LLM_MODEL}")
    llm = LiteLLM(LLM_MODEL)


# --- Moltbook API Client ---

def extract_submolt_name(url: str) -> str | None:
    """
    Extract submolt name from a Moltbook URL.
    
    Examples:
        https://www.moltbook.com/m/technology -> technology
        https://moltbook.com/m/ai-agents -> ai-agents
    
    Args:
        url: Moltbook community URL
    
    Returns:
        Submolt name or None if not found
    """
    # Match /m/submolt-name pattern
    match = re.search(r'/m/([a-zA-Z0-9_-]+)', url)
    return match.group(1) if match else None


def fetch_moltbook_posts(submolt: str, sort: str = "hot", limit: int = 10) -> Dict[str, Any]:
    """
    Fetch posts from Moltbook API.
    
    API Endpoint: GET /api/v1/submolts/{submolt}/feed
    
    Args:
        submolt: Submolt name (e.g., "technology", "ai-agents")
        sort: Sort order - "hot", "new", "top", "rising"
        limit: Number of posts to fetch (max 25)
    
    Returns:
        Dict with posts and metadata
    
    Raises:
        Exception if API call fails
    """
    if not MOLTBOOK_API_KEY:
        raise ValueError("MOLTBOOK_API_KEY environment variable not set. Please register at https://www.moltbook.com and set your API key.")
    
    url = f"{MOLTBOOK_API_BASE}/submolts/{submolt}/feed"
    headers = {
        "Authorization": f"Bearer {MOLTBOOK_API_KEY}",
        "Content-Type": "application/json"
    }
    params = {
        "sort": sort,
        "limit": min(limit, 25)  # API max is 25
    }
    
    logger.info(f"Fetching posts from Moltbook: submolt={submolt}, sort={sort}, limit={limit}")
    
    response = requests.get(url, headers=headers, params=params, timeout=30)
    
    if response.status_code == 401:
        raise ValueError("Invalid MOLTBOOK_API_KEY. Please check your API key.")
    elif response.status_code == 404:
        raise ValueError(f"Submolt '{submolt}' not found on Moltbook.")
    elif response.status_code != 200:
        raise Exception(f"Moltbook API error: {response.status_code} - {response.text}")
    
    data = response.json()
    
    if not data.get("success", False):
        raise Exception(f"Moltbook API returned error: {data.get('error', 'Unknown error')}")
    
    return data


def transform_moltbook_posts(api_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Transform Moltbook API response to our standard post format.
    
    Args:
        api_response: Raw response from Moltbook API
    
    Returns:
        List of posts in standard format
    """
    posts = api_response.get("posts", api_response.get("data", []))
    
    transformed = []
    for post in posts:
        # Calculate simple sentiment based on vote ratio
        upvotes = post.get("upvotes", 0)
        downvotes = post.get("downvotes", 0)
        total_votes = upvotes + downvotes
        
        if total_votes == 0:
            sentiment = "neutral"
        elif upvotes / total_votes > 0.7:
            sentiment = "positive"
        elif upvotes / total_votes < 0.3:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        transformed.append({
            "id": post.get("id", ""),
            "title": post.get("title", ""),
            "content": post.get("content", ""),
            "upvotes": upvotes,
            "downvotes": downvotes,
            "comments_count": post.get("comment_count", post.get("comments_count", 0)),
            "timestamp": post.get("created_at", datetime.utcnow().isoformat() + "Z"),
            "sentiment": sentiment,
            "author": post.get("author", {}).get("name", "unknown")
        })
    
    return transformed


# --- Tool Functions ---

@tool(name="scrape_moltbook_tool")
def scrape_moltbook_tool(url: str) -> Dict[str, Any]:
    """
    Scrape top 10 posts from a Moltbook community.
    
    Currently returns mock data. In production, this will:
    - Fetch HTML from the Moltbook URL
    - Parse posts using BeautifulSoup
    - Filter to past 24 hours
    - Sort by engagement
    - Return top 10 posts
    
    Args:
        url: Moltbook community URL (e.g., https://www.moltbook.com/m/technology)
    
    Returns:
        Dict with posts list and metadata
    """
    logger.info(f"Fetching Moltbook posts for URL: {url}")
    
    # Extract submolt name from URL
    submolt = extract_submolt_name(url)
    if not submolt:
        raise ValueError(f"Could not extract submolt name from URL: {url}. Expected format: https://www.moltbook.com/m/submolt-name")
    
    logger.info(f"Extracted submolt: {submolt}")
    
    # Fetch posts from Moltbook API
    api_response = fetch_moltbook_posts(submolt, sort="hot", limit=10)
    
    # Transform to standard format
    posts = transform_moltbook_posts(api_response)
    
    result = {
        "url": url,
        "submolt": submolt,
        "posts": posts,
        "post_count": len(posts),
        "sort": "hot",
        "fetched_at": datetime.utcnow().isoformat() + "Z"
    }
    
    logger.info(f"Fetched {len(posts)} posts from m/{submolt}")
    return result


@tool(name="analyze_posts_tool")
def analyze_posts_tool(posts: List[Dict[str, Any]], community_url: str) -> str:
    """
    Analyze scraped posts using LLM to generate insights.
    
    Identifies:
    - Main themes and trending topics
    - Overall sentiment and tone
    - Notable developments or concerns
    - Emerging debates or consensus
    
    Args:
        posts: List of post dictionaries from scrape_moltbook_tool
        community_url: The community URL for context
    
    Returns:
        Analysis text (4-6 sentences)
    """
    logger.info(f"Analyzing {len(posts)} posts from {community_url}")
    
    # Format posts for LLM
    posts_text = "\n\n".join([
        f"**Post {i+1}:** {p['title']}\n"
        f"Content: {p['content']}\n"
        f"Engagement: {p['upvotes']} upvotes, {p['comments_count']} comments\n"
        f"Sentiment: {p['sentiment']}"
        for i, p in enumerate(posts)
    ])
    
    prompt = f"""You are a sophisticated reporter, and you write reports based on collected data from a Reddit-like platform called Moltbook for AI agents.

Analyze these top 10 posts from the community and provide insights:

{posts_text}

Your analysis should:
1. Identify the main themes and trending topics (what are agents discussing?)
2. Assess the overall sentiment and tone of the community
3. Highlight any notable developments, concerns, or announcements

write your response in the following format (as a JSON object): 
{{"title": "Lorem ipsum title",
"summary": "Short summary here.",
"content": "Full article content text goes here."}}"""

    logger.debug(f"Sending analysis prompt to LLM")
    resp = llm.complete(prompt, formatted=True)
    analysis = resp.text.strip()
    
    logger.info(f"Analysis generated: {len(analysis)} characters")
    return analysis


def generate_summary(url: str, posts: List[Dict[str, Any]], analysis: str) -> str:
    """
    Generate the final formatted summary combining scraped data and analysis.
    
    Args:
        url: The Moltbook community URL
        posts: List of scraped posts
        analysis: LLM-generated analysis text
    
    Returns:
        Formatted markdown summary (1-2 paragraphs)
    """
    # Find top post by engagement
    top_post = max(posts, key=lambda p: p["upvotes"] + p["comments_count"])
    
    # Calculate sentiment distribution
    sentiments = [p["sentiment"] for p in posts]
    positive = sentiments.count("positive")
    negative = sentiments.count("negative")
    neutral = sentiments.count("neutral")
    
    summary = f"""# Moltbook Community Summary: {url}

**Time Period:** Past 24 hours

## Community Activity Summary

{analysis}

---
*Report generated by Moltbook AI Agent News Service*"""
    
    return summary


# --- Main Agent Class ---

class ScraperAgent:
    """
    Moltbook News Scraper Agent.
    
    Processes requests to scrape and summarize Moltbook communities.
    Uses a linear workflow:
    1. Extract URL from message
    2. Scrape top 10 posts (mock data)
    3. Analyze with LLM
    4. Generate formatted summary
    """
    
    def __init__(self):
        logger.info("Initializing ScraperAgent")
    
    def _extract_url(self, text: str) -> str | None:
        """Extract URL from text using regex."""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)
        return urls[0] if urls else None
    
    async def ainvoke(self, prompt: str) -> str:
        """
        Process a scraping request.
        
        Args:
            prompt: User message containing Moltbook URL to scrape
        
        Returns:
            Formatted summary of the Moltbook community
        """
        logger.info(f"ScraperAgent received prompt: {prompt}")
        
        try:
            # Step 1: Extract URL
            url = self._extract_url(prompt)
            if not url:
                return "⚠️ No URL found in the request. Please provide a Moltbook URL to scrape (e.g., https://www.moltbook.com/m/technology)"
            
            logger.info(f"Extracted URL: {url}")
            
            # Step 2: Scrape top 10 posts (mock data for now)
            scrape_result = scrape_moltbook_tool(url)
            posts = scrape_result["posts"]
            
            if not posts:
                return f"⚠️ No posts found for URL: {url}"
            
            # Step 3: Analyze posts with LLM
            analysis = analyze_posts_tool(posts, url)
            
            # Step 4: Generate formatted summary
            summary = generate_summary(url, posts, analysis)
            
            logger.info(f"Successfully generated summary for {url}")
            return summary
            
        except Exception as e:
            logger.error(f"Error in ScraperAgent: {e}", exc_info=True)
            return f"⚠️ Error processing request: {str(e)}"
