#!/usr/bin/env python3
"""Shell behavioral validation gate for upgrade merge-required entries (Issue #184: extra_excluded_tokens).

Checks every .sh file produced by a 3-way merge for:
  1. Syntax errors via ``bash -n``.
  2. Unresolved function call sites (function called but definition not
     reachable in the same file or in files directly sourced by it).

This is an MVP grep-based heuristic. It covers the dominant failure class —
a function definition silently dropped by a 3-way merge while its call site
is retained — without requiring a full POSIX shell parser.

Scope limitations (by design for MVP):
  - Source-chain resolution is capped at depth 1.
  - Dynamically constructed function names are not detected.
  - Only functions that look "local" (not in the builtins exclusion set) are
    checked as call-site candidates.
  - Non-shell file types are out of scope.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Builtins / common commands exclusion set
# ---------------------------------------------------------------------------
# Call-site tokens matching any name in this set are not flagged as
# potentially unresolved, because they are expected to be provided by the
# shell, the OS, or the blueprint runtime infrastructure (log_*, run_cmd,
# etc.) which may be injected via a source chain deeper than depth-1.
_EXCLUDED_TOKENS: frozenset[str] = frozenset({
    # bash keywords
    "if", "then", "else", "elif", "fi", "for", "do", "done", "while",
    "until", "case", "esac", "in", "function", "select", "time", "coproc",
    # bash builtins
    "alias", "bg", "bind", "break", "builtin", "caller", "cd", "command",
    "compgen", "complete", "compopt", "continue", "declare", "dirs", "disown",
    "echo", "enable", "eval", "exec", "exit", "export", "false", "fc", "fg",
    "getopts", "hash", "help", "history", "jobs", "kill", "let", "local",
    "logout", "mapfile", "popd", "printf", "pushd", "pwd", "read", "readarray",
    "readonly", "return", "set", "shift", "shopt", "source", "suspend",
    "test", "times", "trap", "true", "type", "typeset", "ulimit", "umask",
    "unalias", "unset", "wait",
    # common external commands
    "awk", "basename", "bash", "cat", "chmod", "chown", "cp", "curl", "cut",
    "date", "dirname", "env", "find", "git", "grep", "head", "install", "jq",
    "ln", "ls", "make", "mkdir", "mktemp", "mv", "python3", "python", "rm",
    "rmdir", "sed", "sleep", "sort", "tail", "tee", "touch", "tr", "uname",
    "uniq", "wc", "which", "xargs", "yq",
    # blueprint runtime infrastructure (injected via bootstrap source chain)
    "log_info", "log_warn", "log_error", "log_fatal", "log_debug", "log_metric",
    "run_cmd", "run_cmd_capture", "run_cmd_capture_stdout",
    "require_command", "warn_if_missing_command",
    "ensure_dir", "ensure_file_with_content",
    "set_default_env", "load_env_file_defaults", "require_env_vars",
    "blueprint_load_env_defaults", "start_script_metric_trap", "is_truthy",
    "resolve_repo_root", "display_repo_path",
    # common OS tools absent from the original set (FR-007)
    "tar", "pnpm",
    # blueprint bootstrap-chain runtime functions (FR-008)
    "blueprint_require_runtime_env",
    "blueprint_sanitize_init_placeholder_defaults",
    "ensure_file_from_template",
    "ensure_file_from_rendered_template",
    "postgres_init_env",
    "object_storage_init_env",
    "rabbitmq_seed_env_defaults",
    "public_endpoints_seed_env_defaults",
    "identity_aware_proxy_seed_env_defaults",
    "keycloak_seed_env_defaults",
    "render_optional_module_values_file",
    "apply_optional_module_secret_from_literals",
    "delete_optional_module_secret",
})

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Matches a function definition line:
#   function foo {   |   function foo() {   |   foo() {   |   foo ()
_FUNC_DEF_RE = re.compile(
    r'^\s*(?:function\s+(\w+)\s*(?:\(\s*\))?|(\w+)\s*\(\s*\))\s*[{(]?\s*$'
    r'|^\s*function\s+(\w+)\s*[{(]'
    r'|^\s*(\w+)\s*\(\s*\)\s*[{]'
)

# Simpler patterns for extracting the name from a definition line
_FUNC_DEF_EXTRACT = [
    re.compile(r'^\s*function\s+(\w+)'),      # function foo …
    re.compile(r'^\s*(\w+)\s*\(\s*\)\s*[{(]'),  # foo() { or foo ()
]

# Source directive: `source path` or `. path`
_SOURCE_RE = re.compile(r'^\s*(?:source|\.)\s+(.+)')

# Heredoc start marker: <<MARKER, <<'MARKER', <<"MARKER", <<-MARKER, etc.
_HEREDOC_START_RE = re.compile(r'<<-?\s*[\'"]?(\w+)[\'"]?')

# Comment line
_COMMENT_RE = re.compile(r'^\s*#')

# Variable assignment: FOO=bar or FOO="bar" (not a function call)
_ASSIGNMENT_RE = re.compile(r'^\s*\w+=')

# A valid shell identifier token
_IDENTIFIER_RE = re.compile(r'^\w+$')

# Array initializer opener: local/declare/readonly/typeset var=( (FR-006)
_ARRAY_OPEN_RE = re.compile(r'\b(?:local|declare|readonly|typeset)\b.*\w+=\(')


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ShellBehavioralCheckResult:
    skipped: bool
    files_checked: int
    syntax_errors: list[dict[str, str]]
    unresolved_symbols: list[dict[str, Any]]
    status: str  # "pass" | "fail" | "skipped"
    extra_excluded_count: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "skipped": self.skipped,
            "files_checked": self.files_checked,
            "syntax_errors": list(self.syntax_errors),
            "unresolved_symbols": list(self.unresolved_symbols),
            "status": self.status,
            "extra_excluded_count": self.extra_excluded_count,
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_definitions(content: str) -> set[str]:
    """Extract all function names defined in a shell script content string."""
    defs: set[str] = set()
    for line in content.splitlines():
        if _COMMENT_RE.match(line):
            continue
        for pattern in _FUNC_DEF_EXTRACT:
            m = pattern.match(line)
            if m:
                defs.add(m.group(1))
                break
    return defs


def _resolve_sourced_paths(script_path: Path, content: str) -> list[Path]:
    """Resolve depth-1 source/. directives to absolute file paths."""
    script_dir = script_path.parent
    sourced: list[Path] = []
    for line in content.splitlines():
        if _COMMENT_RE.match(line):
            continue
        m = _SOURCE_RE.match(line)
        if not m:
            continue
        raw = m.group(1).strip().strip('"\'')
        # Expand $SCRIPT_DIR / ${SCRIPT_DIR} to the script's own directory
        raw = re.sub(r'\$\{?SCRIPT_DIR\}?', str(script_dir), raw)
        # Skip lines with remaining variable references (dynamic paths)
        if '$' in raw:
            continue
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = (script_dir / candidate).resolve()
        if candidate.is_file():
            sourced.append(candidate)
    return sourced


def _collect_available_definitions(script_path: Path, content: str) -> set[str]:
    """Collect all function definitions reachable from a script at depth-1."""
    defs = _extract_definitions(content)
    for sourced_path in _resolve_sourced_paths(script_path, content):
        try:
            sourced_content = sourced_path.read_text(encoding="utf-8")
        except OSError:
            continue
        defs.update(_extract_definitions(sourced_content))
    return defs


def _is_definition_line(line: str) -> bool:
    """Return True if the line is a function definition."""
    return any(p.match(line) for p in _FUNC_DEF_EXTRACT)


def _first_token(line: str) -> str | None:
    """Extract the first word token from a non-special line, or None."""
    stripped = line.strip()
    if not stripped:
        return None
    # Remove leading redirections or substitutions
    if stripped[0] in ('$', '(', '[', '{', '!', '-', '"', "'", '\\', '|', '&', ';', '<', '>'):
        return None
    token = re.split(r'[\s=|&;()<>]', stripped)[0]
    if _IDENTIFIER_RE.match(token):
        return token
    return None


def _find_unresolved_call_sites(
    content: str,
    available_defs: set[str],
    *,
    excluded: frozenset[str] = _EXCLUDED_TOKENS,
) -> list[dict[str, Any]]:
    """Find call sites for function names not in available_defs.

    Only non-comment, non-definition, non-assignment lines are scanned.
    Only tokens not in the builtins exclusion set are checked.
    Heredoc bodies and case-label lines are skipped to prevent false positives.
    Returns list of {"symbol": str, "line": int}.
    """
    findings: list[dict[str, Any]] = []
    heredoc_marker: str | None = None
    array_depth: int = 0  # tracks depth inside multi-line array initializers
    for lineno, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()

        # Heredoc body tracking — skip all lines between <<MARKER and MARKER.
        # Must come before the comment check so that body lines starting with
        # "#" are still consumed as body content rather than treated as comments.
        if heredoc_marker is not None:
            if stripped == heredoc_marker:
                heredoc_marker = None
            continue

        # Array initializer body tracking — skip bare-word elements between
        # local/declare/readonly/typeset var=( and the closing ).  (FR-006)
        if array_depth > 0:
            # Strip trailing inline comment before comparing so that
            # ") # end array" is correctly recognised as a close paren.
            if stripped.split("#")[0].rstrip() == ")":
                array_depth -= 1
            continue

        if _COMMENT_RE.match(line):
            continue
        if _ASSIGNMENT_RE.match(line):
            continue
        if _is_definition_line(line):
            continue

        # Detect heredoc start before the token checks so that lines like
        # ``cat <<'EOF'`` correctly activate heredoc tracking even when the
        # first token (``cat``) is an excluded builtin and would otherwise
        # cause an early ``continue`` before the detection could run.
        m = _HEREDOC_START_RE.search(line)
        if m:
            heredoc_marker = m.group(1)

        token = _first_token(line)
        if token is None:
            continue

        # Detect array initializer opener before the excluded-token guard so
        # that ``local/declare/readonly/typeset var=(`` lines are tracked even
        # though their first token is already in _EXCLUDED_TOKENS.  (FR-006)
        if _ARRAY_OPEN_RE.search(line):
            if line.count("(") > line.count(")"):
                array_depth += 1
            continue  # declaration line is never a call site

        if token in excluded:
            continue

        # Skip case-label lines — a first token immediately followed by ")" is a
        # case alternative pattern, not a function call.  For alternation forms
        # like ``build|test)`` or ``deploy | verify)`` the rest starts with "|"
        # BUT we must not also skip pipe operators (``missing_fn | tee``) or
        # logical-or sequences (``missing_fn || fallback``).  Only treat "|" as
        # a case alternation when a closing ")" appears before any command
        # separator (&&, ||, ;) — the invariant for all valid case labels.
        # (FR-005)
        rest_lstripped = stripped[len(token):].lstrip()
        if rest_lstripped.startswith(")"):
            continue
        if rest_lstripped.startswith("|"):
            paren_idx = rest_lstripped.find(")")
            if paren_idx != -1:
                before_paren = rest_lstripped[:paren_idx]
                if "&&" not in before_paren and "||" not in before_paren and ";" not in before_paren:
                    continue

        if token not in available_defs:
            findings.append({"symbol": token, "line": lineno})
    return findings


def _check_syntax(script_path: Path) -> str | None:
    """Run ``bash -n`` on a file. Returns error string, or None if clean."""
    result = subprocess.run(
        ["bash", "-n", str(script_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return (result.stderr or result.stdout).strip()
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_behavioral_check(
    files: list[Path],
    repo_root: Path,
    *,
    skip: bool = False,
    extra_excluded_tokens: frozenset[str] = frozenset(),
) -> ShellBehavioralCheckResult:
    """Run behavioral validation on a list of shell script paths.

    Args:
        files: Absolute paths to .sh files produced by a 3-way merge.
        repo_root: Repository root used to compute display-relative paths.
        skip: When True, skip all checks and return ``status="skipped"``.
        extra_excluded_tokens: Additional token names to treat as resolved,
            merged with ``_EXCLUDED_TOKENS`` per invocation without mutation.
            Non-string and empty entries are silently skipped (NFR-REL-001).

    Returns:
        A :class:`ShellBehavioralCheckResult` with all findings.
    """
    valid_extra: frozenset[str] = frozenset(
        t for t in extra_excluded_tokens if isinstance(t, str) and t
    )
    if valid_extra:
        print(
            f"[BEHAVIORAL-CHECK] applying {len(valid_extra)} consumer extra excluded tokens",
            file=sys.stderr,
        )
    effective_excluded = _EXCLUDED_TOKENS | valid_extra

    if skip:
        return ShellBehavioralCheckResult(
            skipped=True,
            files_checked=0,
            syntax_errors=[],
            unresolved_symbols=[],
            status="skipped",
            extra_excluded_count=len(valid_extra),
        )

    syntax_errors: list[dict[str, str]] = []
    unresolved_symbols: list[dict[str, Any]] = []

    for script_path in files:
        if not script_path.is_file():
            continue

        try:
            display_path = str(script_path.relative_to(repo_root))
        except ValueError:
            display_path = str(script_path)

        # Step 1 — syntax check (bash -n)
        error = _check_syntax(script_path)
        if error:
            syntax_errors.append({"file": display_path, "error": error})
            continue  # skip symbol check for files with syntax errors

        # Step 2 — symbol resolution
        try:
            content = script_path.read_text(encoding="utf-8")
        except OSError:
            continue

        available_defs = _collect_available_definitions(script_path, content)
        call_site_findings = _find_unresolved_call_sites(
            content, available_defs, excluded=effective_excluded
        )
        for finding in call_site_findings:
            unresolved_symbols.append({
                "file": display_path,
                "symbol": finding["symbol"],
                "line": finding["line"],
            })

    status = "fail" if (syntax_errors or unresolved_symbols) else "pass"
    return ShellBehavioralCheckResult(
        skipped=False,
        files_checked=len(files),
        syntax_errors=syntax_errors,
        unresolved_symbols=unresolved_symbols,
        status=status,
        extra_excluded_count=len(valid_extra),
    )
