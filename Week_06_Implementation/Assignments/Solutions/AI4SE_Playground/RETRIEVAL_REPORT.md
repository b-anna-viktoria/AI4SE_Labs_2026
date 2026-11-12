# Chunk retrieval design

`retrieve_chunks.py` loads a query vector and the stored chunk embeddings,
calculates cosine similarity against every record, sorts from highest to
lowest score, and returns at most the requested number of chunks. Results
contain the chunk ID, similarity score, and original metadata (including
source path, line range, and text). Equal scores are ordered by chunk ID for
repeatable output.

Cosine similarity is a standard measure of vector direction. It works for
sparse vectors and is not affected by vector magnitude. The saved TF-IDF
vectors are L2-normalized, so for them cosine similarity is equivalent to
their dot product; the script still computes norms so it can correctly score
other non-zero vectors of the same dimension.

The script expects the existing JSON index format: a top-level `model`
object with `dimensions`, and a `records` array containing `chunk_id`,
`embedding`, and `metadata`. Each stored embedding uses parallel `indices`
and `values` arrays. A query vector may use the same sparse representation or
be a dense JSON array whose length equals the model dimension. Sparse entries
are validated and zero-valued entries are ignored. A zero vector scores zero
against all records.

This design keeps retrieval small, transparent, deterministic, and dependency
free, which suits the repository-sized index. It scans every vector on each
query, so a larger corpus would benefit from a vector index or database.

