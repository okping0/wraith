import os
import sys
import requests
sys.path.append("..")
from dotenv import load_dotenv
from groq import Groq
from tools.code_tools import search_codebase, read_file

load_dotenv()

MODEL = "llama-3.1-8b-instant"


class GitHubIssueSolver:
    def __init__(self, codebase_path: str):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.codebase_path = codebase_path
        self.github_token = os.getenv("GITHUB_TOKEN")

    def _parse_issue_url(self, url: str) -> tuple:
        parts = url.rstrip("/").split("/")
        owner = parts[-4]
        repo = parts[-3]
        issue_number = parts[-1]
        return owner, repo, issue_number

    def fetch_issue(self, issue_url: str) -> dict:
        owner, repo, issue_number = self._parse_issue_url(issue_url)
        api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"

        headers = {}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        response = requests.get(api_url, headers=headers)

        if response.status_code != 200:
            return {"error": f"Could not fetch issue: {response.status_code}"}

        data = response.json()
        return {
            "title": data.get("title", ""),
            "body": data.get("body", ""),
            "labels": [l["name"] for l in data.get("labels", [])],
            "state": data.get("state", "")
        }

    def solve_issue(self, issue_url: str) -> dict:
        print(f"\nFetching issue: {issue_url}")
        issue = self.fetch_issue(issue_url)

        if "error" in issue:
            return issue

        print(f"Issue: {issue['title']}")
        print(f"Searching codebase for relevant code...")

        search_results = search_codebase(
            f"{issue['title']} {issue['body'][:200]}",
            n_results=3
        )

        first_file = None
        skip_extensions = [".md", ".txt", ".yaml", ".yml", ".json"]
        for line in search_results.split("\n"):
            if line.startswith("File:"):
                candidate = line.replace("File:", "").strip()
                if not any(candidate.endswith(ext) for ext in skip_extensions):
                  first_file = candidate
                  break
        if first_file:
            full_code = read_file(first_file, self.codebase_path)
        else:
            full_code = search_results

        prompt = f"""You are Wraith, an expert developer assistant.

A GitHub issue has been reported. Your job is to:
1. Understand what the issue is describing
2. Based on the code context provided, locate exactly where the problem is
3. Explain why this causes the issue
4. Suggest a specific fix with corrected code

GitHub Issue Title: {issue['title']}

Issue Description:
{issue['body'][:500]}

Relevant code from semantic search:
{search_results[:800]}

Full file content (use this for exact line references):
{full_code[:1200]}

Provide:
- Exact file and line number where the bug is
- Why this causes the reported issue
- The fix with corrected code snippet
- Any other files that may need changes

Be direct and technical.
Only reference code that appears EXACTLY in the context above. 
If you cannot find the specific line, say "I could not locate the exact line 
in the provided context." Never invent code."""

        response = self.client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        analysis_text = response.choices[0].message.content
        confidence = 100

        return {
            "issue_title": issue["title"],
            "issue_body": issue["body"][:300],
            "analysis": analysis_text,
            "search_results": search_results[:500],
            "confidence": confidence
        }


if __name__ == "__main__":
    import sys
    codebase = sys.argv[1] if len(sys.argv) > 1 else "."
    issue_url = sys.argv[2] if len(sys.argv) > 2 else None

    solver = GitHubIssueSolver(codebase_path=codebase)

    if issue_url:
        result = solver.solve_issue(issue_url)
        print(f"\n{'='*50}")
        print(f"ISSUE: {result.get('issue_title', 'N/A')}")
        print(f"{'='*50}")
        print(result.get('analysis', result.get('error', 'No result')))
    else:
        print("Usage: python -m tools.github_tool <codebase_path> <github_issue_url>")
        print("\nExample:")
        print('python -m tools.github_tool "C:\\path\\to\\code" "https://github.com/owner/repo/issues/1"')
        print("\nTo test without a real issue, creating a mock test...")

        mock_issue_title = "blink_passed result not checked before marking attendance"
        mock_issue_body = """
In main_attendance.py the process_student method calls wait_for_blink
but does not check the return value before calling mark_attendance.
Attendance gets marked even when blink_passed is False.
        """

        print(f"\nMock Issue: {mock_issue_title}")
        print(f"Searching codebase...")

        search_results = search_codebase(
            f"{mock_issue_title} {mock_issue_body}",
            n_results=3
        )
        first_file = None
        skip_extensions = [".md", ".txt", ".yaml", ".yml", ".json"]
        for line in search_results.split("\n"):
            if line.startswith("File:"):
                candidate = line.replace("File:", "").strip()
                if not any(candidate.endswith(ext) for ext in skip_extensions):
                  first_file = candidate
                  break

        full_code = ""
        skip_extensions = [".md", ".txt", ".yaml", ".yml", ".json"]
        files_read = []

        for line in search_results.split("\n"):
            if line.startswith("File:"):
                candidate = line.replace("File:", "").strip()
                if not any(candidate.endswith(ext) for ext in skip_extensions):
                    if candidate not in files_read:
                        files_read.append(candidate)

        print(f"Reading {len(files_read)} relevant files...")
        file_contents = []
        for f in files_read:
            content = read_file(f, codebase)
            file_contents.append(f"=== {f} ===\n{content[:1500]}")
            print(f"Read: {f}")

        full_code = "\n\n".join(file_contents)

        prompt = f"""You are Wraith, an expert developer assistant.

A GitHub issue has been reported. Your job is to:
1. Understand what the issue is describing
2. Based on the code context provided, locate exactly where the problem is
3. Explain why this causes the issue
4. Suggest a specific fix with corrected code

GitHub Issue Title: {mock_issue_title}

Issue Description: {mock_issue_body}

Relevant code from codebase:
{search_results[:800]}

Full file content (use this for exact line references):
{full_code[:1200]}

Be direct and technical. Reference exact file names and line numbers.
Only reference code that appears EXACTLY in the context above. 
If you cannot find the specific line, say "I could not locate the exact line 
in the provided context." Never invent code."""

        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )

        analysis_text = response.choices[0].message.content

        confidence_response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": analysis_text},
                {"role": "user", "content": (
                    "Rate your confidence 0-100 that every file name, line number, "
                    "and code snippet you referenced above exists VERBATIM in the "
                    "context I gave you. Reply with a single integer only."
                )}
            ],
            temperature=0.0  # deterministic for scoring
        )

        confidence_raw = confidence_response.choices[0].message.content.strip()
        try:
            confidence = int("".join(filter(str.isdigit, confidence_raw)))
        except ValueError:
            confidence = 0

        if confidence < 80:
            analysis_text = (
                f"[Low confidence: {confidence}/100] "
                "The model could not reliably locate the bug in the provided code context. "
                "Try pointing it at a more specific file.\n\n"
                + analysis_text
            )

        print(f"\n{'='*50}")
        print("WRAITH ANALYSIS")
        print(f"{'='*50}")
        print(response.choices[0].message.content)