import httpx
from bs4 import BeautifulSoup
import urllib.parse

from modules.base_modules import OSINTModule

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}


class WebSearch(OSINTModule):
    name = "web_search"
    description = "Searches the web via DuckDuckGo. Returns titles, URLs and snippets."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "max_results": {"type": "integer", "description": "Maximum number of results (default 10)"}
        },
        "required": ["query"]
    }

    async def execute(self, query: str, max_results: int = 10) -> dict:
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"

            async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
                response = await client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            results = []
            for result in soup.find_all('div', class_='result__body')[:max_results]:
                title_elem = result.find('a', class_='result__a')
                snippet_elem = result.find('a', class_='result__snippet')

                if title_elem:
                    href = title_elem.get('href', '')
                    if 'uddg=' in href:
                        actual_url = urllib.parse.unquote(href.split('uddg=')[1].split('&')[0])
                    else:
                        actual_url = href

                results.append({
                    "title": title_elem.text.strip(),
                    "url": actual_url,
                    "snippet": snippet_elem.text.strip() if snippet_elem else ""
                })

            return {
                "query": query,
                "results": results,
                "count": len(results)
            }

        except Exception as e:
            return {"error": str(e), "query": query}
