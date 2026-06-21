## bugs/improvements
No error handling — if Qdrant is down or the API key is wrong, the whole app crashes with no useful message

No batching timeout/retry — if a batch fails mid-upsert, you get partial data silently

Singleton _instance never clears — if the same codebase is re-ingested, the singleton returns the old instance and skips __init__, so it won't pick up a fresh connection

For private repos you need a GitHub token.

increase chunking speed with parallel chunking or something


## Updated roadmap:

# V1
 Explain architecture before coding
 Generate implementation plans
 Find good-first-issues automatically
 Dependency graph (centerpiece) — file-level import/call graph, visualized
 Impact Analysis — query the graph for files/effects/suggested tests given an issue (built directly on dependency graph above)

# V2
 Identify likely maintainers
 Estimate issue difficulty
 Learn from previous merged PRs

# Parked
 Auto-patch generation pipeline