from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Book:
    # Essential Fields (Required during parsing)
    id: str
    title: str
    author: str
    publisher: str
    year: str
    language: str
    pages: str
    size: str
    extension: str
    md5: str
    mirrors: List[str]

    # Optional Fields (Populated later by JSON API)
    date_added: Optional[str] = None
    date_last_modified: Optional[str] = None

    # Result Fields (Placeholders for generated links)
    resolved_download_link: Optional[str] = None

    @property
    def tor_download_link(self) -> str:
        """
        Computes the Tor link on the fly. 
        Since it's just string formatting, it's perfect as a @property.
        """
        return (
            "http://libgenfrialc7tguyjywa36vtrdcplwpxaw43h6o63dmmwhvavo5rqqd.onion"
            f"/LG/01311000/{self.md5}/{self.title}.{self.extension}"
        )

    # Note: I've removed resolve_direct_download_link from here.
    # That logic belongs in LibgenClient because it requires a network session.