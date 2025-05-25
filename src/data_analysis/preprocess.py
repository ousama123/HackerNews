"""
HackerNews Data Preprocessor

Processes raw HackerNews JSON data into structured text documents for RAG systems.
Handles stories, comments, and user profiles with metadata extraction and text cleaning.

Features:
- JSON to text conversion with metadata
- HTML cleaning and URL extraction
- Semantic tagging and categorization
- Full and incremental processing modes

Flow: Raw JSON → Item formatting → Text cleaning → Structured output
"""

import html
import json
import os
import re
from datetime import datetime


def extract_urls_from_text(text):
    """Extract URLs from text using regex pattern matching."""
    if not text:
        return []
    # Pattern matches http/https URLs excluding common terminators
    url_pattern = r'https?://[^\s\]\)<>"]+'
    urls = re.findall(url_pattern, text)
    return list(set(urls))  # Remove duplicates


def clean_text(text):
    """Clean and normalize text content by removing HTML and normalizing whitespace."""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Unescape HTML entities
    text = html.unescape(text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def format_story(story):
    """
    Format a HackerNews story into a structured document for RAG processing.

    Args:
        story (dict): Story data from HackerNews API

    Returns:
        str: Formatted document with metadata, content, and tags
    """
    if not story:
        return ""

    # Extract basic story information
    title = story.get("title", "").strip()
    author = story.get("by", "Unknown")
    score = story.get("score", 0)
    url = story.get("url", "")
    text = clean_text(story.get("text", ""))
    comment_count = len(story.get("kids", []))
    timestamp = story.get("time", 0)
    # Format timestamp for readability
    date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M") if timestamp else "Unknown"
    hn_category = story.get("hn_category", "topstories")
    hn_endpoint = story.get("hn_endpoint", "topstories")

    # Determine story type and content category based on source and title
    story_type = "Story"
    content_category = "general"

    # Categorize based on HN endpoint or title prefix
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
    # Build document with structured metadata and content
    doc = f"""Metadata: type=story, category={content_category}
Story ID: {story.get("id", "Unknown")}
Title: {title}
Description: {story_type}
Author: {author}
Time: {date}
Score: {score} points
Comments: {comment_count} total
Source Endpoint: {hn_endpoint}"""

    # Add external link if present
    if url:
        doc += f"\nLink: {url}"

    # Add text content if available and not flagged/dead
    if text and text != "[flagged]" and text != "[dead]":
        doc += f"\nText: {text}"

        # Extract URLs from text content, excluding the main story URL
        urls = extract_urls_from_text(text)
        if urls:
            # Remove the main story URL if it appears in the text
            filtered_urls = [u for u in urls if u != url]
            if filtered_urls:
                doc += f"\nExtracted URLs: {', '.join(filtered_urls)}"

    # Add semantic tags based on engagement metrics
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
    """
    Format a HackerNews comment into a structured document for RAG processing.

    Args:
        comment (dict): Comment data from HackerNews API

    Returns:
        str: Formatted comment document with metadata and threading context
    """
    if not comment:
        return ""

    # Extract comment metadata
    author = comment.get("by", "Unknown")
    text = clean_text(comment.get("text", ""))
    timestamp = comment.get("time", 0)
    # Format timestamp for readability
    date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M") if timestamp else "Unknown"
    hn_category = comment.get("hn_category", "general")  # Parent story category
    hn_context = comment.get("hn_context", "comment")  # Context from fetcher
    hn_depth = comment.get("hn_depth", 0)  # Nesting level in thread

    # Build document with threading metadata
    doc = f"""Metadata: type=comment, category=discussion
Comment ID: {comment.get("id", "Unknown")}
Author: {author}
Time: {date}
Source Category: {hn_category}
Context: {hn_context}
Comment Depth: {hn_depth}"""

    # Add parent reference for threading context
    if comment.get("parent"):
        doc += f"\nReplying to: {comment['parent']}"

    # Add comment text or indicate if deleted/empty
    if text and text != "[flagged]" and text != "[dead]":
        doc += f"\nText: {text}"

        # Extract URLs from comment text
        urls = extract_urls_from_text(text)
        if urls:
            doc += f"\nExtracted URLs: {', '.join(urls)}"
    else:
        doc += "\nText: [Deleted or empty]"

    # Add tags based on thread position and category
    tags = [hn_category, "comment"]
    if hn_depth == 0:
        tags.append("top_level_comment")  # Direct reply to story
    else:
        tags.append("reply")  # Nested comment

    doc += f"\nTags: {', '.join(tags)}"
    return doc


def format_user(user):
    """
    Format a HackerNews user profile into a structured document for RAG processing.

    Args:
        user (dict): User data from HackerNews API

    Returns:
        str: Formatted user profile document with karma and activity context
    """
    if not user:
        return ""

    # Extract user profile information
    username = user.get("id", "Unknown")
    karma = user.get("karma", 0)
    created = user.get("created", 0)
    about = clean_text(user.get("about", ""))
    # Format account creation date
    created_date = datetime.fromtimestamp(created).strftime("%Y-%m-%d") if created else "Unknown"
    hn_context = user.get("hn_context", "user_profile")  # How user was encountered

    # Build document with user metadata
    doc = f"""Metadata: type=user_profile, category=user_info
Username: {username}
Karma: {karma} points
Member since: {created_date}
Context: {hn_context}"""

    # Add bio information if available
    if about:
        doc += f"\nAbout: {about}"

        # Extract URLs from user's about section
        urls = extract_urls_from_text(about)
        if urls:
            doc += f"\nExtracted URLs: {', '.join(urls)}"

    # Add tags based on activity and karma
    tags = ["user_profile"]
    if karma > 1000:
        tags.append("high_karma_user")  # Established user
    if "author" in hn_context:
        tags.append("content_author")  # Story author
    if "commenter" in hn_context:
        tags.append("active_commenter")  # Active in discussions

    doc += f"\nTags: {', '.join(tags)}"
    return doc


def save_preprocessed_data(items, output_file=None, append_mode=False):
    """
    Save processed HackerNews items to a structured text file for RAG processing.

    Args:
        items (list): List of HackerNews items from the fetcher
        output_file (str, optional): Path to output file. Uses default if None
        append_mode (bool): If True, appends to existing file; if False, overwrites

    Returns:
        str: Path to the output file
    """
    print("Processing HackerNews data...")

    # Use default output path if none provided
    if output_file is None:
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        output_file = os.path.join(project_root, "src", "data", "hackernews_optimized.txt")

    # Ensure output directory exists
    data_dir = os.path.dirname(output_file)
    os.makedirs(data_dir, exist_ok=True)

    documents = []

    # Process each item according to its type
    for item in items:
        if not item:
            continue

        # Determine item type and apply appropriate formatting
        item_type = item.get("type", "")
        if item_type == "story":
            doc_text = format_story(item)
        elif item_type == "comment":
            doc_text = format_comment(item)
        elif "id" in item and "karma" in item:
            # User profiles detected by presence of karma field
            doc_text = format_user(item)
        else:
            # Skip unknown or malformed items
            continue

        # Only add successfully formatted documents
        if doc_text and doc_text.strip():
            documents.append(doc_text.strip())

    # Handle empty document list
    if not documents:
        print("No documents to save")
        return output_file

    # Write documents to file (append or overwrite mode)
    if append_mode and os.path.exists(output_file):
        print(f"Appending {len(documents)} new documents to existing file")
        with open(output_file, "a", encoding="utf-8") as f:
            for doc in documents:
                f.write(f"\n\n{doc}")  # Add separator before each new document
        print(f"Appended {len(documents)} documents")
    else:
        # Write new file or overwrite existing
        with open(output_file, "w", encoding="utf-8") as f:
            for i, doc in enumerate(documents):
                f.write(doc)
                if i < len(documents) - 1:
                    f.write("\n\n")  # Separate documents with double newline

    print(f"Writing to {output_file}...")
    print(f"Done! {len(documents)} documents saved to {output_file}")
    return output_file


def process_hackernews_data():
    """
    Main function to process raw HackerNews data from the fetcher.

    Returns:
        str or None: Path to output file if successful, None if failed
    """
    # Locate project root and input file
    current_file = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    input_file = os.path.join(project_root, "src", "data", "hackernews_raw.json")

    # Check if raw data file exists
    if not os.path.exists(input_file):
        print(f"No raw data found at {input_file}")
        print("Run the fetcher first!")
        return None

    # Load and parse JSON data
    print("Loading raw HackerNews data...")
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extract items from data structure
    items = data.get("items", [])
    print(f"Found {len(items)} items to process")

    # Validate items exist
    if not items:
        print("No items found in the data file")
        return None

    # Process all items and return output path
    return save_preprocessed_data(items)


def append_preprocessed_data(items, output_file=None):
    """
    Append new processed items to existing preprocessed data file.

    Args:
        items (list): List of new HackerNews items to process and append
        output_file (str, optional): Target file path. Uses default if None

    Returns:
        str: Path to the output file
    """
    # Use append mode for incremental updates
    return save_preprocessed_data(items, output_file, append_mode=True)


if __name__ == "__main__":
    # Main execution entry point
    print("HackerNews Preprocessor - Converting JSON to readable text")
    print("=" * 60)

    # Process raw data and get output file path
    output_file = process_hackernews_data()

    # Report results to user
    if output_file:
        print("\nSuccessfully processed data!")
        print(f"Output saved to: {output_file}")
    else:
        print("\nProcessing failed. Make sure to run the fetcher first!")

    print("\nNext step: Run the pipeline to create vector embeddings")
