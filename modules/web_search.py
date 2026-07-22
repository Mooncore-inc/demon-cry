import httpx

from modules.base_modules import OSINTModule
from core.config import config


class WebSearch(OSINTModule):
    name = "web_search"
    description = "Searches the web via SearXNG. Supports Google dorks (site:, filetype:, intitle:, inurl:), categories and time ranges."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query. Supports Google dorks syntax."},
            "category": {
                "type": "string",
                "enum": ["general", "images", "files", "it", "social media", "news"],
                "default": "general",
                "description": "Category to search in. Use 'files' for documents, 'images' for pictures."
            },
            "time_range": {
                "type": "string",
                "enum": ["day", "week", "month", "year", "all"],
                "default": "all",
                "description": "Time filter for the search results."
            }
        },
        "required": ["query"]
    }

    async def execute(self, query: str, category: str = "general", time_range: str = "all") -> dict:
        try:
            params = {
                "q": query,
                "format": "json",
                "categories": category,
            }
            if time_range and time_range != "all":
                params["time_range"] = time_range

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{config.searxng_url}/search",
                    params=params,
                )
                response.raise_for_status()

            data = response.json()

            warnings = []
            for engine, reason in data.get("unresponsive_engines", []):
                warnings.append(f"{engine}: {reason}")

            results = []
            for r in data.get("results", [])[:10]:
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": (lambda c: c[:150] + "..." if len(c) > 150 else c)(r.get("content", "")),
                    "engine": r.get("engine", "unknown"),
                })

            resp = {
                "query": query,
                "category": category,
                "time_range": time_range,
                "results": results,
                "total_found": len(results),
            }
            if warnings:
                resp["warnings"] = warnings
            return resp

        except Exception as e:
            return {"error": str(e), "query": query}
