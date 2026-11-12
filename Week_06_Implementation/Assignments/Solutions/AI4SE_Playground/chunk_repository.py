"""Split Python source files into line-addressable chunks for RAG ingestion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


IGNORED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}
CHARS_PER_TOKEN_ESTIMATE = 4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chunk Python source files into a JSON corpus for RAG."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Repository root to scan (defaults to this script's directory).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON path (defaults to <root>/chunks.json).",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=1600,
        help="Approximate maximum characters per chunk (default: 1600).",
    )
    parser.add_argument(
        "--overlap-chars",
        type=int,
        default=200,
        help="Approximate overlap between chunks (default: 200).",
    )
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=[".py"],
        help="Source extensions to include (default: .py).",
    )
    args = parser.parse_args()
    if args.max_chars < 1:
        parser.error("--max-chars must be positive")
    if args.overlap_chars < 0 or args.overlap_chars >= args.max_chars:
        parser.error("--overlap-chars must be non-negative and smaller than --max-chars")
    if not args.root.is_dir():
        parser.error(f"repository root is not a directory: {args.root}")
    args.root = args.root.resolve()
    args.output = (args.output or args.root / "chunks.json").resolve()
    args.extensions = {
        extension if extension.startswith(".") else f".{extension}"
        for extension in args.extensions
    }
    return args


def source_files(root: Path, extensions: set[str], output: Path) -> list[Path]:
    files = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue
        if any(part.lower() in IGNORED_DIRECTORIES for part in path.relative_to(root).parts):
            continue
        if path.resolve() == output:
            continue
        files.append(path)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix().casefold())


def split_lines(lines: list[str], max_chars: int, overlap_chars: int) -> list[tuple[int, int]]:
    """Return zero-based, end-exclusive line ranges with bounded line overlap."""
    ranges = []
    start = 0
    while start < len(lines):
        end = start
        chunk_chars = 0
        while end < len(lines) and (
            chunk_chars + len(lines[end]) <= max_chars or end == start
        ):
            chunk_chars += len(lines[end])
            end += 1

        if end < len(lines):
            preferred_boundaries = []
            chars_to_boundary = 0
            for index in range(start, end):
                chars_to_boundary += len(lines[index])
                if (
                    not lines[index].strip()
                    and chars_to_boundary >= max_chars * 0.6
                ):
                    preferred_boundaries.append(index + 1)
            if preferred_boundaries:
                end = preferred_boundaries[-1]
                chunk_chars = sum(len(line) for line in lines[start:end])

        ranges.append((start, end))
        if end == len(lines):
            break

        next_start = end
        overlap_target = min(overlap_chars, chunk_chars // 2)
        actual_overlap = 0
        while (
            next_start > start
            and actual_overlap < overlap_target
        ):
            next_start -= 1
            actual_overlap += len(lines[next_start])
        if next_start == start:
            next_start = end
        start = next_start

    return ranges


def build_corpus(root: Path, output: Path, max_chars: int, overlap_chars: int,
                 extensions: set[str]) -> dict[str, Any]:
    files = []
    chunks = []
    for source_path in source_files(root, extensions, output):
        relative_path = source_path.relative_to(root).as_posix()
        source_text = source_path.read_text(encoding="utf-8")
        lines = source_text.splitlines(keepends=True)
        if source_text and not lines:
            lines = [source_text]

        file_chunk_ids = []
        for index, (start, end) in enumerate(split_lines(lines, max_chars, overlap_chars), 1):
            text = "".join(lines[start:end])
            chunk_id = f"{relative_path}#chunk-{index:04d}"
            file_chunk_ids.append(chunk_id)
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "file_path": relative_path,
                    "start_line": start + 1,
                    "end_line": end,
                    "token_count_estimate": max(
                        1, round(len(text) / CHARS_PER_TOKEN_ESTIMATE)
                    ),
                    "text": text,
                }
            )
        files.append(
            {
                "path": relative_path,
                "line_count": len(lines),
                "chunk_ids": file_chunk_ids,
            }
        )

    return {
        "schema_version": 1,
        "source_root": root.name,
        "chunking": {
            "strategy": "line-based; prefer blank-line boundaries; bounded overlap",
            "max_chars": max_chars,
            "overlap_chars": overlap_chars,
            "estimated_chars_per_token": CHARS_PER_TOKEN_ESTIMATE,
            "extensions": sorted(extensions),
        },
        "source_file_count": len(files),
        "chunk_count": len(chunks),
        "files": files,
        "chunks": chunks,
    }


def main() -> None:
    args = parse_args()
    corpus = build_corpus(
        args.root, args.output, args.max_chars, args.overlap_chars, args.extensions
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(corpus, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {corpus['chunk_count']} chunks from "
        f"{corpus['source_file_count']} source files to {args.output}"
    )


if __name__ == "__main__":
    main()
