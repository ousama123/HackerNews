"""
HackerNews Data Preprocessor - Compact Version
Processes raw HN JSON into structured text for RAG systems.
"""

import html
import json
import os
import re
from datetime import datetime

# Configuration
POPULAR_SCORE_THRESHOLD = 100
HIGHLY_POPULAR_THRESHOLD = 500
DISCUSSION_HEAVY_THRESHOLD = 50
HIGH_KARMA_THRESHOLD = 1000


def extract_urls_from_text(text):
    """Extract URLs from text"""
    return list(set(re.findall(r'https?://[^\s\]\)<>"]+', text))) if text else []


def clean_text(text):
    """Clean HTML and normalize whitespace"""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def format_story(story):
    """Format HN story into structured document"""
    if not story:
        return ""

    title = story.get("title", "").strip()
    author = story.get("by", "Unknown")
    score = story.get("score", 0)
    url = story.get("url", "")
    text = clean_text(story.get("text", ""))
    comment_count = len(story.get("kids", []))
    timestamp = story.get("time", 0)
    date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M") if timestamp else "Unknown"
    hn_category = story.get("hn_category", "topstories")

    # Determine story type
    if hn_category == "askstories" or title.startswith("Ask HN:"):
        story_type, content_category = "Ask HN", "ask_hn"
    elif hn_category == "showstories" or title.startswith("Show HN:"):
        story_type, content_category = "Show HN", "show_hn"
    elif hn_category == "jobstories":
        story_type, content_category = "Job Posting", "jobs"
    elif hn_category == "beststories":
        story_type, content_category = "Best Story", "best"
    else:
        story_type, content_category = "Story", "general"

    story_id = story.get("id", "Unknown")
    doc = f"""Metadata: type=story, category={content_category}
Story ID: {story_id}
Title: {title}
Description: {story_type}
Author: {author}
Time: {date}
Score: {score} points
Comments: {comment_count} total
Source Endpoint: {hn_category}"""

    if story_id != "Unknown":
        doc += f"\nStory URL on Hacker News Website: https://news.ycombinator.com/item?id={story_id}"
    if url:
        doc += f"\nArticle: {url}"
    if text and text not in ["[flagged]", "[dead]"]:
        doc += f"\nText: {text}"
        if urls := [u for u in extract_urls_from_text(text) if u != url]:
            doc += f"\nExtracted URLs: {', '.join(urls)}"

    # Add tags
    tags = [content_category, "story"]
    if score > POPULAR_SCORE_THRESHOLD:
        tags.append("popular")
    if score > HIGHLY_POPULAR_THRESHOLD:
        tags.append("highly_popular")
    if comment_count > DISCUSSION_HEAVY_THRESHOLD:
        tags.append("discussion_heavy")

    return doc + f"\nTags: {', '.join(tags)}"


def format_comment(comment):
    """Format HN comment into structured document"""
    if not comment:
        return ""

    author = comment.get("by", "Unknown")
    text = clean_text(comment.get("text", ""))
    timestamp = comment.get("time", 0)
    date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M") if timestamp else "Unknown"
    hn_category = comment.get("hn_category", "general")
    hn_context = comment.get("hn_context", "comment")
    hn_depth = comment.get("hn_depth", 0)
    comment_id = comment.get("id", "Unknown")

    doc = f"""Metadata: type=comment, category=discussion
Comment ID: {comment_id}
Author: {author}
Time: {date}
Source Category: {hn_category}
Context: {hn_context}
Comment Depth: {hn_depth}"""

    if comment_id != "Unknown":
        doc += f"\nComment URL on Hacker News: https://news.ycombinator.com/item?id={comment_id}"
    if comment.get("parent"):
        doc += f"\nReplying to: {comment['parent']}"

    if text and text not in ["[flagged]", "[dead]"]:
        doc += f"\nText: {text}"
        if urls := extract_urls_from_text(text):
            doc += f"\nExtracted URLs: {', '.join(urls)}"
    else:
        doc += "\nText: [Deleted or empty]"

    tags = [hn_category, "comment"]
    tags.append("top_level_comment" if hn_depth == 0 else "reply")

    return doc + f"\nTags: {', '.join(tags)}"


def format_user(user):
    """Format HN user profile into structured document"""
    if not user:
        return ""

    username = user.get("id", "Unknown")
    karma = user.get("karma", 0)
    created = user.get("created", 0)
    about = clean_text(user.get("about", ""))
    created_date = datetime.fromtimestamp(created).strftime("%Y-%m-%d") if created else "Unknown"
    hn_context = user.get("hn_context", "user_profile")

    doc = f"""Metadata: type=user_profile, category=user_info
Username: {username}
Karma: {karma} points
Member since: {created_date}
Context: {hn_context}"""

    if about:
        doc += f"\nAbout: {about}"
        if urls := extract_urls_from_text(about):
            doc += f"\nExtracted URLs: {', '.join(urls)}"

    tags = ["user_profile"]
    if karma > HIGH_KARMA_THRESHOLD:
        tags.append("high_karma_user")
    if "author" in hn_context:
        tags.append("content_author")
    if "commenter" in hn_context:
        tags.append("active_commenter")

    return doc + f"\nTags: {', '.join(tags)}"


def save_preprocessed_data(items, output_file=None, append_mode=False):
    """Save processed HN items to structured text file"""
    print("Processing HackerNews data...")

    if output_file is None:
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        output_file = os.path.join(project_root, "src", "data", "hackernews_optimized.txt")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    documents = []
    for item in items:
        if not item:
            continue

        item_type = item.get("type", "")
        if item_type == "story":
            doc_text = format_story(item)
        elif item_type == "comment":
            doc_text = format_comment(item)
        elif "id" in item and "karma" in item:
            doc_text = format_user(item)
        else:
            continue

        if doc_text and doc_text.strip():
            documents.append(doc_text.strip())

    if not documents:
        print("No documents to save")
        return output_file

    mode = "a" if append_mode and os.path.exists(output_file) else "w"
    with open(output_file, mode, encoding="utf-8") as f:
        if append_mode and os.path.exists(output_file):
            for doc in documents:
                f.write(f"\n\n{doc}")
        else:
            for i, doc in enumerate(documents):
                f.write(doc)
                if i < len(documents) - 1:
                    f.write("\n\n")

    print(f"Done! {len(documents)} documents saved to {output_file}")
    return output_file


def process_hackernews_data():
    """Main function to process raw HN data"""
    current_file = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    input_file = os.path.join(project_root, "src", "data", "hackernews_raw.json")

    if not os.path.exists(input_file):
        print(f"No raw data found at {input_file}")
        print("Run the fetcher first!")
        return None

    print("Loading raw HackerNews data...")
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", [])
    print(f"Found {len(items)} items to process")

    if not items:
        print("No items found in the data file")
        return None

    return save_preprocessed_data(items)


def append_preprocessed_data(items, output_file=None):
    """Append new processed items to existing file"""
    return save_preprocessed_data(items, output_file, append_mode=True)


if __name__ == "__main__":
    print("HackerNews Preprocessor - Converting JSON to readable text")
    print("=" * 60)

    output_file = process_hackernews_data()

    if output_file:
        print("\nSuccessfully processed data!")
        print(f"Output saved to: {output_file}")
    else:
        print("\nProcessing failed. Make sure to run the fetcher first!")

    print("\nNext step: Run the pipeline to create vector embeddings")
