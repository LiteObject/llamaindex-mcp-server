"""
LlamaIndexDocServer module for fetching and searching LlamaIndex documentation resources.
"""

from typing import Any, Dict, List
import logging
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from models import MCPResource

logger = logging.getLogger(__name__)


class LlamaIndexDocServer:
    """Server for fetching and searching LlamaIndex documentation resources."""

    def __init__(self):
        """Initialize the LlamaIndexDocServer with base URL, HTTP client, and resource cache."""
        self.base_url = "https://docs.llamaindex.ai"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.cached_docs = {}
        self.resources = []

    async def initialize(self):
        """Initialize the server and fetch initial documentation structure."""
        try:
            await self._fetch_doc_structure()
            logger.info(
                "Initialized with %d documentation resources", len(self.resources))
        except httpx.HTTPStatusError as e:
            logger.error("HTTP status error during initialization: %s", e)
        except httpx.RequestError as e:
            logger.error("HTTP request error during initialization: %s", e)
        except (AttributeError, TypeError, ValueError) as e:
            logger.error("Unexpected error during initialization: %s", e)

    async def _fetch_doc_structure(self):
        """Fetch the documentation structure from LlamaIndex docs."""
        try:
            response = await self.client.get(f"{self.base_url}/en/stable/")
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            nav_links = soup.find_all('a', href=True)
            doc_links = []
            for link in nav_links:
                href = link.get('href')
                if href and (href.startswith('/') or href.startswith('http')):
                    if 'docs.llamaindex.ai' in href or href.startswith('/'):
                        full_url = urljoin(self.base_url, href)
                        title = link.get_text(strip=True)
                        if title and len(title) > 3:
                            doc_links.append((full_url, title))
            seen_urls = set()
            for url, title in doc_links[:50]:
                if url not in seen_urls:
                    seen_urls.add(url)
                    resource = MCPResource(
                        uri=url,
                        name=f"llamaindex_doc_{len(self.resources)}",
                        description=f"LlamaIndex Documentation: {title}",
                        mime_type="text/html"
                    )
                    self.resources.append(resource)
        except httpx.RequestError as e:
            logger.error("HTTP error fetching doc structure: %s", e)
            self._add_default_resources()
        except (AttributeError, TypeError, ValueError) as e:
            logger.error("Unexpected error fetching doc structure: %s", e)
            self._add_default_resources()

    def _add_default_resources(self):
        """Add default LlamaIndex documentation resources."""
        default_docs = [
            ("/en/stable/getting_started/starter_example.html", "Getting Started"),
            ("/en/stable/module_guides/loading/", "Data Loading"),
            ("/en/stable/module_guides/indexing/", "Indexing"),
            ("/en/stable/module_guides/querying/", "Querying"),
            ("/en/stable/module_guides/agents/", "Agents"),
        ]
        for path, title in default_docs:
            resource = MCPResource(
                uri=f"{self.base_url}{path}",
                name=f"llamaindex_{title.lower().replace(' ', '_')}",
                description=f"LlamaIndex Documentation: {title}",
                mime_type="text/html"
            )
            self.resources.append(resource)

    async def fetch_resource_content(self, uri: str) -> str:
        """Fetch content for a specific documentation resource by URI."""
        if uri in self.cached_docs:
            return self.cached_docs[uri]
        try:
            response = await self.client.get(uri)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            main_content = soup.find('main') or soup.find(
                'article') or soup.find('div', class_='content')
            if main_content:
                for script in main_content(["script", "style", "nav", "header", "footer"]):
                    script.decompose()
                content = main_content.get_text(separator='\n', strip=True)
            else:
                content = soup.get_text(separator='\n', strip=True)
            self.cached_docs[uri] = content
            return content
        except httpx.RequestError as e:
            logger.error("HTTP error fetching content from %s: %s", uri, e)
            return f"HTTP error fetching content: {str(e)}"
        except httpx.HTTPError as e:
            logger.error("HTTP error fetching content from %s: %s", uri, e)
            return f"HTTP error fetching content: {str(e)}"
        except (AttributeError, TypeError, ValueError) as e:
            logger.error(
                "Unexpected error fetching content from %s: %s", uri, e)
            return f"Unexpected error fetching content: {str(e)}"

    async def search_documentation(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search through cached documentation for a query string."""
        results = []
        query_lower = query.lower()
        for resource in self.resources:
            if query_lower in resource.description.lower() or query_lower in resource.name.lower():
                content = await self.fetch_resource_content(resource.uri)
                if query_lower in content.lower():
                    lines = content.split('\n')
                    relevant_lines = [
                        line for line in lines if query_lower in line.lower()]
                    snippet = '\n'.join(relevant_lines[:3])
                    results.append({
                        'uri': resource.uri,
                        'title': resource.description,
                        'snippet': snippet[:200] + '...' if len(snippet) > 200 else snippet
                    })
                    if len(results) >= limit:
                        break
        return results
