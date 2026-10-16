---
name: example
description: Demonstrate a portable skill workflow. Use only when explicitly asked to run the example skill or inspect an Agent Skills example.
---

# Example

## Workflow

1. Ask for the example input if it is missing.
2. Read [the example criteria](references/example.md).
3. Summarize the supplied input in three concise bullet points without introducing new facts.
4. Check every point against the input and identify any missing information.

## Output

Return three summary points followed by a short list of missing information, if any.

## Validation

Check that the summary is faithful, has exactly three points, and clearly separates unknown information from supplied facts.
