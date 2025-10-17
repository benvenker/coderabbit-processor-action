# Setup Instructions

## Files Created

✅ All files have been created in `/Users/ben/code/github-actions/coderabbit-processor-action/`

### Core Files
- `action.yml` - GitHub Action metadata with inputs/outputs
- `coderabbit_processor.py` - Main processor script
- `README.md` - Comprehensive documentation
- `LICENSE` - MIT License
- `.gitignore` - Python ignores

### Examples
- `examples/codex-workflow.yml` - Complete Codex integration example
- `examples/claude-workflow.yml` - Complete Claude integration example

## Next Steps

### 1. Review Files (Optional)
```bash
cd /Users/ben/code/github-actions/coderabbit-processor-action
cat README.md  # Review documentation
cat action.yml # Review action config
```

### 2. Initial Commit & Push
```bash
cd /Users/ben/code/github-actions/coderabbit-processor-action

# Stage all files
git add .

# Initial commit
git commit -m "Initial release: CodeRabbit processor action

- 80% token reduction (71K → 14K tokens)
- Filters to unresolved threads only
- Priority inference (P0-P3)
- Pattern detection
- Agent-optimized markdown output
- Zero dependencies (Python stdlib + gh CLI)
- Comprehensive examples for Codex and Claude"

# Push to GitHub
git push origin main
```

### 3. Create v1.0.0 Release
```bash
# Create and push v1 tag
git tag -a v1.0.0 -m "v1.0.0 - Initial stable release"
git push origin v1.0.0

# Create v1 tag (for major version pinning)
git tag -a v1 -m "v1 - Latest v1.x.x release"
git push origin v1

# Or create release via gh CLI
gh release create v1.0.0 \
  --title "v1.0.0 - Initial Release" \
  --notes "## Features

- ✅ 80% token reduction (71K → 14K tokens)
- ✅ Filters to unresolved threads only
- ✅ Priority inference (P0-P3)
- ✅ Pattern detection for recurring issues
- ✅ Agent-optimized markdown output
- ✅ Zero pip dependencies
- ✅ Complete Codex and Claude workflow examples

## Usage

\`\`\`yaml
- uses: benvenker/coderabbit-processor-action@v1
  with:
    pr-number: \${{ github.event.pull_request.number }}
\`\`\`

See [README.md](https://github.com/benvenker/coderabbit-processor-action#readme) for full documentation."
```

### 4. Test in LocalVantage
```bash
cd /Users/ben/code/localvantage

# Update .github/workflows/codex.yml to use the action
# Replace the manual processing step with:
# - uses: benvenker/coderabbit-processor-action@v1
```

### 5. Publish to GitHub Marketplace (Optional)
1. Go to https://github.com/benvenker/coderabbit-processor-action
2. Click "Releases" → "Draft a new release"
3. Check "Publish this Action to the GitHub Marketplace"
4. Add category tags: "Code quality", "Continuous integration"
5. Publish!

## Usage in Other Projects

Once published, use in any repo:

```yaml
- name: Process CodeRabbit review
  uses: benvenker/coderabbit-processor-action@v1
  with:
    pr-number: ${{ github.event.pull_request.number }}
```

Version pinning options:
- `@v1` - Latest v1.x.x (recommended for stability)
- `@v1.0.0` - Exact version (maximum control)
- `@main` - Latest commit (bleeding edge)

## Verification

After pushing, verify at:
- https://github.com/benvenker/coderabbit-processor-action

The action will be immediately usable across all your repositories!

