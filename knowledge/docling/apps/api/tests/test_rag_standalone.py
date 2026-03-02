"""
Standalone test for RAG service.
Tests RAG functionality without running the full API.
"""

import sys
import os

# Add apps/api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

# Set minimal required env vars before importing
os.environ.setdefault("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
os.environ.setdefault("LANCEDB_PATH", "data/zoo_lancedb")
os.environ.setdefault("CORS_ORIGINS", "[]")

from app.services.rag import RAGService


def test_rag_service():
    """Test RAG service end-to-end."""

    print("=" * 60)
    print("RAG Service Test")
    print("=" * 60)

    # Initialize service
    print("\n1. Initializing RAG service...")
    rag = RAGService()
    print("   ✓ RAG service initialized")

    # Test query
    test_query = "Tell me about lemurs"
    print(f"\n2. Testing query: '{test_query}'")

    # Search context
    print("\n3. Searching LanceDB for context...")
    context, sources, confidence = rag.search_context(test_query, num_results=5)

    print(f"   ✓ Found {len(sources)} sources")
    print(f"   ✓ Confidence: {confidence:.3f}")
    print(f"   ✓ Context length: {len(context)} characters")

    if sources:
        print("\n   Sources:")
        for i, source in enumerate(sources[:3], 1):
            print(f"     {i}. {source.get('animal', 'Unknown')} - {source.get('title', 'N/A')}")

    # Generate response
    print(f"\n4. Generating response with GPT-4o-mini...")
    messages = [{"role": "user", "content": test_query}]
    response = rag.generate_response(messages, context)

    print(f"   ✓ Response generated ({len(response)} characters)")

    # Extract follow-ups
    print("\n5. Extracting follow-up questions...")
    main_response, followups = rag.extract_followup_questions(response)

    print(f"   ✓ Main response: {len(main_response)} characters")
    print(f"   ✓ Follow-ups: {len(followups)} questions")

    # Display results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    print("\nMain Response:")
    print("-" * 60)
    print(main_response)

    if followups:
        print("\n\nFollow-up Questions:")
        print("-" * 60)
        for i, q in enumerate(followups, 1):
            print(f"{i}. {q}")

    print("\n" + "=" * 60)
    print("TEST PASSED ✓")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_rag_service()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
