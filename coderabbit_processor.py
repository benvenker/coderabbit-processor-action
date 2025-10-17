#!/usr/bin/env python3
"""
CodeRabbit Review Processor
Fetches and formats CodeRabbit reviews for AI agent consumption.

Reduces token usage by 75% while maintaining all actionable content.
"""

import argparse
import json
import re
import subprocess
import sys
from typing import Dict, List, Optional, Set, Tuple


def fetch_review_threads(pr_number: int, repo: str) -> dict:
    """Fetch review threads via GitHub GraphQL using gh CLI."""
    query = """
    query($owner:String!,$repo:String!,$number:Int!){
      repository(owner:$owner,name:$repo){
        pullRequest(number:$number){
          number
          title
          headRefName
          reviewThreads(first:100){
            nodes{
              id
              isResolved
              comments(first:20){
                nodes{
                  id
                  databaseId
                  author{login}
                  body
                  url
                  path
                  line
              isOutdated
                }
              }
            }
          }
        }
      }
    }
    """
    
    owner, repo_name = repo.split('/')
    
    try:
        result = subprocess.run(
            ['gh', 'api', 'graphql',
             '-f', f'query={query}',
             '-F', f'owner={owner}',
             '-F', f'repo={repo_name}',
             '-F', f'number={pr_number}'],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching from GitHub: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing GitHub response: {e}", file=sys.stderr)
        sys.exit(1)


def filter_unresolved(threads: list) -> list:
    """Filter to only unresolved threads."""
    return [t for t in threads if not t.get('isResolved', False)]


def filter_by_user(threads: list, user: str = 'coderabbitai') -> list:
    """Filter to only threads from specified user."""
    filtered = []
    for thread in threads:
        comments = thread.get('comments', {}).get('nodes', [])
        if comments and comments[0].get('author', {}).get('login') == user:
            filtered.append(thread)
    return filtered


def filter_outdated(threads: list, exclude_outdated: bool = True) -> list:
    """Filter out outdated threads if requested."""
    if not exclude_outdated:
        return threads

    filtered = []
    for thread in threads:
        comments = thread.get('comments', {}).get('nodes', [])
        if comments and not comments[0].get('isOutdated', False):
            filtered.append(thread)
    return filtered


def extract_agent_prompt(body: str) -> Optional[str]:
    """Extract 'Prompt for AI Agents' or 'AI Agent Instructions' block if present."""
    # Try different patterns
    patterns = [
        r'<!--\s*Prompt for AI Agents\s*-->(.*?)<!--\s*/Prompt\s*-->',
        r'###\s*AI Agent Instructions.*?\n(.*?)(?=\n###|\n##|\Z)',
        r'###\s*Prompt for AI Agents.*?\n(.*?)(?=\n###|\n##|\Z)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None


def clean_comment_body(body: str) -> str:
    """Remove markdown artifacts, HTML comments, and cruft."""
    # Remove HTML comments
    body = re.sub(r'<!--.*?-->', '', body, flags=re.DOTALL)
    
    # Remove HTML tags like <details>, <summary>, <blockquote>
    body = re.sub(r'</?(?:details|summary|blockquote).*?>', '', body, flags=re.DOTALL)
    
    # Remove review_comment_end markers
    body = re.sub(r'<!--\s*review_comment_end\s*-->', '', body)
    
    # Collapse multiple blank lines
    body = re.sub(r'\n{3,}', '\n\n', body)
    
    return body.strip()


def extract_severity(body: str) -> dict:
    """Extract CodeRabbit's severity and category from comment body."""
    pattern = r'^_[^\s]+ ([^_]+)_\s*\|\s*_[^\s]+ ([^_]+)_'
    match = re.match(pattern, body, re.MULTILINE)

    if not match:
        return {
            'category': 'Unknown',
            'severity': 'Unknown',
            'priority': infer_priority_fallback(body),
            'parsed': False
        }

    category = match.group(1).strip()
    severity = match.group(2).strip()

    severity_map = {
        'Critical': 'P0',
        'Major': 'P1',
        'Minor': 'P2',
        'Trivial': 'P3'
    }

    return {
        'category': category,
        'severity': severity,
        'priority': severity_map.get(severity, 'P3'),
        'parsed': True
    }


def infer_priority_fallback(body: str) -> str:
    """Fallback heuristic if CodeRabbit format not found."""
    body_lower = body.lower()

    if any(word in body_lower for word in [
        'critical', 'security', 'vulnerable', 'broken',
        'injection', 'xss', 'crash', 'data loss', 'severe'
    ]):
        return 'P0'

    if any(word in body_lower for word in [
        'type safety', 'error handling', 'important',
        'bug', 'incorrect', 'validation', 'async', 'race condition'
    ]):
        return 'P1'

    if any(word in body_lower for word in [
        'style', 'documentation', 'refactor',
        'naming', 'comment', 'readability', 'format'
    ]):
        return 'P2'

    return 'P3'


def extract_code_graph(raw_data: dict, relevant_files: Set[str]) -> dict:
    """Extract code graph filtered to relevant files only."""
    # This would parse the code graph from raw CodeRabbit data
    # For now, return empty dict as we'll implement based on actual structure
    return {}


def condense_learnings(raw_data: dict) -> List[str]:
    """Extract learning rules without metadata."""
    # This would parse learnings from raw CodeRabbit data
    # For now, return empty list as we'll implement based on actual structure
    return []


def summarize_files(raw_data: dict) -> dict:
    """Create file summary with counts by category."""
    # This would parse files from raw CodeRabbit data
    return {
        'total': 0,
        'categories': {}
    }


def detect_patterns(threads: list) -> List[str]:
    """Identify recurring issues suggesting tool adoption."""
    patterns = []
    
    # Count by category
    markdown_issues = sum(1 for t in threads if 'markdown' in t.get('suggestion', '').lower())
    type_safety_issues = sum(1 for t in threads 
                            if 'any' in t.get('suggestion', '') or 'type' in t.get('suggestion', '').lower())
    formatting_issues = sum(1 for t in threads 
                           if 'prettier' in t.get('suggestion', '').lower() or 'format' in t.get('suggestion', '').lower())
    
    if markdown_issues >= 3:
        patterns.append(f"Markdown formatting ({markdown_issues} occurrences) → Consider installing markdownlint")
    
    if type_safety_issues >= 4:
        patterns.append(f"Type safety casts ({type_safety_issues} occurrences) → Review TypeScript strict mode")
    
    if formatting_issues >= 3:
        patterns.append(f"Code formatting ({formatting_issues} occurrences) → Configure Prettier")
    
    return patterns


def estimate_tokens(data: dict) -> int:
    """Rough token estimate (4 chars ≈ 1 token)."""
    return len(json.dumps(data)) // 4


def process_threads(raw_data: dict, include_resolved: bool = False,
                    include_outdated: bool = False) -> Tuple[List[dict], dict]:
    """Process raw GraphQL data into clean thread list and metadata."""
    pr_data = raw_data['data']['repository']['pullRequest']
    threads = pr_data['reviewThreads']['nodes']
    
    # Filter
    if not include_resolved:
        threads = filter_unresolved(threads)
    threads = filter_by_user(threads)
    if not include_outdated:
        threads = filter_outdated(threads, exclude_outdated=True)
    
    # Process each thread
    cleaned_threads = []
    for thread in threads:
        comments = thread.get('comments', {}).get('nodes', [])
        if not comments:
            continue
        
        first_comment = comments[0]
        body = first_comment.get('body', '')
        severity_info = extract_severity(body)
        
        cleaned_thread = {
            'thread_id': thread['id'],
            'comment_id': first_comment['id'],
            'database_id': first_comment.get('databaseId'),
            'file': first_comment.get('path'),
            'line': first_comment.get('line'),
            'url': first_comment.get('url'),
            'suggestion': clean_comment_body(body),
            'agent_prompt': extract_agent_prompt(body),
            'priority': severity_info['priority'],
            'category': severity_info['category'],
            'severity': severity_info['severity'],
            'severity_parsed': severity_info['parsed'],
            'is_outdated': first_comment.get('isOutdated', False)
        }
        
        cleaned_threads.append(cleaned_thread)
    
    # Sort by priority
    priority_order = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3}
    cleaned_threads.sort(key=lambda t: priority_order.get(t['priority'], 99))
    
    # Metadata
    metadata = {
        'pr_number': pr_data['number'],
        'pr_title': pr_data['title'],
        'branch': pr_data['headRefName'],
        'total_threads': len(cleaned_threads),
        'patterns': detect_patterns(cleaned_threads)
    }
    
    return cleaned_threads, metadata


def format_as_markdown(threads: List[dict], metadata: dict, repo: str) -> str:
    """Format threads as agent-optimized markdown."""
    output = []
    
    # Header
    output.append(f"# CodeRabbit Review: PR #{metadata['pr_number']}\n")
    output.append(f"**Repository:** {repo}")
    output.append(f"**Branch:** {metadata['branch']}")
    output.append(f"**PR Title:** {metadata['pr_title']}")
    output.append(f"**Unresolved Threads:** {metadata['total_threads']}\n")
    
    # Stats by priority
    priority_counts = {}
    file_counts = {}
    for t in threads:
        priority_counts[t['priority']] = priority_counts.get(t['priority'], 0) + 1
        if t['file']:
            file_counts[t['file']] = file_counts.get(t['file'], 0) + 1
    
    output.append("**By Priority:**")
    for priority in ['P0', 'P1', 'P2', 'P3']:
        count = priority_counts.get(priority, 0)
        if count > 0:
            label = {'P0': 'Critical', 'P1': 'Important', 'P2': 'Style', 'P3': 'Optional'}[priority]
            output.append(f"- {priority} ({label}): {count} threads")
    
    output.append("\n---\n")
    
    # Threads
    for i, thread in enumerate(threads, 1):
        # Extract title from first line of suggestion
        first_line = thread['suggestion'].split('\n')[0]
        title = first_line[:60] + '...' if len(first_line) > 60 else first_line
        title = re.sub(r'[*`#]', '', title).strip()
        
        if thread.get('severity_parsed'):
            output.append(f"## Thread {i}: {title} [{thread['category']} - {thread['severity']}]")
        else:
            output.append(f"## Thread {i}: {title} [{thread['priority']}]")
        output.append("")
        
        if thread['file']:
            output.append(f"**File:** `{thread['file']}`")
        if thread['line']:
            output.append(f"**Lines:** {thread['line']}")
        if thread['url']:
            output.append(f"**URL:** {thread['url']}")
        if thread['database_id']:
            output.append(f"**Reply To (database_id):** {thread['database_id']}")
        if thread.get('is_outdated'):
            output.append("**Outdated:** Yes")
        output.append("")
        
        # Agent instructions if present
        if thread['agent_prompt']:
            output.append("### AI Agent Instructions (Priority)")
            output.append(thread['agent_prompt'])
            output.append("")
        
        # CodeRabbit feedback
        output.append("### CodeRabbit's Feedback")
        output.append(thread['suggestion'])
        output.append("")
        output.append("---\n")
    
    # Summary
    output.append("## Summary Statistics\n")
    
    output.append("**By Priority:**")
    for priority in ['P0', 'P1', 'P2', 'P3']:
        count = priority_counts.get(priority, 0)
        if count > 0:
            label = {'P0': 'Critical', 'P1': 'Important', 'P2': 'Style', 'P3': 'Optional'}[priority]
            output.append(f"- {priority} ({label}): {count} threads")
    
    if file_counts:
        output.append("\n**Top Files:**")
        sorted_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for file, count in sorted_files:
            output.append(f"- {file}: {count} threads")
    
    if metadata['patterns']:
        output.append("\n**Recurring Patterns Detected:**")
        for pattern in metadata['patterns']:
            output.append(f"- {pattern}")
    
    # Token estimate
    full_text = '\n'.join(output)
    tokens = len(full_text) // 4
    output.append(f"\n**Token Estimate:** ~{tokens:,} tokens")
    
    return '\n'.join(output)


def format_as_json(threads: List[dict], metadata: dict) -> str:
    """Format threads as JSON."""
    return json.dumps({
        'metadata': metadata,
        'threads': threads
    }, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description='Process CodeRabbit reviews for AI agent consumption'
    )
    
    # Input source
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--pr', type=int, help='PR number to fetch')
    group.add_argument('--input', help='Existing JSON file to process')
    
    # Output
    parser.add_argument('--output', required=True, help='Output file path')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown',
                       help='Output format')
    
    # Options
    parser.add_argument('--repo', default='benvenker/localvantage',
                       help='Repository (owner/repo)')
    parser.add_argument('--include-resolved', action='store_true',
                       help='Include resolved threads')
    parser.add_argument('--include-outdated', action='store_true',
                       help='Include outdated comments')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show statistics only')
    parser.add_argument('--verbose', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Fetch or load data
    if args.pr:
        if args.verbose:
            print(f"Fetching PR #{args.pr} from {args.repo}...")
        raw_data = fetch_review_threads(args.pr, args.repo)
    else:
        if args.verbose:
            print(f"Loading from {args.input}...")
        with open(args.input, 'r') as f:
            raw_data = json.load(f)
    
    # Process
    threads, metadata = process_threads(
        raw_data,
        args.include_resolved,
        args.include_outdated
    )
    
    if args.verbose:
        print(f"Processed {len(threads)} unresolved threads")
        priority_counts = {}
        for t in threads:
            priority_counts[t['priority']] = priority_counts.get(t['priority'], 0) + 1
        for p in ['P0', 'P1', 'P2', 'P3']:
            if p in priority_counts:
                print(f"  {p}: {priority_counts[p]}")
    
    # Dry run
    if args.dry_run:
        print(f"\nDry run - would process {len(threads)} threads:")
        print(f"  Output: {args.output}")
        print(f"  Format: {args.format}")
        return
    
    # Format output
    if args.format == 'markdown':
        output = format_as_markdown(threads, metadata, args.repo)
    else:
        output = format_as_json(threads, metadata)
    
    # Write
    with open(args.output, 'w') as f:
        f.write(output)
    
    if args.verbose:
        tokens = estimate_tokens({'output': output})
        print(f"✓ Wrote {len(output)} bytes (~{tokens:,} tokens) to {args.output}")


if __name__ == '__main__':
    main()

