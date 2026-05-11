"""Code-phase prompt loading and rendering helpers."""

from __future__ import annotations

from pathlib import Path

from ralph.errors import PromptLoadingError

CODE_PROMPT_FILENAME = "prompt.md"
CODE_PROMPT_PATH = Path(__file__).with_name(CODE_PROMPT_FILENAME)
CODE_PROMPT_PLACEHOLDER = "$ARGUMENTS"


def load_code_prompt_text(prompt_path: Path | None = None) -> str:
    """Load the code-phase prompt from disk."""

    resolved_path = CODE_PROMPT_PATH if prompt_path is None else Path(prompt_path)
    try:
        return resolved_path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - exercised through callers
        raise PromptLoadingError(f"Failed to load code prompt: {resolved_path}") from exc


def render_code_prompt(feature_dir: str | Path, *, prompt_text: str | None = None) -> str:
    """Render the code prompt for one resolved feature directory."""

    template = load_code_prompt_text() if prompt_text is None else prompt_text
    return template.replace(CODE_PROMPT_PLACEHOLDER, str(Path(feature_dir)))


__all__ = [
    "CODE_PROMPT_FILENAME",
    "CODE_PROMPT_PATH",
    "CODE_PROMPT_PLACEHOLDER",
    "load_code_prompt_text",
    "render_code_prompt",
]

