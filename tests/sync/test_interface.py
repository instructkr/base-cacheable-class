import time
from abc import ABC


import pytest

from base_cacheable_class.cache.sync import CacheInterface, InMemoryCache


class TestInterfaces:
    def test_cache_interface_is_abstract(self):
        """Test that CacheInterface is abstract and cannot be instantiated"""
        with pytest.raises(TypeError):
            CacheInterface()

    def test_cache_interface_methods(self):
        """Test that CacheInterface has all required abstract methods"""
        assert hasattr(CacheInterface, "set")
        assert hasattr(CacheInterface, "get")
        assert hasattr(CacheInterface, "exists")
        assert hasattr(CacheInterface, "delete")
        assert hasattr(CacheInterface, "clear")
        assert hasattr(CacheInterface, "get_keys")
        assert hasattr(CacheInterface, "get_keys_regex")

    def test_interfaces_inherit_from_abc(self):
        """Test that interfaces inherit from ABC"""
        assert issubclass(CacheInterface, ABC)


class TestInMemoryCache:
    def test_singleton(self):
        """Test that InMemoryCache is a singleton"""
        cache1 = InMemoryCache()
        cache2 = InMemoryCache()
        assert cache1 is cache2

    def test_set_and_get(self):
        """Test basic set and get operations"""
        cache = InMemoryCache()
        cache.clear()

        cache.set("key1", "value1")
        result = cache.get("key1")
        assert result == "value1"

    def test_get_nonexistent(self):
        """Test getting a non-existent key returns None"""
        cache = InMemoryCache()
        cache.clear()

        result = cache.get("nonexistent")
        assert result is None

    def test_ttl_expiration(self):
        """Test that items expire after TTL"""
        cache = InMemoryCache()
        cache.clear()

        cache.set("key1", "value1", ttl=1)  # 1 second TTL

        # Should exist immediately
        result = cache.get("key1")
        assert result == "value1"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        result = cache.get("key1")
        assert result is None

    def test_no_ttl(self):
        """Test that items without TTL don't expire"""
        cache = InMemoryCache()
        cache.clear()

        cache.set("key1", "value1", ttl=None)

        # Should exist even after some time
        time.sleep(0.1)
        result = cache.get("key1")
        assert result == "value1"

    def test_exists(self):
        """Test exists method"""
        cache = InMemoryCache()
        cache.clear()

        cache.set("key1", "value1")
        assert cache.exists("key1") is True
        assert cache.exists("nonexistent") is False

    def test_delete(self):
        """Test delete method"""
        cache = InMemoryCache()
        cache.clear()

        cache.set("key1", "value1")
        assert cache.exists("key1") is True

        cache.delete("key1")
        assert cache.exists("key1") is False

    def test_clear(self):
        """Test clear method"""
        cache = InMemoryCache()
        cache.clear()

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()

        assert cache.exists("key1") is False
        assert cache.exists("key2") is False

    def test_get_keys(self):
        """Test get_keys method"""
        cache = InMemoryCache()
        cache.clear()

        cache.set("test:key1", "value1")
        cache.set("test:key2", "value2")
        cache.set("other:key3", "value3")

        # Get all keys
        all_keys = cache.get_keys()
        assert len(all_keys) == 3
        assert "test:key1" in all_keys
        assert "test:key2" in all_keys
        assert "other:key3" in all_keys

        # Get keys with pattern
        test_keys = cache.get_keys("test:.*")
        assert len(test_keys) == 2
        assert "test:key1" in test_keys
        assert "test:key2" in test_keys
        assert "other:key3" not in test_keys
