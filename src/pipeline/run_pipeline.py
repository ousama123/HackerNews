import os

from langchain_core.documents import Document

from src.data_analysis import preprocess
from src.data_analysis.fetcher import fetch_hackernews_data
from src.loader import load_document, split_documents
from src.vector_store import (
    add_new_chunks_to_vector_store,
    build_vector_store,
    vector_store_exists,
)


def get_new_chunks_only(new_items, output_file):
    """Process only the new items to get their chunks."""
    print(f"Processing {len(new_items)} new items...")

    # Create a temporary processing of just the new items
    temp_docs = []

    for item in new_items:
        if not item:
            continue

        item_type = item.get("type", "")

        if item_type == "story":
            doc_text = preprocess.format_story(item)
            if doc_text:
                temp_docs.append((doc_text, item))
        elif item_type == "comment":
            doc_text = preprocess.format_comment(item)
            if doc_text:
                temp_docs.append((doc_text, item))

    if not temp_docs:
        print("No valid documents found in new items")
        return []

    documents = []
    for doc_text, item in temp_docs:
        # Create Document object with metadata
        new_chunk = Document(
            page_content=doc_text,
            metadata={
                "source": "hackernews.com",
                "item_id": item.get("id", "unknown"),
                "item_type": item.get("type", "unknown"),
                "author": item.get("by", "unknown"),
            },
        )
        documents.append(new_chunk)

    chunks = split_documents(documents)
    print(f"Created {len(chunks)} chunks from {len(new_items)} items")

    return chunks


def main():
    print("Starting HackerNews data pipeline...")

    try:
        print("Fetching new data from HackerNews...")
        new_items = fetch_hackernews_data(stories_per_category=3, max_comments=2)

        if not new_items:
            print("No new data found - everything is up to date")
            if vector_store_exists():
                print("Vector database exists, using current version")
                return True
            else:
                print("No vector database found and no new data")
                return False

        print(f"Found {len(new_items)} new items to process")

        # Get the output file path
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        output_file = os.path.join(
            project_root, "src", "data", "hackernews_optimized.txt"
        )

        # Check if we should append or create new file
        if os.path.exists(output_file) and vector_store_exists():
            print("Incremental update - adding to existing data...")

            # Append new data to existing file
            preprocess.append_preprocessed_data(new_items, output_file)

            # Get chunks only from the new items
            print("Converting new items to chunks...")
            new_chunks = get_new_chunks_only(new_items, output_file)

            # Add only the new chunks to vector store
            print("Adding new chunks to vector database...")
            add_new_chunks_to_vector_store(new_chunks)

        else:
            print("Building new database from scratch...")
            preprocess.save_preprocessed_data(new_items, output_file)

            print("Creating vector database...")
            docs = load_document(output_file)
            chunks = split_documents(docs)
            build_vector_store(chunks)

        print("Update your .env file with:")
        print(f"DATA_PATH={output_file}")

        return True

    except Exception as e:
        print(f"Pipeline error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("Pipeline completed successfully!")
    else:
        print("Pipeline failed")
