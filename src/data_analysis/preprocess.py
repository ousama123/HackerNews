import html
import json
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
    date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M") if timestamp else "Unknown"
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
    doc = f"""Content Type: Hacker News {story_type}
Story ID: {story.get("id", "Unknown")}
Title: {title}
Author: {author}
Time: {date}
Score: {score} points
Comments: {comment_count}
Source: {hn_endpoint}
Category: {content_category}"""
    if url:
        doc += f"\nURL: {url}"
    if text and text != "[flagged]" and text != "[dead]":
        doc += f"\nText: {text}"
    tags = [content_category, "story"]
    if score > 100:
        tags.append("popular")
    if score > 500:
        tags.append("highly_popular")
    if comment_count > 50:
        tags.append("discussion_heavy")
    doc += f"\nTags: {', '.join(tags)}"
    return doc


def format_comment(comment):
    if not comment:
        return ""
    author = comment.get("by", "Unknown")
    text = clean_text(comment.get("text", ""))
    timestamp = comment.get("time", 0)
    date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M") if timestamp else "Unknown"
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
    created_date = datetime.fromtimestamp(created).strftime("%Y-%m-%d") if created else "Unknown"
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
        output_file = os.path.join(project_root, "src", "data", "hackernews_optimized.txt")
    data_dir = os.path.dirname(output_file)
    os.makedirs(data_dir, exist_ok=True)
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
    if append_mode and os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
        existing_docs = content.count("Document ")
        print(f"Appending {len(documents)} new documents starting from document {existing_docs + 1}")
        with open(output_file, "a", encoding="utf-8") as f:
            for i, doc in enumerate(documents):
                f.write(f"\n\nDocument {existing_docs + i + 1}:\n")
                f.write(doc)
        print(f"Appended {len(documents)} documents")
    else:
        with open(output_file, "w", encoding="utf-8") as f:
            for i, doc in enumerate(documents):
                f.write(f"Document {i + 1}:\n")
                f.write(doc)
                if i < len(documents) - 1:
                    f.write("\n\n")
    print(f"Writing to {output_file}...")
    print(f"Done! {len(documents)} documents saved to {output_file}")
    return output_file


def process_hackernews_data():
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
