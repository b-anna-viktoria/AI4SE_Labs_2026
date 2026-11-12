# RAG preparation design

## Chunking

The chunker scans Python source files and tests, skips common generated or
environment directories, and writes repository-relative file paths. It splits
on whole lines, prefers blank-line boundaries, and overlaps adjacent chunks by
up to 200 characters. The default 1,600-character limit is approximately 400
tokens at a rough four characters per token; this keeps chunks focused while
retaining enough code context. Long individual lines are kept intact.

## Embeddings

`create_embeddings.py` creates sparse TF-IDF vectors with deterministic
BLAKE2b feature hashing. Features include complete, lowercased identifiers,
their snake/camel-case parts, and adjacent token bigrams. These lexical
features work well as a simple baseline for code search, where exact names and
symbols often matter. TF-IDF downweights common terms, and L2 normalization
makes vectors directly comparable with cosine similarity.

This is not a pretrained semantic code model: paraphrases with no shared
identifiers or words may not match. The tradeoff keeps setup dependency-free,
offline, reproducible, and fast for this small repository. A pretrained code
encoder could improve semantic matching later, at the cost of model downloads,
runtime dependencies, and more compute.

## Storage and use

`chunk_embeddings.json` stores each chunk ID, sparse vector (`indices` and
`values`), and metadata (source path, inclusive one-based line range, and text).
The index also stores model configuration and document frequencies so query
vectors can use the same tokenizer, hashing, and IDF weights. JSON is human
inspectable and portable, though less compact and slower to load than a binary
vector index at larger scale.


The embedding script can also rank chunks for a query after writing the index.
The script defaults to 262,144 hash dimensions; vector entries are stored
sparsely, so records only serialize active features. The corpus and embedding
index are generated files and should be rebuilt together to keep them in sync.
