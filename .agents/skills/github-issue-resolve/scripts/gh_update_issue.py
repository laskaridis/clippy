#!/usr/bin/env python3
"""Assign a GitHub issue to @me and set its project status.

Prerequisites:
- `gh` CLI installed and authenticated.
- Access to the repository and the target project.

Configuration precedence for project identity:
1) `--owner` and `--project`
2) `GITHUB_PROJECT_OWNER` and `GITHUB_PROJECT_NUMBER`
3) `.local/github.toml` with:
   - `[general].user`
   - `[project].project_id`
4) Defaults: owner=`laskaridis`, project=`6`

Examples:
  gh_update_issue.py --issue 42
  gh_update_issue.py --issue 42 --status "In review" --skip-assign
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def run_json(cmd: list[str]) -> object:
    try:
        out = subprocess.check_output(cmd, text=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"Command failed ({' '.join(cmd)}): {exc}") from exc
    try:
        return json.loads(out)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON from {' '.join(cmd)}") from exc


def run_cmd(cmd: list[str]) -> None:
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"Command failed ({' '.join(cmd)}): {exc}") from exc


def load_local_config() -> tuple[str | None, str | None]:
    config_path = Path(".local/github.toml")
    if not config_path.exists():
        return None, None

    if sys.version_info >= (3, 11):
        import tomllib  # type: ignore[attr-defined]
    else:  # pragma: no cover
        raise SystemExit("Python 3.11+ is required (tomllib not available)")

    cfg = tomllib.loads(config_path.read_text(encoding="utf-8"))
    owner = (cfg.get("general") or {}).get("user")
    project_number = (cfg.get("project") or {}).get("project_id")
    return (str(owner) if owner else None), (
        str(project_number) if project_number is not None else None
    )


def resolve_owner_and_project(
    owner_arg: str | None, project_arg: str | None
) -> tuple[str, str]:
    config_owner, config_project = load_local_config()
    owner = owner_arg or os.getenv("GITHUB_PROJECT_OWNER") or config_owner or "laskaridis"
    project = project_arg or os.getenv("GITHUB_PROJECT_NUMBER") or config_project or "6"

    return owner, project


def normalize_list(payload: object, list_key: str) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        maybe = payload.get(list_key)
        if isinstance(maybe, list):
            return [item for item in maybe if isinstance(item, dict)]
    return []


def content_repo_full_name(content: dict) -> str | None:
    repo = content.get("repository")
    if isinstance(repo, dict):
        owner = repo.get("owner")
        name = repo.get("name")
        if isinstance(owner, dict):
            owner = owner.get("login")
        if owner and name:
            return f"{owner}/{name}"
    if isinstance(repo, str):
        return repo
    return None


def find_issue_item_id(items: list[dict], issue_number: int, repo_full_name: str) -> str:
    for item in items:
        content = item.get("content")
        if not isinstance(content, dict):
            continue
        if str(content.get("number", "")) != str(issue_number):
            continue
        repo_name = content_repo_full_name(content)
        if repo_name is not None and repo_name != repo_full_name:
            continue
        item_id = item.get("id")
        if isinstance(item_id, str) and item_id:
            return item_id
    raise SystemExit(
        f"Could not find project item for issue #{issue_number} in {repo_full_name}. "
        "Ensure the issue is added to the configured project."
    )


def find_status_ids(fields: list[dict], status_name: str) -> tuple[str, str]:
    status_field_id: str | None = None
    status_option_id: str | None = None

    for field in fields:
        if not isinstance(field, dict):
            continue
        if (field.get("name") or "").strip().lower() != "status":
            continue

        field_id = field.get("id")
        if isinstance(field_id, str) and field_id:
            status_field_id = field_id

        for option in field.get("options") or []:
            if not isinstance(option, dict):
                continue
            name = (option.get("name") or "").strip().lower()
            if name == status_name.strip().lower():
                opt_id = option.get("id")
                if isinstance(opt_id, str) and opt_id:
                    status_option_id = opt_id
                    break

    if not status_field_id:
        raise SystemExit("Could not find Status field in the configured project")
    if not status_option_id:
        raise SystemExit(f'Could not find Status option "{status_name}"')
    return status_field_id, status_option_id


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Assign a GitHub issue to @me and update its project status.",
        epilog=(
            "Examples:\n"
            "  gh_update_issue.py --issue 42\n"
            "  gh_update_issue.py --issue 42 --status \"In review\" --skip-assign\n\n"
            "Owner/project resolution order:\n"
            "  --owner/--project > GITHUB_PROJECT_OWNER/GITHUB_PROJECT_NUMBER > .local/github.toml > defaults (laskaridis/6)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--issue", type=int, required=True, help="Issue number")
    parser.add_argument(
        "--status",
        default="In progress",
        help='Project status option name (default: "In progress")',
    )
    parser.add_argument(
        "--skip-assign",
        action="store_true",
        help="Do not assign the issue to @me",
    )
    parser.add_argument("--owner", help="Project owner login (or org)")
    parser.add_argument("--project", help="Project number")
    args = parser.parse_args()

    owner, project_number = resolve_owner_and_project(args.owner, args.project)

    repo = run_json(["gh", "repo", "view", "--json", "nameWithOwner"])
    if not isinstance(repo, dict) or not isinstance(repo.get("nameWithOwner"), str):
        raise SystemExit("Unable to resolve repository name with gh repo view")
    repo_full_name = repo["nameWithOwner"]

    project_view = run_json(
        ["gh", "project", "view", project_number, "--owner", owner, "--format", "json"]
    )
    if not isinstance(project_view, dict) or not isinstance(project_view.get("id"), str):
        raise SystemExit("Unable to resolve project node id from gh project view")
    project_id = project_view["id"]

    items = run_json(
        [
            "gh",
            "project",
            "item-list",
            project_number,
            "--owner",
            owner,
            "--format",
            "json",
            "--limit",
            "200",
        ]
    )
    fields = run_json(
        ["gh", "project", "field-list", project_number, "--owner", owner, "--format", "json"]
    )

    item_nodes = normalize_list(items, "items")
    field_nodes = normalize_list(fields, "fields")
    item_id = find_issue_item_id(item_nodes, args.issue, repo_full_name)
    status_name = args.status
    status_field_id, status_option_id = find_status_ids(field_nodes, status_name)

    if not args.skip_assign:
        run_cmd(["gh", "issue", "edit", str(args.issue), "--add-assignee", "@me"])

    run_cmd(
        [
            "gh",
            "project",
            "item-edit",
            "--id",
            item_id,
            "--project-id",
            project_id,
            "--field-id",
            status_field_id,
            "--single-select-option-id",
            status_option_id,
        ]
    )

    print(
        f"Updated issue #{args.issue}: "
        f"{'assigned to @me and ' if not args.skip_assign else ''}"
        f"set status to '{status_name}' (project={project_number}, owner={owner})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
