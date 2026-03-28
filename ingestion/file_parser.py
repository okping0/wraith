import os
from pathlib import Path

SUPPORTED_EXTENSIONS = {
  ".py", ".js", ".ts",".jsx", ".tsx", ".java",".cpp",".c",".h", ".cs",".go",".rb",".php",".html","..css", ".sql", ".sh", ".yaml", ".yml", ".json", ".md", ".txt"
}

IGNORED_DIRS = {
  ".git", "__pycache__", "node_modules", "venv",".venv", "env", "dist", "build", ".idea", ".vscode", "coverage", ".pytest_cache"
}

def get_all_files(root_path: str) -> list[dict]:
  root = Path(root_path).resolve()
  collected_files =[]

  if not root.exists():
    raise ValueError(f"Path does not exists: {root_path}")
  
  if not root.is_dir():
    raise ValueError(f"Path is not a directory: {root_path}")
  
  for dirpath, dirnames, filenames in os.walk(root):
    dirnames[:] = [
      d for d in dirnames
      if d not in IGNORED_DIRS and not d.startswith(".")
    ]
    for filename in filenames:
      file_path = Path(dirpath) / filename
      extension = file_path.suffix.lower()

      if extension not in SUPPORTED_EXTENSIONS:
        continue

      try:
        size = file_path.stat().st_size

        if size == 0 or size > 1_000_000:
          continue

        collected_files.append({
          "path": str(file_path),
          "relative_path": str(file_path.relative_to(root)),
          "extension": extension,
          "size_bytes":size
        })

      except (OSError, PermissionError):
        continue

  return collected_files

def read_file(file_info:dict) -> str | None:
  try:
    with open(file_info["path"], "r", encoding="utf-8", errors = "ignore") as f:
      return f.read()
  except Exception:
    return None
  
if __name__ == "__main__":
  import sys

  test_path = sys.argv[1] if len(sys.argv) >1 else "."
  files = get_all_files(test_path)

  print(f"\nCodeLens File Scanner")
  print(f"{'='*40}")
  print(f"Found {len(files)} files in: {test_path}")
  print(f"{'='*40}")

  for f in files:
        size_kb = f['size_bytes'] / 1024
        print(f"  {f['relative_path']:<50} {size_kb:.1f} KB")