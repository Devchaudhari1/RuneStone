# Development Notes

## Benchmarking

RuneStone benchmarks should measure both agent behavior and final task correctness.

Agent validation records whether the agent itself ran a successful test.

Independent validation checks the final workspace state separately from the agent's own validation.

## Editing

For existing files, RuneStone should prefer minimal edits instead of rewriting entire files.

The edit_file tool supports exact text replacement and optional source ranges.

## Future Work

The RAG benchmark should contain queries that require distinguishing between multiple knowledge sources.

Retrieval weights should only be tuned after establishing a baseline evaluation dataset.