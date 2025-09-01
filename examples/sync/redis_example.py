import os

from base_cacheable_class import BaseCacheableClass, SyncCacheDecoratorFactory


class ProductService(BaseCacheableClass):
    def __init__(self, redis_host="localhost", redis_port=6379, redis_password=None):
        # Initialize Redis cache
        cache_decorator = SyncCacheDecoratorFactory.redis(
            host=redis_host, port=redis_port, password=redis_password or "", username="default", db=0, default_ttl=3600
        )
        super().__init__(cache_decorator)
        self._redis_cache = cache_decorator.cache  # Keep reference for cleanup

        # Simulate product database
        self.products = {
            1: {"id": 1, "name": "Laptop", "price": 999.99, "stock": 10},
            2: {"id": 2, "name": "Mouse", "price": 29.99, "stock": 100},
            3: {"id": 3, "name": "Keyboard", "price": 79.99, "stock": 50},
        }

    @BaseCacheableClass.cache(ttl=300)  # Cache for 5 minutes
    def get_product(self, product_id: int):
        print(f"Fetching product {product_id} from database...")
        return self.products.get(product_id)

    @BaseCacheableClass.cache(ttl=600)  # Cache for 10 minutes
    def search_products(self, keyword: str):
        print(f"Searching products with keyword: {keyword}")
        results = []
        for product in self.products.values():
            if keyword.lower() in str(product["name"]).lower():
                results.append(product)
        return results

    @BaseCacheableClass.cache(ttl=60)  # Cache for 1 minute
    def get_inventory_status(self):
        print("Calculating inventory status...")
        total_products = len(self.products)
        total_stock = sum(p["stock"] for p in self.products.values())
        low_stock = [p for p in self.products.values() if int(p["stock"]) < 20]
        return {
            "total_products": total_products,
            "total_stock": total_stock,
            "low_stock_items": len(low_stock),
            "low_stock_products": low_stock,
        }

    @BaseCacheableClass.invalidate("get_product", param_mapping={"product_id": "product_id"})
    @BaseCacheableClass.invalidate("get_inventory_status")
    def update_stock(self, product_id: int, new_stock: int):
        print(f"Updating stock for product {product_id} to {new_stock}")
        if product_id in self.products:
            self.products[product_id]["stock"] = new_stock
            return self.products[product_id]
        return None

    @BaseCacheableClass.invalidate_all()
    def refresh_catalog(self):
        print("Refreshing entire product catalog...")
        # Simulate reloading products from database
        return "Catalog refreshed and all caches cleared"

    def close(self):
        """Clean up Redis connection"""
        self._redis_cache.close()


def main():
    # Configure Redis connection from environment or use defaults
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_password = os.getenv("REDIS_PASSWORD")

    print("=== Redis Cache Example ===")
    print(f"Connecting to Redis at {redis_host}:{redis_port}")

    service = ProductService(redis_host, redis_port, redis_password)

    try:
        # Test connection
        service._redis_cache.ping()
        print("Successfully connected to Redis!")
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        print("Make sure Redis is running. You can start it with: redis-server")
        return

    try:
        # Clear any existing cache
        service._redis_cache.clear()

        # Get product - will fetch from DB
        print("\n1. Get product 1:")
        product = service.get_product(1)
        print(f"Result: {product}")

        # Get same product - will return from Redis cache
        print("\n2. Get product 1 again (from Redis):")
        product = service.get_product(1)
        print(f"Result: {product}")

        # Search products
        print("\n3. Search for 'board':")
        results = service.search_products("board")
        print(f"Found {len(results)} products")

        # Get inventory status
        print("\n4. Get inventory status:")
        status = service.get_inventory_status()
        print(
            f"Status: Total products: {status['total_products']}, "
            f"Total stock: {status['total_stock']}, "
            f"Low stock items: {status['low_stock_items']}"
        )

        # Update stock - will invalidate related caches
        print("\n5. Update stock for product 1:")
        updated = service.update_stock(1, 5)
        print(f"Updated: {updated}")

        # Get product again - will fetch from DB (cache invalidated)
        print("\n6. Get product 1 after stock update:")
        product = service.get_product(1)
        print(f"Result: {product}")

        # Get inventory status again - will recalculate (cache invalidated)
        print("\n7. Get inventory status after update:")
        status = service.get_inventory_status()
        print(f"Low stock items: {status['low_stock_items']}")

        # Demonstrate cache persistence across instances
        print("\n8. Creating new service instance:")
        service2 = ProductService(redis_host, redis_port, redis_password)

        # This will use cached data from the first instance
        print("Getting product 2 from new instance (should be cached):")
        service.get_product(2)  # Cache it first
        product = service2.get_product(2)  # Get from cache
        print(f"Result: {product}")

        service2.close()

    finally:
        # Clean up
        service.close()
        print("\nClosed Redis connections")


if __name__ == "__main__":
    main()
