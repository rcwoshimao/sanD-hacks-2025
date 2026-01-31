# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from a2a.types import (
    AgentCapabilities, 
    AgentCard,
    AgentSkill)

AGENT_SKILL = AgentSkill(
    id="scrape_and_summarize",
    name="Scrape and Summarize",
    description="Scrapes a URL and summarizes the content using LLM.",
    tags=["scraping", "news", "summarization"],
    examples=[
        "Scrape and summarize: https://reddit.com/r/technology",
        "Scrape and summarize: https://example.com/news/article",
        "Get content from: https://news.ycombinator.com",
    ]
)   

AGENT_CARD = AgentCard(
    name='News Scraper Agent',
    id='news-scraper-agent',
    description='An AI agent that scrapes web pages and summarizes content using LLM.',
    url='',
    version='1.0.0',
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[AGENT_SKILL],
    supportsAuthenticatedExtendedCard=False,
)