# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
import re
from typing import Literal

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.litellm import LiteLLM
from config.config import LLM_MODEL
from ioa_observe.sdk.decorators import tool, agent, graph
from llama_index.llms.azure_openai import AzureOpenAI
import os

logger = logging.getLogger("lungo.news_scraper.agent")

# Scraper agent is a llama_index based agent
# Initialize llm with llama_index_LiteLLM
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

# --- 1. Define Intent Type ---
IntentType = Literal["scrape", "general"]

# --- 2. Tool Functions ---

@tool(name="scrape_tool")
def handle_scrape_tool(user_message: str) -> str:
    """
    Handle scraping and summarization requests.
    Extracts URL from message, scrapes content, and summarizes using LLM.
    
    TODO (Person B): Implement actual web scraping logic here.
    - Use requests/BeautifulSoup to fetch HTML
    - Parse and extract text content
    - Use LLM to summarize
    """
    # Extract URL from message
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, user_message)
    
    if not urls:
        return "⚠️ SCRAPER FALLBACK: No URL found in the request. Please provide a URL to scrape."
    
    url = urls[0]
    logger.info(f"Scraping URL: {url}")
    
    # TODO (Person B): Implement actual scraping
    # For now, return a placeholder response
    prompt = (
        "You are a helpful web scraping assistant. "
        "A user wants to scrape and summarize content from: {url}\n\n"
        "Since scraping is not yet implemented, provide a helpful message explaining "
        "that the scraping functionality will be available soon. "
        "For now, acknowledge the URL: {url}"
    ).format(url=url)
    
    resp = llm.complete(prompt, formatted=True)
    text = resp.text.strip()
    logger.info(f"Scrape response generated: {text}")
    return text

@tool(name="general_tool")
def handle_general_tool(user_message: str) -> str:
    """Handle general queries that don't require scraping."""
    prompt = (
        "You are a helpful web scraping assistant. "
        "The user sent: {user_message}\n\n"
        "Please provide a helpful response."
    ).format(user_message=user_message)
    resp = llm.complete(prompt, formatted=True)
    text = resp.text.strip()
    logger.info(f"General response generated: {text}")
    return text

# --- 3. Sub-Agents ---

scrape_agent = FunctionAgent(
    name="scrape_agent",
    llm=llm,
    system_prompt="""You are a web scraping agent. Your job is to scrape URLs and summarize content.
    When you receive a request with a URL, use the scrape_tool to fetch and summarize the content.
    Always extract the URL from the user's message and pass it to the scrape_tool.""",
    tools=[handle_scrape_tool],
)

general_agent = FunctionAgent(
    name="general_agent",
    llm=llm,
    system_prompt="You are a helpful assistant for a web scraping service. Handle general queries politely.",
    tools=[handle_general_tool],
)

# --- 4. Root Agent (Coordinator) ---

root_agent = FunctionAgent(
    name="scraper_coordinator",
    llm=llm,
    system_prompt="""You are the main coordinator for a web scraping service.
    Your role is to analyze user queries and delegate to the appropriate specialist:
    
    - If the query contains a URL (http:// or https://), delegate to scrape_agent
    - Otherwise, delegate to general_agent
    
    Always delegate to the appropriate sub-agent based on the query content.""",
    tools=[],
    sub_agents=[scrape_agent, general_agent],
)

# --- 5. Agent Class Wrapper ---

class ScraperAgent:
    """
    Wrapper class for the scraper agent.
    Provides ainvoke method compatible with agent_executor.
    """
    def __init__(self):
        self.agent = root_agent
    
    async def ainvoke(self, prompt: str) -> str:
        """
        Invoke the scraper agent with a prompt.
        
        Args:
            prompt: User prompt containing URL to scrape or general query
            
        Returns:
            str: Scraped and summarized content
        """
        try:
            # Use the root agent to process the prompt
            response = await self.agent.achat(prompt)
            logger.debug(f"Response type: {type(response)}, Response: {response}")
            # Handle different response formats
            if hasattr(response, 'message') and hasattr(response.message, 'content'):
                return response.message.content
            elif hasattr(response, 'content'):
                return response.content
            elif isinstance(response, str):
                return response
            else:
                logger.error(f"Unexpected response format: {response}")
                return str(response)
        except Exception as e:
            logger.error(f"Error in scraper agent: {e}", exc_info=True)
            return f"⚠️ SCRAPER ERROR FALLBACK: Error processing request: {str(e)}"
