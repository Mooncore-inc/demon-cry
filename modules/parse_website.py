from modules.base_modules import OSINTModule

from curl_cffi import requests
from bs4 import BeautifulSoup


class ParseWebsite(OSINTModule):
    name = "parse_website"
    description = "Загружает веб-страницу по URL и извлекает текст, заголовки и ссылки."
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL страницы для парсинга"}
        },
        "required": ["url"]
    }

    def execute(self, url: str) -> dict:
        try:
            response = requests.get(url, impersonate="chrome110", timeout=15)
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
