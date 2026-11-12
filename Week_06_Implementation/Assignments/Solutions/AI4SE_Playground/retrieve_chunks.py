"""Rank stored repository chunks against an input embedding vector."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


DEFAULT_STORAGE = Path(__file__).resolve().parent / "chunk_embeddings.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Retrieve the top-N chunks by cosine similarity."
    )
    parser.add_argument(
        "--query-vector",
        type=Path,
        required=True,
        help="JSON file containing a dense array or sparse indices/values vector.",
    )
    parser.add_argument(
        "--storage",
        type=Path,
        default=DEFAULT_STORAGE,
        help="Embedding storage JSON (defaults to chunk_embeddings.json beside this script).",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        required=True,
        help="Number of matching chunks to return; must be positive.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for JSON results; otherwise results are written to stdout.",
    )
    args = parser.parse_args()
    if args.top_n < 1:
        parser.error("--top-n must be positive")
    return args


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def _sparse_vector(vector: Any, dimensions: int, label: str) -> dict[int, float]:
    if isinstance(vector, list):
        if len(vector) != dimensions:
            raise ValueError(
                f"{label} has {len(vector)} dimensions; expected {dimensions}"
            )
        return {
            index: value
            for index, raw_value in enumerate(vector)
            if (value := _number(raw_value, f"{label}[{index}]")) != 0.0
        }

    if not isinstance(vector, dict) or set(vector) != {"indices", "values"}:
        raise ValueError(
            f"{label} must be a dense array or an object with 'indices' and 'values'"
        )
    indices = vector["indices"]
    values = vector["values"]
    if not isinstance(indices, list) or not isinstance(values, list):
        raise ValueError(f"{label} indices and values must be arrays")
    if len(indices) != len(values):
        raise ValueError(f"{label} indices and values must have equal lengths")

    result = {}
    for position, (raw_index, raw_value) in enumerate(zip(indices, values)):
        if isinstance(raw_index, bool) or not isinstance(raw_index, int):
            raise ValueError(f"{label} index at position {position} must be an integer")
        if not 0 <= raw_index < dimensions:
            raise ValueError(
                f"{label} index {raw_index} is outside 0..{dimensions - 1}"
            )
        if raw_index in result:
            raise ValueError(f"{label} contains duplicate index {raw_index}")
        result[raw_index] = _number(raw_value, f"{label} value at position {position}")
    return {index: value for index, value in result.items() if value != 0.0}


def cosine_similarity(left: dict[int, float], right: dict[int, float]) -> float:
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    dot_product = sum(
        value * right.get(index, 0.0) for index, value in left.items()
    )
    return dot_product / (left_norm * right_norm)


def retrieve(
    query_vector: Any, storage: dict[str, Any], top_n: int
) -> list[dict[str, Any]]:
    if top_n < 1:
        raise ValueError("top_n must be positive")
    model = storage.get("model")
    records = storage.get("records")
    if not isinstance(model, dict) or not isinstance(records, list):
        raise ValueError("storage must contain a model object and records array")
    dimensions = model.get("dimensions")
    if isinstance(dimensions, bool) or not isinstance(dimensions, int) or dimensions < 1:
        raise ValueError("storage model must specify a positive integer dimensions")
    query = _sparse_vector(query_vector, dimensions, "query vector")

    ranked = []
    seen_ids = set()
    for position, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"storage record {position} must be an object")
        chunk_id = record.get("chunk_id")
        metadata = record.get("metadata")
        if not isinstance(chunk_id, str) or not chunk_id:
            raise ValueError(f"storage record {position} has an invalid chunk_id")
        if chunk_id in seen_ids:
            raise ValueError(f"storage contains duplicate chunk_id: {chunk_id}")
        seen_ids.add(chunk_id)
        if not isinstance(metadata, dict):
            raise ValueError(f"storage record {chunk_id} has invalid metadata")
        stored_vector = _sparse_vector(
            record.get("embedding"), dimensions, f"embedding for {chunk_id}"
        )
        ranked.append(
            {
                "chunk_id": chunk_id,
                "similarity": cosine_similarity(query, stored_vector),
                "metadata": metadata,
            }
        )
    ranked.sort(key=lambda result: (-result["similarity"], result["chunk_id"]))
    return ranked[:top_n]


def main() -> None:
    args = parse_args()
    try:
        query_vector = json.loads(args.query_vector.read_text(encoding="utf-8"))
        storage = json.loads(args.storage.read_text(encoding="utf-8"))
        results = retrieve(query_vector, storage, args.top_n)
        rendered = json.dumps(results, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"{Path(sys.argv[0]).name}: error: {error}", file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()
