#!/usr/bin/env python3
"""Block likely credentials without printing their values.

The scanner intentionally reports only a path, line number, and rule name. It can
scan the working tree, the staged snapshot, or every changed blob in a revision
range. The pre-push mode reads Git's standard ref update lines from stdin.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


MAX_FILE_SIZE = 2 * 1024 * 1024
ZERO_SHA = "0" * 40

ALLOWED_PRIVATE_KEY_FIXTURES = {
    "backend/internal/payment/provider/wxpay_test.go",
    "backend/internal/service/vertex_service_account_test.go",
    "frontend/src/components/account/__tests__/EditAccountModal.spec.ts",
}
ALLOWED_CREDENTIAL_URL_FIXTURES = {
    "backend/internal/pkg/proxyurl/parse_test.go",
    "backend/internal/service/proxy_test.go",
}

KNOWN_TOKEN = re.compile(
    r"(?:AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|"
    r"gh[pousr]_[0-9A-Za-z]{20,}|github_pat_[0-9A-Za-z_]{20,}|"
    r"sk_live_[0-9A-Za-z]{16,}|xox[baprs]-[0-9A-Za-z-]{16,}|"
    r"sk-[A-Za-z0-9_-]{32,})"
)
PRIVATE_KEY = re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----")
CREDENTIAL_URL = re.compile(
    r"(?:postgres(?:ql)?|mysql|mongodb|redis|https?|ssh)://"
    r"[^/@\s:]+:[^/@\s]+@",
    re.IGNORECASE,
)
ASSIGNMENT = re.compile(
    r"^\s*(?:export\s+|set\s+)?[\"']?"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_.-]*(?:password|passwd|pwd|secret|token|"
    r"api[_-]?key|private[_-]?key)[A-Za-z0-9_.-]*)[\"']?"
    r"\s*(?::=|=|:)\s*(?P<value>.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
CONTENT_CANDIDATE_PATTERN = (
    r"-----BEGIN ([A-Z0-9 ]+ )?PRIVATE KEY-----|"
    r"AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[0-9A-Za-z]{20,}|"
    r"github_pat_[0-9A-Za-z_]{20,}|sk_live_[0-9A-Za-z]{16,}|"
    r"xox[baprs]-[0-9A-Za-z-]{16,}|sk-[A-Za-z0-9_-]{32,}|"
    r"(postgres(ql)?|mysql|mongodb|redis|https?|ssh)://[^/@[:space:]]+:[^/@[:space:]]+@|"
    r"(password|passwd|pwd|secret|token|api[_-]?key|private[_-]?key)"
    r"[A-Za-z0-9_.-]*[[:space:]]*(:=|=|:)"
)

PLACEHOLDER_MARKERS = (
    "change-me",
    "change_me",
    "changeme",
    "dummy",
    "example",
    "fake",
    "not-a-real",
    "placeholder",
    "redacted",
    "replace",
    "test-only",
    "your-",
    "your_",
    "xxxx",
)
REFERENCE_PREFIXES = (
    "$",
    "${",
    "{{",
    "<",
    "config.",
    "credentials.",
    "env.",
    "form.",
    "input.",
    "os.getenv",
    "process.env",
    "req.",
    "secret.",
    "secrets.",
    "viper.",
)


@dataclass(frozen=True)
class Finding:
    source: str
    path: str
    line: int
    rule: str


def git(*args: str) -> bytes:
    result = subprocess.run(
        ["git", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(message or f"git {' '.join(args)} failed")
    return result.stdout


def git_grep_candidates() -> list[str]:
    result = subprocess.run(
        ["git", "grep", "-Il", "-i", "-E", "-e", CONTENT_CANDIDATE_PATTERN, "--"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode not in (0, 1):
        message = result.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(message or "git grep failed")
    return result.stdout.decode("utf-8", "surrogateescape").splitlines()


def nul_paths(data: bytes) -> list[str]:
    return [item.decode("utf-8", "surrogateescape") for item in data.split(b"\0") if item]


def is_example_path(path: str) -> bool:
    lowered = path.lower()
    parts = lowered.split("/")
    return any(
        marker in part
        for part in parts
        for marker in ("example", "sample", "template", "fixture")
    )


def is_test_path(path: str) -> bool:
    lowered = path.lower()
    return (
        "/__tests__/" in lowered
        or "/testdata/" in lowered
        or lowered.endswith(("_test.go", ".spec.ts", ".spec.js", ".test.ts", ".test.js"))
    )


def should_scan_assignments(path: str) -> bool:
    lowered = path.lower()
    suffix = Path(lowered).suffix
    if suffix in {".env", ".ini", ".conf", ".properties", ".toml", ".yaml", ".yml", ".json"}:
        return True
    if suffix in {".sh", ".bash", ".zsh", ".ps1", ".py", ".js", ".mjs", ".cjs"}:
        return "/" not in lowered or lowered.startswith(("deploy/", "scripts/", "tools/", ".github/"))
    return lowered.endswith(("/dockerfile", "dockerfile"))


def sensitive_filename(path: str) -> bool:
    normalized = path.replace("\\", "/")
    lowered = normalized.lower()
    base = lowered.rsplit("/", 1)[-1]
    if normalized == "frontend/.env.development" or is_example_path(normalized):
        return False
    if base == ".env" or base.startswith(".env."):
        return True
    if base in {".npmrc", ".pypirc", "credentials.json", "auth.json"}:
        if normalized == "frontend/.npmrc":
            return False
        return True
    if base.startswith(("id_rsa", "id_ed25519", "service-account")):
        return True
    if base.endswith((".pem", ".p12", ".pfx", ".ppk", ".keystore", ".kdbx", ".tfvars")):
        return True
    if re.fullmatch(r"(?:secrets?|credentials?)(?:\.[a-z0-9_-]+)?", base):
        return True
    return False


def line_number(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def concrete_assignment_value(raw: str) -> bool:
    value = raw.strip().rstrip(",;").strip()
    if value.startswith(("\"", "'")) and value[-1:] == value[:1]:
        value = value[1:-1].strip()
    lowered = value.lower()
    if not value or len(value) < 6:
        return False
    if lowered.startswith(REFERENCE_PREFIXES):
        return False
    if any(marker in lowered for marker in PLACEHOLDER_MARKERS):
        return False
    if len(set(value)) == 1:
        return False
    if lowered in {"password", "postgres", "sub2api", "localhost", "undefined", "null", "none"}:
        return False
    return True


def placeholder_credential_url(value: str) -> bool:
    lowered = value.lower()
    return any(character in value for character in "<>{}$") or any(
        marker in lowered for marker in PLACEHOLDER_MARKERS
    ) or any(
        marker in lowered for marker in ("user:pass@", "username:password@", "postgres:postgres@")
    )


def scan_blob(source: str, path: str, data: bytes) -> list[Finding]:
    normalized = path.replace("\\", "/")
    findings: list[Finding] = []
    if sensitive_filename(normalized):
        findings.append(Finding(source, normalized, 1, "sensitive-filename"))
    if len(data) > MAX_FILE_SIZE or b"\0" in data[:8192]:
        return findings

    text = data.decode("utf-8", "replace")
    if normalized not in ALLOWED_PRIVATE_KEY_FIXTURES:
        match = PRIVATE_KEY.search(text)
        if match:
            findings.append(Finding(source, normalized, line_number(text, match.start()), "private-key"))
    match = KNOWN_TOKEN.search(text)
    if match:
        findings.append(Finding(source, normalized, line_number(text, match.start()), "known-token"))
    if normalized not in ALLOWED_CREDENTIAL_URL_FIXTURES:
        for match in CREDENTIAL_URL.finditer(text):
            if not placeholder_credential_url(match.group(0)):
                findings.append(Finding(source, normalized, line_number(text, match.start()), "credential-url"))
                break

    if (
        normalized != "tools/check_secrets.py"
        and should_scan_assignments(normalized)
        and not is_test_path(normalized)
        and not is_example_path(normalized)
    ):
        for match in ASSIGNMENT.finditer(text):
            if concrete_assignment_value(match.group("value")):
                findings.append(
                    Finding(source, normalized, line_number(text, match.start()), "hardcoded-secret-assignment")
                )
                break
    return findings


def scan_paths(
    source: str,
    paths: Iterable[str],
    loader: Callable[[str], bytes],
) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        try:
            findings.extend(scan_blob(source, path, loader(path)))
        except (OSError, RuntimeError) as exc:
            print(f"secret scan could not read {source}:{path}: {exc}", file=sys.stderr)
            raise
    return findings


def scan_worktree() -> list[Finding]:
    paths = nul_paths(git("ls-files", "-z"))
    findings = [
        Finding("worktree", path.replace("\\", "/"), 1, "sensitive-filename")
        for path in paths
        if sensitive_filename(path)
    ]
    findings.extend(
        scan_paths("worktree", git_grep_candidates(), lambda path: Path(path).read_bytes())
    )
    return findings


def scan_staged() -> list[Finding]:
    paths = nul_paths(git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"))
    return scan_paths("staged", paths, lambda path: git("show", f":{path}"))


def commits_for_range(revision_range: str) -> list[str]:
    return git("rev-list", "--reverse", revision_range).decode().splitlines()


def scan_commits(commits: Iterable[str]) -> list[Finding]:
    findings: list[Finding] = []
    for revision in commits:
        paths = nul_paths(
            git(
                "diff-tree",
                "--root",
                "--no-commit-id",
                "--name-only",
                "-r",
                "--diff-filter=ACMR",
                "-z",
                revision,
            )
        )
        source = revision[:12]
        findings.extend(scan_paths(source, paths, lambda path, rev=revision: git("show", f"{rev}:{path}")))
    return findings


def pre_push_commits(remote: str | None) -> list[str]:
    revisions: set[str] = set()
    for line in sys.stdin:
        fields = line.split()
        if len(fields) != 4:
            continue
        _local_ref, local_sha, _remote_ref, remote_sha = fields
        if local_sha == ZERO_SHA:
            continue
        if remote_sha != ZERO_SHA:
            revisions.update(commits_for_range(f"{remote_sha}..{local_sha}"))
        else:
            args = ["rev-list", local_sha, "--not"]
            args.append(f"--remotes={remote}" if remote else "--remotes")
            revisions.update(git(*args).decode().splitlines())
    return sorted(revisions)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan Git content for likely plaintext credentials")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--staged", action="store_true", help="scan added/modified staged blobs")
    mode.add_argument("--range", dest="revision_range", help="scan changed blobs in a Git revision range")
    mode.add_argument("--pre-push", action="store_true", help="read pre-push ref updates from stdin")
    parser.add_argument("--remote", help="remote name used by --pre-push for new branches")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.staged:
            findings = scan_staged()
        elif args.revision_range:
            findings = scan_commits(commits_for_range(args.revision_range))
        elif args.pre_push:
            findings = scan_commits(pre_push_commits(args.remote))
        else:
            findings = scan_worktree()
    except RuntimeError as exc:
        print(f"secret scan failed: {exc}", file=sys.stderr)
        return 2

    unique = sorted(set(findings), key=lambda item: (item.source, item.path, item.line, item.rule))
    if not unique:
        print("Secret scan passed (values were not printed).")
        return 0

    print("Blocked: likely credentials detected. Values are intentionally hidden.", file=sys.stderr)
    for finding in unique:
        print(
            f"  {finding.source}:{finding.path}:{finding.line} [{finding.rule}]",
            file=sys.stderr,
        )
    print("Move real values to local environment files or GitHub Secrets before retrying.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
