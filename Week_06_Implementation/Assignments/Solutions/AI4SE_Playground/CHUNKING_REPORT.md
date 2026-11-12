# RAG source chunking

## Repository scope

The repository is a Python project: its package contains domain and simulation
modules, and its tests contain examples of expected behavior. The generated
corpus therefore includes all `.py` files in the repository, including tests
and the chunking script itself. Empty Python files are listed in the JSON file
manifest but do not produce content-free chunks. Common generated and
environment directories (such as `.git`, `__pycache__`, and virtual
environments) are excluded.

## Design decisions

- **Line-based chunks with blank-line preference:** Keeping original source
  lines intact avoids splitting statements or identifiers in the middle.
  Blank-line boundaries tend to separate declarations and test cases while
  still allowing the chunker to process incomplete or syntactically invalid
  source without requiring a parser.
- **About 400 tokens per chunk:** The default 1,600-character limit, using a
  rough four-characters-per-token estimate, is small enough for focused
  retrieval while retaining useful code context. A single unusually long line
  may exceed the configured limit rather than being corrupted.
- **About 50 tokens of overlap:** The 200-character overlap helps retrieval
  retain context across chunk boundaries. Overlap is kept on whole lines and
  capped relative to chunk size.
- **Traceable, portable metadata:** Every chunk contains a repository-relative
  POSIX path, inclusive one-based start/end line numbers, its text, and an
  approximate token count. Stable chunk IDs and a file manifest support
  citations and account for empty files. The JSON is deterministic and uses
  only the Python standard library.

## Usage and output


python .\chunk_repository.py

writes `chunks.json`. Chunk size, overlap, root, output path, and included
extensions can be changed with `--max-chars`, `--overlap-chars`, `--root`,
`--output`, and `--extensions`. Token counts are estimates, not model-tokenizer
counts. The generated default corpus contains 145 chunks from 29 Python files;
the empty test package initializer appears in the manifest but has no chunks.
