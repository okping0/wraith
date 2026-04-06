import os
import sys
sys.path.append("..")
from dotenv import load_dotenv
from groq import Groq
from tools.code_tools import read_file, list_files, search_codebase
from ingestion.file_parser import get_all_files

load_dotenv()

MODEL = "llama-3.1-8b-instant"


class CodeAnalyzer:
    def __init__(self, codebase_path: str):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.codebase_path = codebase_path

    def _analyze_chunk(self, code: str, file_path: str) -> str:
        prompt = f"""You are a senior security and code quality engineer.
Analyze this code for:
1. Bugs — logic errors, edge cases, crashes
2. Security issues — injection, hardcoded secrets, unsafe input
3. Anti-patterns — bad practices, poor error handling
4. Performance issues — unnecessary loops, memory leaks

For each issue found:
- State the issue clearly
- Reference the exact line number
- Explain why it is a problem
- Suggest a specific fix

File: {file_path}

Code:
{code}

If no issues found, say "No issues found."
Be direct and technical. No fluff."""

        response = self.client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        return response.choices[0].message.content

    def analyze_file(self, file_path: str) -> dict:
        print(f"Analyzing: {file_path}")
        content = read_file(file_path, self.codebase_path)

        if "Error" in content or "not found" in content:
            return {"file": file_path, "issues": "Could not read file"}

        # split into chunks to stay within token limit
        lines = content.split("\n")
        chunk_size = 80
        all_issues = []

        for i in range(0, len(lines), chunk_size):
            chunk = "\n".join(lines[i:i+chunk_size])
            if chunk.strip():
                issues = self._analyze_chunk(chunk, file_path)
                if "No issues found" not in issues:
                    all_issues.append(issues)

        return {
            "file": file_path,
            "issues": "\n\n".join(all_issues) if all_issues else "No issues found"
        }

    def analyze_codebase(self) -> list[dict]:
        files = get_all_files(self.codebase_path)
        results = []

        # focus on core logic files only, skip tests and scripts
        priority_files = [
            f for f in files
            if f["extension"] == ".py"
            and "test" not in f["relative_path"].lower()
            and "script" not in f["relative_path"].lower()
        ]

        print(f"\nAnalyzing {len(priority_files)} core files...")

        for file_info in priority_files:
            result = self.analyze_file(file_info["relative_path"])
            results.append(result)

        return results

    def security_scan(self) -> list[dict]:
        print("\nRunning security scan...")
        dangerous_patterns = [
            "hardcoded password or secret",
            "SQL injection vulnerability",
            "unsafe eval or exec",
            "missing authentication check",
            "exposed API key"
        ]

        findings = []
        for pattern in dangerous_patterns:
            results = search_codebase(pattern, n_results=2)
            if "No relevant" not in results:
                findings.append({
                    "pattern": pattern,
                    "found_in": results[:300]
                })

        return findings


if __name__ == "__main__":
    import sys
    codebase = sys.argv[1] if len(sys.argv) > 1 else "."

    analyzer = CodeAnalyzer(codebase_path=codebase)

    print("=" * 50)
    print("WRAITH — Bug Detection & Security Analysis")
    print("=" * 50)

    # analyze core files
    results = analyzer.analyze_codebase()

    for r in results:
        print(f"\n{'='*50}")
        print(f"FILE: {r['file']}")
        print(f"{'='*50}")
        print(r['issues'])

    # security scan
    print(f"\n{'='*50}")
    print("SECURITY SCAN RESULTS")
    print(f"{'='*50}")
    findings = analyzer.security_scan()

    if findings:
        for f in findings:
            print(f"\nPattern: {f['pattern']}")
            print(f"Found in:\n{f['found_in']}")
    else:
        print("No obvious security issues detected")