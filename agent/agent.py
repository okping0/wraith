import os
import sys
import json
sys.path.append("..")
from dotenv import load_dotenv
from groq import Groq
from tools.code_tools import TOOLS

load_dotenv()

MODEL = "llama-3.1-8b-instant"
MAX_ITERATIONS = 3


class WraithAgent:
    def __init__(self, codebase_path: str):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.codebase_path = codebase_path
        self.conversation = []
        print("Wraith Agent ready")

    def _build_system_prompt(self) -> str:
        tool_descriptions = []
        for name, tool in TOOLS.items():
            # here returning something like (tool name(whihc is name here), {dictonary of tools data like description parameters} (whihc is the tool here in for loop))
            tool_descriptions.append(
                f"- {name}: {tool['description']}\n"
                f"  params: {tool['params']}"
            )
        tools_text = "\n".join(tool_descriptions)

        return f"""You are Wraith, an expert codebase analysis agent.

You have access to these tools:
{tools_text}

To use a tool, respond with EXACTLY this format and nothing else:
TOOL: tool_name
PARAMS: {{"param1": "value1", "param2": "value2"}}

When you have enough information to answer, respond with:
FINAL: your complete answer here

Rules:
- Always search the codebase before answering
- Reference specific file names and line numbers
- If one search isn't enough, search again with different terms
- Be precise and technical
- codebase_path is always: {self.codebase_path}"""

    def _parse_tool_call(self, response: str):
        lines = response.strip().split("\n")
        tool_name = None
        params = {}

        for i, line in enumerate(lines):
            if line.startswith("TOOL:"):
                tool_name = line.replace("TOOL:", "").strip()
            if line.startswith("PARAMS:"):
                params_str = line.replace("PARAMS:", "").strip()
                j=i+1
                while j< len(lines) and not lines[j].startswith("TOOL:"):
                    j += 1
                try:
                    params = json.loads(params_str)
                except json.JSONDecodeError:
                    params = {}
                break

        return tool_name, params

    def _run_tool(self, tool_name: str, params: dict) -> str:
        if tool_name not in TOOLS:
            return f"Unknown tool: {tool_name}"

        tool = TOOLS[tool_name]
        fn = tool["fn"]

        try:
            result = fn(**params)
            return result
        except Exception as e:
            return f"Tool error: {str(e)}"

    def run(self, question: str) -> str:
        print(f"\nWraith thinking about: '{question}'")
        print("=" * 50)

        system_prompt = self._build_system_prompt()
        self.conversation = [
            {"role": "user", "content": question}
        ]

        for iteration in range(MAX_ITERATIONS):
            print(f"\nIteration {iteration + 1}...")

            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *self.conversation
                ],
                temperature=0.2
            )

            agent_message = response.choices[0].message.content
            print(f"Agent: {agent_message[:100]}...")

            if agent_message.startswith("FINAL:"):
                final_answer = agent_message.replace("FINAL:", "").strip()
                print("\n" + "=" * 50)
                print("WRAITH ANSWER:")
                print("=" * 50)
                print(final_answer)
                return final_answer

            tool_name, params = self._parse_tool_call(agent_message)

            if tool_name:
                print(f"Using tool: {tool_name}")
                print(f"Params: {params}")
                tool_result = self._run_tool(tool_name, params)
                print(f"Tool result preview: {tool_result[:150]}...")

                self.conversation.append(
                    {"role": "assistant", "content": agent_message}
                )
                self.conversation.append(
                    {"role": "user", "content": f"Tool result:\n{tool_result}"}
                )
            else:
                return agent_message

        return "Max iterations reached. Could not find a complete answer."


if __name__ == "__main__":
    import sys
    codebase = sys.argv[1] if len(sys.argv) > 1 else "."

    agent = WraithAgent(codebase_path=codebase)

    questions = [
        "how is liveness detection implemented and is there any bug in it",
        "list all files and tell me which one handles database models",
    ]

    for q in questions:
        result = agent.run(q)
        print("\n")