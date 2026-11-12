"""Create deterministic sparse TF-IDF vectors for repository code chunks."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_DIMENSIONS = 262_144
IDENTIFIER_PATTERN = re.compile(r"[A-Za-z_]\w*|\d+(?:\.\d+)?")
IDENTIFIER_PART_PATTERN = re.compile(r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|\d+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build sparse code-oriented TF-IDF embeddings from chunks.json."
    )
    parser.add_argument(
        "--chunks",
        type=Path,
        default=Path(__file__).resolve().parent / "chunks.json",
        help="Input chunk corpus (defaults to chunks.json beside this script).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "chunk_embeddings.json",
        help="Output index (defaults to chunk_embeddings.json beside this script).",
    )
    parser.add_argument(
        "--dimensions",
        type=int,
        default=DEFAULT_DIMENSIONS,
        help=f"Feature-hashing vector dimension (default: {DEFAULT_DIMENSIONS}).",
    )
    parser.add_argument(
        "--query",
        help="Optionally retrieve matching chunks after generating the index.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of chunks to show for --query (default: 5).",
    )
    args = parser.parse_args()
    if args.dimensions < 1:
        parser.error("--dimensions must be positive")
    if args.top_k < 1:
        parser.error("--top-k must be positive")
    if not args.chunks.is_file():
        parser.error(f"chunk corpus does not exist: {args.chunks}")
    return args


def tokenize_code(text: str) -> list[str]:
    """Keep whole identifiers while also exposing snake/camel-case components."""
    tokens = []
    for match in IDENTIFIER_PATTERN.finditer(text):
        identifier = match.group().lower()
        tokens.append(identifier)
        parts = IDENTIFIER_PART_PATTERN.findall(match.group())
        tokens.extend(part.lower() for part in parts if part.lower() != identifier)
    return tokens


def feature_counts(text: str, dimensions: int) -> Counter[int]:
    tokens = tokenize_code(text)
    features = Counter(f"token:{token}" for token in tokens)
    features.update(
        f"bigram:{left} {right}" for left, right in zip(tokens, tokens[1:])
    )
    counts: Counter[int] = Counter()
    for feature, count in features.items():
        digest = hashlib.blake2b(
            feature.encode("utf-8"), digest_size=8, person=b"ai4se-rag"
        ).digest()
        counts[int.from_bytes(digest, "big") % dimensions] += count
    return counts


def normalized_tfidf(
    counts: Counter[int], document_frequencies: dict[int, int], document_count: int
) -> dict[int, float]:
    weighted = {
        index: (1.0 + math.log(term_count))
        * (math.log((1 + document_count) / (1 + document_frequencies.get(index, 0))) + 1.0)
        for index, term_count in counts.items()
    }
    norm = math.sqrt(sum(value * value for value in weighted.values()))
    if not norm:
        return {}
    return {index: value / norm for index, value in weighted.items()}


def build_index(corpus: dict[str, Any], dimensions: int) -> dict[str, Any]:
    chunks = corpus.get("chunks")
    if not isinstance(chunks, list):
        raise ValueError("chunk corpus must contain a 'chunks' list")

    counts_by_chunk = []
    document_frequencies: Counter[int] = Counter()
    seen_ids = set()
    for chunk in chunks:
        if not isinstance(chunk, dict):
            raise ValueError("each chunk must be a JSON object")
        for field in ("chunk_id", "file_path", "start_line", "end_line", "text"):
            if field not in chunk:
                raise ValueError(f"chunk is missing required field: {field}")
        chunk_id = chunk["chunk_id"]
        if not isinstance(chunk_id, str) or not chunk_id:
            raise ValueError("chunk_id must be a non-empty string")
        if chunk_id in seen_ids:
            raise ValueError(f"duplicate chunk_id: {chunk_id}")
        seen_ids.add(chunk_id)
        if not isinstance(chunk["text"], str):
            raise ValueError(f"chunk text must be a string: {chunk_id}")

        counts = feature_counts(chunk["text"], dimensions)
        counts_by_chunk.append((chunk, counts))
        document_frequencies.update(counts.keys())

    document_count = len(counts_by_chunk)
    records = []
    for chunk, counts in counts_by_chunk:
        vector = normalized_tfidf(counts, document_frequencies, document_count)
        records.append(
            {
                "chunk_id": chunk["chunk_id"],
                "embedding": {
                    "indices": sorted(vector),
                    "values": [vector[index] for index in sorted(vector)],
                },
                "metadata": {
                    "file_path": chunk["file_path"],
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                    "text": chunk["text"],
                },
            }
        )

    return {
        "schema_version": 1,
        "model": {
            "name": "code-hashing-tfidf-v1",
            "type": "sparse lexical TF-IDF",
            "dimensions": dimensions,
            "normalization": "L2",
            "tokenization": "lowercase identifiers, snake/camel-case parts, and adjacent bigrams",
            "hash": "BLAKE2b feature hashing; unsigned modulo dimensions",
            "idf": "log((1 + document_count) / (1 + document_frequency)) + 1",
            "term_frequency": "1 + log(term_count)",
            "document_count": document_count,
            "document_frequencies": {
                str(index): document_frequencies[index]
                for index in sorted(document_frequencies)
            },
        },
        "source_corpus": corpus.get("source_root"),
        "chunk_count": len(records),
        "records": records,
    }


def retrieve(index: dict[str, Any], query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Rank chunks by cosine similarity to a query using the stored TF-IDF model."""
    model = index["model"]
    dimensions = model["dimensions"]
    document_frequencies = {
        int(feature_index): frequency
        for feature_index, frequency in model["document_frequencies"].items()
    }
    query_counts = feature_counts(query, dimensions)
    query_vector = normalized_tfidf(
        query_counts, document_frequencies, model["document_count"]
    )
    if not query_vector:
        return []

    scored = []
    for record in index["records"]:
        vector = record["embedding"]
        score = sum(
            query_vector[feature_index] * value
            for feature_index, value in zip(vector["indices"], vector["values"])
            if feature_index in query_vector
        )
        if score > 0:
            scored.append((score, record))
    scored.sort(key=lambda result: (-result[0], result[1]["chunk_id"]))
    return [
        {"score": score, **record}
        for score, record in scored[:top_k]
    ]


def main() -> None:
    args = parse_args()
    corpus = json.loads(args.chunks.read_text(encoding="utf-8"))
    index = build_index(corpus, args.dimensions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote embeddings for {index['chunk_count']} chunks to {args.output}")
    if args.query is not None:
        results = retrieve(index, args.query, args.top_k)
        if not results:
            print("No matching chunks found.")
        for result in results:
            metadata = result["metadata"]
            print(
                f"{result['score']:.4f}  {metadata['file_path']}:"
                f"{metadata['start_line']}-{metadata['end_line']}  "
                f"{result['chunk_id']}"
            )


if __name__ == "__main__":
    main()
