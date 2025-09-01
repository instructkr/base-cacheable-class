import time
from base_cacheable_class import BaseCacheableClass, SyncCacheDecoratorFactory


class WeatherService(BaseCacheableClass):
    def __init__(self):
        cache_decorator = SyncCacheDecoratorFactory.in_memory(default_ttl=300)
        super().__init__(cache_decorator)

    @BaseCacheableClass.cache(ttl=60)  # Cache for 1 minute
    def get_weather(self, city: str):
        print(f"Fetching weather for {city}...")
        # Simulate API call
        return {"city": city, "temp": 25, "condition": "Sunny"}

    @BaseCacheableClass.cache(ttl=30)  # Cache for 30 seconds
    def get_forecast(self, city: str, days: int = 7):
        print(f"Fetching {days}-day forecast for {city}...")
        # Simulate API call
        return {"city": city, "days": days, "forecast": [{"day": i, "temp": 20 + i} for i in range(days)]}


def main():
    service = WeatherService()

    print("=== Weather Service Example ===")

    # First call - will fetch from source
    print("\n1. First call to get_weather:")
    weather = service.get_weather("Seoul")
    print(f"Result: {weather}")

    # Second call - will return from cache
    print("\n2. Second call to get_weather (cached):")
    weather = service.get_weather("Seoul")
    print(f"Result: {weather}")

    # Different city - will fetch from source
    print("\n3. Different city:")
    weather = service.get_weather("Tokyo")
    print(f"Result: {weather}")

    # Forecast example
    print("\n4. Get forecast:")
    forecast = service.get_forecast("Seoul", days=3)
    print(f"Result: {forecast}")

    # Wait for cache to expire
    print("\n5. Waiting 31 seconds for forecast cache to expire...")
    time.sleep(31)

    # This will fetch again
    print("\n6. Get forecast after cache expiry:")
    forecast = service.get_forecast("Seoul", days=3)
    print(f"Result: {forecast}")


if __name__ == "__main__":
    main()
