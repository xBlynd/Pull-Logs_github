# 👻 WRAITH - Git & GitHub History Exporter

> **W**orkflow **R**ecord **A**nd **I**ntelligent **T**racking **H**istory

A powerful Python toolkit for extracting and documenting your entire Git repository and GitHub project history into human-readable and AI-optimized formats.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 🎯 What Is WRAITH?

WRAITH is a modular export system that transforms your Git repositories and GitHub projects into comprehensive documentation files. Perfect for:

- 📚 **Project Documentation** - Generate complete project snapshots for archival
- 🤖 **AI Training & Analysis** - Feed your codebase to LLMs like Gemini, GPT, or Claude
- 🔍 **Code Review** - Get a bird's-eye view of your entire project structure
- 📊 **Project Audits** - Track all commits, PRs, reviews, and approvals in one place
- 🎓 **Learning & Reference** - Study codebases with organized, navigable exports

## ⚡ Features

### 📦 `pack_project.py` - Project Source Exporter

Exports your entire project source code into **two optimized formats**:

#### Human-Readable Output (`PROJECT_HUMAN_READABLE.md`)
- 📑 **Table of Contents** with section navigation
- 🗂️ **Organized by file type** (Python modules, configs, docs)
- 🔍 **Symbol extraction** - Classes, functions, and methods with line numbers
- 📊 **File statistics** - Line counts, file sizes, metadata
- 🎨 **Visual hierarchy** with emojis and formatting

#### AI-Optimized Output (`PROJECT_AI_OPTIMIZED.md`)
- 🤖 **Flat, parseable structure** with explicit delimiters
- 🔧 **Pipe-separated values** for easy parsing
- 📍 **Clear boundaries** (`FILE_START`, `CONTENT_END`, etc.)
- 🎯 **Minimal formatting** to reduce token overhead
- ⚡ **Direct content access** without nested navigation

**Solves Issues With:**
- Google Gemini file reading problems
- GitHub file size limits
- Complex directory structures
- Multi-file context for AI tools

### 📊 `pack_github-logs.py` - Git & GitHub History Exporter

Exports complete repository history including **Git commits** and **GitHub API data**:

#### Modular Export Options
Toggle exactly what you need:
- ✅ Repository information and statistics
- 👥 Contributors with commit counts
- 🌿 Branch information
- 🏷️ Git tags and releases
- 📝 Full commit history with messages
- 📈 Commit statistics (insertions/deletions)
- 📄 File change tracking
- 🔀 Pull request data
- ✅ PR reviews and approvals
- 💬 PR review comments
- 🔗 Issue references

#### Dual Output Formats
- **Human version**: Rich markdown with navigation, collapsibles, and formatting
- **AI version**: Structured flat format with pipe delimiters for LLM parsing

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.8 or higher
python --version

# Install requests for GitHub API features (optional)
pip install requests
```

### Installation

```bash
# Clone the repository
git clone https://github.com/xBlynd/wraith.git
cd wraith

# Or download individual scripts
curl -O https://raw.githubusercontent.com/xBlynd/wraith/main/pack_project.py
curl -O https://raw.githubusercontent.com/xBlynd/wraith/main/pack_github-logs.py
```

### Usage

#### Export Project Source

```bash
# Navigate to your project directory
cd /path/to/your/project

# Run the project packer
python pack_project.py

# Output files created:
# - PROJECT_HUMAN_READABLE.md
# - PROJECT_AI_OPTIMIZED.md
```

#### Export Git History

```bash
# Navigate to your git repository
cd /path/to/your/repo

# Run the git history exporter
python pack_github-logs.py

# Output files created:
# - GIT_HISTORY_HUMAN.md
# - GIT_HISTORY_AI.md
```

#### Export with GitHub API Data

```bash
# Set your GitHub token (for PR reviews, comments, etc.)
export GITHUB_TOKEN='your_github_personal_access_token'

# Run with full GitHub integration
python pack_github-logs.py
```

## ⚙️ Configuration

### Project Packer (`pack_project.py`)

Edit configuration at the top of the script:

```python
# Output filenames
OUTPUT_HUMAN = "PROJECT_HUMAN_READABLE.md"
OUTPUT_AI = "PROJECT_AI_OPTIMIZED.md"

# Directories to ignore
IGNORE_DIRS = {'.git', '__pycache__', 'venv', 'node_modules'}

# Files to ignore
IGNORE_FILES = {'.DS_Store', 'package-lock.json'}

# File extensions to include
ALLOWED_EXTENSIONS = {'.py', '.md', '.json', '.bat', '.sh', '.txt'}
```

### Git History Exporter (`pack_github-logs.py`)

Customize what data to export:

```python
EXPORT_MODULES = {
    'repo_info': True,          # Basic repository information
    'contributors': True,        # All contributors with stats
    'branches': True,            # Branch information
    'tags': True,                # Git tags
    'commits': True,             # All commit history
    'commit_stats': True,        # File changes and diff stats
    'commit_files': True,        # Detailed file changes
    'commit_diffs': False,       # Full diff content (large!)
    'pr_data': True,             # Pull request info (needs token)
    'pr_reviews': True,          # PR reviews/approvals (needs token)
    'pr_comments': True,         # PR comments (needs token)
    'issue_references': True,    # Issues mentioned in commits
}

# Limit commits (None for all)
COMMIT_LIMIT = None  # or set to 100, 500, etc.
```

## 🔑 GitHub Token Setup

To export PR reviews, approvals, and comments, you need a GitHub personal access token:

1. Go to [GitHub Settings > Developer Settings > Personal Access Tokens](https://github.com/settings/tokens)
2. Click **Generate new token (classic)**
3. Select scopes:
   - `repo` - Full control of private repositories
   - `read:org` - Read org and team membership (if needed)
4. Generate and copy your token
5. Set as environment variable:

```bash
# Linux/Mac
export GITHUB_TOKEN='ghp_your_token_here'

# Windows (PowerShell)
$env:GITHUB_TOKEN='ghp_your_token_here'

# Or edit the script directly
GITHUB_TOKEN = 'ghp_your_token_here'
```

## 📋 Use Cases

### For AI/LLM Integration

```bash
# Export your project for AI analysis
python pack_project.py

# Upload PROJECT_AI_OPTIMIZED.md to:
# - Google Gemini
# - ChatGPT
# - Claude
# - GitHub Copilot
```

The AI-optimized format uses explicit delimiters that help LLMs understand file boundaries and structure without ambiguity.

### For Documentation

```bash
# Generate human-readable docs
python pack_project.py

# Open PROJECT_HUMAN_READABLE.md in your browser/editor
# Share with team members or include in project documentation
```

### For Code Review

```bash
# Export both source and history
python pack_project.py
python pack_github-logs.py

# Review complete project context:
# - All source code
# - Commit history
# - PR discussions and approvals
```

### For Project Archival

```bash
# Create complete project snapshot
python pack_project.py
python pack_github-logs.py

# Archive outputs with your project backups
```

## 📁 Output Examples

### Project Structure Export

```markdown
## 🗂️ Project Structure

📁 my-project/
│   ├── 📄 README.md
│   ├── 📄 setup.py
│   ├── 📁 src/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 main.py
│   │   └── 📄 utils.py
│   └── 📁 tests/
│       └── 📄 test_main.py
```

### Commit History Export

```markdown
### 📝 Commit #42: Add user authentication

**Hash:** `abc123def456...`
**Author:** Ian Martin <ian@xsvstudio.com>
**Date:** 2026-02-10 14:30:00 -0500
**Pull Request:** #15

**Files Changed:**
- ✅ Added `src/auth.py`
- 📝 Modified `src/main.py`
- 📝 Modified `README.md`
```

## 🛠️ Technical Details

### Dependencies

- **Python 3.8+** - Core language
- **Git** - Must be installed and in PATH
- **requests** - Optional, for GitHub API features

### File Size Considerations

- **Project exports** can be large (10MB+ for big codebases)
- **Git history exports** can be massive with full diffs enabled
- Use `COMMIT_LIMIT` to restrict history size
- Disable `commit_diffs` for production use

### Performance

- **Project export**: ~1-5 seconds for typical projects
- **Git history export**: ~1 second per 100 commits
- **GitHub API calls**: ~1-2 seconds per PR (with reviews/comments)

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] Support for more programming languages in symbol extraction
- [ ] Integration with GitLab, Bitbucket APIs
- [ ] Web UI for configuration
- [ ] Export to JSON/XML formats
- [ ] Diff highlighting in AI-optimized outputs
- [ ] Incremental exports (only new commits)

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Credits

Created by [Ian Martin](https://github.com/xBlynd) / [xsvStudio, LLC](https://www.xsvstudio.com)

Inspired by issues with Google Gemini's file reading and the need for better AI-optimized code exports.

## 🔗 Links

- **GitHub**: [https://github.com/xBlynd/wraith](https://github.com/xBlynd/wraith)
- **Issues**: [https://github.com/xBlynd/wraith/issues](https://github.com/xBlynd/wraith/issues)
- **Author**: [@xBlynd](https://github.com/xBlynd)

---

**Made with ☕ in Pennsylvania**
```

This README covers everything: features, setup, configuration, use cases, and examples. The name "WRAITH" fits perfectly with your Ghost Shell theme and sounds professional. Want me to adjust anything or go with a different name?