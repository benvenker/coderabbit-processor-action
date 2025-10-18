# CodeRabbit Codex Processor Action

**Automated CodeRabbit review processing with Codex - from review to fixes in one action.**

A GitHub Action that processes CodeRabbit reviews and automatically applies fixes using OpenAI Codex, with intelligent priority handling, project-aware processing, and automatic PR updates.

**Two modes available:**
- **v2 (Full Pipeline)**: Complete automation - processes reviews, runs Codex, applies fixes, and pushes changes
- **v1 (Processor Only)**: Just the review processor - 80% token reduction for use with any AI agent

[![GitHub](https://img.shields.io/badge/GitHub-benvenker%2Fcoderabbit--processor--action-blue?logo=github)](https://github.com/benvenker/coderabbit-processor-action)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

### v2 (Full Pipeline)
✅ **Complete Automation** - Reviews → Fixes → PR updates in one step
✅ **Codex Integration** - OpenAI GPT-5 Codex processes and applies fixes
✅ **Project-Aware** - Reads AGENTS.md for project standards
✅ **Priority-Based** - Handles P0 (critical) → P3 (optional) systematically
✅ **Task Management** - Integrates with Beads, Linear, or GitHub Issues
✅ **Configurable** - Customize models, instructions, and environment

### v1 (Processor Only)
✅ **80% Token Reduction** - Reduces ~71K tokens → ~14K tokens
✅ **Unresolved Only** - Automatically filters to open conversations
✅ **Priority Inference** - Categorizes threads as P0-P3
✅ **Pattern Detection** - Identifies recurring issues
✅ **Agent-Ready Format** - Clean markdown with reply-to IDs
✅ **Zero Dependencies** - Uses only Python stdlib + gh CLI

## Quick Start

### v2: Full Pipeline (Recommended)

The complete end-to-end solution - perfect for most projects:

```yaml
name: Codex Code Review
on:
  pull_request_review_comment:
    types: [created]

jobs:
  codex-review:
    if: contains(github.event.comment.user.login, 'coderabbitai')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Checkout PR branch
        run: |
          gh pr checkout ${{ github.event.pull_request.number }}
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
        env:
          GH_TOKEN: ${{ github.token }}

      - uses: benvenker/coderabbit-processor-action@v2
        with:
          pr-number: ${{ github.event.pull_request.number }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
          project-manager: 'beads'  # or 'linear', 'github', 'none'
          install-go-tools: 'true'  # if using Beads
```

That's it! When CodeRabbit posts a review, Codex will:
1. Process and prioritize the feedback (P0 → P3)
2. Read your AGENTS.md for project standards
3. Apply fixes and commit changes
4. Push to the PR branch
5. Reply to threads with status updates
6. Post a summary comment

### v1: Processor Only

Use this if you want to handle Codex execution yourself:

```yaml
name: Process CodeRabbit Reviews
on:
  pull_request_review_comment:
    types: [created]

jobs:
  process:
    runs-on: ubuntu-latest
    steps:
      - name: Process CodeRabbit review
        uses: benvenker/coderabbit-processor-action@v1
        with:
          pr-number: ${{ github.event.pull_request.number }}
          output-file: review_for_agent.md

      - name: Use processed review
        run: cat review_for_agent.md
```

## Inputs

### v2 (Full Pipeline) Inputs

| Input                | Description                                          | Required | Default                |
| -------------------- | ---------------------------------------------------- | -------- | ---------------------- |
| `pr-number`          | Pull request number to process                       | ✅ Yes    | -                      |
| `github-token`       | GitHub token with repo and PR permissions            | ✅ Yes    | -                      |
| `openai-api-key`     | OpenAI API key for Codex                             | ✅ Yes    | -                      |
| `agent-docs-path`    | Path to project agent docs (AGENTS.md, README.md)    | No       | `AGENTS.md`            |
| `project-manager`    | Project management tool (beads\|linear\|github\|none) | No       | `none`                 |
| `codex-model`        | Codex model to use                                   | No       | `gpt-5-codex`          |
| `custom-instructions`| Additional instructions for Codex                    | No       | -                      |
| `node-version`       | Node.js version to setup                             | No       | `20`                   |
| `install-go-tools`   | Install Go tools (required for Beads)                | No       | `false`                |
| `npm-ci`             | Run npm ci to install dependencies                   | No       | `false`                |
| `output-file`        | Output file for processed review                     | No       | `review_for_codex.md`  |
| `include-resolved`   | Include resolved threads                             | No       | `false`                |
| `include-outdated`   | Include outdated comments                            | No       | `false`                |

### v1 (Processor Only) Inputs

| Input              | Description                          | Required | Default               |
| ------------------ | ------------------------------------ | -------- | --------------------- |
| `pr-number`        | Pull request number to process       | ✅ Yes    | -                     |
| `output-file`      | Output file path                     | No       | `review_processed.md` |
| `format`           | Output format (`markdown` or `json`) | No       | `markdown`            |
| `repo`             | Repository (`owner/repo`)            | No       | Current repo          |
| `include-resolved` | Include resolved threads             | No       | `false`               |
| `verbose`          | Enable verbose output                | No       | `false`               |

## Outputs

### v2 (Full Pipeline) Outputs

| Output           | Description                                  |
| ---------------- | -------------------------------------------- |
| `threads-count`  | Number of unresolved threads processed       |
| `token-estimate` | Estimated tokens in processed review         |
| `changes-pushed` | Whether changes were pushed to the PR branch |

### v1 (Processor Only) Outputs

| Output           | Description                            |
| ---------------- | -------------------------------------- |
| `threads-count`  | Number of unresolved threads processed |
| `token-estimate` | Estimated tokens in output             |
| `output-file`    | Path to generated file                 |

## Usage Examples

### Basic Usage with Codex

```yaml
name: Codex CodeRabbit Processor
on:
  pull_request_review_comment:
    types: [created]

jobs:
  codex-review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Process CodeRabbit review
        uses: benvenker/coderabbit-processor-action@v1
        with:
          pr-number: ${{ github.event.pull_request.number }}
          output-file: review_for_codex.md
          verbose: true

      - name: Run Codex to address feedback
        uses: openai/codex-action@v1
        with:
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
          prompt-file: review_for_codex.md
```

### With Claude Code Action

```yaml
name: Claude CodeRabbit Processor
on:
  issue_comment:
    types: [created]

jobs:
  claude-review:
    if: contains(github.event.comment.body, '@claude-review-all')
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Process CodeRabbit review
        uses: benvenker/coderabbit-processor-action@v1
        with:
          pr-number: ${{ github.event.issue.number }}
          output-file: review_for_claude.md

      - name: Run Claude
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
          prompt: |
            Read review_for_claude.md for pre-processed CodeRabbit feedback.
            Process each thread systematically...
```

### JSON Output for Custom Processing

```yaml
- name: Process as JSON
  uses: benvenker/coderabbit-processor-action@v1
  with:
    pr-number: ${{ github.event.pull_request.number }}
    output-file: review.json
    format: json

- name: Parse and use JSON
  run: |
    jq '.threads[] | select(.priority == "P0")' review.json
```

### Include Resolved Threads

```yaml
- name: Process all threads (including resolved)
  uses: benvenker/coderabbit-processor-action@v1
  with:
    pr-number: ${{ github.event.pull_request.number }}
    output-file: full_review.md
    include-resolved: true
```

### Use Outputs in Subsequent Steps

```yaml
- name: Process review
  id: process
  uses: benvenker/coderabbit-processor-action@v1
  with:
    pr-number: ${{ github.event.pull_request.number }}

- name: Comment with statistics
  uses: actions/github-script@v7
  with:
    script: |
      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: `📊 Processed ${{ steps.process.outputs.threads-count }} threads (~${{ steps.process.outputs.token-estimate }} tokens)`
      })
```

## Output Format

The action generates clean, structured markdown:

```markdown
# CodeRabbit Review: PR #123

**Repository:** owner/repo
**Branch:** feature/scanner
**Unresolved Threads:** 31

**By Priority:**
- P0 (Critical): 3 threads
- P1 (Important): 15 threads
- P2 (Style): 12 threads
- P3 (Optional): 1 threads

---

## Thread 1: Type Safety Issue [P0]

**File:** `server/routes.ts`
**Lines:** 45
**URL:** https://github.com/.../pull/1#discussion_r123
**Thread ID (for replies):** PR_kwDOABCDEF4ABCDEFGH

### AI Agent Instructions (Priority)
Ensure type validation before database insertion.

### CodeRabbit's Feedback
Remove `any` cast to preserve type safety...

---

## Summary Statistics

**Recurring Patterns Detected:**
- Type safety casts (17 occurrences) → Review TypeScript strict mode

**Token Estimate:** ~14,250 tokens
```

## Priority Classification

Threads are automatically categorized:

- **P0 (Critical)**: security, vulnerable, broken, crash, data loss
- **P1 (Important)**: type safety, error handling, bug, validation
- **P2 (Style)**: documentation, refactor, naming, readability
- **P3 (Optional)**: nitpicks, suggestions

## Token Efficiency

Real-world results from PR processing:

| Source               | Tokens      | Reduction |
| -------------------- | ----------- | --------- |
| Raw GraphQL Response | ~71,477     | baseline  |
| **Processed Output** | **~14,425** | **80%** ✅ |

## Requirements

- Python 3.7+
- `gh` CLI (GitHub CLI) - automatically available in GitHub Actions runners

## Local Usage

You can also use the processor script locally:

```bash
# Clone the action repo
git clone https://github.com/benvenker/coderabbit-processor-action.git
cd coderabbit-processor-action

# Process a PR
python3 coderabbit_processor.py \
  --pr 123 \
  --output review.md \
  --verbose

# Dry run to see statistics
python3 coderabbit_processor.py \
  --pr 123 \
  --output review.md \
  --dry-run
```

## How It Works

1. **Fetches** review threads via GitHub GraphQL API
2. **Filters** to unresolved threads from CodeRabbit
3. **Cleans** removes HTML, linters, metadata (80% reduction)
4. **Enhances** adds priority labels, reply-to IDs, pattern detection
5. **Formats** generates clean markdown optimized for AI agents

## Pattern Detection

Automatically identifies recurring issues:

- **3+ markdown issues** → Suggests markdownlint
- **4+ type safety issues** → Suggests TypeScript strict mode
- **3+ formatting issues** → Suggests Prettier

## Migration Guide: v1 → v2

Upgrading from v1 (processor only) to v2 (full pipeline) is straightforward:

### Before (v1)
```yaml
steps:
  - uses: actions/checkout@v4

  - name: Process review
    uses: benvenker/coderabbit-processor-action@v1
    with:
      pr-number: ${{ github.event.pull_request.number }}
      output-file: review.md

  - name: Install Codex
    run: npm install -g @openai/codex

  - name: Auth Codex
    run: |
      # ... auth steps ...

  - name: Run Codex
    run: |
      codex exec --model gpt-5-codex ...

  - name: Push changes
    run: git push

  - name: Comment on PR
    uses: actions/github-script@v7
    # ... etc
```

### After (v2)
```yaml
steps:
  - uses: actions/checkout@v4

  - name: Checkout PR branch
    run: |
      gh pr checkout ${{ github.event.pull_request.number }}
      git config user.name "github-actions[bot]"
      git config user.email "github-actions[bot]@users.noreply.github.com"
    env:
      GH_TOKEN: ${{ github.token }}

  - uses: benvenker/coderabbit-processor-action@v2
    with:
      pr-number: ${{ github.event.pull_request.number }}
      github-token: ${{ secrets.GITHUB_TOKEN }}
      openai-api-key: ${{ secrets.OPENAI_API_KEY }}
```

**Benefits:**
- ✅ Reduced from ~50+ lines to ~15 lines
- ✅ All Codex setup, auth, and execution handled automatically
- ✅ Built-in PR commenting with summaries
- ✅ Project-aware processing with AGENTS.md support
- ✅ Task management integration

## Version Compatibility

| Version | Status       | Use Case                                    |
| ------- | ------------ | ------------------------------------------- |
| v2.x    | ✅ Current    | Full pipeline: processing + Codex + fixes   |
| v1.x    | ✅ Maintained | Processor only, bring your own AI agent     |

Both versions are actively maintained. Use v2 for turnkey automation, v1 for custom workflows.

## Contributing

Contributions welcome! Please open an issue or PR.

## License

MIT License - see [LICENSE](LICENSE) file.

## Author

Created by [Ben Venker](https://github.com/benvenker)

## Related Projects

- [Claude Code Action](https://github.com/anthropics/claude-code-action)
- [OpenAI Codex Action](https://github.com/openai/codex-action)
- [CodeRabbit AI](https://coderabbit.ai)

## Support

- 🐛 [Report a bug](https://github.com/benvenker/coderabbit-processor-action/issues)
- 💡 [Request a feature](https://github.com/benvenker/coderabbit-processor-action/issues)
- 📖 [View documentation](https://github.com/benvenker/coderabbit-processor-action#readme)

