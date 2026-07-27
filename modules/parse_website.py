import httpx
import re
from selectolax.parser import HTMLParser
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
                timeout=15.0,
                follow_redirects=True,
                verify=False 
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type:
                return {"error": f"Not an HTML page. Content-Type: {content_type}", "url": url}

            response.encoding = response.charset_encoding or "utf-8"
            tree = HTMLParser(response.text)

            useful_meta = ["description", "og:description", "og:title", "keywords", "author"]
            meta = {}
            for tag in tree.css("meta"):
                name = tag.attributes.get("name") or tag.attributes.get("property")
                content = tag.attributes.get("content")
                if name in useful_meta and content:
                    meta[name] = content

            title_node = tree.css_first("title")
            title = title_node.text(strip=True) if title_node else ""
            if not title:
                title = meta.get("og:title", "")

            kill_selectors = (
                "script, style, nav, footer, header, noscript, iframe, svg, "
                "[hidden], [aria-hidden='true'], .Skeleton, .js-pinned-items-reorder-container, "
                ".sidebar, .infobox, .toc, table, form"
            )
            for tag in tree.css(kill_selectors):
                tag.decompose()

            main = tree.css_first(".markdown-body, .mw-parser-output, #content, article, main, .post-content, .entry-content")
            target_node = main or tree.body or tree

            text = target_node.text(separator="\n", strip=True)

            text = re.sub(r'\n\s*\n+', '\n\n', text)
            text = "\n".join(line.strip() for line in text.split("\n") if line.strip())

            MAX_CHARS = 4000
            truncated = len(text) > MAX_CHARS
            if truncated:
                text = text[:MAX_CHARS] + "\n\n[... TEXT TRUNCATED DUE TO LENGTH. USE web_search FOR MORE DETAILS ...]"

            links = []
            for a in tree.css("a[href]"):
                href = urljoin(str(response.url), a.attributes.get("href"))
                if href.startswith(("http://", "https://")) and href != str(response.url):
                    links.append({
                        "title": a.text(strip=True)[:50] or "No title", 
                        "url": href
                    })
            
            unique_links = list({v['url']: v for v in links}.values())[:15]

            return {
                "final_url": str(response.url),
                "status_code": response.status_code,
                "title": title,
                "meta": meta,
                "text": text,
                "links": unique_links,
            }

        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code} ({e.response.reason_phrase})", "url": url}
        except httpx.RequestError as e:
            return {"error": f"Network error: {str(e)}", "url": url}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}", "url": url}