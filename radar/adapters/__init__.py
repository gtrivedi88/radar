"""External system adapters"""

from .fetchers import FetcherRegistry, BaseFetcher
from .sources import SourceLoader
from .storage import FileStorage

__all__ = [
    "FetcherRegistry",
    "BaseFetcher",
    "SourceLoader",
    "FileStorage",
]