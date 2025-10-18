# Agent Development Guide

This document provides context for AI agents (or developers) working on the CodeRabbit Processor Action project.

## Project Overview

**CodeRabbit Codex Processor Action** is a GitHub Action available in two versions:

- **v2 (Full Pipeline)**: Complete end-to-end automation - processes CodeRabbit reviews with Codex, applies fixes, and updates PRs
- **v1 (Processor Only)**: Fetches and processes CodeRabbit review threads into agent-optimized markdown (80% token reduction)

**Key Value**:
- v2: Turnkey automation from review → fixes → PR updates
- v1: 80% token reduction (71K → 14K tokens) for custom AI workflows

## Architecture

### v2 (Full Pipeline) Components

1. **`action.yml`** - Main composite action (v2)
   - Orchestrates complete workflow
   - Handles environment setup (Node, Go, npm)
   - Calls processor, Codex, git operations, PR commenting
   - ~215 lines

2. **`processor/action.yml`** - Review processor sub-action (v1)
   - Runs `coderabbit_processor.py`
   - Outputs threads-count and token-estimate
   - Can be used standalone as @v1

3. **`codex-prompt-template.sh`** - Codex prompt generator
   - Parameterized prompt template
   - Supports multiple project managers
   - Environment variable substitution

4. **`coderabbit_processor.py`** - Python processor script
   - Uses GitHub GraphQL API (via `gh` CLI)
   - Zero external dependencies (stdlib only)
   - ~480 lines of code

5. **`tests/test_processor.py`** - Test suite
   - Unit tests for core functions
   - No dependencies (simple assertions)
   - Run via: `python3 tests/test_processor.py`

### v1 (Processor Only) Components

Same as items 2, 4, and 5 above - focused on just the processor functionality.

### Key Functions

```python
fetch_review_threads(repo, pr_number)
  → Fetches raw GraphQL data from GitHub

filter_unresolved(threads)
  → Filters to only unresolved conversations

filter_outdated(threads, exclude_outdated=True)
  → Filters out outdated comments (default)

extract_severity(body)
  → Parses CodeRabbit's severity labels (Critical/Major/Minor/Trivial)
  → Maps to P0/P1/P2/P3 priorities
  → Falls back to keyword heuristics if format not found

process_threads(raw_data, include_resolved, include_outdated)
  → Orchestrates filtering, cleaning, and priority assignment

format_as_markdown(threads, metadata)
  → Outputs agent-optimized markdown
  → Includes thread_id for replying to conversations
```

## Features

### 1. Severity Parsing (New in v1.1.0)

CodeRabbit embeds severity in comment bodies:
```
_⚠️ Potential issue_ | _🟠 Major_

**Description here**
```

We parse this format and map to priorities:
- **Critical** → P0
- **Major** → P1
- **Minor** → P2
- **Trivial** → P3

**Fallback**: If format not found, uses keyword-based heuristics (security → P0, bug → P1, etc.)

### 2. Outdated Filtering (New in v1.1.0)

GitHub marks comments as "outdated" when code changes make them irrelevant. We filter these by default to reduce noise.

**Flag**: `--include-outdated` / `include-outdated: true` to keep them

### 3. Priority Inference

Every thread gets a P0-P3 priority for sorting:
- **P0**: Critical issues (security, crashes, data loss)
- **P1**: Important (bugs, type safety, validation)
- **P2**: Style/refactoring
- **P3**: Optional improvements

### 4. Thread ID for Replies

The markdown output includes `Thread ID (for replies)` which is the GraphQL `thread['id']` needed for the `addPullRequestReviewComment` mutation:

```graphql
mutation {
  addPullRequestReviewComment(input: {
    pullRequestReviewThreadId: "PR_kwDOABCDEF4ABCDEFGH",
    body: "Your reply here"
  }) {
    comment {
      id
      body
    }
  }
}
```

**Important**: Use `thread_id`, not `database_id` or `comment_id` for replying to threads.

### 5. Pattern Detection

Identifies recurring issues across threads for systematic fixes.

## Development Workflow

### Local Development

1. **Make changes** to `coderabbit_processor.py`

2. **Run tests locally**:
   ```bash
   python3 tests/test_processor.py
   ```

3. **Test with real data** (requires `gh` CLI):
   ```bash
   python3 coderabbit_processor.py \
     --pr-number 123 \
     --repo owner/repo \
     --output-file test_output.md
   ```

4. **Check test fixtures**:
   - `fixtures/review_threads.json` - Example GraphQL output from CodeRabbit

### Testing Strategy

**Current Approach**: Simple unit tests with no dependencies
- Tests core functions in isolation
- Uses realistic test data
- Fast execution (~0.5s)

**Test Coverage**:
- ✅ Severity parsing (valid format, fallback, all severities)
- ✅ Outdated filtering (exclude/include modes)
- ✅ Priority fallback (keyword matching)
- ✅ Comment cleaning (HTML removal)

**Running Tests**:
```bash
# Local
python3 tests/test_processor.py

# Expected output:
# ✓ extract_severity: parses category
# ✓ extract_severity: parses severity
# ... (21 tests)
# Tests: 21/21 passed
```

### CI/CD

**GitHub Actions Workflow**: `.github/workflows/test.yml`

Runs on:
- Every push to `main`
- All pull requests

Steps:
1. Checkout code
2. Setup Python 3.x
3. Run test suite
4. Fail CI if any tests fail

**Check Status**: See the Actions tab on GitHub

## Release Process

### Version Strategy

We use semantic versioning: `vMAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes (e.g., changing input names)
- **MINOR**: New features (e.g., adding `--include-outdated`)
- **PATCH**: Bug fixes

### Current Versions

- **v2.0.0** (latest) - Full pipeline with Codex integration
- **v1.1.0** - Severity parsing + outdated filtering + tests (processor only)
- **v1.0.0** - Initial release (processor only)
- **v2** (rolling) - Always points to latest v2.x.x
- **v1** (rolling) - Always points to latest v1.x.x

### Creating a Release

```bash
# 1. Ensure all changes are committed and pushed
git status

# 2. Create version tag
git tag -a v1.2.0 -m "v1.2.0: Brief description of changes"

# 3. Push the tag
git push origin v1.2.0

# 4. Update the rolling v1 tag (so @v1 users get updates)
git tag -fa v1 -m "Update v1 to v1.2.0"
git push origin v1 --force

# 5. Create GitHub Release (optional, but recommended)
# Go to: https://github.com/benvenker/coderabbit-processor-action/releases/new
# - Tag: v1.2.0
# - Title: v1.2.0: Brief description
# - Description: Detailed changelog
```

### Usage in Other Projects

Users can reference the action:
```yaml
- uses: benvenker/coderabbit-processor-action@v1      # Gets latest v1.x.x
- uses: benvenker/coderabbit-processor-action@v1.1.0  # Specific version
- uses: benvenker/coderabbit-processor-action@main    # Latest commit (not recommended)
```

## Repository Organization

```
/
├── action.yml                    # v2: Main composite action (full pipeline)
├── processor/
│   └── action.yml                # v1: Review processor sub-action
├── codex-prompt-template.sh      # v2: Codex prompt generator
├── coderabbit_processor.py       # Core processor script
├── tests/
│   └── test_processor.py         # Test suite
├── fixtures/
│   └── review_threads.json       # Example GraphQL data
├── examples/
│   ├── claude-workflow.yml       # Example usage with Claude
│   └── codex-workflow.yml        # Example usage with Codex
├── .github/
│   └── workflows/
│       └── test.yml              # CI workflow
├── README.md                     # User documentation (v1 & v2)
├── SETUP.md                      # Setup guide
├── AGENTS.md                     # This file
└── LICENSE
```

**Key Paths**:
- **v2 users**: Use `benvenker/coderabbit-processor-action@v2` (action.yml)
- **v1 users**: Use `benvenker/coderabbit-processor-action@v1` (processor/action.yml or old action.yml)

## Key Design Decisions

### v2-Specific Decisions

#### 1. Composite Action Pattern

**Why**: Composite actions allow us to orchestrate multiple steps while remaining shareable and reusable across repositories without requiring custom Docker images or JavaScript.

**Benefits**:
- No build step required
- Fast execution (no image pull)
- Easy to debug (all steps visible in workflow logs)
- Supports calling other actions and shell scripts

#### 2. Nested Action Structure (processor/ subdirectory)

**Why**: Maintaining v1 as a standalone sub-action preserves backward compatibility while allowing v2 to build on top.

**Approach**:
- v1 users continue using `@v1` tag (points to processor/)
- v2 users use `@v2` tag (points to root action.yml)
- Both versions maintained independently

**Limitation**: Composite actions can't call other composite actions via `uses:`, so we inline the processor logic in v2's action.yml instead of calling `processor/action.yml`.

#### 3. Template-Based Prompt Generation

**Why**: Different projects have different needs (project managers, file paths, custom instructions).

**Approach**:
- Shell script template with environment variable substitution
- Supports Beads, Linear, GitHub Issues, or no project manager
- Users can append custom instructions
- Keeps prompt logic separate from action orchestration

#### 4. Optional Environment Setup

**Why**: Not all projects need Node, Go, or npm - make it configurable.

**Inputs**:
- `npm-ci`: Install npm dependencies if needed
- `install-go-tools`: Install Go/Beads if needed
- `node-version`: Specify Node version

**Default**: Skip setup (fastest execution)

### v1 Design Decisions (Processor Core)

#### 1. No External Dependencies

**Why**: GitHub Actions should be lightweight and reliable. Using only stdlib + `gh` CLI means:
- No dependency management
- No security vulnerabilities from packages
- Faster execution
- Easier maintenance

### 2. GraphQL over REST

**Why**: GitHub's GraphQL API lets us fetch exactly what we need in one request:
- Review threads
- Comments
- Metadata (resolved status, outdated status)
- Reduces API calls and latency

### 3. Explicit Severity Parsing with Fallback

**Why**: CodeRabbit's format is structured but not guaranteed:
- Parse explicit format when available (most accurate)
- Fall back to keyword heuristics (better than nothing)
- Never fail if format changes

### 4. Filter by Default, Opt-in to Include

**Why**: Most users want clean, actionable reviews:
- Exclude resolved threads by default
- Exclude outdated comments by default
- Provide `--include-*` flags for power users

## Testing Philosophy

**Approach**: Keep it simple
- No pytest, unittest, or other frameworks
- Simple assertions with clear output
- Fast execution for tight feedback loops
- Test the logic, not the API (use fixtures)

**Trade-offs**:
- ✅ Zero dependencies
- ✅ Easy to understand
- ✅ Fast execution
- ❌ Less sophisticated than pytest
- ❌ No test discovery (but we only have one file)

## Future Considerations

### Potential Enhancements

1. **More sophisticated pattern detection**
   - Cluster similar issues
   - Suggest batch fixes

2. **Configurable priority mapping**
   - Let users define their own severity → priority mappings
   - Different teams have different priorities

3. **Support for other review tools**
   - Generalize beyond CodeRabbit
   - Parse other bot formats (Copilot, Sourcery, etc.)

4. **Caching**
   - Cache GraphQL responses to reduce API calls
   - Useful for large PRs with many workflow runs

5. **Incremental processing**
   - Only process new comments since last run
   - Requires state management

### Constraints to Keep

- **No external dependencies** - Keep it simple and secure
- **Fast execution** - Action should complete in <10s
- **Backward compatibility** - Don't break existing workflows

## Debugging

### Common Issues

**1. Test failures after changes**
- Run: `python3 tests/test_processor.py`
- Check if your changes broke existing behavior
- Update tests if behavior change is intentional

**2. CI failures**
- Check the Actions tab on GitHub
- Usually means tests pass locally but fail in CI
- Often due to uncommitted changes

**3. Action fails in workflows**
- Check `gh` CLI is available (it should be in GitHub Actions)
- Verify PR number is correct
- Check repo permissions (needs `contents: read`)

### Useful Commands

```bash
# Test locally with real PR
python3 coderabbit_processor.py --pr-number 123 --repo owner/repo --verbose

# Run tests
python3 tests/test_processor.py

# Check git status
git status

# View recent tags
git tag -l

# View commit history
git log --oneline -10
```

## Contributing Guidelines

### Before Making Changes

1. Read this file (you're doing it!)
2. Run tests to ensure baseline passes
3. Check existing issues/PRs to avoid duplication

### Making Changes

1. Create a feature branch (optional for solo dev)
2. Make focused changes (one feature/fix at a time)
3. Add/update tests for new functionality
4. Run tests locally
5. Commit with clear messages
6. Push and verify CI passes

### Code Style

- Follow existing patterns in the codebase
- Use descriptive variable names
- Add docstrings to functions
- Keep functions focused and small
- Comment complex logic

## Contact & Resources

- **Repository**: https://github.com/benvenker/coderabbit-processor-action
- **Issues**: https://github.com/benvenker/coderabbit-processor-action/issues
- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **GitHub GraphQL API**: https://docs.github.com/en/graphql

---

*Last updated: October 2024*
*For the latest version of this guide, see the repository.*

