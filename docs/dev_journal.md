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

## Chunking problem
**Problem:** When chunking a file using sliding window, it can divide a function into chunks. The function will loose their proper meaning this way.

**Fix Applied:** To address this issue, i used AST(abstract syntax tree) based chunking. Instead of blindly cutting every 40 lines, you parse the code and cut at natural boundaries — functions, classes, methods.

**remaining limitation:** This only works for python written code. To make it valid for all languages, we will be using tree-sitter(right now, at this stage, we wouldnt use it since installation would be complex. I'll integrate this after the completion of phase 7) 



# unsolved


## if i inserted an issue's link inthe ask section, it blbbers
**problem -** 1 _ UX problem. if a link is received, it should make the user aware. 

2_This is actually the hallucination problem, but in a different form. The LLM gets chunks that are loosely related and starts connecting dots that don't exist

**fix should be applied** The fix is in qa_engine.py — add a relevance threshold.



# BUGS

## github issue need cloning of the repo first.
- right now you will have to do it manually, but after fixing the global space bug of vector db, i will implement automatic cloning


-(SEARCH IMPROVEMENT IN THE CODEBASE TO SEE FOR MORE BUGS AND IMPROVEMENT PLANS)