"""HackerNews RAG Pipeline"""

import os
import traceback

from langchain_core.documents import Document

from src.data_analysis.extract import Extracter
from src.data_analysis.load import Loader
from src.data_analysis.transform import Transformer
from src.loader import load_document, split_documents
from src.vector_store import add_new_chunks_to_vector_store, build_vector_store, vector_store_exists


def get_new_chunks_only(new_items):
    """Process new items into document chunks for incremental updates"""
    print(f"Processing {len(new_items)} new items...")
    temp_docs = []
    transformer = Transformer()

    for item in new_items:
        if not item or not (item_type := item.get("type", "")):
            continue

        # Process stories and comments into formatted text documents
        if item_type == "story" and (doc_text := transformer.format_story(item)):
            temp_docs.append((doc_text, item))
        elif item_type == "comment" and (doc_text := transformer.format_comment(item)):
            temp_docs.append((doc_text, item))

    if not temp_docs:
        print("No valid documents found in new items")
        return []

    # Create LangChain Documents with comprehensive metadata for better retrieval
    documents = [
        Document(
            page_content=doc_text,
            metadata={
                "source": "hackernews.com",
                "item_id": item.get("id", "unknown"),
                "item_type": item.get("type", "unknown"),
                "author": item.get("by", "unknown"),
            },
        )
        for doc_text, item in temp_docs
    ]

    chunks = split_documents(documents)
    print(f"Created {len(chunks)} chunks from {len(new_items)} items")
    return chunks


def main():
    """Main pipeline orchestration function"""
    print("Starting HackerNews data pipeline...")

    try:
        print("Fetching new data from HackerNews...")
        # Configuration: 10 stories per category, max 5 comment levels deep
        # Adjust these parameters based on processing capacity and data needs
        extracter = Extracter(stories_per_category=10, max_comment_depth=5)
        new_items = extracter.fetch_hackernews_data()

        if not new_items:
            print("No new data found - everything is up to date")
            return vector_store_exists()

        print(f"Found {len(new_items)} new items to process")

        # Construct output file path relative to project root
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        output_file = os.path.join(project_root, "src", "data", "hackernews_optimized.txt")

        loader = Loader()

        # Determine processing strategy: incremental update vs full rebuild
        if os.path.exists(output_file) and vector_store_exists():
            print("Incremental update - adding to existing data...")
            loader.append_preprocessed_data(new_items, output_file)
            print("Converting new items to chunks...")
            new_chunks = get_new_chunks_only(new_items, output_file)
            print("Adding new chunks to vector database...")
            add_new_chunks_to_vector_store(new_chunks)
        else:
            # Full rebuild when no existing data or vector store
            print("Building new database from scratch...")
            loader.save_preprocessed_data(new_items, output_file)
            print("Creating vector database...")
            chunks = split_documents(load_document(output_file))
            build_vector_store(chunks)

        print(f"Update your .env file with:\nDATA_PATH={output_file}")
        return True

    except Exception as e:
        print(f"Pipeline error: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Pipeline completed successfully!" if main() else "Pipeline failed")
