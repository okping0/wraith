from pathlib import Path

CHUNK_SIZE = 40
CHUNK_OVERLAP = 10

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
          "total_lines": total_lines
        }
      }) 

    start += (CHUNK_SIZE-CHUNK_OVERLAP)

  return chunks

def chunk_codebase(file_infos: list[dict], file_contents: list[str]) -> list[dict]:
  all_chunks = []
  for file_info, content in zip(file_infos, file_contents):
    if content is None:
      continue

    file_chunks = chunk_file(file_info, content)
    all_chunks.extend(file_chunks)

  return all_chunks

if __name__ == "__main__":
    import sys
    from file_parser import get_all_files, read_file

    path = sys.argv[1] if len(sys.argv) > 1 else "."
    files = get_all_files(path)
    contents = [read_file(f) for f in files]
    chunks = chunk_codebase(files, contents)

    print(f"\nCodeLens Chunker")
    print(f"{'='*40}")
    print(f"Files scanned:   {len(files)}")
    print(f"Total chunks:    {len(chunks)}")
    print(f"{'='*40}")

    print(f"\nSample chunk from: {chunks[0]['metadata']['file_path']}")
    print(f"Lines {chunks[0]['metadata']['start_line']} to {chunks[0]['metadata']['end_line']}")
    print(f"{'-'*40}")
    print(chunks[0]['text'])