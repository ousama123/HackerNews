"""
HackerNews Data Fetcher

Fetches data from HackerNews API endpoints for RAG processing.
Handles stories, comments, and user profiles with rate limiting and duplicate tracking.

Features:
- Multi-endpoint fetching (top, new, best, ask, show, jobs)
- Recursive comment fetching with depth limits
- User profile collection for authors and commenters
- Incremental updates with processed ID tracking
- Async operations for efficient API usage

Flow: Load IDs → Fetch stories → Get comments → Collect users → Save JSON
"""

import asyncio
import json
import os
import platform

import aiohttp

# Windows-specific event loop policy for compatibility
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def get_project_data_path():
    """
    Locate the project's data directory by searching for pyproject.toml.

    Traverses up the directory tree from the current file location to find
    the project root (indicated by pyproject.toml), then returns the data path.

    Returns:
        str: Absolute path to the src/data directory

    Search Strategy:
        1. Start from current file's directory
        2. Move up directories until finding pyproject.toml
        3. Return {project_root}/src/data path
        4. Falls back to relative path calculation if not found
    """
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    while current_dir != os.path.dirname(current_dir):
        if os.path.exists(os.path.join(current_dir, "pyproject.toml")):
            return os.path.join(current_dir, "src", "data")
        current_dir = os.path.dirname(current_dir)
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_file))), "src", "data")


def load_processed_ids():
    """Load previously processed HackerNews item IDs to avoid duplicates."""
    data_dir = get_project_data_path()
    ids_file = os.path.join(data_dir, "processed_ids.json")
    if os.path.exists(ids_file):
        with open(ids_file) as f:
            return set(json.load(f))  # Convert list back to set for fast lookups
    return set()  # Return empty set if no previous runs


def save_processed_ids(processed_ids):
    """Save updated set of processed item IDs to disk for incremental updates."""
    data_dir = get_project_data_path()
    os.makedirs(data_dir, exist_ok=True)  # Create directory if needed
    ids_file = os.path.join(data_dir, "processed_ids.json")
    with open(ids_file, "w") as f:
        json.dump(list(processed_ids), f, indent=2)  # Convert set to list for JSON


async def fetch_json(session, url):
    """Fetch JSON data from a URL using an aiohttp session."""
    async with session.get(url) as response:
        return await response.json()  # Parse and return JSON response


async def get_stories_by_category(session, category, limit=10):
    """Fetch story IDs from a specific HackerNews category endpoint."""
    # Map category names to API endpoints
    endpoints = {
        "topstories": "https://hacker-news.firebaseio.com/v0/topstories.json",
        "newstories": "https://hacker-news.firebaseio.com/v0/newstories.json",
        "beststories": "https://hacker-news.firebaseio.com/v0/beststories.json",
        "askstories": "https://hacker-news.firebaseio.com/v0/askstories.json",
        "showstories": "https://hacker-news.firebaseio.com/v0/showstories.json",
        "jobstories": "https://hacker-news.firebaseio.com/v0/jobstories.json",
    }

    # Return empty list for unknown categories
    if category not in endpoints:
        return []

    # Fetch story IDs and apply limit if specified
    story_ids = await fetch_json(session, endpoints[category])
    return story_ids[:limit] if limit else story_ids


async def get_all_stories(stories_per_category=5):
    """
    Fetch story IDs from all HackerNews category endpoints.

    Args:
        stories_per_category (int): Number of stories per category

    Returns:
        dict: Category names mapped to story ID lists
    """
    results = {}
    # Define all HackerNews category endpoints
    categories = ["topstories", "newstories", "beststories", "askstories", "showstories", "jobstories"]

    async with aiohttp.ClientSession() as session:
        for category in categories:
            try:
                # Fetch story IDs for each category with limit
                story_ids = await get_stories_by_category(session, category, stories_per_category)
                results[category] = story_ids
                print(f" {category}: {len(story_ids)} stories")
            except Exception as e:
                # Continue with other categories if one fails
                print(f" Error fetching {category}: {e}")
                results[category] = []
    return results


async def get_item(session, item_id):
    """
    Fetch a specific HackerNews item by its ID.

    Args:
        session (aiohttp.ClientSession): Active HTTP session
        item_id (int): Unique HackerNews item ID

    Returns:
        dict: Item data with fields like id, type, by, time, text, kids, etc.
    """
    url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
    return await fetch_json(session, url)


async def get_user(session, username):
    """
    Fetch a HackerNews user profile by username.

    Args:
        session (aiohttp.ClientSession): Active HTTP session
        username (str): HackerNews username

    Returns:
        dict: User profile data with id, karma, created, about, etc.
    """
    url = f"https://hacker-news.firebaseio.com/v0/user/{username}.json"
    return await fetch_json(session, url)


async def get_comments_with_metadata(session, comment_ids, comments, users, seen_items, seen_users, processed_ids, depth, max_depth, parent_category):
    """
    Recursively fetch comments and their authors with enhanced metadata.

    Args:
        session: HTTP session
        comment_ids: List of comment IDs to fetch
        comments: List to append comments to (modified in-place)
        users: List to append user profiles to (modified in-place)
        seen_items: Set of processed item IDs (modified in-place)
        seen_users: Set of processed usernames (modified in-place)
        processed_ids: Set of globally processed IDs to skip
        depth: Current recursion depth
        max_depth: Maximum depth to traverse
        parent_category: Category of parent story for metadata
    """
    # Stop recursion at maximum depth to prevent excessive API calls
    if depth >= max_depth:
        return

    for comment_id in comment_ids:
        # Skip already processed comments to avoid duplicates
        if comment_id in seen_items or comment_id in processed_ids:
            continue

        # Fetch comment data from HackerNews API
        comment = await get_item(session, comment_id)
        if comment and comment.get("type") == "comment":
            # Add metadata for RAG context enrichment
            comment["hn_category"] = parent_category
            comment["hn_context"] = f"comment_on_{parent_category}_story"
            comment["hn_depth"] = depth
            comments.append(comment)
            seen_items.add(comment_id)

            # Fetch commenter profile for additional context
            author = comment.get("by")
            if author and author not in seen_users:
                user = await get_user(session, author)
                if user:
                    # Add role-based context to user profile
                    user["hn_context"] = f"commenter_on_{parent_category}"
                    users.append(user)
                    seen_users.add(author)

            # Recursively fetch child comments (limited to first 3)
            if comment.get("kids") and depth < max_depth - 1:
                await get_comments_with_metadata(session, comment["kids"][:3], comments, users, seen_items, seen_users, processed_ids, depth + 1, max_depth, parent_category)


async def get_hn_content_with_metadata(story_ids_by_category, processed_ids, max_depth=3):
    """
    Fetch comprehensive HackerNews content with enhanced metadata.

    Args:
        story_ids_by_category (dict): Category names mapped to story ID lists
        processed_ids (set): Set of already processed item IDs to skip
        max_depth (int): Maximum comment tree depth to traverse

    Returns:
        dict: Contains "stories", "comments", and "users" lists with metadata
    """
    # Initialize collections for different content types
    stories, comments, users, seen_items, seen_users = [], [], [], set(), set()

    async with aiohttp.ClientSession() as session:
        for category, story_ids in story_ids_by_category.items():
            print(f"Processing {category}: {len(story_ids)} stories")
            for story_id in story_ids:
                # Skip already processed stories for incremental updates
                if story_id in processed_ids:
                    continue

                # Fetch full story data from HackerNews API
                story = await get_item(session, story_id)
                if story and story.get("type") == "story":
                    # Add category metadata for RAG context
                    story["hn_category"] = category
                    story["hn_endpoint"] = category
                    stories.append(story)
                    seen_items.add(story_id)

                    # Fetch story author profile with context
                    author = story.get("by")
                    if author and author not in seen_users:
                        user = await get_user(session, author)
                        if user:
                            # Add role-based context to author profile
                            user["hn_context"] = f"author_of_{category}_story"
                            users.append(user)
                            seen_users.add(author)

                    # Fetch top-level comments (limited to first 5 for relevance)
                    if story.get("kids"):
                        await get_comments_with_metadata(session, story["kids"][:5], comments, users, seen_items, seen_users, processed_ids, 0, max_depth, category)

    return {"stories": stories, "comments": comments, "users": users}


def fetch_hackernews_data(stories_per_category=3, max_comments=2):
    """
    Main entry point for fetching fresh HackerNews data across all endpoints.

    Args:
        stories_per_category (int): Number of stories to fetch from each category
        max_comments (int): Maximum depth to traverse in comment trees

    Returns:
        list: List of all newly fetched items (stories, comments, users)
    """

    async def _fetch():
        # Load tracking data for incremental updates
        processed_ids = load_processed_ids()
        print(f"Already processed {len(processed_ids)} items")

        # Fetch story IDs from all HackerNews endpoints
        all_story_ids = await get_all_stories(stories_per_category)

        # Filter out already processed stories to avoid duplicates
        new_story_ids_by_category = {}
        total_new_stories = 0
        for category, story_ids in all_story_ids.items():
            # Identify new stories not in processed set
            new_ids = [sid for sid in story_ids if sid not in processed_ids]
            new_story_ids_by_category[category] = new_ids
            total_new_stories += len(new_ids)
            print(f"  {category}: {len(new_ids)} new stories (out of {len(story_ids)} total)")

        print(f"Found {total_new_stories} total new stories across all categories")
        if total_new_stories == 0:
            print("No new stories to process - everything is up to date!")
            return []

        # Fetch comprehensive content with metadata for new stories only
        data = await get_hn_content_with_metadata(new_story_ids_by_category, processed_ids, max_depth=max_comments)

        # Prepare data directory and file paths
        data_dir = get_project_data_path()
        os.makedirs(data_dir, exist_ok=True)
        raw_file = os.path.join(data_dir, "hackernews_raw.json")

        # Add comprehensive fetch metadata for tracking and debugging
        data["fetch_metadata"] = {
            "endpoints_used": list(all_story_ids.keys()),
            "stories_per_category": stories_per_category,
            "max_comment_depth": max_comments,
            "total_stories_fetched": len(data["stories"]),
            "total_comments_fetched": len(data["comments"]),
            "total_users_fetched": len(data["users"]),
            "fetch_timestamp": asyncio.get_event_loop().time(),
        }

        # Save raw JSON data for preprocessing pipeline
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Raw data with metadata saved to: {raw_file}")

        # Flatten all new items for return value and ID tracking
        new_items = []
        new_items.extend(data["stories"])
        new_items.extend(data["comments"])
        new_items.extend(data["users"])

        # Update processed IDs tracking with all newly fetched items
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
    """
    MAin entry point for testing the enhanced HackerNews data fetcher separately.
    """
    print("Enhanced HackerNews Fetcher - Testing All Endpoints")
    print("=" * 60)

    # Ensure data directory exists for output files
    data_dir = get_project_data_path()
    os.makedirs(data_dir, exist_ok=True)
    output_file = os.path.join(data_dir, "enhanced_hackernews_data.json")

    # Execute main fetching workflow with test parameters
    items = fetch_hackernews_data(stories_per_category=3, max_comments=2)

    # Save test results for inspection and debugging
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"items": items}, f, indent=2)
    print(f"Saved {len(items)} items to {output_file}")

    # Display summary of fetched content by category
    if items:
        categories = {}
        for item in items:
            if item.get("hn_category"):
                category = item["hn_category"]
                categories[category] = categories.get(category, 0) + 1
        print("\nContent Categories Collected:")
        for category, count in categories.items():
            print(f"  {category}: {count} items")

    print("\nEnhanced fetching test complete!")
