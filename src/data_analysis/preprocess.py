import html
import os
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

    hn_category = story.get("hn_category", "topstories")
    hn_endpoint = story.get("hn_endpoint", "topstories")

    story_type = "Story"
    content_category = "general"

    if hn_category == "askstories" or title.startswith("Ask HN:"):
        story_type = "Ask HN"
        content_category = "ask_hn"
    elif hn_category == "showstories" or title.startswith("Show HN:"):
        story_type = "Show HN"
        content_category = "show_hn"
    elif hn_category == "jobstories":
        story_type = "Job Posting"
        content_category = "jobs"
    elif hn_category == "beststories":
        story_type = "Best Story"
        content_category = "best"
    elif hn_category == "newstories":
        story_type = "New Story"
        content_category = "new"

    doc = f"""Content Type: Hacker News Story
Story ID: {story.get("id", "Unknown")}
Title: {title}
Description: {story_type}
Category: {content_category}
Source Endpoint: {hn_endpoint}
Author: {author}
Score: {score} points
Comments: {comment_count} total
Posted: {date}"""

    if url:
        doc += f"\nLink: {url}"

    if text:
        doc += f"\nText: {text}"

    tags = [content_category, hn_category]
    if (
        "AI" in title.upper()
        or "ML" in title.upper()
        or "MACHINE LEARNING" in title.upper()
    ):
        tags.append("ai_ml")
    if "STARTUP" in title.upper():
        tags.append("startup")
    if "PROGRAMMING" in title.upper() or "CODE" in title.upper():
        tags.append("programming")

    doc += f"\nTags: {', '.join(tags)}"

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

    hn_category = comment.get("hn_category", "general")
    hn_context = comment.get("hn_context", "comment")
    hn_depth = comment.get("hn_depth", 0)

    doc = f"""Content Type: Hacker News Comment
Comment ID: {comment.get("id", "Unknown")}
Author: {author}
Time: {date}
Source Category: {hn_category}
Context: {hn_context}
Comment Depth: {hn_depth}"""

    if comment.get("parent"):
        doc += f"\nReplying to: {comment['parent']}"

    if text and text != "[flagged]" and text != "[dead]":
        doc += f"\nText: {text}"
    else:
        doc += "\nText: [Deleted or empty]"

    tags = [hn_category, "comment"]
    if hn_depth == 0:
        tags.append("top_level_comment")
    else:
        tags.append("reply")

    doc += f"\nTags: {', '.join(tags)}"

    return doc


def format_user(user):
    if not user:
        return ""

    username = user.get("id", "Unknown")
    karma = user.get("karma", 0)
    created = user.get("created", 0)
    about = clean_text(user.get("about", ""))

    created_date = (
        datetime.fromtimestamp(created).strftime("%Y-%m-%d") if created else "Unknown"
    )

    hn_context = user.get("hn_context", "user_profile")

    doc = f"""Content Type: Hacker News User Profile
Username: {username}
Karma: {karma} points
Member since: {created_date}
Context: {hn_context}"""

    if about:
        doc += f"\nAbout: {about}"

    tags = ["user_profile"]
    if karma > 1000:
        tags.append("high_karma_user")
    if "author" in hn_context:
        tags.append("content_author")
    if "commenter" in hn_context:
        tags.append("active_commenter")

    doc += f"\nTags: {', '.join(tags)}"

    return doc


def save_preprocessed_data(items, output_file=None, append_mode=False):
    print("Processing HackerNews data...")

    if output_file is None:
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        output_file = os.path.join(
            project_root, "src", "data", "hackernews_optimized.txt"
        )

    data_dir = os.path.dirname(output_file)
    os.makedirs(data_dir, exist_ok=True)

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
        elif item_type == "user" or item.get("karma") is not None:
            doc = format_user(item)
            if doc:
                documents.append(doc)

    if not documents:
        print("No new documents to process")
        return output_file

    doc_start_num = 1
    if append_mode and os.path.exists(output_file):
        with open(output_file, encoding="utf-8") as f:
            content = f.read()
            existing_docs = content.count("DOCUMENT ")
            doc_start_num = existing_docs + 1
        print(
            f"Appending {len(documents)} new documents starting from "
            f"document {doc_start_num}"
        )

    file_mode = "a" if append_mode else "w"
    with open(output_file, file_mode, encoding="utf-8") as f:
        for i, doc in enumerate(documents, doc_start_num):
            f.write(f"DOCUMENT {i}\n")
            f.write("=" * 50 + "\n")
            f.write(doc + "\n\n")
            f.write("=" * 50 + "\n\n")

    action = "Appended" if append_mode else "Generated"
    print(f"{action} {len(documents)} documents")
    print(f"Writing to {output_file}...")
    print(f"Done! {len(documents)} documents saved to {output_file}")

    return output_file


def append_preprocessed_data(items, output_file=None):
    return save_preprocessed_data(items, output_file, append_mode=True)
