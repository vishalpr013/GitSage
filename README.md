# 🧙 git-sage — AI-Powered Git Assistant

**git-sage** is an AI-powered CLI tool that integrates directly into your Git workflow. It uses a multi-agent AI system to analyze staged changes, identify issues, suggest fixes, generate commit messages, explain commits, trace bugs through Git history, and create changelogs — all from the terminal.

## Features

- 🔍 **AI Code Review** — Reviews staged changes with specialized agents (Bug, Security, Style, Complexity)
- 🔧 **Auto Fix** — Generates and applies AI-powered code fixes after your confirmation
- 💬 **Semantic Commit Messages** — Creates meaningful commit messages from code changes
- 📖 **Commit Explanation** — Explains any commit in plain English
- 🔎 **AI Blame** — Traces runtime errors back to the responsible commit
- 📋 **Changelog Generation** — Produces categorized release notes from Git history

## Installation
 pip
```bash
pip install git-sage
```

## Quick Start

```bash
# Review staged changes
git add .
git-sage review

# Generate a commit message
git-sage commit

# Explain a commit
git-sage explain HEAD

# Trace an error to a commit
git-sage blame "TypeError: cannot read property 'name'"

# Generate changelog
git-sage changelog
```

## Configuration

Set your Gemini API key:

```bash
# In your .env file or environment
export GEMINI_API_KEY=your_key_here
```

Create a `.gitsage.toml` in your project root for project-specific settings:

```toml
[llm]
model = "gemini-3.1-flash-lite"
temperature = 0.1

[agents]
enabled = ["bug", "security", "style", "complexity"]

[commit]
style = "conventional"
```

## License

MIT
