import os

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
    # Create a temporary processing of just the new items
    temp_docs = []

    for item in new_items:
        if not item:
            continue

        item_type = item.get("type", "")

        if item_type == "story":
            doc_text = preprocess.format_story(item)
            if doc_text:
                temp_docs.append(doc_text)
        elif item_type == "comment":
            doc_text = preprocess.format_comment(item)
            if doc_text:
                temp_docs.append(doc_text)

    if not temp_docs:
        return []

    # Convert to Document objects and split into chunks
    from langchain.schema import Document

    documents = [Document(page_content=doc) for doc in temp_docs]
    chunks = split_documents(documents)

    return chunks


def main():
    print("Starting HackerNews data pipeline...")

    try:
        print("Fetching new data from HackerNews...")
        new_items = fetch_hackernews_data(stories_per_category=3, max_comments=2)

        if not new_items:
            print("No new data to process - everything is up to date!")
            if vector_store_exists():
                print("Using existing vector database")
                return True
            else:
                print("No vector database exists and no data to process")
                return False

        print(f"Fetched {len(new_items)} new items")

        # Get the output file path
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        output_file = os.path.join(
            project_root, "src", "data", "hackernews_optimized.txt"
        )

        # Check if we should append or create new file
        if os.path.exists(output_file) and vector_store_exists():
            print("Incremental update mode - appending new data...")

            # Append new data to existing file
            preprocess.append_preprocessed_data(new_items, output_file)

            # Get chunks only from the new items
            print("Processing new items into chunks...")
            new_chunks = get_new_chunks_only(new_items, output_file)

            # Add only the new chunks to vector store
            print("Adding new chunks to existing vector database...")
            add_new_chunks_to_vector_store(new_chunks)

        else:
            print("Full rebuild mode - creating new data file and vector database...")
            preprocess.save_preprocessed_data(new_items, output_file)

            print("Building new vector database...")
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
