"""
Usage:  python app/api/scripts/test_retrieval.py <owner_user_id> "<query>"
"""

import sys
import uuid

from app.services.rag.retrieval import retrieve_relevant_chunks


def main() -> None:
    owner_id = uuid.UUID(sys.argv[1])
    query = sys.argv[2]

    results = retrieve_relevant_chunks(query, owner_id)
    print(f"Found {len(results)} relevant chunks for: {query!r}\n")
    for r in results:
        print(f"--- score={r.score:.3f} document={r.document_id} chunk={r.chunk_index} ---")
        print(r.text[:300])
        print()


if __name__ == "__main__":
    main()
