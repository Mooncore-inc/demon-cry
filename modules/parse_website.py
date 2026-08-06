import re
import httpx
from urllib.parse import urljoin
from selectolax.parser import HTMLParser
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
    name: str = "parse_website"
    description: str = "Parse web page: extract text, links, metadata. Handles redirects"
    category: str = "content"
    parameters: dict = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to parse"}
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

            tree = HTMLParser(response.text)
            page_url = str(response.url)

            useful_meta = {"description", "og:description", "og:title", "keywords", "author"}
            meta = {}
            for tag in tree.css("meta"):
                attrs = tag.attributes
                name = attrs.get("name") or attrs.get("property")
                if name in useful_meta and (content := attrs.get("content")):
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

            text = re.sub(r'\n\s*\n+', '\n\n', text).strip()
            text = "\n".join(line.strip() for line in text.split("\n") if line.strip())

            MAX_CHARS = 4000
            truncated = len(text) > MAX_CHARS
            if truncated:
                text = text[:MAX_CHARS] + "\n\n[... TEXT TRUNCATED DUE TO LENGTH. USE web_search FOR MORE DETAILS ...]"

            seen = set()
            links_md_lines = []
            for a in tree.css("a[href]"):
                href = urljoin(page_url, a.attributes.get("href"))
                if href.startswith(("http://", "https://")) and href != page_url and href not in seen:
                    seen.add(href)
                    link_title = a.text(strip=True)[:50] or "No title"
                    links_md_lines.append(f"- [{link_title}]({href})")
                if len(links_md_lines) >= 15:
                    break

            meta_md = "\n".join([f"- **{k}**: {v}" for k, v in meta.items()]) if meta else "- None\n"
            links_md = "\n".join(links_md_lines) if links_md_lines else "- None"

            return {
                "report": (
                    f"Title: {title}\n\n"
                    f"URL Source: {page_url}\n\n"
                    f"Meta Data: {meta_md}\n\n"
                    f"Content:\n{text}\n\n"
                    f"Links:{links_md}"
                )
            }

        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code} ({e.response.reason_phrase})", "url": url}
        except httpx.RequestError as e:
            return {"error": f"Network error: {str(e)}", "url": url}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}", "url": url}
