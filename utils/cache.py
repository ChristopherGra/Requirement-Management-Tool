"""
File processing cache management.
Stores user choices (sheet selections, column mappings) to avoid re-prompting.
"""

import os
import json
import hashlib
from pathlib import Path
from utils.constants import CACHE_DIR, CACHE_FILE


class FileCache:
    """
    Manages persistent cache of user choices for file processing.
    
    Uses file hash (path + mtime + size) as key to detect file changes.
    Cache is stored as JSON in .cache/file_processing_cache.json
    """
    
    def __init__(self, cache_dir=None):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory for cache file (default from constants)
        """
        self.cache_dir = Path(cache_dir or CACHE_DIR)
        self.cache_file = self.cache_dir / CACHE_FILE
        self._cache = None  # Lazy load
        
    def _get_file_hash(self, file_path):
        """
        Generate a hash of the file to uniquely identify it.
        
        Uses path + modification time + size to detect changes.
        
        Args:
            file_path: Path to file
            
        Returns:
            MD5 hash string
        """
        try:
            stat = os.stat(file_path)
            unique_string = f"{file_path}_{stat.st_mtime}_{stat.st_size}"
            return hashlib.md5(unique_string.encode()).hexdigest()
        except FileNotFoundError:
            # File doesn't exist yet (template generation, etc.)
            return hashlib.md5(str(file_path).encode()).hexdigest()
    
    def _load_cache(self):
        """Load the processing cache from disk."""
        if self._cache is not None:
            return self._cache
            
        if not self.cache_file.exists():
            self._cache = {}
            return self._cache
            
        try:
            with open(self.cache_file, 'r') as f:
                self._cache = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load cache: {e}")
            self._cache = {}
            
        return self._cache
    
    def _save_cache(self):
        """Save the processing cache to disk."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")
    
    def get_choices(self, file_path):
        """
        Get cached user choices for a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary of cached choices (may be empty)
        """
        cache = self._load_cache()
        file_hash = self._get_file_hash(file_path)
        return cache.get(file_hash, {})
    
    def save_choices(self, file_path, **choices):
        """
        Save user choices for a file to the cache.
        
        Args:
            file_path: Path to file
            **choices: Keyword arguments of choices to save
                      (e.g., sheet_name='Sheet1', column_mappings={...})
        """
        cache = self._load_cache()
        file_hash = self._get_file_hash(file_path)
        
        # Merge new choices with existing ones
        existing = cache.get(file_hash, {})
        existing.update(choices)
        cache[file_hash] = existing
        
        self._save_cache()
    
    def clear(self, file_path=None):
        """
        Clear cache entries.
        
        Args:
            file_path: If provided, clear only this file's cache.
                      If None, clear entire cache.
        """
        cache = self._load_cache()
        
        if file_path:
            file_hash = self._get_file_hash(file_path)
            cache.pop(file_hash, None)
            print(f"Cleared cache for {file_path}")
        else:
            cache.clear()
            print("Cleared entire cache")
            
        self._save_cache()
    
    def list_cached_files(self):
        """
        List all files in cache (for debugging).
        
        Returns:
            List of file hashes in cache
        """
        cache = self._load_cache()
        return list(cache.keys())
