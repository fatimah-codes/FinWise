"""LLM caching: InMemoryCache (RAM) and SQLiteCache (file on disk).

set_llm_cache() registers ONE global cache. LangChain checks it before every
call, so repeating the same prompt skips the API call (faster + cheaper).
"""
import os

from langchain_core.caches import InMemoryCache
from langchain_core.globals import set_llm_cache

from src.config import SQLITE_PATH

# Keep one instance of each cache alive across Streamlit reruns. Creating a new
# SQLiteCache on every rerun would open a new database engine each time.
_MEMORY_CACHE = InMemoryCache()
_SQLITE_CACHE = None


def _sqlite_cache():
    global _SQLITE_CACHE
    if _SQLITE_CACHE is None:
        from langchain_community.cache import SQLiteCache
        _SQLITE_CACHE = SQLiteCache(database_path=SQLITE_PATH)
    return _SQLITE_CACHE


def configure_cache(mode: str) -> str:
    """Switch the global cache. Returns a short human-readable status."""
    if mode == "In-Memory":
        set_llm_cache(_MEMORY_CACHE)
        return "In-memory cache active (RAM, cleared on restart)"
    if mode == "SQLite":
        set_llm_cache(_sqlite_cache())
        return f"SQLite cache active ({SQLITE_PATH}, survives restarts)"
    set_llm_cache(None)
    return "Caching off (every call goes to the API)"


def clear_cache(mode: str) -> None:
    """Empty the chosen cache."""
    if mode == "In-Memory":
        _MEMORY_CACHE.clear()
    elif mode == "SQLite":
        _sqlite_cache().clear()


def sqlite_size_kb() -> float:
    try:
        return os.path.getsize(SQLITE_PATH) / 1024
    except OSError:
        return 0.0
