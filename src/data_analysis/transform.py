import html
import re
from datetime import datetime
from langchain_core.documents import Document


class Transformer:
    def __init__(self):
        # Configuration thresholds
        self.POPULAR_SCORE_THRESHOLD = 100
        self.HIGHLY_POPULAR_THRESHOLD = 500
        self.DISCUSSION_HEAVY_THRESHOLD = 50
        self.HIGH_KARMA_THRESHOLD = 1000

    def extract_urls_from_text(self, text):
        """Extract URLs from text"""
        if not text:
            return []
        pattern = r"https?://[^\s\]\)(<>\"]+"
        return list(set(re.findall(pattern, text)))

    def clean_text(self, text):
        """Clean HTML and normalize whitespace"""
        if not text:
            return ""
        text = re.sub(r"<[^>]+>", "", text)
        text = html.unescape(text)
        return re.sub(r"\s+", " ", text).strip()

    def format_story(self, story):
        """Format HN story into structured document"""
        if not story:
            return ""

        story_id = story.get("id", "Unknown")
        title = story.get("title", "").strip()
        author = story.get("by", "Unknown")
        score = story.get("score", 0)
        url = story.get("url", "")
        text = self.clean_text(story.get("text", ""))
        comment_ids = story.get("kids", [])
        comment_count = len(comment_ids)
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

        parts = [
            f"Metadata: type=story, category={content_category}",
            f"Story ID: {story_id}",
            f"Title: {title}",
            f"Description: {story_type}",
            f"Author: {author}",
            f"Author Profile URL: https://news.ycombinator.com/user?id={author}",
            f"Time: {date}",
            f"Score: {score} points",
            f"Comments: {comment_count} total",
            f"Comment IDs: {', '.join(str(i) for i in comment_ids)}" if comment_ids else None,
            f"Source Endpoint: {hn_category}",
            f"Story URL: https://news.ycombinator.com/item?id={story_id}",
        ]
        parts = [p for p in parts if p]

        if url:
            parts.append(f"Article URL: {url}")
        if text and text not in ["[flagged]", "[dead]"]:
            parts.append(f"Text: {text}")
            urls = [u for u in self.extract_urls_from_text(text) if u != url]
            if urls:
                parts.append(f"Extracted URLs: {', '.join(urls)}")

        # Add tags
        tags = [content_category, "story"]
        if score > self.POPULAR_SCORE_THRESHOLD:
            tags.append("popular")
        if score > self.HIGHLY_POPULAR_THRESHOLD:
            tags.append("highly_popular")
        if comment_count > self.DISCUSSION_HEAVY_THRESHOLD:
            tags.append("discussion_heavy")

        parts.append(f"Tags: {', '.join(tags)}")
        return "\n".join(parts)

    def format_comment(self, comment):
        """Format HN comment into structured document"""
        if not comment:
            return ""

        comment_id = comment.get("id", "Unknown")
        author = comment.get("by", "Unknown")
        text = self.clean_text(comment.get("text", ""))
        timestamp = comment.get("time", 0)
        date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M") if timestamp else "Unknown"
        hn_category = comment.get("hn_category", "general")
        hn_context = comment.get("hn_context", "comment")
        hn_depth = comment.get("hn_depth", 0)
        parent = comment.get("parent")

        # Add description field
        comment_type = "Top-level Comment" if hn_depth == 0 else "Reply"

        parts = [
            "Metadata: type=comment, category=discussion",
            f"Comment ID: {comment_id}",
            f"Description: {comment_type}",
            f"Author: {author}",
            f"Author Profile URL: https://news.ycombinator.com/user?id={author}",
            # Relation by ID
            f"Parent ID: {parent}" if parent else None,
            f"Time: {date}",
            f"Source Category: {hn_category}",
            f"Context: {hn_context}",
            f"Comment Depth: {hn_depth}",
        ]
        parts = [p for p in parts if p]

        if text and text not in ["[flagged]", "[dead]"]:
            parts.append(f"Text: {text}")
            urls = self.extract_urls_from_text(text)
            if urls:
                parts.append(f"Extracted URLs: {', '.join(urls)}")
        else:
            parts.append("Text: [Deleted or empty]")

        # Tags
        tags = [hn_category, "comment"]
        tags.append("top_level_comment" if hn_depth == 0 else "reply")
        parts.append(f"Tags: {', '.join(tags)}")

        return "\n".join(parts)

    def format_user(self, user):
        """Format HN user profile into structured document"""
        if not user:
            return ""

        username = user.get("id", "Unknown")
        karma = user.get("karma", 0)
        created = user.get("created", 0)
        about = self.clean_text(user.get("about", ""))
        created_date = datetime.fromtimestamp(created).strftime("%Y-%m-%d") if created else "Unknown"
        hn_context = user.get("hn_context", "user_profile")

        # Add description field
        if karma > self.HIGH_KARMA_THRESHOLD:
            user_desc = "High Karma User"
        elif "author_of" in hn_context:
            user_desc = "Content Author"
        elif "commenter" in hn_context:
            user_desc = "Active Commenter"
        else:
            user_desc = "Hacker News User"

        submitted = user.get("submitted", [])
        preview = submitted[:10]
        preview_str = ", ".join(str(i) for i in preview) + ("…" if len(submitted) > 10 else "")

        parts = [
            "Metadata: type=user_profile, category=user_info",
            f"Username: {username}",
            f"Description: {user_desc}",
            f"Profile URL: https://news.ycombinator.com/user?id={username}",
            f"Karma: {karma} points",
            f"Member since: {created_date}",
            f"Context: {hn_context}",
        ]
        if about:
            parts.append(f"About: {about}")
            urls = self.extract_urls_from_text(about)
            if urls:
                parts.append(f"Extracted URLs: {', '.join(urls)}")

        if submitted:
            parts.append(f"Submitted IDs: {preview_str}")

        # Tags
        tags = ["user_profile"]
        if karma > self.HIGH_KARMA_THRESHOLD:
            tags.append("high_karma_user")
        if "author" in hn_context:
            tags.append("content_author")
        if "commenter" in hn_context:
            tags.append("active_commenter")
        parts.append(f"Tags: {', '.join(tags)}")

        return "\n".join(parts)

    def format_items_to_documents(self, new_items) -> list[Document]:
        """
        Convert raw HackerNews JSON items into langchain Documents.
        """
        docs = []
        for item in new_items:
            t = item.get("type")
            if t == "story":
                text = self.format_story(item)
            elif t == "comment":
                text = self.format_comment(item)
            elif t == "user":
                text = self.format_user(item)
            else:
                continue

            if not text:
                continue

            docs.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": "hackernews.com",
                        "item_id": item.get("id"),
                        "item_type": t,
                        "author": item.get("by", "unknown"),
                    },
                )
            )
        return docs
