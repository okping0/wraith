import ast
from pathlib import Path

CHUNK_SIZE = 40
CHUNK_OVERLAP = 10

def get_function_chunks(source_code: str) -> list[dict]:
  """
  Parse Python source code and extract funtions and classes as individual chunks with their line numbers
  """
  try:
    tree = ast.parse(source_code)
  except SyntaxError:
    return []
  
  chunks = []
  lines = source_code.splitlines()

  for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
      start_line = node.lineno -1
      end_line = node.end_lineno
      chunk_lines = lines[start_line:end_line]
      chunk_text = "\n".join(chunk_lines)

      if chunk_text.strip():
        chunks.append({
          "text": chunk_text,
          "start_line": start_line,
          "end_line": end_line,
          "name": node.name,
          "type": type(node).__name__
        })

  return chunks

def chunk_file_smart(file_info: dict, content: str) -> list[dict]:
    """
    Smart chunking strategy:
    1. If Python file — try AST function-level chunking
    2. If function too big — split it with sliding window
    3. If not Python or AST fails — fall back to sliding window
    """
    if file_info["extension"] == ".py":
        function_chunks = get_function_chunks(content)
        
        if function_chunks:
            result = []
            for fc in function_chunks:
                line_count = fc["end_line"] - fc["start_line"]
                
                if line_count <= CHUNK_SIZE:
                    result.append({
                        "text": fc["text"],
                        "metadata": {
                            "file_path": file_info["relative_path"],
                            "extension": file_info["extension"],
                            "start_line": fc["start_line"],
                            "end_line": fc["end_line"],
                            "chunk_type": "function",
                            "name": fc["name"]
                        }
                    })
                else:
                    lines = fc["text"].splitlines()
                    start = 0
                    while start < len(lines):
                        end = min(start + CHUNK_SIZE, len(lines))
                        chunk_text = "\n".join(lines[start:end])
                        if chunk_text.strip():
                            result.append({
                                "text": chunk_text,
                                "metadata": {
                                    "file_path": file_info["relative_path"],
                                    "extension": file_info["extension"],
                                    "start_line": fc["start_line"] + start,
                                    "end_line": fc["start_line"] + end,
                                    "chunk_type": "function_part",
                                    "name": fc["name"]
                                }
                            })
                        start += (CHUNK_SIZE - CHUNK_OVERLAP)
            return result

    return chunk_file(file_info, content)

def chunk_file(file_info: dict, content: str) -> list[dict]:
  lines = content.splitlines()
  chunks=[]
  total_lines = len(lines)

  if total_lines == 0:
    return chunks

  start = 0

  while start < total_lines:
    end = min(start +CHUNK_SIZE, total_lines)
    chunk_lines = lines[start:end]
    chunk_text = "\n".join(chunk_lines)

    if chunk_text.strip():
      chunks.append({
        "text": chunk_text,
        "metadata":{
          "file_path": file_info["relative_path"],
          "extension": file_info["extension"],
          "start_line": start+1,
          "end_line": end,
          "total_lines": total_lines,
          "chunk_type": "lines",
          "name": None,
        }
      }) 

    start += (CHUNK_SIZE-CHUNK_OVERLAP)

  return chunks

def chunk_codebase(file_infos: list[dict], file_contents: list[str]) -> list[dict]:
  all_chunks = []
  for file_info, content in zip(file_infos, file_contents):
    if content is None:
      continue

    file_chunks = chunk_file_smart(file_info, content)
    all_chunks.extend(file_chunks)

  return all_chunks

if __name__ == "__main__":
    import sys
    from file_parser import get_all_files, read_file

    path = sys.argv[1] if len(sys.argv) > 1 else "."
    files = get_all_files(path)
    contents = [read_file(f) for f in files]
    chunks = chunk_codebase(files, contents)

    print(f"\nWraith Chunker")
    print(f"{'='*40}")
    print(f"Files scanned:   {len(files)}")
    print(f"Total chunks:    {len(chunks)}")
    print(f"{'='*40}")

    print(f"\nSample chunk from: {chunks[0]['metadata']['file_path']}")
    print(f"Lines {chunks[0]['metadata']['start_line']} to {chunks[0]['metadata']['end_line']}")
    print(f"{'-'*40}")
    print(chunks[0]['text'])