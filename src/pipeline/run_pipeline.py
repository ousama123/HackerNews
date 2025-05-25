"""
HackerNews RAG Pipeline

Orchestrates the complete data processing workflow for the HackerNews RAG system.
Handles fetching, preprocessing, vectorization, and incremental updates.

Features:
- Fetches fresh data from HackerNews API endpoints
- Processes stories and comments into optimized text format
- Builds or updates vector database for RAG retrieval
- Supports incremental updates to avoid reprocessing
- Handles both full rebuilds and partial updates

Flow: Fetch new data → Process to chunks → Update vector store → Save metadata
"""

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
    """
    Process only new items into document chunks for incremental vector store updates.

    Args:
        new_items (list): List of new HackerNews items (stories, comments, users)
        output_file (str): Path to output file (for reference, not used directly)

    Returns:
        list: Document chunks ready for vector store insertion
    """
    print(f"Processing {len(new_items)} new items...")

    # Create temporary collection for valid documents
    temp_docs = []

    for item in new_items:
        # Skip empty or invalid items
        if not item:
            continue

        item_type = item.get("type", "")

        # Process stories into formatted text documents
        if item_type == "story":
            doc_text = preprocess.format_story(item)
            if doc_text:
                temp_docs.append((doc_text, item))
        # Process comments into formatted text documents
        elif item_type == "comment":
            doc_text = preprocess.format_comment(item)
            if doc_text:
                temp_docs.append((doc_text, item))

    if not temp_docs:
        print("No valid documents found in new items")
        return []

    documents = []
    for doc_text, item in temp_docs:
        # Create LangChain Document with comprehensive metadata
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

    # Split documents into chunks suitable for vector embedding
    chunks = split_documents(documents)
    print(f"Created {len(chunks)} chunks from {len(new_items)} items")

    return chunks


def main():
    """
    Main pipeline orchestration function.

    Coordinates the complete HackerNews RAG data processing workflow:
    fetching, preprocessing, vectorization, and database updates.

    Returns:
        bool: True if pipeline completed successfully, False otherwise
    """
    print("Starting HackerNews data pipeline...")

    try:
        # Fetch new data from HackerNews API with configured limits
        print("Fetching new data from HackerNews...")
        # Configuration: 10 stories per category, max 5 comment levels deep
        # Adjust these parameters based on processing capacity and data needs
        new_items = fetch_hackernews_data(stories_per_category=10, max_comments=5)

        # Handle case where no new data is available
        if not new_items:
            print("No new data found - everything is up to date")
            if vector_store_exists():
                print("Vector database exists, using current version")
                return True
            else:
                print("No vector database found and no new data")
                return False

        print(f"Found {len(new_items)} new items to process")

        # Construct output file path relative to project root
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        output_file = os.path.join(project_root, "src", "data", "hackernews_optimized.txt")

        # Determine processing strategy: incremental update vs full rebuild
        if os.path.exists(output_file) and vector_store_exists():
            print("Incremental update - adding to existing data...")

            # Append new data to existing preprocessed file
            preprocess.append_preprocessed_data(new_items, output_file)

            # Convert only new items to document chunks for efficiency
            print("Converting new items to chunks...")
            new_chunks = get_new_chunks_only(new_items, output_file)

            # Add only new chunks to existing vector database
            print("Adding new chunks to vector database...")
            add_new_chunks_to_vector_store(new_chunks)

        else:
            # Full rebuild when no existing data or vector store
            print("Building new database from scratch...")
            preprocess.save_preprocessed_data(new_items, output_file)

            # Create vector database from all processed data
            print("Creating vector database...")
            docs = load_document(output_file)
            chunks = split_documents(docs)
            build_vector_store(chunks)

        # Provide user guidance for environment configuration
        print("Update your .env file with:")
        print(f"DATA_PATH={output_file}")

        return True

    except Exception as e:
        # Comprehensive error handling with traceback for debugging
        print(f"Pipeline error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()

    # Report final pipeline status
    if success:
        print("Pipeline completed successfully!")
    else:
        print("Pipeline failed")
