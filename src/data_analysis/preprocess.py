import html
import re
from datetime import datetime


def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def format_story(story):
    if not story:
        return ""

    title = story.get("title", "").strip()
    author = story.get("by", "Unknown")
    score = story.get("score", 0)
    url = story.get("url", "")
    text = clean_text(story.get("text", ""))
    comment_count = len(story.get("kids", []))

    timestamp = story.get("time", 0)
    date = (
        datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
        if timestamp
        else "Unknown"
    )

    story_type = "Story"
    if title.startswith("Ask HN:"):
        story_type = "Ask HN"
    elif title.startswith("Show HN:"):
        story_type = "Show HN"

    doc = f"""Content Type: Hacker News Story
Story ID: {story.get("id", "Unknown")}
Title: {title}
Description: {story_type}
Author: {author}
Score: {score} points
Comments: {comment_count} total
Posted: {date}"""

    if url:
        doc += f"\nLink: {url}"

    if text:
        doc += f"\nText: {text}"

    return doc


def format_comment(comment):
    if not comment:
        return ""

    author = comment.get("by", "Unknown")
    text = clean_text(comment.get("text", ""))

    timestamp = comment.get("time", 0)
    date = (
        datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
        if timestamp
        else "Unknown"
    )

    doc = f"""Content Type: Hacker News Comment
Comment ID: {comment.get("id", "Unknown")}
Author: {author}
Time: {date}"""

    if comment.get("parent"):
        doc += f"\nReplying to: {comment['parent']}"

    if text and text != "[flagged]" and text != "[dead]":
        doc += f"\nText: {text}"
    else:
        doc += "\nText: [Deleted or empty]"

    return doc


def save_preprocessed_data(items, output_file="src/data/hackernews_processed.txt"):
    """Process items and save to file."""
    print("Processing HackerNews data...")

    documents = []

    for item in items:
        if not item:
            continue

        item_type = item.get("type", "")

        if item_type == "story":
            doc = format_story(item)
            if doc:
                documents.append(doc)
        elif item_type == "comment":
            doc = format_comment(item)
            if doc:
                documents.append(doc)

    with open(output_file, "w", encoding="utf-8") as f:
        for i, doc in enumerate(documents, 1):
            f.write(f"DOCUMENT {i}\n")
            f.write("=" * 50 + "\n")
            f.write(doc + "\n\n")
            f.write("=" * 50 + "\n\n")

    print(f"Generated {len(documents)} documents")
    print(f"Writing to {output_file}...")
    print(f"Done! {len(documents)} documents saved to {output_file}")

    return output_file
