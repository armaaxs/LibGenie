import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, parse_qs
from typing import List, Dict, Any, Optional

from client import LibgenClient
from book import Book

class LibgenParser:
    def parse_search_results(self, html_content: str, base_url: str) -> List[Book]:
        soup = BeautifulSoup(html_content, "lxml")
        
        # Target the main results table
        table = soup.select_one("table[width='100%'], table.table")
        if not table:
            return []

        books = []
        # Skip header row
        rows = table.find_all("tr")[1:]

        for row in rows:
            tds = row.find_all("td", recursive=False)
            if len(tds) < 9:
                continue

            # Title & ID Extraction
            title_anchor = tds[0].find("a", href=True)
            if not title_anchor:
                continue
            
            title = " ".join(title_anchor.get_text(strip=True).split())
            book_id = parse_qs(urlparse(title_anchor['href']).query).get("id", [""])[0]

            # Mirrors & MD5 Extraction
            mirror_anchors = tds[8].find_all("a", href=True)[:4]
            mirrors = [urljoin(base_url, a['href']) for a in mirror_anchors]
            
            md5 = ""
            if mirrors:
                md5_match = parse_qs(urlparse(mirrors[0]).query).get("md5", [""])
                md5 = md5_match[0] if md5_match else ""

            books.append(Book(
                id=book_id,
                title=title,
                author=tds[1].get_text(strip=True),
                publisher=tds[2].get_text(strip=True),
                year=tds[3].get_text(strip=True),
                language=tds[4].get_text(strip=True),
                pages=tds[5].get_text(strip=True),
                size=tds[6].get_text(strip=True),
                extension=tds[7].get_text(strip=True),
                md5=md5,
                mirrors=mirrors
            ))
            
        return books

class LibgenSearch:
    def __init__(self, mirror: str = "https://libgen.li"):
        self.mirror = mirror

    def search(
        self, 
        query: str, 
        search_columns: list, 
        search_topics: list, 
        limit: int,
        filters: Optional[Dict[str, Any]] = None,
        exact_match: bool = False,
        add_upload_info: bool = False
    ) -> List[Book]:
        
        client = LibgenClient(
            mirror_url=self.mirror,
            query=query,
            search_columns=search_columns,
            search_topics=search_topics,
            limit=limit,
        )

        try:
            html = client.get_html()
            
            # INTEGRATION: Calling the Parser logic
            results = self._parse_results(html) 

            if add_upload_info and results:
                book_ids = [b.id for b in results]
                extra_data = client.get_upload_info(book_ids)
                self._enrich_books(results, extra_data)

            if filters:
                results = self.filter_books(results, filters, exact_match)
            
            return results

        finally:
            client.session.close()

    def _enrich_books(self, books: List[Book], extra_data: dict):
        for book in books:
            if info := extra_data.get(book.id):
                book.date_added = info.get("timeadded")
                book.date_last_modified = info.get("timelastmodified")

    def _parse_results(self, html: str) -> List[Book]:
        # INTEGRATION: Initializing and running the parser
        parser = LibgenParser()
        return parser.parse_search_results(html, self.mirror)

    @staticmethod
    def filter_books(books: List[Book], filters: Dict[str, Any], exact: bool) -> List[Book]:
        filtered = []
        for book in books:
            match = True
            for field, value in filters.items():
                book_val = str(getattr(book, field, "")).lower()
                target_val = str(value).lower()
                if exact and book_val != target_val:
                    match = False; break
                if not exact and target_val not in book_val:
                    match = False; break
            if match:
                filtered.append(book)
        return filtered
    
ls = LibgenSearch()
results = ls.search('48 laws', ["t"],['l'], 5)
print(results)