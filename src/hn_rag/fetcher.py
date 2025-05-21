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


# TODO add other endpoints later
def get_top_stories_url():
    """Generate the URL for fetching top stories."""
    return "https://hacker-news.firebaseio.com/v0/topstories.json"


async def fetch_json(session, url):
    """Get JSON data from URL."""
    async with session.get(url) as response:
        return await response.json()


async def get_top_stories(limit=10):
    """Get IDs of top stories."""
    async with aiohttp.ClientSession() as session:
        story_ids = await fetch_json(session, get_top_stories_url())
        return story_ids[:limit]


# TODO check different max_depth
async def get_hn_content(story_ids, max_depth=2):
    """Build content structure from stories and comments."""
    stories = []
    comments = []
    seen_ids = set()

    # Queue format: (item_id, depth, parent_id)
    queue = [(id, 0, None) for id in story_ids]

    async with aiohttp.ClientSession() as session:
        while queue:
            # Process items in batches of 20
            current_batch, queue = queue[:20], queue[20:]

            # Get items we haven't seen yet
            new_ids = []
            for item_id, _, _ in current_batch:
                if item_id not in seen_ids:
                    new_ids.append(item_id)

            if not new_ids:
                continue

            # Fetch all items in batch
            fetch_tasks = []
            for item_id in new_ids:
                item_url = get_item_url(item_id)
                fetch_tasks.append(fetch_json(session, item_url))

            items = await asyncio.gather(*fetch_tasks)

            # Process each item
            for item_id, item in zip(new_ids, items):
                if not item or item_id in seen_ids:
                    continue

                seen_ids.add(item_id)
                # Find the corresponding batch item information
                batch_ids = []
                for i in current_batch:
                    batch_ids.append(i[0])
                item_index = batch_ids.index(item_id)
                item_info = current_batch[item_index]

                depth = item_info[1]
                parent_id = item_info[2]

                # Handle different item types
                # TODO check if there is a better approach to build the data structure
                if item.get("type") == "story":
                    # Create story data dictionary
                    story = {}
                    story["id"] = item_id
                    story["title"] = item.get("title", "")
                    story["url"] = item.get("url", "")
                    story["text"] = item.get("text", "")
                    story["by"] = item.get("by", "")
                    story["time"] = item.get("time", 0)
                    story["score"] = item.get("score", 0)
                    story["kids"] = item.get("kids", [])
                    stories.append(story)

                elif item.get("type") == "comment":
                    # Create comment data dictionary
                    comment = {}
                    comment["id"] = item_id
                    comment["story_id"] = story_ids[0]
                    comment["parent_id"] = parent_id
                    comment["by"] = item.get("by", "")
                    comment["text"] = item.get("text", "")
                    comment["time"] = item.get("time", 0)
                    comment["depth"] = max(0, depth - 1)
                    comment["kids"] = item.get("kids", [])
                    comments.append(comment)

                # Add children to queue if we haven't reached max depth
                if depth < max_depth and item.get("kids"):
                    kid_ids = item.get("kids", [])
                    for kid_id in kid_ids:
                        queue.append((kid_id, depth + 1, item_id))

    return {"stories": stories, "comments": comments}


async def main():
    """Main function to fetch and save Hacker News data."""
    # Create data directory
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)

    # TODO move to .env or .secrets
    # TODO rename based on the endpoint (To categorize files)
    output_path = data_dir
    output_file = os.path.join(output_path, "topstories.json")

    # Variables for tracking data
    existing_stories = []
    existing_comments = []
    existing_story_ids = set()

    # Load existing data if available
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
            existing_stories = existing_data.get("stories", [])
            existing_comments = existing_data.get("comments", [])

            # Extract existing story IDs for comparison
            for story in existing_stories:
                existing_story_ids.add(story["id"])

    # Get new stories
    # TODO check if limit=None would cause problems
    top_story_ids = await get_top_stories(limit=10)

    # Find new stories that we don't already have
    new_story_ids = []
    for story_id in top_story_ids:
        if story_id not in existing_story_ids:
            new_story_ids.append(story_id)

    if new_story_ids:
        # Get content for new stories
        new_data = await get_hn_content(new_story_ids)

        # Combine with existing data
        # TODO check if more data is needed for the data structure
        all_stories = existing_stories + new_data["stories"]
        all_comments = existing_comments + new_data["comments"]

        # Save combined data
        output_data = {"stories": all_stories, "comments": all_comments}

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)

        # Output statistics
        new_story_count = len(new_data["stories"])
        new_comment_count = len(new_data["comments"])
        msg_1 = f"Added {new_story_count} new stories"
        msg_2 = f"and {new_comment_count} comments"
        print(f"{msg_1} {msg_2}")
    else:
        print("No new stories to add")

    # Calculate total story count
    if new_story_ids:
        new_count = len(new_story_ids)
    else:
        new_count = 0

    story_count = len(existing_stories) + new_count
    print(f"Data file now has {story_count} stories")


if __name__ == "__main__":
    asyncio.run(main())
