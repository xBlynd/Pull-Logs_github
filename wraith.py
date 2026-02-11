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
import requests
import argparse
from datetime import datetime

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

# [Previous helper functions remain the same: run_git_command, get_repo_info, etc.]
# ... [Include all the helper functions from before]

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
    if args.interactive or (not any(vars(args).values()) or all(v is None or v is False for v in vars(args).values() if not isinstance(v, str))):
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
    if GITHUB_TOKEN and data.get('repo_info'):
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
