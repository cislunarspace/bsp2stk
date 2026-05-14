# Issue tracker

This project uses **GitHub Issues**.

## Creating issues

Use the `gh` CLI:

```bash
gh issue create --title "..." --body "..." --label "..."
```

## Reading issues

List open issues:

```bash
gh issue list --state open
```

View a specific issue:

```bash
gh issue view <number>
```

## Required setup

- Install `gh` CLI: https://cli.github.com
- Authenticate: `gh auth login`
