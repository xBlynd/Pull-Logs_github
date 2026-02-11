#!/usr/bin/env python3
"""
Pull Logs - GitHub Edition
===========================

Modular Git & GitHub history exporter with interactive CLI.

Exports repository history including commits, PRs, reviews, and approvals.
Choose exactly what data you need and output format (Human/AI/Both).

GitHub: https://github.com/xBlynd/pull-logs-github
Author: Ian Martin (@xBlynd) - xsvStudio, LLC
License: MIT

Usage:
    python pack_github-logs.py              # Interactive mode
    python pack_github-logs.py --all        # Export everything
    python pack_github-logs.py --help       # Show all options
"""

import os
import subprocess
import json
import time
import argparse
from datetime import datetime

# Optional: requests for GitHub API
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠️  'requests' library not found. GitHub API features disabled.")
    print("   Install with: pip install requests\n")

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
OUTPUT_HUMAN = "GIT_HISTORY_HUMAN.md"
OUTPUT_AI = "GIT_HISTORY_AI.md"

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
GITHUB_API = "https://api.github.com"

# Available export modules
AVAILABLE_MODULES = {
    'repo_info': 'Basic repository information and statistics',
    'contributors': 'All contributors with commit counts',
    'branches': 'Branch information (local and remote)',
    'tags': 'Git tags and releases',
    'commits': 'Complete commit history',
    'commit_stats': 'File change statistics per commit',
    'commit_files': 'Detailed file changes per commit',
    'commit_diffs': 'Full diff content (WARNING: Can be very large)',
    'pr_data': 'Pull request information (requires GitHub token)',
    'pr_reviews': 'PR reviews and approvals (requires GitHub token)',
    'pr_comments': 'PR review comments (requires GitHub token)',
    'issue_references': 'Issues mentioned in commits',
}

# ---------------------------------------------------------
# GIT OPERATIONS
# ---------------------------------------------------------

def run_git_command(cmd):
    """Execute git command and return output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        return result.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"

def get_repo_info():
    """Get basic repository information."""
    repo_url = run_git_command("git config --get remote.origin.url")
    current_branch = run_git_command("git branch --show-current")
    total_commits = run_git_command("git rev-list --count HEAD")
    first_commit_date = run_git_command('git log --reverse --format="%ai" | head -1')
    last_commit_date = run_git_command('git log -1 --format="%ai"')
    
    # Parse GitHub owner/repo from URL
    owner, repo = parse_github_url(repo_url)
    
    return {
        'repo_url': repo_url,
        'owner': owner,
        'repo': repo,
        'branch': current_branch,
        'total_commits': total_commits,
        'first_commit': first_commit_date,
        'last_commit': last_commit_date
    }

def parse_github_url(url):
    """Extract owner and repo name from GitHub URL."""
    if not url:
        return None, None
    
    # Handle different URL formats
    url = url.replace('.git', '')
    
    if 'github.com' in url:
        parts = url.split('github.com/')[-1].split('/')
        if len(parts) >= 2:
            return parts[0], parts[1]
    
    return None, None

def get_contributors():
    """Get list of all contributors with commit counts."""
    contributors_raw = run_git_command('git shortlog -sne --all')
    contributors = []
    
    for line in contributors_raw.split('\n'):
        if line.strip():
            parts = line.strip().split('\t')
            if len(parts) == 2:
                count = parts[0].strip()
                author_info = parts[1]
                contributors.append({
                    'count': count,
                    'info': author_info
                })
    
    return contributors

def get_branches():
    """Get information about branches."""
    branches_raw = run_git_command('git branch -a -v')
    branches = []
    
    for line in branches_raw.split('\n'):
        if line.strip():
            branches.append(line.strip())
    
    return branches

def get_tags():
    """Get all tags with associated commits."""
    tags_raw = run_git_command('git tag -l --format="%(refname:short)|%(objectname:short)|%(creatordate:short)|%(subject)"')
    tags = []
    
    for line in tags_raw.split('\n'):
        if line.strip():
            parts = line.split('|')
            if len(parts) >= 2:
                tags.append({
                    'name': parts[0],
                    'hash': parts[1],
                    'date': parts[2] if len(parts) > 2 else '',
                    'subject': parts[3] if len(parts) > 3 else ''
                })
    
    return tags

def get_all_commits(branch='HEAD', limit=None):
    """Get list of all commit hashes."""
    limit_flag = f'-n {limit}' if limit else ''
    commits = run_git_command(f'git log {limit_flag} --format="%H" {branch}')
    return commits.split('\n') if commits else []

def get_commit_details(commit_hash, include_stats=True, include_files=True, include_diff=False):
    """Get detailed information for a specific commit."""
    
    # Basic commit info
    author = run_git_command(f'git show -s --format="%an" {commit_hash}')
    author_email = run_git_command(f'git show -s --format="%ae" {commit_hash}')
    date = run_git_command(f'git show -s --format="%ai" {commit_hash}')
    subject = run_git_command(f'git show -s --format="%s" {commit_hash}')
    body = run_git_command(f'git show -s --format="%b" {commit_hash}')
    
    details = {
        'hash': commit_hash,
        'short_hash': commit_hash[:7],
        'author': author,
        'email': author_email,
        'date': date,
        'subject': subject,
        'body': body.strip() if body else '',
    }
    
    # Get parent commits (for merge commits)
    parents = run_git_command(f'git show -s --format="%P" {commit_hash}').split()
    details['parents'] = parents
    details['is_merge'] = len(parents) > 1
    
    # Extract PR number from commit message
    import re
    pr_match = re.search(r'#(\d+)', subject)
    details['pr_number'] = pr_match.group(1) if pr_match else None
    
    # Extract issue references
    issue_matches = re.findall(r'#(\d+)', subject + ' ' + body)
    details['issue_refs'] = list(set(issue_matches)) if issue_matches else []
    
    # Optional: Get commit stats
    if include_stats:
        stats = run_git_command(f'git show --stat --format="" {commit_hash}')
        details['stats'] = stats
    
    # Optional: Get file changes
    if include_files:
        files_changed = run_git_command(f'git show --name-status --format="" {commit_hash}')
        details['files'] = parse_file_changes(files_changed)
    
    # Optional: Get full diff
    if include_diff:
        diff = run_git_command(f'git show {commit_hash}')
        details['diff'] = diff
    
    return details

def parse_file_changes(files_raw):
    """Parse file changes into structured format."""
    changes = []
    
    for line in files_raw.split('\n'):
        if line.strip():
            parts = line.split('\t')
            if len(parts) >= 2:
                status = parts[0]
                filepath = parts[1]
                changes.append({
                    'status': status[0],
                    'path': filepath
                })
    
    return changes

# ---------------------------------------------------------
# GITHUB API OPERATIONS
# ---------------------------------------------------------

def github_api_request(endpoint, params=None):
    """Make GitHub API request."""
    if not HAS_REQUESTS:
        return None
    
    if not GITHUB_TOKEN:
        return None
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        response = requests.get(f"{GITHUB_API}{endpoint}", headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"GitHub API Error: {response.status_code} - {endpoint}")
            return None
    except Exception as e:
        print(f"GitHub API Exception: {e}")
        return None

def get_pull_requests(owner, repo):
    """Get all pull requests from GitHub."""
    if not owner or not repo:
        return []
    
    prs = []
    page = 1
    
    while True:
        data = github_api_request(f"/repos/{owner}/{repo}/pulls", {
            'state': 'all',
            'per_page': 100,
            'page': page
        })
        
        if not data:
            break
        
        prs.extend(data)
        
        if len(data) < 100:
            break
        
        page += 1
    
    return prs

def get_pr_reviews(owner, repo, pr_number):
    """Get reviews for a specific PR."""
    if not owner or not repo:
        return []
    
    return github_api_request(f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews") or []

def get_pr_comments(owner, repo, pr_number):
    """Get review comments for a specific PR."""
    if not owner or not repo:
        return []
    
    return github_api_request(f"/repos/{owner}/{repo}/pulls/{pr_number}/comments") or []

def get_issue_info(owner, repo, issue_number):
    """Get information about a specific issue."""
    if not owner or not repo:
        return None
    
    return github_api_request(f"/repos/{owner}/{repo}/issues/{issue_number}")

# ---------------------------------------------------------
# HUMAN-READABLE FORMAT
# ---------------------------------------------------------

def generate_human_readable(data):
    """Generate human-friendly markdown document."""
    output = []
    
    # Header
    output.append("# 📚 Git & GitHub History")
    output.append(f"\n**Generated:** {time.strftime('%B %d, %Y at %I:%M %p')}")
    if data.get('repo_info'):
        output.append(f"**Repository:** [{data['repo_info']['owner']}/{data['repo_info']['repo']}]({data['repo_info']['repo_url']})")
        output.append(f"**Branch:** `{data['repo_info']['branch']}`")
        output.append(f"**Total Commits:** {data['repo_info']['total_commits']}\n")
    output.append("---\n")
    
    # Table of Contents
    output.append("## 📑 Table of Contents\n")
    toc_num = 1
    if data.get('repo_info'):
        output.append(f"{toc_num}. [Repository Overview](#repository-overview)")
        toc_num += 1
    if data.get('contributors'):
        output.append(f"{toc_num}. [Contributors](#contributors)")
        toc_num += 1
    if data.get('branches'):
        output.append(f"{toc_num}. [Branches](#branches)")
        toc_num += 1
    if data.get('tags'):
        output.append(f"{toc_num}. [Tags](#tags)")
        toc_num += 1
    if data.get('pull_requests'):
        output.append(f"{toc_num}. [Pull Requests](#pull-requests)")
        toc_num += 1
    if data.get('commits'):
        output.append(f"{toc_num}. [Commit History](#commit-history)")
        toc_num += 1
    output.append("\n---\n")
    
    # Repository Overview
    if data.get('repo_info'):
        info = data['repo_info']
        output.append("## 📊 Repository Overview\n")
        output.append(f"- **Repository URL:** {info['repo_url']}")
        output.append(f"- **Current Branch:** {info['branch']}")
        output.append(f"- **Total Commits:** {info['total_commits']}")
        output.append(f"- **First Commit:** {info['first_commit']}")
        output.append(f"- **Last Commit:** {info['last_commit']}\n")
    
    # Contributors
    if data.get('contributors'):
        output.append("## 👥 Contributors\n")
        for contrib in data['contributors']:
            output.append(f"- **{contrib['count']} commits** - {contrib['info']}")
        output.append("")
    
    # Branches
    if data.get('branches'):
        output.append("## 🌿 Branches\n")
        output.append("```")
        for branch in data['branches']:
            output.append(branch)
        output.append("```\n")
    
    # Tags
    if data.get('tags'):
        output.append("## 🏷️ Tags\n")
        for tag in data['tags']:
            output.append(f"- **{tag['name']}** (`{tag['hash']}`) - {tag['date']}")
            if tag.get('subject'):
                output.append(f"  - {tag['subject']}")
        output.append("")
    
    # Pull Requests
    if data.get('pull_requests'):
        output.append("## 🔀 Pull Requests\n")
        
        for pr in data['pull_requests']:
            state_emoji = "✅" if pr['state'] == 'closed' and pr.get('merged_at') else "❌" if pr['state'] == 'closed' else "🔄"
            output.append(f"### {state_emoji} PR #{pr['number']}: {pr['title']}")
            output.append(f"**Author:** {pr['user']['login']}  ")
            output.append(f"**State:** {pr['state']}  ")
            output.append(f"**Created:** {pr['created_at'][:10]}  ")
            
            if pr.get('merged_at'):
                output.append(f"**Merged:** {pr['merged_at'][:10]}  ")
                if pr.get('merged_by'):
                    output.append(f"**Merged By:** {pr['merged_by']['login']}  ")
            
            output.append(f"**Base:** `{pr['base']['ref']}` ← **Head:** `{pr['head']['ref']}`  ")
            
            if pr.get('body'):
                output.append(f"\n**Description:**\n{pr['body'][:300]}{'...' if len(pr['body']) > 300 else ''}\n")
            
            # Reviews
            if pr.get('reviews'):
                output.append("\n**Reviews:**")
                for review in pr['reviews']:
                    state_icon = "✅" if review['state'] == 'APPROVED' else "❌" if review['state'] == 'CHANGES_REQUESTED' else "💬"
                    output.append(f"- {state_icon} **{review['user']['login']}** - {review['state']} ({review['submitted_at'][:10]})")
                    if review.get('body'):
                        output.append(f"  > {review['body'][:150]}{'...' if len(review['body']) > 150 else ''}")
                output.append("")
            
            # Comments
            if pr.get('comments'):
                output.append(f"\n**Review Comments:** ({len(pr['comments'])} comments)")
                for comment in pr['comments'][:5]:  # Limit to first 5
                    output.append(f"- **{comment['user']['login']}** on `{comment.get('path', 'N/A')}`")
                    output.append(f"  > {comment['body'][:100]}{'...' if len(comment['body']) > 100 else ''}")
                if len(pr['comments']) > 5:
                    output.append(f"  *...and {len(pr['comments']) - 5} more comments*")
                output.append("")
            
            output.append("---\n")
    
    # Commit History
    if data.get('commits'):
        output.append("## 📝 Commit History\n")
        
        for i, commit in enumerate(data['commits'], 1):
            merge_icon = "🔀" if commit['is_merge'] else "📝"
            output.append(f"### {merge_icon} Commit #{i}: {commit['subject']}")
            output.append(f"**Hash:** `{commit['hash']}`  ")
            output.append(f"**Author:** {commit['author']} <{commit['email']}>  ")
            output.append(f"**Date:** {commit['date']}  ")
            
            if commit['is_merge']:
                output.append(f"**Merge Commit** - Parents: {', '.join([p[:7] for p in commit['parents']])}  ")
            
            if commit.get('pr_number'):
                output.append(f"**Pull Request:** #{commit['pr_number']}  ")
            
            if commit.get('issue_refs'):
                output.append(f"**References Issues:** {', '.join(['#' + ref for ref in commit['issue_refs']])}  ")
            
            output.append("")
            
            if commit.get('body'):
                output.append("**Message:**")
                output.append("```")
                output.append(commit['body'])
                output.append("```\n")
            
            if commit.get('files'):
                output.append("**Files Changed:**")
                status_map = {'A': '✅ Added', 'M': '📝 Modified', 'D': '❌ Deleted', 'R': '🔄 Renamed'}
                for file in commit['files']:
                    status_icon = status_map.get(file['status'], file['status'])
                    output.append(f"- {status_icon} `{file['path']}`")
                output.append("")
            
            if commit.get('stats'):
                output.append("<details><summary>Statistics</summary>\n")
                output.append("```")
                output.append(commit['stats'])
                output.append("```")
                output.append("</details>\n")
            
            if commit.get('diff'):
                output.append("<details><summary>Full Diff</summary>\n")
                output.append("```diff")
                output.append(commit['diff'])
                output.append("```")
                output.append("</details>\n")
            
            output.append("---\n")
    
    return "\n".join(output)

# ---------------------------------------------------------
# AI-OPTIMIZED FORMAT
# ---------------------------------------------------------

def generate_ai_optimized(data):
    """Generate AI-friendly flat structure."""
    output = []
    
    # Header
    output.append("AI_OPTIMIZED_GIT_HISTORY")
    output.append(f"GENERATION_TIMESTAMP: {time.strftime('%Y-%m-%d_%H:%M:%S')}")
    
    if data.get('repo_info'):
        info = data['repo_info']
        output.append(f"REPO_URL: {info['repo_url']}")
        output.append(f"REPO_OWNER: {info['owner']}")
        output.append(f"REPO_NAME: {info['repo']}")
        output.append(f"CURRENT_BRANCH: {info['branch']}")
        output.append(f"TOTAL_COMMITS: {info['total_commits']}")
        output.append(f"FIRST_COMMIT_DATE: {info['first_commit']}")
        output.append(f"LAST_COMMIT_DATE: {info['last_commit']}")
    
    output.append("")
    
    # Contributors
    if data.get('contributors'):
        output.append("CONTRIBUTORS_START")
        for contrib in data['contributors']:
            output.append(f"CONTRIBUTOR|{contrib['count']}|{contrib['info']}")
        output.append("CONTRIBUTORS_END")
        output.append("")
    
    # Branches
    if data.get('branches'):
        output.append("BRANCHES_START")
        for branch in data['branches']:
            output.append(f"BRANCH|{branch}")
        output.append("BRANCHES_END")
        output.append("")
    
    # Tags
    if data.get('tags'):
        output.append("TAGS_START")
        for tag in data['tags']:
            output.append(f"TAG|{tag['name']}|{tag['hash']}|{tag['date']}|{tag.get('subject', '')}")
        output.append("TAGS_END")
        output.append("")
    
    # Pull Requests
    if data.get('pull_requests'):
        output.append("PULL_REQUESTS_START")
        
        for pr in data['pull_requests']:
            output.append(f"PR_START|{pr['number']}")
            output.append(f"PR_TITLE|{pr['title']}")
            output.append(f"PR_AUTHOR|{pr['user']['login']}")
            output.append(f"PR_STATE|{pr['state']}")
            output.append(f"PR_CREATED|{pr['created_at']}")
            output.append(f"PR_BASE|{pr['base']['ref']}")
            output.append(f"PR_HEAD|{pr['head']['ref']}")
            
            if pr.get('merged_at'):
                output.append(f"PR_MERGED|{pr['merged_at']}")
                if pr.get('merged_by'):
                    output.append(f"PR_MERGED_BY|{pr['merged_by']['login']}")
            
            if pr.get('body'):
                output.append(f"PR_BODY_START")
                output.append(pr['body'])
                output.append(f"PR_BODY_END")
            
            # Reviews
            if pr.get('reviews'):
                output.append("PR_REVIEWS_START")
                for review in pr['reviews']:
                    output.append(f"REVIEW|{review['user']['login']}|{review['state']}|{review['submitted_at']}")
                    if review.get('body'):
                        output.append(f"REVIEW_BODY|{review['body']}")
                output.append("PR_REVIEWS_END")
            
            # Comments
            if pr.get('comments'):
                output.append("PR_COMMENTS_START")
                for comment in pr['comments']:
                    output.append(f"COMMENT|{comment['user']['login']}|{comment.get('path', '')}|{comment.get('line', '')}")
                    output.append(f"COMMENT_BODY|{comment['body']}")
                output.append("PR_COMMENTS_END")
            
            output.append(f"PR_END|{pr['number']}")
            output.append("")
        
        output.append("PULL_REQUESTS_END")
        output.append("")
    
    # Commits
    if data.get('commits'):
        output.append("COMMITS_START")
        
        for commit in data['commits']:
            output.append(f"COMMIT_START|{commit['hash']}")
            output.append(f"COMMIT_SHORT_HASH|{commit['short_hash']}")
            output.append(f"COMMIT_AUTHOR|{commit['author']}")
            output.append(f"COMMIT_EMAIL|{commit['email']}")
            output.append(f"COMMIT_DATE|{commit['date']}")
            output.append(f"COMMIT_SUBJECT|{commit['subject']}")
            output.append(f"COMMIT_IS_MERGE|{commit['is_merge']}")
            
            if commit['is_merge']:
                output.append(f"COMMIT_PARENTS|{','.join(commit['parents'])}")
            
            if commit.get('pr_number'):
                output.append(f"COMMIT_PR|{commit['pr_number']}")
            
            if commit.get('issue_refs'):
                output.append(f"COMMIT_ISSUES|{','.join(commit['issue_refs'])}")
            
            if commit.get('body'):
                output.append("COMMIT_BODY_START")
                output.append(commit['body'])
                output.append("COMMIT_BODY_END")
            
            if commit.get('files'):
                output.append("COMMIT_FILES_START")
                for file in commit['files']:
                    output.append(f"FILE|{file['status']}|{file['path']}")
                output.append("COMMIT_FILES_END")
            
            if commit.get('stats'):
                output.append("COMMIT_STATS_START")
                output.append(commit['stats'])
                output.append("COMMIT_STATS_END")
            
            if commit.get('diff'):
                output.append("COMMIT_DIFF_START")
                output.append(commit['diff'])
                output.append("COMMIT_DIFF_END")
            
            output.append(f"COMMIT_END|{commit['hash']}")
            output.append("")
        
        output.append("COMMITS_END")
    
    return "\n".join(output)

# ---------------------------------------------------------
# CLI INTERFACE
# ---------------------------------------------------------

def interactive_menu():
    """Interactive CLI menu for selecting export options."""
    print("\n" + "="*60)
    print("  🔍 Pull Logs - GitHub Edition")
    print("  Interactive Export Configuration")
    print("="*60 + "\n")
    
    # Check for git repo
    if not os.path.exists('.git'):
        print("❌ Error: Not a git repository!")
        print("   Run this script from the root of your git project.\n")
        return None
    
    # Get repo info
    repo_info = get_repo_info()
    print(f"📦 Repository: {repo_info['owner']}/{repo_info['repo']}")
    print(f"🌿 Branch: {repo_info['branch']}")
    print(f"📊 Total Commits: {repo_info['total_commits']}\n")
    
    # Check GitHub token
    if GITHUB_TOKEN:
        print(f"✅ GitHub token detected (for PR data)\n")
    else:
        print(f"⚠️  No GitHub token (PR data will be skipped)")
        print(f"   Set GITHUB_TOKEN environment variable for full features\n")
    
    print("="*60)
    print("  Select Data to Export")
    print("="*60 + "\n")
    
    # Module selection
    selected_modules = {}
    
    print("Select modules to export (y/n):\n")
    
    for i, (key, description) in enumerate(AVAILABLE_MODULES.items(), 1):
        # Skip GitHub API modules if no token
        if key in ['pr_data', 'pr_reviews', 'pr_comments'] and not GITHUB_TOKEN:
            selected_modules[key] = False
            continue
        
        # Default selections
        default = 'y' if key not in ['commit_diffs'] else 'n'
        
        response = input(f"  [{i:2d}] {description}\n       Export? (Y/n) [{default}]: ").strip().lower()
        
        if response == '':
            response = default
        
        selected_modules[key] = response == 'y'
        print()
    
    # Commit limit
    print("="*60)
    limit_response = input("Limit commits? (Enter number or press Enter for all): ").strip()
    commit_limit = int(limit_response) if limit_response.isdigit() else None
    
    if commit_limit:
        print(f"✅ Will export last {commit_limit} commits\n")
    else:
        print(f"✅ Will export all commits\n")
    
    # Output format selection
    print("="*60)
    print("  Select Output Format")
    print("="*60 + "\n")
    
    print("1. Human-readable only")
    print("2. AI-optimized only")
    print("3. Both formats (recommended)\n")
    
    format_choice = input("Choose format (1/2/3) [3]: ").strip() or '3'
    
    output_formats = {
        '1': ['human'],
        '2': ['ai'],
        '3': ['human', 'ai']
    }
    
    selected_formats = output_formats.get(format_choice, ['human', 'ai'])
    
    print()
    
    return {
        'modules': selected_modules,
        'commit_limit': commit_limit,
        'formats': selected_formats,
        'repo_info': repo_info
    }

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Pull Logs - GitHub Edition: Export Git & GitHub history',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pack_github-logs.py                    # Interactive mode
  python pack_github-logs.py --all              # Export everything
  python pack_github-logs.py --all --ai-only    # Export all data, AI format only
  python pack_github-logs.py --commits --prs    # Export only commits and PRs
  python pack_github-logs.py --limit 100        # Export last 100 commits only

For more info: https://github.com/xBlynd/pull-logs-github
        """
    )
    
    # Quick options
    parser.add_argument('--all', action='store_true',
                        help='Export all available data')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Force interactive mode (default if no args)')
    
    # Individual modules
    parser.add_argument('--repo-info', action='store_true',
                        help='Include repository information')
    parser.add_argument('--contributors', action='store_true',
                        help='Include contributors')
    parser.add_argument('--branches', action='store_true',
                        help='Include branches')
    parser.add_argument('--tags', action='store_true',
                        help='Include tags')
    parser.add_argument('--commits', action='store_true',
                        help='Include commit history')
    parser.add_argument('--commit-stats', action='store_true',
                        help='Include commit statistics')
    parser.add_argument('--commit-files', action='store_true',
                        help='Include commit file changes')
    parser.add_argument('--commit-diffs', action='store_true',
                        help='Include full commit diffs (large)')
    parser.add_argument('--prs', action='store_true',
                        help='Include pull requests (requires token)')
    parser.add_argument('--pr-reviews', action='store_true',
                        help='Include PR reviews (requires token)')
    parser.add_argument('--pr-comments', action='store_true',
                        help='Include PR comments (requires token)')
    parser.add_argument('--issues', action='store_true',
                        help='Include issue references')
    
    # Limits
    parser.add_argument('--limit', type=int, metavar='N',
                        help='Limit number of commits to export')
    
    # Output formats
    parser.add_argument('--human-only', action='store_true',
                        help='Generate only human-readable format')
    parser.add_argument('--ai-only', action='store_true',
                        help='Generate only AI-optimized format')
    
    # Output files
    parser.add_argument('--output-human', default=OUTPUT_HUMAN,
                        help=f'Human output filename (default: {OUTPUT_HUMAN})')
    parser.add_argument('--output-ai', default=OUTPUT_AI,
                        help=f'AI output filename (default: {OUTPUT_AI})')
    
    return parser.parse_args()

def build_config_from_args(args):
    """Build export configuration from command-line arguments."""
    
    # Determine if any specific modules were selected
    specific_modules = any([
        args.repo_info, args.contributors, args.branches, args.tags,
        args.commits, args.commit_stats, args.commit_files, args.commit_diffs,
        args.prs, args.pr_reviews, args.pr_comments, args.issues
    ])
    
    # If --all or no specific modules, enable all (except diffs by default)
    if args.all or not specific_modules:
        modules = {key: True for key in AVAILABLE_MODULES.keys()}
        if not args.all:
            modules['commit_diffs'] = False  # Don't include diffs by default
    else:
        # Enable only selected modules
        modules = {
            'repo_info': args.repo_info,
            'contributors': args.contributors,
            'branches': args.branches,
            'tags': args.tags,
            'commits': args.commits or args.all,
            'commit_stats': args.commit_stats,
            'commit_files': args.commit_files,
            'commit_diffs': args.commit_diffs,
            'pr_data': args.prs,
            'pr_reviews': args.pr_reviews,
            'pr_comments': args.pr_comments,
            'issue_references': args.issues,
        }
    
    # Determine output formats
    if args.human_only:
        formats = ['human']
    elif args.ai_only:
        formats = ['ai']
    else:
        formats = ['human', 'ai']
    
    return {
        'modules': modules,
        'commit_limit': args.limit,
        'formats': formats,
        'output_files': {
            'human': args.output_human,
            'ai': args.output_ai
        }
    }

# ---------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------

def main():
    args = parse_arguments()
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("❌ Error: Not a git repository!")
        print("   Run this script from the root of your git project.")
        return 1
    
    # Determine mode: interactive or command-line
    # Check if any flags were passed (excluding defaults)
    has_flags = any([
        args.all, args.repo_info, args.contributors, args.branches,
        args.tags, args.commits, args.commit_stats, args.commit_files,
        args.commit_diffs, args.prs, args.pr_reviews, args.pr_comments,
        args.issues, args.limit, args.human_only, args.ai_only
    ])
    
    if args.interactive or not has_flags:
        # Interactive mode
        config = interactive_menu()
        if not config:
            return 1
        
        output_files = {
            'human': OUTPUT_HUMAN,
            'ai': OUTPUT_AI
        }
    else:
        # Command-line mode
        config = build_config_from_args(args)
        config['repo_info'] = get_repo_info()
        output_files = config.get('output_files', {
            'human': OUTPUT_HUMAN,
            'ai': OUTPUT_AI
        })
    
    print("\n" + "="*60)
    print("  🚀 Starting Export")
    print("="*60 + "\n")
    
    # Collect all data based on configuration
    data = {}
    
    # Repository info
    if config['modules'].get('repo_info', True):
        print("📊 Gathering repository info...")
        data['repo_info'] = config.get('repo_info') or get_repo_info()
    
    # Contributors
    if config['modules'].get('contributors'):
        print("👥 Gathering contributors...")
        data['contributors'] = get_contributors()
    
    # Branches
    if config['modules'].get('branches'):
        print("🌿 Gathering branches...")
        data['branches'] = get_branches()
    
    # Tags
    if config['modules'].get('tags'):
        print("🏷️  Gathering tags...")
        data['tags'] = get_tags()
    
    # Commits
    if config['modules'].get('commits'):
        limit = config.get('commit_limit')
        print(f"📝 Gathering commits{f' (limit: {limit})' if limit else ' (all)'}...")
        commit_hashes = get_all_commits(limit=limit)
        commits = []
        
        total = len(commit_hashes)
        for i, commit_hash in enumerate(commit_hashes, 1):
            if commit_hash:
                print(f"   Processing commit {i}/{total}...", end='\r')
                commit_data = get_commit_details(
                    commit_hash,
                    include_stats=config['modules'].get('commit_stats', True),
                    include_files=config['modules'].get('commit_files', True),
                    include_diff=config['modules'].get('commit_diffs', False)
                )
                commits.append(commit_data)
        
        data['commits'] = commits
        print(f"   ✅ Processed {len(commits)} commits" + " " * 20)
    
    # GitHub API data
    if HAS_REQUESTS and GITHUB_TOKEN and data.get('repo_info'):
        owner = data['repo_info']['owner']
        repo = data['repo_info']['repo']
        
        if owner and repo:
            # Pull Requests
            if config['modules'].get('pr_data'):
                print("🔀 Gathering pull requests from GitHub...")
                prs = get_pull_requests(owner, repo)
                
                # Get reviews and comments if requested
                if config['modules'].get('pr_reviews') or config['modules'].get('pr_comments'):
                    for i, pr in enumerate(prs, 1):
                        print(f"   Processing PR #{pr['number']} ({i}/{len(prs)})...", end='\r')
                        
                        if config['modules'].get('pr_reviews'):
                            pr['reviews'] = get_pr_reviews(owner, repo, pr['number'])
                        
                        if config['modules'].get('pr_comments'):
                            pr['comments'] = get_pr_comments(owner, repo, pr['number'])
                    
                    print(f"   ✅ Processed {len(prs)} pull requests" + " " * 20)
                
                data['pull_requests'] = prs
    
    # Generate outputs
    print("\n" + "="*60)
    print("  📄 Generating Output Files")
    print("="*60 + "\n")
    
    if 'human' in config['formats']:
        print("📘 Generating human-readable format...")
        human_content = generate_human_readable(data)
        with open(output_files['human'], 'w', encoding='utf-8') as f:
            f.write(human_content)
        print(f"   ✅ Saved: {output_files['human']} ({len(human_content):,} chars)")
    
    if 'ai' in config['formats']:
        print("🤖 Generating AI-optimized format...")
        ai_content = generate_ai_optimized(data)
        with open(output_files['ai'], 'w', encoding='utf-8') as f:
            f.write(ai_content)
        print(f"   ✅ Saved: {output_files['ai']} ({len(ai_content):,} chars)")
    
    print("\n✨ Export complete!\n")
    
    if not GITHUB_TOKEN and any(config['modules'].get(k) for k in ['pr_data', 'pr_reviews', 'pr_comments']):
        print("💡 Tip: Set GITHUB_TOKEN environment variable for PR data:")
        print("   export GITHUB_TOKEN='your_token_here'\n")
    
    return 0

if __name__ == "__main__":
    exit(main())
