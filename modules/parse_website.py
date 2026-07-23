import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from modules.base_modules import OSINTModule

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

class ParseWebsite(OSINTModule):
    name = "parse_website"
    description = "Loads a web page, extracts metadata, main text, and absolute links. Handles redirects and bad SSL."
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL of the page to parse"}
        },
        "required": ["url"]
    }

    async def execute(self, url: str) -> dict:
        try:
            async with httpx.AsyncClient(
                headers=HEADERS, 
                timeout=30.0, 
                follow_redirects=True,
                verify=False 
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type:
                return {"error": f"Not an HTML page. Content-Type: {content_type}", "url": url}

            response.encoding = response.charset_encoding or "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")

            meta = {}
            for tag in soup.find_all("meta"):
                name = tag.get("name") or tag.get("property")
                content = tag.get("content")
                if name and content:
                    meta[name] = content

            title = (soup.title.string.strip() if soup.title and soup.title.string else "") or meta.get("og:title", "")

            for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe", "svg"]):
                tag.decompose()

            headings = [
                {"level": h.name, "text": h.get_text(strip=True)} 
                for h in soup.find_all(["h1", "h2", "h3"]) 
                if h.get_text(strip=True)
            ]

            text = soup.get_text(separator="\n", strip=True)
            if len(text) > 4000:
                text = text[:4000] + "\n\n[... TEXT TRUNCATED DUE TO LENGTH. USE web_search FOR MORE DETAILS ...]"

            links = []
            for a in soup.find_all("a", href=True):
                href = urljoin(str(response.url), a["href"])
                if href.startswith(("http://", "https://")) and href != str(response.url):
                    links.append({
                        "title": a.get_text(strip=True)[:50] or "No title", 
                        "url": href
                    })
            
            unique_links = list({v['url']: v for v in links}.values())[:15]

            return {
                "final_url": str(response.url),
                "status_code": response.status_code,
                "title": title,
                "meta": meta,
                "headings": headings,
                "text": text,
                "links": unique_links,
            }

        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code} ({e.response.reason_phrase})", "url": url}
        except httpx.RequestError as e:
            return {"error": f"Network error: {str(e)}", "url": url}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}", "url": url}