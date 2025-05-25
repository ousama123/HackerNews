import asyncio
import json
import os
import platform

import aiohttp

# Fix for Windows async event loop compatibility
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def load_processed_ids():
    """Load IDs we've already processed."""
    ids_file = "src/data/processed_ids.json"
    if os.path.exists(ids_file):
        with open(ids_file, "r") as f:
            return set(json.load(f))
    return set()


def save_processed_ids(processed_ids):
    """Save processed IDs to file."""
    os.makedirs("src/data", exist_ok=True)
    with open("src/data/processed_ids.json", "w") as f:
        json.dump(list(processed_ids), f, indent=2)


async def fetch_json(session, url):
    """Fetch JSON data from a URL."""
    async with session.get(url) as response:
        return await response.json()


async def get_stories_by_category(session, category, limit=10):
    """Get story IDs from a specific HackerNews endpoint."""
    endpoints = {
        "topstories": "https://hacker-news.firebaseio.com/v0/topstories.json",
        "newstories": "https://hacker-news.firebaseio.com/v0/newstories.json",
        "beststories": "https://hacker-news.firebaseio.com/v0/beststories.json",
        "askstories": "https://hacker-news.firebaseio.com/v0/askstories.json",
        "showstories": "https://hacker-news.firebaseio.com/v0/showstories.json",
        "jobstories": "https://hacker-news.firebaseio.com/v0/jobstories.json",
    }

    if category not in endpoints:
        return []

    story_ids = await fetch_json(session, endpoints[category])
    return story_ids[:limit] if limit else story_ids


async def get_all_stories(stories_per_category=5):
    """Get stories from all HackerNews endpoints."""
    results = {}
    categories = [
        "topstories",
        "newstories",
        "beststories",
        "askstories",
        "showstories",
        "jobstories",
    ]

    async with aiohttp.ClientSession() as session:
        for category in categories:
            try:
                story_ids = await get_stories_by_category(
                    session, category, stories_per_category
                )
                results[category] = story_ids
                print(f" {category}: {len(story_ids)} stories")
            except Exception as e:
                print(f" Error fetching {category}: {e}")
                results[category] = []

    return results


async def get_item(session, item_id):
    """Get a specific item (story, comment, etc.) by ID."""
    url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
    return await fetch_json(session, url)


async def get_user(session, username):
    """Get user information by username."""
    url = f"https://hacker-news.firebaseio.com/v0/user/{username}.json"
    return await fetch_json(session, url)


async def get_comments(
    session,
    comment_ids,
    comments,
    users,
    seen_items,
    seen_users,
    processed_ids,
    depth,
    max_depth,
):
    """Recursively fetch comments and their replies."""
    if depth >= max_depth:
        return

    for comment_id in comment_ids:
        if comment_id in seen_items or comment_id in processed_ids:
            continue

        comment = await get_item(session, comment_id)
        if comment and comment.get("type") == "comment":
            comments.append(comment)
            seen_items.add(comment_id)

            author = comment.get("by")
            if author and author not in seen_users:
                user = await get_user(session, author)
                if user:
                    users.append(user)
                    seen_users.add(author)

            if comment.get("kids") and depth < max_depth - 1:
                await get_comments(
                    session,
                    comment["kids"][:3],
                    comments,
                    users,
                    seen_items,
                    seen_users,
                    processed_ids,
                    depth + 1,
                    max_depth,
                )


async def get_hn_content(story_ids, processed_ids, max_depth=3):
    """Fetch stories, their comments, and user profiles."""
    stories = []
    comments = []
    users = []
    seen_items = set()  # Track items in this session
    seen_users = set()  # Track users in this session

    async with aiohttp.ClientSession() as session:
        for story_id in story_ids:
            # Skip already processed stories
            if story_id in processed_ids:
                continue

            story = await get_item(session, story_id)
            if story and story.get("type") == "story":
                stories.append(story)
                seen_items.add(story_id)

                # Get story author
                author = story.get("by")
                if author and author not in seen_users:
                    user = await get_user(session, author)
                    if user:
                        users.append(user)
                        seen_users.add(author)

                # Get comments for this story
                if story.get("kids"):
                    await get_comments(
                        session,
                        story["kids"][:5],  # First 5 top-level comments
                        comments,
                        users,
                        seen_items,
                        seen_users,
                        processed_ids,
                        0,  # Start at depth 0
                        max_depth,
                    )

    return {"stories": stories, "comments": comments, "users": users}


async def get_hn_content_with_metadata(
    story_ids_by_category, processed_ids, max_depth=3
):
    """Fetch stories, comments, and users with enhanced metadata."""
    stories = []
    comments = []
    users = []
    seen_items = set()
    seen_users = set()

    async with aiohttp.ClientSession() as session:
        for category, story_ids in story_ids_by_category.items():
            print(f"Processing {category}: {len(story_ids)} stories")

            for story_id in story_ids:
                if story_id in processed_ids:
                    continue

                story = await get_item(session, story_id)
                if story and story.get("type") == "story":
                    story["hn_category"] = category
                    story["hn_endpoint"] = category
                    stories.append(story)
                    seen_items.add(story_id)

                    author = story.get("by")
                    if author and author not in seen_users:
                        user = await get_user(session, author)
                        if user:
                            user["hn_context"] = f"author_of_{category}_story"
                            users.append(user)
                            seen_users.add(author)

                    if story.get("kids"):
                        await get_comments_with_metadata(
                            session,
                            story["kids"][:5],
                            comments,
                            users,
                            seen_items,
                            seen_users,
                            processed_ids,
                            0,
                            max_depth,
                            category,
                        )

    return {"stories": stories, "comments": comments, "users": users}


async def get_comments_with_metadata(
    session,
    comment_ids,
    comments,
    users,
    seen_items,
    seen_users,
    processed_ids,
    depth,
    max_depth,
    parent_category,
):
    """Recursively fetch comments with metadata."""
    if depth >= max_depth:
        return

    for comment_id in comment_ids:
        if comment_id in seen_items or comment_id in processed_ids:
            continue

        comment = await get_item(session, comment_id)
        if comment and comment.get("type") == "comment":
            comment["hn_category"] = parent_category
            comment["hn_context"] = f"comment_on_{parent_category}_story"
            comment["hn_depth"] = depth
            comments.append(comment)
            seen_items.add(comment_id)

            author = comment.get("by")
            if author and author not in seen_users:
                user = await get_user(session, author)
                if user:
                    user["hn_context"] = f"commenter_on_{parent_category}"
                    users.append(user)
                    seen_users.add(author)

            if comment.get("kids") and depth < max_depth - 1:
                await get_comments_with_metadata(
                    session,
                    comment["kids"][:3],
                    comments,
                    users,
                    seen_items,
                    seen_users,
                    processed_ids,
                    depth + 1,
                    max_depth,
                    parent_category,
                )


def fetch_hackernews_data(stories_per_category=3, max_comments=2):
    """Fetch only NEW HackerNews data from ALL endpoints that we haven't processed before."""

    async def _fetch():
        processed_ids = load_processed_ids()
        print(f"Already processed {len(processed_ids)} items")

        all_story_ids = await get_all_stories(stories_per_category)

        new_story_ids_by_category = {}
        total_new_stories = 0

        # Filter out already processed stories
        for category, story_ids in all_story_ids.items():
            new_ids = [sid for sid in story_ids if sid not in processed_ids]
            new_story_ids_by_category[category] = new_ids
            total_new_stories += len(new_ids)
            print(
                f"  {category}: {len(new_ids)} new stories (out of {len(story_ids)} total)"
            )

        print(f"Found {total_new_stories} total new stories across all categories")

        if total_new_stories == 0:
            print("No new stories to process - everything is up to date!")
            return []

        data = await get_hn_content_with_metadata(
            new_story_ids_by_category, processed_ids, max_depth=max_comments
        )

        # Save raw data with metadata
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        data_dir = os.path.join(project_root, "src", "data")
        os.makedirs(data_dir, exist_ok=True)
        raw_file = os.path.join(data_dir, "hackernews_raw.json")

        data["fetch_metadata"] = {
            "endpoints_used": list(all_story_ids.keys()),
            "stories_per_category": stories_per_category,
            "max_comment_depth": max_comments,
            "total_stories_fetched": len(data["stories"]),
            "total_comments_fetched": len(data["comments"]),
            "total_users_fetched": len(data["users"]),
            "fetch_timestamp": asyncio.get_event_loop().time(),
        }

        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Raw data with metadata saved to: {raw_file}")

        # Collect all new items for ID tracking
        new_items = []
        new_items.extend(data["stories"])
        new_items.extend(data["comments"])
        new_items.extend(data["users"])

        # Update processed IDs
        new_ids = set()
        for item in new_items:
            if item and item.get("id"):
                new_ids.add(item["id"])

        processed_ids.update(new_ids)
        save_processed_ids(processed_ids)
        print(f"Added {len(new_ids)} new IDs to tracking (total: {len(processed_ids)})")

        return new_items

    return asyncio.run(_fetch())


if __name__ == "__main__":
    print(" Enhanced HackerNews Fetcher - Testing All Endpoints")
    print("=" * 60)

    current_file = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    data_dir = os.path.join(project_root, "src", "data")
    os.makedirs(data_dir, exist_ok=True)
    output_file = os.path.join(data_dir, "enhanced_hackernews_data.json")

    items = fetch_hackernews_data(stories_per_category=3, max_comments=2)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"items": items}, f, indent=2)

    print(f"💾 Saved {len(items)} items to {output_file}")

    if items:
        categories = {}
        for item in items:
            if item.get("hn_category"):
                category = item["hn_category"]
                categories[category] = categories.get(category, 0) + 1

        print("\n Content Categories Collected:")
        for category, count in categories.items():
            print(f"  {category}: {count} items")

    print("\n Enhanced fetching test complete!")
