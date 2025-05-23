import asyncio
import json
import os
import platform

import aiohttp

# Fix for Windows event loop
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def get_item_url(item_id):
    """Generate the URL for fetching a specific item."""
    base_url = "https://hacker-news.firebaseio.com/v0/item"
    return f"{base_url}/{item_id}.json"


def get_user_url(username):
    """Generate the URL for fetching a specific user."""
    base_url = "https://hacker-news.firebaseio.com/v0/user"
    return f"{base_url}/{username}.json"


# TODO add other endpoints later
def get_top_stories_url():
    """Generate the URL for fetching top stories."""
    return "https://hacker-news.firebaseio.com/v0/topstories.json"


async def fetch_json(session, url):
    """Get JSON data from URL."""
    async with session.get(url) as response:
        return await response.json()


async def get_top_stories(limit=None):
    """Get IDs of top stories."""
    async with aiohttp.ClientSession() as session:
        story_ids = await fetch_json(session, get_top_stories_url())
        if limit is None:
            return story_ids  # Return ALL stories
        return story_ids[:limit]


# TODO check different max_depth
async def get_hn_content(story_ids, max_depth=5):
    """Build content structure from stories and comments."""
    stories = []
    comments = []
    users = []
    seen_ids = set()
    seen_users = set()

    # Queue format: (item_id, depth, parent_id, story_id)
    queue = [(id, 0, None, id) for id in story_ids]

    async with aiohttp.ClientSession() as session:
        while queue:
            # Process items in batches of 20
            current_batch, queue = queue[:20], queue[20:]

            # Get items we haven't seen yet
            new_ids = []
            batch_info = {}
            for item_id, depth, parent_id, story_id in current_batch:
                if item_id not in seen_ids:
                    new_ids.append(item_id)
                    batch_info[item_id] = (depth, parent_id, story_id)

            if not new_ids:
                continue

            # Fetch all items in batch
            fetch_tasks = []
            for item_id in new_ids:
                item_url = get_item_url(item_id)
                fetch_tasks.append(fetch_json(session, item_url))

            items = await asyncio.gather(*fetch_tasks)

            # Collect usernames for batch fetching
            usernames_to_fetch = []

            # Process each item
            for item_id, item in zip(new_ids, items):
                if not item or item_id in seen_ids:
                    continue

                seen_ids.add(item_id)
                depth, parent_id, story_id = batch_info[item_id]

                # Collect username for fetching
                username = item.get("by", "")
                if username and username not in seen_users:
                    usernames_to_fetch.append(username)
                    seen_users.add(username)

                # Handle different item types - keep pure API data
                # TODO study the data more to check if there is
                # another way to build the data structure
                if item.get("type") == "story":
                    # Store exactly what API returns
                    stories.append(dict(item))

                elif item.get("type") == "comment":
                    # Store exactly what API returns
                    comments.append(dict(item))

                # Add children to queue if we haven't reached max depth
                if depth < max_depth and item.get("kids"):
                    kid_ids = item.get("kids", [])
                    for kid_id in kid_ids:
                        queue.append((kid_id, depth + 1, item_id, story_id))

            # Fetch users in batch
            if usernames_to_fetch:
                user_fetch_tasks = []
                for username in usernames_to_fetch:
                    user_url = get_user_url(username)
                    user_fetch_tasks.append(fetch_json(session, user_url))

                user_data = await asyncio.gather(*user_fetch_tasks)

                # Process user data - capture ALL fields automatically
                for username, user in zip(usernames_to_fetch, user_data):
                    if user:
                        # Start with all fields from API response
                        user_record = dict(user)
                        users.append(user_record)

    return {"stories": stories, "comments": comments, "users": users}


async def main():
    """Main function to fetch and save Hacker News data."""

    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)

    # TODO rename based on the endpoint (To categorize files)
    output_file = os.path.join(data_dir, "topstories.json")

    # Always fetch fresh data (no loading existing data)
    print("Fetching fresh top stories...")

    # Get current top stories
    top_story_ids = await get_top_stories(limit=10)

    # Get content for all stories (fresh fetch every time)
    data = await get_hn_content(top_story_ids)

    # Always save new data (overwrites existing file)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    story_count = len(data["stories"])
    comment_count = len(data["comments"])
    user_count = len(data["users"])
    print(
        f"Saved {story_count} stories, {comment_count} comments, and {user_count} users"
    )
    print(f"Data saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
