import asyncio

from base_cacheable_class import BaseCacheableClass, AsyncCacheDecoratorFactory


class UserRepository(BaseCacheableClass):
    def __init__(self):
        cache_decorator = AsyncCacheDecoratorFactory.in_memory(default_ttl=600)  # 10 minutes default
        super().__init__(cache_decorator)
        # Simulate database
        self.db = {
            1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
            2: {"id": 2, "name": "Bob", "email": "bob@example.com"},
            3: {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
        }

    @BaseCacheableClass.cache(ttl=300)  # Cache for 5 minutes
    async def get_user(self, user_id: int):
        print(f"Fetching user {user_id} from database...")
        await asyncio.sleep(0.5)  # Simulate DB query
        return self.db.get(user_id)

    @BaseCacheableClass.cache()  # Cache indefinitely
    async def get_all_users(self):
        print("Fetching all users from database...")
        await asyncio.sleep(1)  # Simulate DB query
        return list(self.db.values())

    @BaseCacheableClass.invalidate("get_user", param_mapping={"user_id": "user_id"})
    @BaseCacheableClass.invalidate("get_all_users")
    async def update_user(self, user_id: int, name: str | None = None, email: str | None = None):
        print(f"Updating user {user_id}...")
        if user_id in self.db:
            if name:
                self.db[user_id]["name"] = name
            if email:
                self.db[user_id]["email"] = email
            return self.db[user_id]
        return None

    @BaseCacheableClass.invalidate("get_user", param_mapping={"user_id": "user_id"})
    @BaseCacheableClass.invalidate("get_all_users")
    async def delete_user(self, user_id: int):
        print(f"Deleting user {user_id}...")
        return self.db.pop(user_id, None)

    @BaseCacheableClass.invalidate_all()
    async def refresh_cache(self):
        print("Refreshing all caches...")
        return "All caches cleared"


async def main():
    repo = UserRepository()

    print("=== Cache Invalidation Example ===")

    # Get user - will fetch from DB
    print("\n1. Get user 1:")
    user = await repo.get_user(1)
    print(f"Result: {user}")

    # Get same user - will return from cache
    print("\n2. Get user 1 again (cached):")
    user = await repo.get_user(1)
    print(f"Result: {user}")

    # Get all users - will fetch from DB
    print("\n3. Get all users:")
    users = await repo.get_all_users()
    print(f"Count: {len(users)}")

    # Update user - will invalidate specific user cache and all users cache
    print("\n4. Update user 1:")
    updated = await repo.update_user(1, name="Alice Updated")
    print(f"Updated: {updated}")

    # Get user again - will fetch from DB (cache was invalidated)
    print("\n5. Get user 1 after update:")
    user = await repo.get_user(1)
    print(f"Result: {user}")

    # Get all users again - will fetch from DB (cache was invalidated)
    print("\n6. Get all users after update:")
    users = await repo.get_all_users()
    print(f"Count: {len(users)}")

    # Cache some data
    print("\n7. Cache multiple users:")
    await repo.get_user(1)
    await repo.get_user(2)
    await repo.get_user(3)
    print("Users 1, 2, 3 are now cached")

    # Clear all caches
    print("\n8. Clear all caches:")
    await repo.refresh_cache()

    # All will fetch from DB
    print("\n9. Get users after cache clear:")
    user1 = await repo.get_user(1)
    user2 = await repo.get_user(2)
    print(f"User 1: {user1}")
    print(f"User 2: {user2}")


if __name__ == "__main__":
    asyncio.run(main())
