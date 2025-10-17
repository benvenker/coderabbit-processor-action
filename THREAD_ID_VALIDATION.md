# Thread ID Validation

## Purpose

This document validates that we're using the correct ID property for replying to GitHub pull request review threads.

## GitHub GraphQL API Documentation

### Replying to Review Threads

According to GitHub's GraphQL API, to reply to a pull request review thread, you use the `addPullRequestReviewComment` mutation:

```graphql
mutation ($threadId: ID!, $body: String!) {
  addPullRequestReviewComment(input: {
    pullRequestReviewThreadId: $threadId,
    body: $body
  }) {
    comment {
      id
      body
    }
  }
}
```

**Key parameter**: `pullRequestReviewThreadId` must be the **thread's `id`** field (GraphQL global ID).

### Query Structure

Our GraphQL query fetches:

```graphql
reviewThreads(first:100){
  nodes{
    id                    # ← This is the thread ID for replying
    isResolved
    comments(first:20){
      nodes{
        id                # ← This is the comment ID (NOT for replying to thread)
        databaseId        # ← This is the REST API ID (NOT for replying to thread)
        body
        ...
      }
    }
  }
}
```

## Current Implementation

### Data Structure (✅ Correct)

In `coderabbit_processor.py` lines 264-278, we correctly extract:

```python
cleaned_thread = {
    'thread_id': thread['id'],           # ✅ CORRECT for replying
    'comment_id': first_comment['id'],   # Comment's GraphQL ID
    'database_id': first_comment.get('databaseId'),  # Comment's REST API ID
    ...
}
```

### Markdown Output (✅ Correct after fix)

In `coderabbit_processor.py` we now output the thread ID in the generated markdown:

```python
if thread['thread_id']:
    output.append(f"**Thread ID (for replies):** {thread['thread_id']}")
```

This ensures the published review markdown contains the GraphQL thread ID needed to reply via `addPullRequestReviewComment`.

## What Each ID Is Used For

| ID Field                | Type              | Purpose                     | Used For                                                    |
| ----------------------- | ----------------- | --------------------------- | ----------------------------------------------------------- |
| `thread['id']`          | GraphQL Global ID | Identify the review thread  | ✅ **Replying to thread with `addPullRequestReviewComment`** |
| `comment['id']`         | GraphQL Global ID | Identify a specific comment | Editing/deleting a specific comment                         |
| `comment['databaseId']` | Integer           | REST API compatibility      | Legacy REST API operations, permalinks                      |

## Correction Needed

We should output the `thread_id` in the markdown, as that's what AI agents need to reply to the conversation thread:

```python
if thread['thread_id']:
    output.append(f"**Reply To (thread_id):** {thread['thread_id']}")
```

Or provide both for reference:

```python
output.append(f"**Thread ID (for replies):** {thread['thread_id']}")
if thread['database_id']:
    output.append(f"**Comment Database ID:** {thread['database_id']}")
```

## Validation Results

✅ **Data extraction**: Correctly using `thread['id']` for thread identification  
✅ **Markdown output**: Shows `thread_id` (GraphQL ID) required for replies  
✅ **Documentation**: README/AGENTS now explain thread IDs for replies

## References

- GitHub GraphQL API Docs: [Pull Request Review Threads](https://docs.github.com/en/graphql/reference/objects#pullrequestreviewthread)
- GitHub GraphQL API Docs: [addPullRequestReviewComment Mutation](https://docs.github.com/en/graphql/reference/mutations#addpullrequestreviewcomment)

