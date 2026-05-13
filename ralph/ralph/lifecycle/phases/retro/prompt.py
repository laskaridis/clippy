"""Retrospective prompt loading and rendering helpers."""

from __future__ import annotations

from pathlib import Path

from ralph.errors import PromptLoadingError

RETRO_PROMPT_FILENAME = "prompt.md"
RETRO_PROMPT_PATH = Path(__file__).with_name(RETRO_PROMPT_FILENAME)
RETRO_PROMPT_PLACEHOLDER = "$ARGUMENTS"


def load_retro_prompt_text(prompt_path: Path | None = None) -> str:
    """Load the retrospective prompt from disk."""

    resolved_path = RETRO_PROMPT_PATH if prompt_path is None else Path(prompt_path)
    try:
        return resolved_path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - exercised through callers
        raise PromptLoadingError(f"Failed to load retro prompt: {resolved_path}") from exc


def render_retro_prompt(feature_dir: str | Path, *, prompt_text: str | None = None) -> str:
    """Render the retrospective prompt for one resolved feature directory."""

    template = load_retro_prompt_text() if prompt_text is None else prompt_text
    return template.replace(RETRO_PROMPT_PLACEHOLDER, str(Path(feature_dir)))


__all__ = [
    "RETRO_PROMPT_FILENAME",
    "RETRO_PROMPT_PATH",
    "RETRO_PROMPT_PLACEHOLDER",
    "load_retro_prompt_text",
    "render_retro_prompt",
]

