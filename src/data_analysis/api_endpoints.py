# endpoints.py
import aiohttp


class Endpoints:
    async def fetch_json(self, session, url):
        """Fetch JSON from URL"""
        async with session.get(url) as response:
            return await response.json()

    # used for fetching comment and story data from HN API
    async def get_item(self, session, item_id):
        """Fetch HackerNews item by ID"""
        return await self.fetch_json(session, f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json")

    async def get_user(self, session, username):
        """Fetch HackerNews user profile"""
        return await self.fetch_json(session, f"https://hacker-news.firebaseio.com/v0/user/{username}.json")

    # used for fetchign story IDs from various HN endpoints with number of stories per category
    async def get_all_stories(self, stories_per_category=5):
        """Fetch story IDs from all HN endpoints"""
        endpoints = {
            "topstories": "https://hacker-news.firebaseio.com/v0/topstories.json",
            "newstories": "https://hacker-news.firebaseio.com/v0/newstories.json",
            "beststories": "https://hacker-news.firebaseio.com/v0/beststories.json",
            "askstories": "https://hacker-news.firebaseio.com/v0/askstories.json",
            "showstories": "https://hacker-news.firebaseio.com/v0/showstories.json",
            "jobstories": "https://hacker-news.firebaseio.com/v0/jobstories.json",
        }
        results = {}
        async with aiohttp.ClientSession() as session:
            for category, url in endpoints.items():
                try:
                    story_ids = await self.fetch_json(session, url)
                    results[category] = story_ids[:stories_per_category]
                    print(f" {category}: {len(results[category])} stories")
                except Exception as e:
                    print(f" Error fetching {category}: {e}")
                    results[category] = []
        return results
