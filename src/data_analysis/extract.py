"""
HackerNews Data extracter
Fetches data from HackerNews API with batching, caching, and concurrent processing.
"""

import asyncio
import json
import os
import platform

import aiohttp

from .api_endpoints import Endpoints

# Windows-specific asyncio fix for event loop policy issues
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class Extracter:
    def __init__(
        self,
        stories_per_category=5,  # Number of stories to fetch per category
        max_comment_depth=3,  # Maximum depth for comment threads to avoid excessive recursion
        # Limits for various data fetches
        max_top_comments=5,  # Limit top-level comments to avoid overwhelming the output
        max_child_comments=3,  # Limit child comments to avoid deep recursion
        batch_size=10,  # Number of items to fetch in each batch
    ):
        self.stories_per_category = stories_per_category
        self.max_comment_depth = max_comment_depth
        self.max_top_comments = max_top_comments
        self.max_child_comments = max_child_comments
        self.batch_size = batch_size
        self.ep = Endpoints()

    def get_project_data_path(self):
        """Find project data directory by locating pyproject.toml (robust path resolution)"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        while current_dir != os.path.dirname(current_dir):
            if os.path.exists(os.path.join(current_dir, "pyproject.toml")):
                return os.path.join(current_dir, "src", "data")
            current_dir = os.path.dirname(current_dir)
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src", "data")

    def load_processed_ids(self):
        """Load previously processed IDs"""
        ids_file = os.path.join(self.get_project_data_path(), "processed_ids.json")
        return set(json.load(open(ids_file))) if os.path.exists(ids_file) else set()

    def save_processed_ids(self, processed_ids):
        """Save processed IDs to disk"""
        data_dir = self.get_project_data_path()
        os.makedirs(data_dir, exist_ok=True)
        with open(os.path.join(data_dir, "processed_ids.json"), "w") as f:
            json.dump(list(processed_ids), f, indent=2)

    async def fetch_batch(self, session, ids_or_names, fetch_func, item_type, batch_size=None):
        """Generic batch fetcher with concurrency and rate limiting"""
        bs = batch_size or self.batch_size
        all_results = []
        for i in range(0, len(ids_or_names), bs):
            batch_data = ids_or_names[i : i + bs]
            tasks = [fetch_func(session, item) for item in batch_data]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            valid_results = [r for r in batch_results if r and not isinstance(r, Exception)]
            all_results.extend(valid_results)
            print(f"  Fetched batch of {len(valid_results)}/{len(batch_data)} {item_type}")
        return all_results

    async def get_comments_with_metadata(self, session, comment_ids, comments, users, seen_items, seen_users, processed_ids, depth, parent_category):
        """Recursively fetch comments and authors with batching and depth control"""
        if depth >= self.max_comment_depth or not comment_ids:
            return

        new_comment_ids = [cid for cid in comment_ids if cid not in seen_items and cid not in processed_ids]
        if not new_comment_ids:
            return

        print(f"    Fetching {len(new_comment_ids)} comments at depth {depth} in batches...")
        batch_comments = await self.fetch_batch(session, new_comment_ids, self.ep.get_item, "items")

        comment_authors, child_comment_ids = [], []
        for comment in batch_comments:
            if comment and comment.get("type") == "comment":
                # Add metadata for categorization
                comment.update(
                    {
                        "hn_category": parent_category,
                        "hn_context": f"comment_on_{parent_category}_story",
                        "hn_depth": depth,
                    }
                )
                comments.append(comment)
                seen_items.add(comment["id"])

                if (author := comment.get("by")) and author not in seen_users:
                    comment_authors.append(author)
                    seen_users.add(author)  # Limit recursion depth and child count
                if comment.get("kids") and depth < self.max_comment_depth - 1:
                    child_comment_ids.extend(comment["kids"][: self.max_child_comments])

        if comment_authors:
            print(f"    Fetching {len(comment_authors)} commenter profiles in batches...")
            for user in await self.fetch_batch(session, comment_authors, self.ep.get_user, "user profiles"):
                if user:
                    user["hn_context"] = f"commenter_on_{parent_category}"
                    users.append(user)

        if child_comment_ids and depth < self.max_comment_depth - 1:
            await self.get_comments_with_metadata(session, child_comment_ids, comments, users, seen_items, seen_users, processed_ids, depth + 1, parent_category)

    async def get_hn_content_with_metadata(self, story_ids_by_category, processed_ids):
        """Fetch comprehensive HN content with metadata"""
        stories, comments, users = [], [], []
        seen_items, seen_users = set(), set()

        async with aiohttp.ClientSession() as session:
            for category, story_ids in story_ids_by_category.items():
                print(f"Processing {category}: {len(story_ids)} stories")
                new_story_ids = [sid for sid in story_ids if sid not in processed_ids]
                if not new_story_ids:
                    print(f"  All {len(story_ids)} stories already processed")
                    continue

                print(f"  Fetching {len(new_story_ids)} new stories in batches...")
                batch_stories = await self.fetch_batch(session, new_story_ids, self.ep.get_item, "items")

                story_authors, all_comment_ids = [], []
                for story in batch_stories:
                    if story and story.get("type") == "story":  # Add metadata for categorization
                        story.update({"hn_category": category, "hn_endpoint": category})
                        stories.append(story)
                        seen_items.add(story["id"])

                        if (author := story.get("by")) and author not in seen_users:
                            story_authors.append(author)
                            seen_users.add(author)

                        if story.get("kids"):
                            all_comment_ids.extend(story["kids"][: self.max_top_comments])

                if story_authors:
                    print(f"  Fetching {len(story_authors)} author profiles in batches...")
                    for user in await self.fetch_batch(session, story_authors, self.ep.get_user, "user profiles"):
                        if user:
                            user["hn_context"] = f"author_of_{category}_story"
                            users.append(user)

                if all_comment_ids:
                    await self.get_comments_with_metadata(session, all_comment_ids, comments, users, seen_items, seen_users, processed_ids, 0, category)

        return {"stories": stories, "comments": comments, "users": users}

    def fetch_hackernews_data(self):
        """Main entry point for fetching HN data"""

        async def _fetch():
            processed_ids = self.load_processed_ids()
            print(f"Already processed {len(processed_ids)} items")

            all_story_ids = await self.ep.get_all_stories(self.stories_per_category)
            new_story_ids_by_category = {}
            total_new_stories = 0

            for category, story_ids in all_story_ids.items():
                new_ids = [sid for sid in story_ids if sid not in processed_ids]
                new_story_ids_by_category[category] = new_ids
                total_new_stories += len(new_ids)
                print(f"  {category}: {len(new_ids)} new stories, {len(story_ids) - len(new_ids)} already processed")

            print(f"Summary: {total_new_stories} new stories")
            if total_new_stories == 0:
                print("No new stories to process - everything is up to date!")
                return []

            data = await self.get_hn_content_with_metadata(new_story_ids_by_category, processed_ids)

            def save_raw_data():
                data_dir = self.get_project_data_path()
                os.makedirs(data_dir, exist_ok=True)

                data["fetch_metadata"] = {
                    "endpoints_used": list(all_story_ids.keys()),
                    "stories_per_category": self.stories_per_category,
                    "max_comment_depth": self.max_comment_depth,
                    "total_stories_fetched": len(data["stories"]),
                    "total_comments_fetched": len(data["comments"]),
                    "total_users_fetched": len(data["users"]),
                    "fetch_timestamp": asyncio.get_event_loop().time(),
                }

                with open(os.path.join(data_dir, "hackernews_raw.json"), "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                print("Raw data saved")

                new_items = data["stories"] + data["comments"] + data["users"]
                new_ids = {item["id"] for item in new_items if item and item.get("id")}
                processed_ids.update(new_ids)
                self.save_processed_ids(processed_ids)

                with open(os.path.join(data_dir, "enhanced_hackernews_data.json"), "w", encoding="utf-8") as f:
                    json.dump({"items": new_items}, f, indent=2)
                print(f"Saved {len(new_items)} items (total tracked: {len(processed_ids)})")

                return new_items

            return save_raw_data()

        return asyncio.run(_fetch())
