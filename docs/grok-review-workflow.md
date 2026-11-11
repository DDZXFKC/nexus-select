# Grok ↔ ChatGPT review workflow

This branch is a shared, **public** code-review staging area for the NEXUS SELECT sourcing collector. It is not an automated Grok connection.

## Workflow
1. ChatGPT publishes a sanitized source-code change on this branch or in a pull request.
2. Grok reads the GitHub branch/PR URL and provides a review, preferably as GitHub issue or PR comment if its GitHub access permits.
3. ChatGPT reads the feedback, fixes code, and reports test evidence.
4. Human approval is required before merging or enabling any live purchasing, partner task release, or WooCommerce publishing.

## Security and data rules
- Never commit credentials, cookies, API keys, customer orders, supplier pricing, margins, partner personal data, or private BUYMA HTML.
- Do not run automatic BUYMA scraping unless applicable terms and access permissions are checked.
- Treat product availability as unverified without timestamped evidence.
- Keep partner tasks gated by confirmed orders, inventory, cost and human approval.
- Do not modify the live WooCommerce storefront from this workflow.

## Current status
GitHub access from ChatGPT is verified. Grok's ability to read or comment on this repository is **not yet verified**. No Grok API connection or autonomous two-way synchronization has been established.
