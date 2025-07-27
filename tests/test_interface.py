from abc import ABC
import asyncio

import pytest
from unittest.mock import patch

from base_cacheable_class import CacheDecoratorInterface, CacheInterface, CacheItem
from base_cacheable_class.cache.in_memory.cache import InMemoryCache
from base_cacheable_class.cache.in_memory.decorator import InMemoryCacheDecorator


class TestCacheItem:
    def test_cache_item_creation(self):
        """Test CacheItem dataclass creation"""
        item = CacheItem(value="test_value", expire_at=123456.789)
        assert item.value == "test_value"
        assert item.expire_at == 123456.789

    def test_cache_item_with_none_expire(self):
        """Test CacheItem with None expire_at"""
        item = CacheItem(value={"key": "value"}, expire_at=None)
        assert item.value == {"key": "value"}
        assert item.expire_at is None


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

    def test_cache_decorator_interface_is_abstract(self):
        """Test that CacheDecoratorInterface is abstract and cannot be instantiated"""
        with pytest.raises(TypeError):
            CacheDecoratorInterface()

    def test_cache_decorator_interface_methods(self):
        """Test that CacheDecoratorInterface has all required abstract methods"""
        assert callable(CacheDecoratorInterface)
        assert hasattr(CacheDecoratorInterface, "invalidate")
        assert hasattr(CacheDecoratorInterface, "invalidate_all")

    def test_interfaces_inherit_from_abc(self):
        """Test that interfaces inherit from ABC"""
        assert issubclass(CacheInterface, ABC)
        assert issubclass(CacheDecoratorInterface, ABC)


class TestInMemoryCache:
    @pytest.mark.asyncio
    async def test_singleton(self):
        """Test that InMemoryCache is a singleton"""
        cache1 = InMemoryCache()
        cache2 = InMemoryCache()
        assert cache1 is cache2

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """Test basic set and get operations"""
        cache = InMemoryCache()
        await cache.clear()  # Clear any existing data

        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self):
        """Test getting a non-existent key returns None"""
        cache = InMemoryCache()
        await cache.clear()

        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """Test that items expire after TTL"""
        cache = InMemoryCache()
        await cache.clear()

        await cache.set("key1", "value1", ttl=1)  # 1 second TTL

        # Should exist immediately
        result = await cache.get("key1")
        assert result == "value1"

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be expired
        result = await cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_no_ttl(self):
        """Test that items without TTL don't expire"""
        cache = InMemoryCache()
        await cache.clear()

        await cache.set("key1", "value1", ttl=None)

        # Should exist even after some time
        await asyncio.sleep(0.1)
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_exists(self):
        """Test exists method"""
        cache = InMemoryCache()
        await cache.clear()

        await cache.set("key1", "value1")
        assert await cache.exists("key1") is True
        assert await cache.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test delete method"""
        cache = InMemoryCache()
        await cache.clear()

        await cache.set("key1", "value1")
        assert await cache.exists("key1") is True

        await cache.delete("key1")
        assert await cache.exists("key1") is False

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clear method"""
        cache = InMemoryCache()

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        await cache.clear()

        assert await cache.exists("key1") is False
        assert await cache.exists("key2") is False

    @pytest.mark.asyncio
    async def test_get_keys(self):
        """Test get_keys method"""
        cache = InMemoryCache()
        await cache.clear()

        await cache.set("test:key1", "value1")
        await cache.set("test:key2", "value2")
        await cache.set("other:key3", "value3")

        # Get all keys
        all_keys = await cache.get_keys()
        assert len(all_keys) == 3
        assert "test:key1" in all_keys
        assert "test:key2" in all_keys
        assert "other:key3" in all_keys

        # Get keys with pattern
        test_keys = await cache.get_keys("test:.*")
        assert len(test_keys) == 2
        assert "test:key1" in test_keys
        assert "test:key2" in test_keys
        assert "other:key3" not in test_keys


class TestInMemoryCacheDecorator:
    @pytest.mark.asyncio
    async def test_basic_caching(self):
        """Test basic caching functionality"""
        cache = InMemoryCache()
        await cache.clear()
        decorator = InMemoryCacheDecorator(cache, default_ttl=60)

        call_count = 0

        @decorator(ttl=10)
        async def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result = await test_func(5)
        assert result == 10
        assert call_count == 1

        # Second call should use cache
        result = await test_func(5)
        assert result == 10
        assert call_count == 1  # Not incremented

        # Different argument should call function
        result = await test_func(3)
        assert result == 6
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_key_builder(self):
        """Test key builder creates correct keys"""
        cache = InMemoryCache()
        decorator = InMemoryCacheDecorator(cache)

        def test_func():
            pass

        # Test with different arguments
        key1 = decorator.key_builder(test_func, "self", "arg1", "arg2")
        assert key1 == "test_func:('self', 'arg1', 'arg2'):{}"

        key2 = decorator.key_builder(test_func, "self", kwarg1="value1")
        assert key2 == "test_func:('self',):{'kwarg1': 'value1'}"

        # Test without self (function call)
        key3 = decorator.key_builder(test_func, "arg1", "arg2")
        assert key3 == "test_func:('arg1', 'arg2'):{}"

    @pytest.mark.asyncio
    async def test_invalidate(self):
        """Test cache invalidation"""
        cache = InMemoryCache()
        await cache.clear()
        decorator = InMemoryCacheDecorator(cache)

        call_count = 0

        @decorator()
        async def get_data(key):
            nonlocal call_count
            call_count += 1
            return f"data_{key}"

        @decorator.invalidate("get_data", param_mapping={"key": "key"})
        async def update_data(key, value):
            return f"updated_{key}_{value}"

        # Cache some data
        result = await get_data("test")
        assert result == "data_test"
        assert call_count == 1

        # Should use cache
        result = await get_data("test")
        assert result == "data_test"
        assert call_count == 1

        # Update should invalidate cache
        await update_data("test", "new")

        # Next call should hit function
        result = await get_data("test")
        assert result == "data_test"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_invalidate_all(self):
        """Test invalidate all functionality"""
        cache = InMemoryCache()
        await cache.clear()
        decorator = InMemoryCacheDecorator(cache)

        call_count = 0

        @decorator()
        async def get_data(key):
            nonlocal call_count
            call_count += 1
            return f"data_{key}"

        @decorator.invalidate_all()
        async def clear_cache():
            return "cleared"

        # Cache multiple items
        await get_data("test1")
        await get_data("test2")
        assert call_count == 2

        # Should use cache
        await get_data("test1")
        await get_data("test2")
        assert call_count == 2

        # Clear all caches
        await clear_cache()

        # Should call functions again
        await get_data("test1")
        await get_data("test2")
        assert call_count == 4

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in decorator"""
        cache = InMemoryCache()
        decorator = InMemoryCacheDecorator(cache)

        # Mock cache.get to raise an exception
        with patch.object(cache, "get", side_effect=Exception("Cache error")):

            @decorator()
            async def test_func(x):
                return x * 2

            # Should still work even if cache fails
            result = await test_func(5)
            assert result == 10

    @pytest.mark.asyncio
    async def test_none_result_caching(self):
        """Test that None results are not cached"""
        cache = InMemoryCache()
        await cache.clear()
        decorator = InMemoryCacheDecorator(cache)

        call_count = 0

        @decorator()
        async def test_func():
            nonlocal call_count
            call_count += 1
            return None

        # First call
        result = await test_func()
        assert result is None
        assert call_count == 1

        # Second call should also call function (None not cached)
        result = await test_func()
        assert result is None
        assert call_count == 2
