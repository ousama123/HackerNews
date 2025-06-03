"""HackerNews RAG Pipeline"""

import os
import traceback

from src.data_analysis.extract import Extracter
from src.data_analysis.load import Loader
from src.data_analysis.transform import Transformer
from src.document_splitter import load_document, split_documents
from src.vector_store import add_new_chunks_to_vector_store, build_vector_store, vector_store_exists

OUTPUT_FILE = "src/data/hackernews_optimized.txt"

def main():
    """Main pipeline orchestration function"""
    print("Starting HackerNews data pipeline...")

    try:
        print("Fetching new data from HackerNews...")
        # Configuration: 10 stories per category, max 5 comment levels deep
        # Adjust these parameters based on processing capacity and data needs
        extracter = Extracter(stories_per_category=2, max_comment_depth=2)
        transformer = Transformer()
        loader = Loader()

        new_items = extracter.fetch_hackernews_data()
        if not new_items:
            print("No new data found - everything is up to date")
            return vector_store_exists()

        print(f"Found {len(new_items)} new items to process")

        # Determine processing strategy: incremental update vs full rebuild
        if os.path.exists(OUTPUT_FILE) and vector_store_exists():
            print("Incremental update - adding to existing data...")
            loader.append_preprocessed_data(new_items, OUTPUT_FILE)
            print("Converting new items to chunks...")
            new_chunks = transformer.process_new_items_to_chunks(new_items, split_documents)
            print("Adding new chunks to vector database...")
            add_new_chunks_to_vector_store(new_chunks)
        else:
            # Full rebuild when no existing data or vector store
            print("Building new database from scratch...")
            loader.save_preprocessed_data(new_items, OUTPUT_FILE)
            print("Creating vector database...")
            chunks = split_documents(load_document(OUTPUT_FILE))
            build_vector_store(chunks)

        print(f"Update your .env file with:\nDATA_PATH={OUTPUT_FILE}")
        return True

    except Exception as e:
        print(f"Pipeline error: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Pipeline completed successfully!" if main() else "Pipeline failed")