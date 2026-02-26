#!/usr/bin/env python3
"""Set a GitHub project item status for a repository issue."""

from __future__ import annotations

import argparse
import json
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


def load_project_config() -> tuple[str, str]:
    config_path = Path('.local/github.toml')
    if not config_path.exists():
        raise SystemExit('Missing .local/github.toml')

    if sys.version_info >= (3, 11):
        import tomllib  # type: ignore[attr-defined]
    else:  # pragma: no cover
        raise SystemExit('Python 3.11+ is required (tomllib not available)')

    cfg = tomllib.loads(config_path.read_text(encoding='utf-8'))
    owner = (cfg.get('general') or {}).get('user')
    project_number = (cfg.get('project') or {}).get('project_id')

    if not owner or project_number is None:
        raise SystemExit('github.toml must include [general].user and [project].project_id')

    return str(owner), str(project_number)


def normalize_list(payload: object, list_key: str) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        maybe = payload.get(list_key)
        if isinstance(maybe, list):
            return [item for item in maybe if isinstance(item, dict)]
    return []


def content_repo_full_name(content: dict) -> str | None:
    repo = content.get('repository')
    if isinstance(repo, dict):
        owner = repo.get('owner')
        name = repo.get('name')
        if isinstance(owner, dict):
            owner = owner.get('login')
        if owner and name:
            return f"{owner}/{name}"
    if isinstance(repo, str):
        return repo
    return None


def find_issue_item_id(items: list[dict], issue_number: int, repo_full_name: str) -> str:
    for item in items:
        content = item.get('content')
        if not isinstance(content, dict):
            continue
        if str(content.get('number', '')) != str(issue_number):
            continue
        repo_name = content_repo_full_name(content)
        if repo_name is not None and repo_name != repo_full_name:
            continue
        item_id = item.get('id')
        if isinstance(item_id, str) and item_id:
            return item_id
    raise SystemExit(
        f'Could not find project item for issue #{issue_number} in {repo_full_name}. '
        'Ensure the issue is added to the configured project.'
    )


def find_status_ids(fields: list[dict], status_name: str) -> tuple[str, str]:
    status_field_id: str | None = None
    status_option_id: str | None = None

    for field in fields:
        if not isinstance(field, dict):
            continue
        if (field.get('name') or '').strip().lower() != 'status':
            continue

        field_id = field.get('id')
        if isinstance(field_id, str) and field_id:
            status_field_id = field_id

        for option in field.get('options') or []:
            if not isinstance(option, dict):
                continue
            name = (option.get('name') or '').strip().lower()
            if name == status_name.strip().lower():
                opt_id = option.get('id')
                if isinstance(opt_id, str) and opt_id:
                    status_option_id = opt_id
                    break

    if not status_field_id:
        raise SystemExit('Could not find Status field in the configured project')
    if not status_option_id:
        raise SystemExit(f'Could not find Status option "{status_name}"')

    return status_field_id, status_option_id


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--issue', type=int, required=True, help='Issue number')
    parser.add_argument('--status', required=True, help='Project status option name')
    args = parser.parse_args()

    owner, project_number = load_project_config()

    repo = run_json(['gh', 'repo', 'view', '--json', 'nameWithOwner'])
    if not isinstance(repo, dict) or not isinstance(repo.get('nameWithOwner'), str):
        raise SystemExit('Unable to resolve repository name with gh repo view')
    repo_full_name = repo['nameWithOwner']

    project_view = run_json(
        ['gh', 'project', 'view', project_number, '--owner', owner, '--format', 'json']
    )
    if not isinstance(project_view, dict) or not isinstance(project_view.get('id'), str):
        raise SystemExit('Unable to resolve project node id from gh project view')
    project_id = project_view['id']

    items = run_json(
        [
            'gh',
            'project',
            'item-list',
            project_number,
            '--owner',
            owner,
            '--format',
            'json',
            '--limit',
            '200',
        ]
    )
    fields = run_json(
        ['gh', 'project', 'field-list', project_number, '--owner', owner, '--format', 'json']
    )

    item_nodes = normalize_list(items, 'items')
    field_nodes = normalize_list(fields, 'fields')

    item_id = find_issue_item_id(item_nodes, args.issue, repo_full_name)
    status_field_id, status_option_id = find_status_ids(field_nodes, args.status)

    run_cmd(
        [
            'gh',
            'project',
            'item-edit',
            '--id',
            item_id,
            '--project-id',
            project_id,
            '--field-id',
            status_field_id,
            '--single-select-option-id',
            status_option_id,
        ]
    )

    print(
        f"Updated issue #{args.issue} status to '{args.status}' "
        f"(project={project_number}, owner={owner})"
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
