"""
Zoo Q&A Chatbot - Knowledge Base Builder
Extracts, chunks, and embeds animal content from trusted sources.
"""

import os
from typing import List

import lancedb
from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter
from dotenv import load_dotenv
from lancedb.embeddings import get_registry
from lancedb.pydantic import LanceModel, Vector
from openai import OpenAI

from utils.tokenizer import OpenAITokenizerWrapper
from zoo_sources import get_phase1_urls, get_all_urls

load_dotenv()

# Initialize OpenAI client
client = OpenAI()

# Tokenizer settings
tokenizer = OpenAITokenizerWrapper()
MAX_TOKENS = 8191  # text-embedding-3-large's maximum context length

# LanceDB settings (use environment variable if set, for Docker compatibility)
DB_PATH = os.environ.get("LANCEDB_PATH", "data/zoo_lancedb")
TABLE_NAME = "animals"


def extract_animal_content(urls: List[str], verbose: bool = True) -> List[tuple]:
    """
    Extract content from animal education websites.

    Args:
        urls: List of URLs to extract content from
        verbose: Whether to print progress

    Returns:
        List of (document, url) tuples
    """
    converter = DocumentConverter()
    documents = []

    if verbose:
        print(f"Extracting content from {len(urls)} URLs...")

    # Convert all URLs
    for i, url in enumerate(urls):
        try:
            if verbose:
                print(f"  [{i+1}/{len(urls)}] {url[:60]}...")

            result = converter.convert(url)
            if result.document:
                documents.append((result.document, url))  # Keep URL with document
                if verbose:
                    print(f"    ✓ Extracted successfully")
        except Exception as e:
            if verbose:
                print(f"    ✗ Failed: {str(e)[:50]}")
            continue

    if verbose:
        print(f"\nExtracted {len(documents)} documents successfully")

    return documents


def chunk_documents(documents: List[tuple], verbose: bool = True) -> List[tuple]:
    """
    Chunk documents using hybrid chunking strategy.

    Args:
        documents: List of (document, url) tuples
        verbose: Whether to print progress

    Returns:
        List of (chunk, url) tuples with metadata
    """
    chunker = HybridChunker(
        tokenizer=tokenizer,
        max_tokens=MAX_TOKENS,
        merge_peers=True,
    )

    all_chunks = []

    if verbose:
        print(f"Chunking {len(documents)} documents...")

    for doc, url in documents:
        try:
            chunk_iter = chunker.chunk(dl_doc=doc)
            chunks = list(chunk_iter)
            # Pair each chunk with its source URL
            all_chunks.extend([(chunk, url) for chunk in chunks])
        except Exception as e:
            if verbose:
                print(f"  ✗ Failed to chunk document: {str(e)[:50]}")
            continue

    if verbose:
        print(f"Created {len(all_chunks)} chunks")

    return all_chunks


def prepare_chunks_for_db(chunks: List[tuple]) -> List[dict]:
    """
    Prepare chunks for insertion into LanceDB.

    Args:
        chunks: List of (chunk, url) tuples

    Returns:
        List of dictionaries ready for LanceDB
    """
    processed_chunks = []

    for chunk, url in chunks:
        # Extract animal name from URL or title if possible
        animal_name = None
        if chunk.meta.headings:
            animal_name = chunk.meta.headings[0]

        processed_chunks.append({
            "text": chunk.text,
            "metadata": {
                "animal_name": animal_name,
                "filename": chunk.meta.origin.filename if chunk.meta.origin else None,
                "title": chunk.meta.headings[0] if chunk.meta.headings else None,
                "url": url,  # Include source URL
            },
        })

    return processed_chunks


def create_vector_db(processed_chunks: List[dict], verbose: bool = True):
    """
    Create LanceDB database and embed chunks.

    Args:
        processed_chunks: List of chunk dictionaries
        verbose: Whether to print progress

    Returns:
        LanceDB table object
    """
    if verbose:
        print(f"Creating vector database at {DB_PATH}...")

    # Create database
    db = lancedb.connect(DB_PATH)

    # Get OpenAI embedding function
    func = get_registry().get("openai").create(name="text-embedding-3-large")

    # Define metadata schema (simplified to avoid nested list issues)
    class ChunkMetadata(LanceModel):
        """Metadata for each chunk."""
        animal_name: str | None
        filename: str | None
        title: str | None
        url: str | None

    # Define main schema
    class AnimalChunks(LanceModel):
        text: str = func.SourceField()
        vector: Vector(func.ndims()) = func.VectorField()  # type: ignore
        metadata: ChunkMetadata

    # Create table
    table = db.create_table(TABLE_NAME, schema=AnimalChunks, mode="overwrite")

    if verbose:
        print(f"Embedding and storing {len(processed_chunks)} chunks...")
        print("  (This may take a few minutes due to embedding API calls)")

    # Add chunks in batches to avoid rate limits
    batch_size = 50
    for i in range(0, len(processed_chunks), batch_size):
        batch = processed_chunks[i:i + batch_size]
        table.add(batch)
        if verbose:
            print(f"  Processed {min(i + batch_size, len(processed_chunks))}/{len(processed_chunks)} chunks")

    if verbose:
        print(f"\n✓ Vector database created with {table.count_rows()} rows")

    return table


def build_knowledge_base(verbose: bool = True, expanded: bool = True):
    """
    Complete pipeline to build the zoo knowledge base.

    Args:
        verbose: Whether to print progress
        expanded: Use expanded sources (petting zoo + exotics + Leesburg park)

    Returns:
        LanceDB table object
    """
    print("=" * 60)
    print("🐘 Building Zoo Q&A Knowledge Base")
    print("=" * 60)

    # Get URLs based on mode
    if expanded:
        urls = get_all_urls()
        print(f"\nExpanded Mode: Processing {len(urls)} animal sources")
        print("(Includes Nat Geo Kids, Ducksters, SeaWorld, Simple Wikipedia)\n")
    else:
        urls = get_phase1_urls()
        print(f"\nPhase 1: Processing {len(urls)} animal sources (Nat Geo Kids)\n")

    # Step 1: Extract content
    print("Step 1: Extracting content from trusted sources")
    print("-" * 40)
    documents = extract_animal_content(urls, verbose=verbose)

    if not documents:
        print("❌ No documents extracted. Check your internet connection and URLs.")
        return None

    # Step 2: Chunk documents
    print("\nStep 2: Chunking documents")
    print("-" * 40)
    chunks = chunk_documents(documents, verbose=verbose)

    if not chunks:
        print("❌ No chunks created.")
        return None

    # Step 3: Prepare for database
    print("\nStep 3: Preparing chunks for embedding")
    print("-" * 40)
    processed_chunks = prepare_chunks_for_db(chunks)
    print(f"Prepared {len(processed_chunks)} chunks")

    # Step 4: Create vector database
    print("\nStep 4: Creating vector database and embeddings")
    print("-" * 40)
    table = create_vector_db(processed_chunks, verbose=verbose)

    print("\n" + "=" * 60)
    print("✅ Knowledge base built successfully!")
    print(f"   Database: {DB_PATH}")
    print(f"   Table: {TABLE_NAME}")
    print(f"   Total chunks: {table.count_rows()}")
    print("=" * 60)

    return table


if __name__ == "__main__":
    build_knowledge_base()
