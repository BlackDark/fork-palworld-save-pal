import json
import os
import platform
import sys
from typing import Any, Dict, Optional
from threading import Lock

from palworld_save_pal.utils.logging_config import create_logger

logger = create_logger(__name__)

# Module-level cache for JSON files
_json_cache: Dict[str, Dict[str, Any]] = {}
_cache_mtimes: Dict[str, float] = {}
_cache_lock = Lock()


def sanitize_string(value: str) -> str:
    if not value:
        return value
    try:
        # First try normal encoding - if it works, string is clean
        value.encode("utf-8")
        return value
    except UnicodeEncodeError:
        # String contains surrogates - remove them
        return value.encode("utf-8", errors="surrogatepass").decode(
            "utf-8", errors="replace"
        )


def find_data_file(filename):
    # If we're on Mac and frozen, make sure we use the correct path
    if getattr(sys, "frozen", False) and platform.system() == "Darwin":
        # The application is frozen
        datadir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        datadir = ""
    return os.path.join(datadir, filename)


class JsonManager:
    def __init__(self, file_path: str):
        self.file_path = find_data_file(file_path)
        self.ensure_file_exists()

    def ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _get_file_mtime(self) -> Optional[float]:
        """Get file modification time, or None if file doesn't exist."""
        try:
            return os.path.getmtime(self.file_path)
        except OSError:
            return None

    def _is_cache_valid(self) -> bool:
        """Check if the cached data is still valid (file hasn't changed)."""
        if self.file_path not in _json_cache:
            return False

        cached_mtime = _cache_mtimes.get(self.file_path)
        current_mtime = self._get_file_mtime()

        if current_mtime is None:
            return False

        # Cache is valid if modification times match
        return cached_mtime == current_mtime

    def read(self) -> Dict[str, Any]:
        """Read JSON file, using cache if available and valid."""
        with _cache_lock:
            # Check if we have a valid cache entry
            if self._is_cache_valid():
                logger.debug(f"JSON cache hit for {self.file_path}")
                return _json_cache[self.file_path].copy()

            # Cache miss or invalid - read from disk
            logger.debug(f"JSON cache miss for {self.file_path}, reading from disk")
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Store in cache
            mtime = self._get_file_mtime()
            if mtime is not None:
                _json_cache[self.file_path] = data
                _cache_mtimes[self.file_path] = mtime

            return data.copy()

    def invalidate_cache(self):
        """Invalidate the cache for this file."""
        with _cache_lock:
            if self.file_path in _json_cache:
                del _json_cache[self.file_path]
            if self.file_path in _cache_mtimes:
                del _cache_mtimes[self.file_path]
            logger.debug(f"Cache invalidated for {self.file_path}")

    @staticmethod
    def clear_all_cache():
        """Clear all cached JSON data. Useful for testing or memory management."""
        global _json_cache, _cache_mtimes
        with _cache_lock:
            _json_cache.clear()
            _cache_mtimes.clear()
            logger.debug("All JSON cache cleared")

    def write(self, data: Dict[str, Any]):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        # Invalidate cache after write
        self.invalidate_cache()

    def append(self, key: str, value: Any):
        data = self.read()
        data[key] = value
        self.write(data)

    def update_name(self, key: str, value: Any):
        data = self.read()
        entry = data.get(key, None)
        if entry is None:
            return
        entry["name"] = value
        self.write(data)

    def delete(self, key: str):
        data = self.read()
        if key in data:
            del data[key]
            self.write(data)
