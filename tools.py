from langchain_core.tools import tool
from tavily import TavilyClient
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import requests
import os

load_dotenv()


# Tavily client
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


# --------------------------------------------------
# Tool 1: Web Search using Tavily
# --------------------------------------------------

@tool
def web_search(query: str) -> str:
    """Search the web using Tavily and return relevant search results."""

    response = tavily_client.search(
        query=query,
        search_depth="advanced",
        max_results=5
    )

    results = []

    for result in response.get("results", []):
        results.append(
            f"Title: {result.get('title', '')}\n"
            f"URL: {result.get('url', '')}\n"
            f"Content: {result.get('content', '')}\n"
        )

    return "\n---\n".join(results)


# --------------------------------------------------
# Tool 2: Web Scraping using BeautifulSoup
# --------------------------------------------------

@tool
def scrape_url(url: str) -> str:
    """Scrape readable text from a webpage."""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        # Don't crash the agent for blocked/dead pages
        if response.status_code == 403:
            return (
                f"SCRAPING FAILED: Website blocked automated access (403).\n"
                f"URL: {url}\n"
                f"Instruction: Use web_search to find another accessible source."
            )

        if response.status_code == 404:
            return (
                f"SCRAPING FAILED: Page not found (404).\n"
                f"URL: {url}\n"
                f"Instruction: Use web_search to find another source."
            )

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove unnecessary HTML
        for element in soup(
            ["script", "style", "nav", "footer", "header", "aside"]
        ):
            element.decompose()

        text = soup.get_text(separator="\n")

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        return "\n".join(lines)

    except requests.RequestException as e:
        return (
            f"SCRAPING FAILED.\n"
            f"URL: {url}\n"
            f"Error: {str(e)}\n"
            f"Instruction: Use web_search to find another accessible source."
        )
