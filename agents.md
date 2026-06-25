git-sage — AI-Powered Git Assistant

git-sage is an AI-powered CLI tool that integrates directly into the Git workflow. Instead of simply reviewing code, it uses a multi-agent AI system to analyze staged changes, identify issues, suggest fixes, generate commit messages, explain commits, trace bugs through Git history, and create changelogs—all from the terminal.

How it works

When a developer runs a git-sage command, the tool reads the relevant Git context (such as staged diffs, commit history, or logs) and sends it through a LangGraph-based multi-agent pipeline.

Each agent has a specialized role:

🐛 Bug Agent – Detects logic errors, edge cases, and potential bugs.
🔐 Security Agent – Identifies vulnerabilities such as hardcoded secrets, SQL injection risks, and insecure coding practices.
✨ Style Agent – Reviews code readability, naming conventions, and maintainability.
⚡ Complexity Agent – Evaluates algorithmic complexity and suggests simplifications.
🔧 Fix Agent – Generates safe code patches to resolve detected issues after user approval.
👨‍⚖️ Chair Agent – Combines all findings and produces the final verdict.
Features
AI Code Review – Reviews staged changes before every commit.
Auto Fix – Generates and applies AI-powered code fixes after user confirmation.
Semantic Commit Messages – Creates meaningful commit messages from code changes.
Commit Explanation – Explains any commit in plain English, including why it was made.
AI Blame – Traces runtime errors back to the commit most likely responsible and suggests fixes.
Automatic Changelog Generation – Produces categorized release notes directly from Git history