# Known Issues & Limitations

## 1. Hallucination in Issue Analysis (Fixed)
**Problem:** When analyzing GitHub issues, the LLM was inventing 
code and line numbers that didn't exist in the actual codebase.

**Root Cause:** Two things caused this:
- Semantic search was returning non-code files (README.md) as top matches
- The LLM was filling gaps in its context with training knowledge

**Fix Applied:**
- Added file extension filtering to skip .md, .txt, .yaml files 
  when selecting the full file to read
- Added strict prompt instructions telling the LLM to never 
  reference code outside the provided context
- Added confidence scoring — responses below 80/100 are flagged

**Remaining Limitation:** 
If the relevant code spans multiple files, Wraith currently only 
reads the top matched file fully. Multi-file reading will be 
added in a future phase.

## 2. Token Limit on Free Groq Tier
**Problem:** Large codebases with many chunks hit Groq's 6000 
tokens per minute limit.

**Fix Applied:** Reduced MAX_ITERATIONS to 3 and n_results to 3 
per search to stay within limits.

**Remaining Limitation:** 
Not suitable for very large codebases on free tier. Solution is 
either Groq Dev tier or switching to Ollama for local inference.