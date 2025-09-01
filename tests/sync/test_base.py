import pytest
from unittest.mock import patch
from base_cacheable_class import (
    CacheDecoratorInterface,
    BaseCacheableClass,
)
from base_cacheable_class import SyncCacheDecoratorFactory


class SyncMockCacheDecorator(CacheDecoratorInterface):
    def __init__(self):
        self.call_count = 0
        self.invalidate_count = 0
        self.invalidate_all_count = 0

    def __call__(self, ttl=None):
        def decorator(func):
            def wrapper(*args, **kwargs):
                self.call_count += 1
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def invalidate(self, target_func_name, param_mapping=None):
        def decorator(func):
            def wrapper(*args, **kwargs):
                self.invalidate_count += 1
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def invalidate_all(self):
        def decorator(func):
            def wrapper(*args, **kwargs):
                self.invalidate_all_count += 1
                return func(*args, **kwargs)

            return wrapper

        return decorator


class TestService(BaseCacheableClass):
    def __init__(self, cache_decorator):
        super().__init__(cache_decorator)

    @BaseCacheableClass.cache(ttl=60)
    def get_data(self, key: str):
        return f"data_{key}"

    @BaseCacheableClass.invalidate("get_data", param_mapping={"key": "key"})
    def update_data(self, key: str, value: str):
        return f"updated_{key}_{value}"

    @BaseCacheableClass.invalidate_all()
    def clear_all(self):
        return "cleared"


class TestSyncBaseCacheableClass:
    def test_cache_decorator(self):
        """Test cache decorator functionality"""
        mock_decorator = SyncMockCacheDecorator()
        service = TestService(mock_decorator)

        result = service.get_data("test")
        assert result == "data_test"
        assert mock_decorator.call_count == 1

    def test_invalidate_decorator(self):
        """Test invalidate decorator functionality"""
        mock_decorator = SyncMockCacheDecorator()
        service = TestService(mock_decorator)

        result = service.update_data("test", "value")
        assert result == "updated_test_value"
        assert mock_decorator.invalidate_count == 1

    def test_invalidate_all_decorator(self):
        """Test invalidate_all decorator functionality"""
        mock_decorator = SyncMockCacheDecorator()
        service = TestService(mock_decorator)

        result = service.clear_all()
        assert result == "cleared"
        assert mock_decorator.invalidate_all_count == 1

    def test_cache_decorator_without_init(self):
        """Test cache decorator raises error when _cache_decorator not found"""

        class BadService(BaseCacheableClass):
            def __init__(self):
                # Not calling super().__init__()
                pass

            @BaseCacheableClass.cache()
            def get_data(self):
                return "data"

        service = BadService()
        with pytest.raises(AttributeError, match="_cache_decorator not found"):
            service.get_data()

    def test_invalidate_decorator_without_init(self):
        """Test invalidate decorator raises error when _cache_decorator not found"""

        class BadService(BaseCacheableClass):
            def __init__(self):
                # Not calling super().__init__()
                pass

            @BaseCacheableClass.invalidate("some_func")
            def update_data(self):
                return "data"

        service = BadService()
        with pytest.raises(AttributeError, match="_cache_decorator not found"):
            service.update_data()

    def test_invalidate_all_decorator_without_init(self):
        """Test invalidate_all decorator raises error when _cache_decorator not found"""

        class BadService(BaseCacheableClass):
            def __init__(self):
                # Not calling super().__init__()
                pass

            @BaseCacheableClass.invalidate_all()
            def clear_data(self):
                return "data"

        service = BadService()
        with pytest.raises(AttributeError, match="_cache_decorator not found"):
            service.clear_data()


class TestSyncInMemoryCacheDecorator:
    def test_basic_caching(self):
        """Test basic caching functionality"""
        decorator = SyncCacheDecoratorFactory.in_memory(default_ttl=60)
        decorator.invalidate_all()

        call_count = 0

        @decorator(ttl=10)
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result = test_func(5)
        assert result == 10
        assert call_count == 1

        # Second call should use cache
        result = test_func(5)
        assert result == 10
        assert call_count == 1  # Not incremented

        # Different argument should call function
        result = test_func(10)
        assert result == 20
        assert call_count == 2

    def test_invalidate(self):
        """Test invalidate functionality"""
        decorator = SyncCacheDecoratorFactory.in_memory(default_ttl=60)
        decorator.invalidate_all()

        call_count = 0

        @decorator()
        def get_data(key):
            nonlocal call_count
            call_count += 1
            return f"data_{key}"

        @decorator.invalidate("get_data", param_mapping={"key": "key"})
        def update_data(key, value):
            return f"updated_{key}_{value}"

        # Cache some data
        result = get_data("test")
        assert result == "data_test"
        assert call_count == 1

        # Should use cache
        result = get_data("test")
        assert result == "data_test"
        assert call_count == 1

        # Update should invalidate cache
        update_data("test", "new")

        # Next call should hit function
        result = get_data("test")
        assert result == "data_test"
        assert call_count == 2

    def test_invalidate_all(self):
        """Test invalidate all functionality"""
        decorator = SyncCacheDecoratorFactory.in_memory(default_ttl=60)
        decorator.invalidate_all()

        call_count = 0

        @decorator()
        def get_data(key):
            nonlocal call_count
            call_count += 1
            return f"data_{key}"

        @decorator.invalidate_all()
        def clear_cache():
            return "cleared"

        # Cache multiple items
        get_data("test1")
        get_data("test2")
        assert call_count == 2

        # Should use cache
        get_data("test1")
        get_data("test2")
        assert call_count == 2

        # Clear all caches
        clear_cache()

        # Should call functions again
        get_data("test1")
        get_data("test2")
        assert call_count == 4

    def test_error_handling(self):
        """Test error handling in decorator"""
        decorator = SyncCacheDecoratorFactory.in_memory(default_ttl=60)
        cache = decorator.cache

        # Mock cache.get to raise an exception
        with patch.object(cache, "get", side_effect=Exception("Cache error")):

            @decorator()
            def test_func(x):
                return x * 2

            # Should still work even if cache fails
            result = test_func(5)
            assert result == 10

    @pytest.mark.asyncio
    async def test_none_result_caching(self):
        """Test that None results are not cached"""
        decorator = SyncCacheDecoratorFactory.in_memory(default_ttl=60)
        decorator.invalidate_all()

        call_count = 0

        @decorator()
        def test_func():
            nonlocal call_count
            call_count += 1
            return None

        # First call
        result = test_func()
        assert result is None
        assert call_count == 1

        # Second call should also call function (None not cached)
        result = test_func()
        assert result is None
        assert call_count == 2
