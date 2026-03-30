"""Pure content renderers for blueprint init-repo."""

from __future__ import annotations

import re


def _replace_scalar_once(content: str, pattern: str, replacement: str, label: str) -> str:
    compiled = re.compile(pattern, flags=re.MULTILINE)
    updated, count = compiled.subn(replacement, content, count=1)
    if count != 1:
        raise ValueError(f"unable to update {label}")
    return updated


def _replace_js_string_key(content: str, key: str, value: str, label: str) -> str:
    pattern = re.compile(rf'^(\s*{re.escape(key)}:\s*")[^"]*(".*)$', flags=re.MULTILINE)

    def repl(match: re.Match[str]) -> str:
        return f'{match.group(1)}{value}{match.group(2)}'

    updated, count = pattern.subn(repl, content, count=1)
    if count != 1:
        raise ValueError(f"unable to update {label}")
    return updated


def _replace_quoted_assignment_once(content: str, key: str, value: str, label: str) -> str:
    pattern = re.compile(rf'^(\s*{re.escape(key)}\s*=\s*")[^"]*(".*)$', flags=re.MULTILINE)

    def repl(match: re.Match[str]) -> str:
        return f'{match.group(1)}{value}{match.group(2)}'

    updated, count = pattern.subn(repl, content, count=1)
    if count != 1:
        raise ValueError(f"unable to update {label}")
    return updated


def render_contract(
    content: str,
    repo_name: str,
    default_branch: str,
    repo_mode: str,
    module_enablement: dict[str, bool],
) -> str:
    content = _replace_scalar_once(
        content,
        r"^(\s*name:\s*).+$",
        rf"\1{repo_name}",
        "blueprint contract metadata.name",
    )
    content = _replace_scalar_once(
        content,
        r"^(\s*default_branch:\s*).+$",
        rf"\1{default_branch}",
        "blueprint contract repository.default_branch",
    )
    content = _replace_scalar_once(
        content,
        r"^(\s*repo_mode:\s*).+$",
        rf"\1{repo_mode}",
        "blueprint contract repository.repo_mode",
    )
    # Persist init-time module selection so generated repos can treat the contract
    # as their steady-state default without replaying the original init env.
    for module_id, enabled in module_enablement.items():
        content = _replace_scalar_once(
            content,
            rf"(^\s{{6}}{re.escape(module_id)}:\n(?:\s{{8}}.*\n)*?\s{{8}}enabled_by_default:\s*)(true|false)",
            rf"\g<1>{str(enabled).lower()}",
            f"optional module default enablement for {module_id}",
        )
    return content


def render_docusaurus_config(
    content: str,
    docs_title: str,
    docs_tagline: str,
    github_org: str,
    github_repo: str,
    default_branch: str,
) -> str:
    edit_url = f"https://github.com/{github_org}/{github_repo}/edit/{default_branch}/docs/"

    content = _replace_js_string_key(content, "title", docs_title, "docs title")
    content = _replace_js_string_key(content, "tagline", docs_tagline, "docs tagline")
    content = _replace_js_string_key(content, "organizationName", github_org, "docs organizationName")
    content = _replace_js_string_key(content, "projectName", github_repo, "docs projectName")
    content = _replace_js_string_key(content, "editUrl", edit_url, "docs editUrl")
    return content


def render_argocd_repo_urls(
    content: str,
    github_org: str,
    github_repo: str,
) -> str:
    repo_url = f"https://github.com/{github_org}/{github_repo}.git"

    content = re.sub(
        r"(^\s*repoURL:\s*)https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git(\s*$)",
        rf"\g<1>{repo_url}\g<2>",
        content,
        flags=re.MULTILINE,
    )
    content = re.sub(
        r"(^\s*-\s*)https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git(\s*$)",
        rf"\g<1>{repo_url}\g<2>",
        content,
        flags=re.MULTILINE,
    )
    return content


def render_stackit_bootstrap_tfvars(
    content: str,
    environment: str,
    stackit_region: str,
    tenant_slug: str,
    platform_slug: str,
    stackit_project_id: str,
    stackit_tfstate_key_prefix: str,
) -> str:
    content = _replace_quoted_assignment_once(
        content,
        "environment",
        environment,
        f"bootstrap tfvars {environment} environment",
    )
    content = _replace_quoted_assignment_once(
        content,
        "stackit_region",
        stackit_region,
        f"bootstrap tfvars {environment} stackit_region",
    )
    content = _replace_quoted_assignment_once(
        content,
        "tenant_slug",
        tenant_slug,
        f"bootstrap tfvars {environment} tenant_slug",
    )
    content = _replace_quoted_assignment_once(
        content,
        "platform_slug",
        platform_slug,
        f"bootstrap tfvars {environment} platform_slug",
    )
    content = _replace_quoted_assignment_once(
        content,
        "stackit_project_id",
        stackit_project_id,
        f"bootstrap tfvars {environment} stackit_project_id",
    )
    content = _replace_quoted_assignment_once(
        content,
        "state_key_prefix",
        stackit_tfstate_key_prefix,
        f"bootstrap tfvars {environment} state_key_prefix",
    )
    return content


def render_stackit_foundation_tfvars(
    content: str,
    environment: str,
    stackit_region: str,
    tenant_slug: str,
    platform_slug: str,
    stackit_project_id: str,
) -> str:
    content = _replace_quoted_assignment_once(
        content,
        "environment",
        environment,
        f"foundation tfvars {environment} environment",
    )
    content = _replace_quoted_assignment_once(
        content,
        "tenant_slug",
        tenant_slug,
        f"foundation tfvars {environment} tenant_slug",
    )
    content = _replace_quoted_assignment_once(
        content,
        "platform_slug",
        platform_slug,
        f"foundation tfvars {environment} platform_slug",
    )
    content = _replace_quoted_assignment_once(
        content,
        "stackit_project_id",
        stackit_project_id,
        f"foundation tfvars {environment} stackit_project_id",
    )
    content = _replace_quoted_assignment_once(
        content,
        "stackit_region",
        stackit_region,
        f"foundation tfvars {environment} stackit_region",
    )
    return content


def render_stackit_backend_hcl(
    content: str,
    environment: str,
    layer: str,
    stackit_region: str,
    stackit_tfstate_bucket: str,
    stackit_tfstate_key_prefix: str,
) -> str:
    content = _replace_quoted_assignment_once(
        content,
        "bucket",
        stackit_tfstate_bucket,
        f"{layer} backend {environment} bucket",
    )
    content = _replace_quoted_assignment_once(
        content,
        "key",
        f"{stackit_tfstate_key_prefix}/{environment}/{layer}.tfstate",
        f"{layer} backend {environment} key",
    )
    content = _replace_quoted_assignment_once(
        content,
        "region",
        stackit_region,
        f"{layer} backend {environment} region",
    )
    content = _replace_scalar_once(
        content,
        r'(^\s*s3\s*=\s*")https://object\.storage\.[^"]+(".*$)',
        rf'\1https://object.storage.{stackit_region}.onstackit.cloud\2',
        f"{layer} backend {environment} s3 endpoint",
    )
    return content
