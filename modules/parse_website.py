import httpx
from bs4 import BeautifulSoup

from modules.base_modules import OSINTModule

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}


class ParseWebsite(OSINTModule):
    name = "parse_website"
    description = "Loads a web page by URL and extracts text, headings and links."
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL of the page to parse"}
        },
        "required": ["url"]
    }

    async def execute(self, url: str) -> dict:
        try:
            async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
                response = await client.get(url)
            soup = BeautifulSoup(response.text, "html.parser")

            title = soup.title.string.strip() if soup.title and soup.title.string else ""

            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            headings = []
            for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
                text = h.get_text(strip=True)
                if text:
                    headings.append({"level": h.name, "text": text})

            paragraphs = []
            for p in soup.find_all("p"):
                text = p.get_text(strip=True)
                if text:
                    paragraphs.append(text)

            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith(("http://", "https://")):
                    link_title = a.get_text(strip=True)
                    links.append({"title": link_title, "url": href})

            return {
                "url": url,
                "title": title,
                "headings": headings,
                "text": "\n".join(paragraphs),
                "links": links,
            }

        except Exception as e:
            return {"error": str(e), "url": url}
