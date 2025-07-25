"""
HackerNews Data Load class
Saves formatted documents to disk.
"""

import json
import os

from .transform import Transformer


class Loader:
    def __init__(self):
        self.transformer = Transformer()

    def save_preprocessed_data(self, items, output_file=None, append_mode=False):
        """Save processed HN items to structured text file"""
        print("Processing HackerNews data...")

        if output_file is None:
            current_file = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            output_file = os.path.join(project_root, "src", "data", "hackernews_optimized.txt")

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        #TODO use format_items_to_documents in Transformer instead
        documents = []
        for item in items:
            if not item:
                continue

            item_type = item.get("type", "")
            if item_type == "story":
                doc_text = self.transformer.format_story(item)
            elif item_type == "comment":
                doc_text = self.transformer.format_comment(item)
            elif "id" in item and "karma" in item:
                doc_text = self.transformer.format_user(item)
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
    

    def append_preprocessed_data(self, items, output_file=None):
        """Append new processed items to existing file"""
        return self.save_preprocessed_data(items, output_file, append_mode=True)
