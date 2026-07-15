# Security and credential handling

Real passwords, API keys, access tokens, private keys, server addresses paired
with credentials, and production connection strings must never be committed.

- Store local deployment values in ignored files such as
  `deploy/servers.local.env`; keep only redacted `.example` templates in Git.
- Store CI/CD values in GitHub Secrets and reference them as `${{ secrets.NAME }}`.
- Before committing, run `python tools/check_secrets.py --staged`.
- If a credential reaches any commit, revoke or rotate it immediately. Deleting
  the file in a later commit does not remove the value from Git history.

This repository includes local pre-commit and pre-push guards. Enable them with:

```sh
git config core.hooksPath .githooks
```

The scanner never prints the matched value; it reports only the source, path,
line number, and detection rule.
