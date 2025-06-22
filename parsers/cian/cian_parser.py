import asyncio
import re
import html
from selectolax.parser import HTMLParser
import httpx


class EstatePageParser:
    def __init__(self, url: str, client: httpx.AsyncClient):
        self.url = url
        self.client = client

    async def _fetch_html(self) -> str:
        resp = await self.client.get(self.url)
        resp.raise_for_status()
        return resp.text

    async def parse_page(self) -> dict:
        html_text = await self._fetch_html()
        tree = HTMLParser(html_text)

        return {
            "link": self.url,
            "address": self.parse_address(tree),
            "price": self.parse_price(tree),
            "photos": self.parse_photos(tree),
            "description": self.parse_description(tree),
            "factoids": self.parse_factoids(tree),
            "summary": self.parse_summary(tree),
            "type": "rent" if "rent" in self.url or "snyat" in self.url else "sale",
            "title": self.parse_title(tree)
        }

    @staticmethod
    def parse_address(tree):
        items = tree.css('a[data-name="AddressItem"]')
        return [html.unescape(i.text(strip=True)) for i in items if i.text()]

    @staticmethod
    def parse_price(tree):
        price_node = tree.css_first('div[data-testid="price-amount"] span')
        if price_node:
            price_text = html.unescape(price_node.text())
            return ''.join(c for c in price_text if c.isdigit())
        return None

    @staticmethod
    def parse_photos(tree):
        photos = tree.css('div[data-name="OfferGallery"] img[src]')
        return [img.attributes.get("src") for img in photos[:10]]

    @staticmethod
    def parse_description(tree):
        desc_node = tree.css_first('div[data-name="Description"] span')
        return html.unescape(desc_node.text(strip=True)) if desc_node else None

    @staticmethod
    def parse_factoids(tree):
        factoids = tree.css('div[data-name="ObjectFactoidsItem"] span')
        return [html.unescape(f.text(strip=True)) for f in factoids if f.text()]

    @staticmethod
    def parse_summary(tree):
        summaries = tree.css('div[data-name="OfferSummaryInfoItem"] p')
        return [html.unescape(s.text(strip=True)) for s in summaries if s.text()]

    @staticmethod
    def parse_title(tree):
        title_text = tree.css_first('div[data-name="OfferTitleNew"] h1')
        print(title_text)
        return html.unescape(title_text.text(strip=True)) if title_text else None


class UrlCollector:
    def __init__(self, client: httpx.AsyncClient, debug_mode=False):
        self.client = client
        self.debug_mode = debug_mode

    async def get_urls_from_page(self, url: str):
        try:
            res = await self.client.get(url)
            res.raise_for_status()
            tree = HTMLParser(res.text)

            containers = tree.css('div[data-testid="offer-card"]')
            links = []
            for container in containers:
                a_tag = container.css_first("a")
                if a_tag and "href" in a_tag.attributes:
                    links.append(a_tag.attributes["href"])

            page_match = re.search(r"p=(\d+)", url)
            page = int(page_match.group(1)) if page_match else 1

            if self.debug_mode:
                for link in links:
                    print(link, page)
                return None

            return {"urls": links, "page": page}

        except Exception as e:
            print(f"Error fetching URL list from {url}: {e}")
            return {"urls": [], "page": 0}

    async def get_next_page(self, current_url: str):
        match = re.search(r"([?&])p=(\d+)", current_url)
        if match:
            sep = match.group(1)
            current_page = int(match.group(2))
            new_url = re.sub(r"([?&])p=\d+", f"{sep}p={current_page + 1}", current_url, count=1)
            return new_url
        else:
            res = await self.client.get(current_url)
            res.raise_for_status()
            tree = HTMLParser(res.text)
            nav = tree.css_first('nav[data-name="pagination"]')
            if nav:
                first_a = nav.css_first('a')
                if first_a:
                    href = first_a.attributes.get('href')
                    return href
                else:
                    print("Тег <a> не найден.")





async def main():
    async with httpx.AsyncClient() as client:
        parser = EstatePageParser("https://chelyabinsk.cian.ru/sale/flat/306663166/", client)
        print(await parser.parse_page())


if __name__ == "__main__":
    asyncio.run(main())