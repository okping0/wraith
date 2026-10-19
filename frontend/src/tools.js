import { MessageSquare, Bot, ScanSearch, GitPullRequest, Globe } from "lucide-react";

export const TOOLS = [
  { id: "ask", label: "Ask", icon: MessageSquare, desc: "Ask questions about your codebase in plain English." },
  { id: "agent", label: "Agent", icon: Bot, desc: "Multi-step reasoning with tools across your code." },
  { id: "analyze", label: "Analyze", icon: ScanSearch, desc: "Find bugs, security issues and anti-patterns." },
  { id: "issues", label: "Issues", icon: GitPullRequest, desc: "Paste a GitHub issue and locate the code to fix it." },
  { id: "research", label: "Research", icon: Globe, desc: "Stack-aware web research for your problem." },
];