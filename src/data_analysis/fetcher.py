import asyncio
import json
import os
import platform

import aiohttp

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def fetch_json(session, url):
    async with session.get(url) as response:
        return await response.json()


async def get_top_stories(limit=10):
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    async with aiohttp.ClientSession() as session:
        story_ids = await fetch_json(session, url)
        return story_ids[:limit] if limit else story_ids


async def get_item(session, item_id):
    url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
    return await fetch_json(session, url)


async def get_user(session, username):
    url = f"https://hacker-news.firebaseio.com/v0/user/{username}.json"
    return await fetch_json(session, url)


async def get_comments(
    session, comment_ids, comments, users, seen_items, seen_users, depth, max_depth
):
    if depth >= max_depth:
        return

    for comment_id in comment_ids:
        if comment_id in seen_items:
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
                    depth + 1,
                    max_depth,
                )


async def get_hn_content(story_ids, max_depth=3):
    stories = []
    comments = []
    users = []
    seen_items = set()
    seen_users = set()

    async with aiohttp.ClientSession() as session:
        for story_id in story_ids:
            story = await get_item(session, story_id)
            if story and story.get("type") == "story":
                stories.append(story)
                seen_items.add(story_id)

                author = story.get("by")
                if author and author not in seen_users:
                    user = await get_user(session, author)
                    if user:
                        users.append(user)
                        seen_users.add(author)

                if story.get("kids"):
                    await get_comments(
                        session,
                        story["kids"][:5],
                        comments,
                        users,
                        seen_items,
                        seen_users,
                        0,
                        max_depth,
                    )

    return {"stories": stories, "comments": comments, "users": users}


def fetch_hackernews_data(max_stories=8, max_comments=2):
    """Fetch HackerNews data and return items for processing."""

    async def _fetch():
        story_ids = await get_top_stories(limit=max_stories)
        data = await get_hn_content(story_ids, max_depth=max_comments)

        items = []
        items.extend(data["stories"])
        items.extend(data["comments"])
        items.extend(data["users"])
        return items

    return asyncio.run(_fetch())


if __name__ == "__main__":
    # Test function when run directly
    data_dir = "src/data"
    os.makedirs(data_dir, exist_ok=True)
    output_file = os.path.join(data_dir, "topstories.json")

    print("Fetching top stories...")
    items = fetch_hackernews_data(max_stories=5, max_comments=2)

    # Save as JSON for inspection
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"items": items}, f, indent=2)

    print(f"Saved {len(items)} items to {output_file}")
