"""Feature-local Ralph session and lock persistence."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from datetime import timedelta
from enum import Enum
import errno
import json
import os
from pathlib import Path
import socket
import tempfile
from typing import Any, Mapping
from uuid import uuid4

from ralph.config import RunConfig
from ralph.errors import BookkeepingValidationError

SESSION_SCHEMA_VERSION = 1
POINTER_SCHEMA_VERSION = 1
LOCK_SCHEMA_VERSION = 1
LOCK_STALE_AFTER = timedelta(minutes=10)

SESSION_ID_ALPHABET = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
TERMINAL_RUN_OUTCOMES = ("completed", "blocked", "failed", "max_iterations", "degraded")
DEFAULT_CURRENT_PHASE = "code"

_MISSING = object()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_timestamp(moment: datetime) -> str:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _from_timestamp(raw_value: object, *, source: str) -> datetime:
    if not isinstance(raw_value, str):
        raise BookkeepingValidationError(f"Expected ISO timestamp string at {source}: {raw_value!r}")
    try:
        parsed = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BookkeepingValidationError(f"Invalid ISO timestamp at {source}: {raw_value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _validate_session_id(raw_value: object, *, source: str) -> str:
    if not isinstance(raw_value, str) or not raw_value:
        raise BookkeepingValidationError(f"Invalid session id at {source}: {raw_value!r}")
    if any(character not in SESSION_ID_ALPHABET for character in raw_value):
        raise BookkeepingValidationError(f"Session id contains unsupported characters at {source}: {raw_value!r}")
    return raw_value


def _validate_positive_int(raw_value: object, *, source: str, allow_zero: bool = True) -> int:
    if isinstance(raw_value, bool) or not isinstance(raw_value, int):
        raise BookkeepingValidationError(f"Expected integer at {source}: {raw_value!r}")
    if allow_zero:
        if raw_value < 0:
            raise BookkeepingValidationError(f"Expected non-negative integer at {source}: {raw_value!r}")
    elif raw_value <= 0:
        raise BookkeepingValidationError(f"Expected positive integer at {source}: {raw_value!r}")
    return raw_value


def _validate_string(raw_value: object, *, source: str, allow_empty: bool = False) -> str:
    if not isinstance(raw_value, str):
        raise BookkeepingValidationError(f"Expected string at {source}: {raw_value!r}")
    if not allow_empty and not raw_value:
        raise BookkeepingValidationError(f"Expected non-empty string at {source}: {raw_value!r}")
    return raw_value


def _validate_optional_string(raw_value: object, *, source: str) -> str | None:
    if raw_value is None:
        return None
    return _validate_string(raw_value, source=source)


def _validate_outcome(raw_value: object, *, source: str) -> str | None:
    if raw_value is None:
        return None
    outcome = _validate_string(raw_value, source=source)
    if outcome not in TERMINAL_RUN_OUTCOMES:
        raise BookkeepingValidationError(f"Invalid terminal outcome at {source}: {raw_value!r}")
    return outcome


def _validate_mapping(raw_value: object, *, source: str) -> dict[str, Any]:
    if not isinstance(raw_value, Mapping):
        raise BookkeepingValidationError(f"Expected mapping at {source}: {raw_value!r}")
    return dict(raw_value)


def _validate_path(raw_value: object, *, source: str) -> Path:
    return Path(_validate_string(raw_value, source=source))


def _current_hostname() -> str:
    return socket.gethostname()


def _process_is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError as exc:
        if getattr(exc, "errno", None) == errno.ESRCH:
            return False
        return True
    return True


def _new_session_id(moment: datetime | None = None) -> str:
    stamp = (moment or _utc_now()).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid4().hex[:8]}"


def _config_snapshot(config: RunConfig) -> dict[str, Any]:
    return {
        "feature_dir": str(config.feature_dir),
        "max_iterations": config.max_iterations,
        "coding_model": config.coding_model,
        "retro_model": config.retro_model,
        "retro_only": config.retro_only,
        "agent_identifier": config.agent_identifier,
        "spec_path": str(config.spec_path),
        "tasks_path": str(config.tasks_path),
        "ralph_txt_path": str(config.ralph_txt_path),
        "retro_path": str(config.retro_path),
        "ralph_dir": str(config.ralph_dir),
        "sessions_dir": str(config.sessions_dir),
        "current_session_path": str(config.current_session_path),
        "lock_path": str(config.lock_path),
    }


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BookkeepingValidationError(f"Failed to read bookkeeping file: {path}") from exc

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise BookkeepingValidationError(f"Failed to parse bookkeeping file as JSON: {path}") from exc

    if not isinstance(parsed, dict):
        raise BookkeepingValidationError(f"Bookkeeping file must contain a JSON object: {path}")
    return parsed


def _validate_config_snapshot(raw_value: object, *, source: str) -> dict[str, Any]:
    payload = _validate_mapping(raw_value, source=source)
    required_keys = (
        "feature_dir",
        "max_iterations",
        "coding_model",
        "retro_model",
        "retro_only",
        "agent_identifier",
        "spec_path",
        "tasks_path",
        "ralph_txt_path",
        "retro_path",
        "ralph_dir",
        "sessions_dir",
        "current_session_path",
        "lock_path",
    )
    for key in required_keys:
        if key not in payload:
            raise BookkeepingValidationError(f"Missing config field at {source}: {key}")
    return payload


@dataclass(frozen=True, slots=True)
class RunSession:
    """Immutable snapshot of one Ralph execution."""

    session_id: str
    feature_dir: Path
    config: Mapping[str, Any]
    current_phase: str
    iteration_count: int
    last_phase_outcome: str | None
    last_agent_result_metadata: Mapping[str, Any] | None
    started_at: datetime
    updated_at: datetime
    ended_at: datetime | None
    overall_outcome: str | None

    @property
    def is_terminal(self) -> bool:
        return self.overall_outcome is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SESSION_SCHEMA_VERSION,
            "session_id": self.session_id,
            "feature_dir": str(self.feature_dir),
            "config": dict(self.config),
            "current_phase": self.current_phase,
            "iteration_count": self.iteration_count,
            "last_phase_outcome": self.last_phase_outcome,
            "last_agent_result_metadata": None if self.last_agent_result_metadata is None else dict(self.last_agent_result_metadata),
            "started_at": _to_timestamp(self.started_at),
            "updated_at": _to_timestamp(self.updated_at),
            "ended_at": None if self.ended_at is None else _to_timestamp(self.ended_at),
            "overall_outcome": self.overall_outcome,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, source: Path | str) -> RunSession:
        source_label = str(source)
        schema_version = _validate_positive_int(payload.get("schema_version"), source=f"{source_label}.schema_version", allow_zero=False)
        if schema_version != SESSION_SCHEMA_VERSION:
            raise BookkeepingValidationError(
                f"Unsupported session schema version at {source_label}: {schema_version}"
            )
        session_id = _validate_session_id(payload.get("session_id"), source=f"{source_label}.session_id")
        feature_dir = _validate_path(payload.get("feature_dir"), source=f"{source_label}.feature_dir")
        config = _validate_config_snapshot(payload.get("config"), source=f"{source_label}.config")
        current_phase = _validate_string(payload.get("current_phase"), source=f"{source_label}.current_phase")
        iteration_count = _validate_positive_int(payload.get("iteration_count"), source=f"{source_label}.iteration_count")
        last_phase_outcome = _validate_optional_string(payload.get("last_phase_outcome"), source=f"{source_label}.last_phase_outcome")
        last_agent_result_raw = payload.get("last_agent_result_metadata")
        last_agent_result_metadata = None if last_agent_result_raw is None else _validate_mapping(
            last_agent_result_raw,
            source=f"{source_label}.last_agent_result_metadata",
        )
        started_at = _from_timestamp(payload.get("started_at"), source=f"{source_label}.started_at")
        updated_at = _from_timestamp(payload.get("updated_at"), source=f"{source_label}.updated_at")
        ended_at = payload.get("ended_at")
        parsed_ended_at = None if ended_at is None else _from_timestamp(ended_at, source=f"{source_label}.ended_at")
        overall_outcome = _validate_outcome(payload.get("overall_outcome"), source=f"{source_label}.overall_outcome")
        return cls(
            session_id=session_id,
            feature_dir=feature_dir,
            config=config,
            current_phase=current_phase,
            iteration_count=iteration_count,
            last_phase_outcome=last_phase_outcome,
            last_agent_result_metadata=last_agent_result_metadata,
            started_at=started_at,
            updated_at=updated_at,
            ended_at=parsed_ended_at,
            overall_outcome=overall_outcome,
        )


@dataclass(frozen=True, slots=True)
class RunSessionPointer:
    """Pointer to the current or most recent session."""

    session_id: str
    status: str
    updated_at: datetime
    overall_outcome: str | None

    @property
    def is_terminal(self) -> bool:
        return self.overall_outcome is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": POINTER_SCHEMA_VERSION,
            "session_id": self.session_id,
            "status": self.status,
            "updated_at": _to_timestamp(self.updated_at),
            "overall_outcome": self.overall_outcome,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, source: Path | str) -> RunSessionPointer:
        source_label = str(source)
        schema_version = _validate_positive_int(payload.get("schema_version"), source=f"{source_label}.schema_version", allow_zero=False)
        if schema_version != POINTER_SCHEMA_VERSION:
            raise BookkeepingValidationError(
                f"Unsupported session pointer schema version at {source_label}: {schema_version}"
            )
        session_id = _validate_session_id(payload.get("session_id"), source=f"{source_label}.session_id")
        status = _validate_string(payload.get("status"), source=f"{source_label}.status")
        updated_at = _from_timestamp(payload.get("updated_at"), source=f"{source_label}.updated_at")
        overall_outcome = _validate_outcome(payload.get("overall_outcome"), source=f"{source_label}.overall_outcome")
        if status == "incomplete" and overall_outcome is not None:
            raise BookkeepingValidationError(
                f"Pointer marked incomplete but has a terminal outcome at {source_label}"
            )
        if status != "incomplete" and status != overall_outcome:
            raise BookkeepingValidationError(
                f"Pointer status and outcome disagree at {source_label}: {status!r} vs {overall_outcome!r}"
            )
        return cls(
            session_id=session_id,
            status=status,
            updated_at=updated_at,
            overall_outcome=overall_outcome,
        )


@dataclass(frozen=True, slots=True)
class RunLock:
    """Structured active-run ownership record."""

    session_id: str
    pid: int
    hostname: str
    started_at: datetime
    last_heartbeat_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": LOCK_SCHEMA_VERSION,
            "session_id": self.session_id,
            "pid": self.pid,
            "hostname": self.hostname,
            "started_at": _to_timestamp(self.started_at),
            "last_heartbeat_at": _to_timestamp(self.last_heartbeat_at),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, source: Path | str) -> RunLock:
        source_label = str(source)
        schema_version = _validate_positive_int(payload.get("schema_version"), source=f"{source_label}.schema_version", allow_zero=False)
        if schema_version != LOCK_SCHEMA_VERSION:
            raise BookkeepingValidationError(
                f"Unsupported lock schema version at {source_label}: {schema_version}"
            )
        session_id = _validate_session_id(payload.get("session_id"), source=f"{source_label}.session_id")
        pid = _validate_positive_int(payload.get("pid"), source=f"{source_label}.pid", allow_zero=False)
        hostname = _validate_string(payload.get("hostname"), source=f"{source_label}.hostname")
        started_at = _from_timestamp(payload.get("started_at"), source=f"{source_label}.started_at")
        last_heartbeat_at = _from_timestamp(payload.get("last_heartbeat_at"), source=f"{source_label}.last_heartbeat_at")
        return cls(
            session_id=session_id,
            pid=pid,
            hostname=hostname,
            started_at=started_at,
            last_heartbeat_at=last_heartbeat_at,
        )


class LockState(str, Enum):
    """Current lock state as seen by the session store."""

    ABSENT = "absent"
    ACTIVE = "active"
    STALE = "stale"


@dataclass(frozen=True, slots=True)
class LockInspection:
    """Snapshot of the current lock state."""

    state: LockState
    lock: RunLock | None
    checked_at: datetime
    heartbeat_age: timedelta | None
    host_matches: bool | None
    process_running: bool | None

    @property
    def is_stale(self) -> bool:
        return self.state is LockState.STALE


@dataclass(slots=True)
class RunSessionStore:
    """Feature-local persistence boundary for Ralph sessions."""

    config: RunConfig

    @property
    def ralph_dir(self) -> Path:
        return self.config.ralph_dir

    @property
    def sessions_dir(self) -> Path:
        return self.config.sessions_dir

    @property
    def current_session_path(self) -> Path:
        return self.config.current_session_path

    @property
    def lock_path(self) -> Path:
        return self.config.lock_path

    def ensure_state_tree(self) -> None:
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def create_session(
        self,
        *,
        current_phase: str = DEFAULT_CURRENT_PHASE,
        session_id: str | None = None,
        started_at: datetime | None = None,
    ) -> RunSession:
        created_at = started_at or _utc_now()
        session = RunSession(
            session_id=session_id if session_id is not None else _new_session_id(created_at),
            feature_dir=self.config.feature_dir,
            config=_config_snapshot(self.config),
            current_phase=current_phase,
            iteration_count=0,
            last_phase_outcome=None,
            last_agent_result_metadata=None,
            started_at=created_at,
            updated_at=created_at,
            ended_at=None,
            overall_outcome=None,
        )
        return self.write_session(session)

    def load_session(self, session_id: str) -> RunSession:
        session_id = _validate_session_id(session_id, source="session_id")
        path = self.session_path(session_id)
        if not path.is_file():
            raise BookkeepingValidationError(f"Missing session record: {path}")
        return RunSession.from_dict(_read_json(path), source=path)

    def load_current_pointer(self) -> RunSessionPointer | None:
        if not self.current_session_path.is_file():
            return None
        return RunSessionPointer.from_dict(_read_json(self.current_session_path), source=self.current_session_path)

    def load_current_session(self) -> RunSession | None:
        pointer = self.load_current_pointer()
        if pointer is None:
            return None
        return self.load_session(pointer.session_id)

    def load_lock(self) -> RunLock | None:
        if not self.lock_path.is_file():
            return None
        return RunLock.from_dict(_read_json(self.lock_path), source=self.lock_path)

    def inspect_lock(self, *, now: datetime | None = None) -> LockInspection:
        checked_at = now or _utc_now()
        lock = self.load_lock()
        if lock is None:
            return LockInspection(
                state=LockState.ABSENT,
                lock=None,
                checked_at=checked_at,
                heartbeat_age=None,
                host_matches=None,
                process_running=None,
            )

        host_matches = lock.hostname == _current_hostname()
        process_running = _process_is_running(lock.pid) if host_matches else None
        heartbeat_age = checked_at - lock.last_heartbeat_at
        is_stale = host_matches and process_running is False and heartbeat_age > LOCK_STALE_AFTER
        return LockInspection(
            state=LockState.STALE if is_stale else LockState.ACTIVE,
            lock=lock,
            checked_at=checked_at,
            heartbeat_age=heartbeat_age,
            host_matches=host_matches,
            process_running=process_running,
        )

    def is_lock_stale(self, *, now: datetime | None = None) -> bool:
        return self.inspect_lock(now=now).is_stale

    def acquire_lock(
        self,
        session_id: str,
        *,
        pid: int | None = None,
        hostname: str | None = None,
        started_at: datetime | None = None,
        last_heartbeat_at: datetime | None = None,
    ) -> RunLock:
        session_id = _validate_session_id(session_id, source="session_id")

        created_at = started_at or _utc_now()
        lock = RunLock(
            session_id=session_id,
            pid=_validate_positive_int(os.getpid() if pid is None else pid, source="pid", allow_zero=False),
            hostname=_validate_string(_current_hostname() if hostname is None else hostname, source="hostname"),
            started_at=created_at,
            last_heartbeat_at=last_heartbeat_at or created_at,
        )
        self._validate_lock_for_store(lock)
        self.ensure_state_tree()
        self._write_lock_record_exclusive(lock)
        return lock

    def refresh_lock_heartbeat(
        self,
        session_id: str | None = None,
        *,
        heartbeat_at: datetime | None = None,
    ) -> RunLock:
        lock = self.load_lock()
        if lock is None:
            raise BookkeepingValidationError(f"Cannot refresh heartbeat without an existing lock: {self.lock_path}")
        if session_id is not None and lock.session_id != _validate_session_id(session_id, source="session_id"):
            raise BookkeepingValidationError(
                f"Cannot refresh heartbeat for a different session: {session_id!r} != {lock.session_id!r}"
            )

        next_lock = replace(lock, last_heartbeat_at=heartbeat_at or _utc_now())
        self._validate_lock_for_store(next_lock)
        self._write_lock_record(next_lock)
        return next_lock

    def release_lock(self, session_id: str | None = None) -> None:
        lock = self.load_lock()
        if lock is None:
            return
        if session_id is not None and lock.session_id != _validate_session_id(session_id, source="session_id"):
            raise BookkeepingValidationError(
                f"Cannot release a different session's lock: {session_id!r} != {lock.session_id!r}"
            )
        try:
            self.lock_path.unlink()
        except FileNotFoundError:
            return

    def write_session(self, session: RunSession) -> RunSession:
        self._validate_session_for_store(session)
        self.ensure_state_tree()
        self._write_session_record(session)
        self._write_current_pointer(RunSessionPointer(
            session_id=session.session_id,
            status="incomplete" if not session.is_terminal else session.overall_outcome or "incomplete",
            updated_at=session.updated_at,
            overall_outcome=session.overall_outcome,
        ))
        return session

    def update_session(
        self,
        session_id: str,
        *,
        current_phase: str | None = None,
        iteration_count: int | None = None,
        last_phase_outcome: str | None | object = _MISSING,
        last_agent_result_metadata: Mapping[str, Any] | None | object = _MISSING,
        updated_at: datetime | None = None,
    ) -> RunSession:
        session = self.load_session(session_id)
        if session.is_terminal:
            raise BookkeepingValidationError(f"Cannot update terminal session: {session_id}")

        next_session = session
        if current_phase is not None:
            next_session = replace(next_session, current_phase=_validate_string(current_phase, source="current_phase"))
        if iteration_count is not None:
            next_session = replace(
                next_session,
                iteration_count=_validate_positive_int(iteration_count, source="iteration_count"),
            )
        if last_phase_outcome is not _MISSING:
            next_session = replace(
                next_session,
                last_phase_outcome=_validate_optional_string(last_phase_outcome, source="last_phase_outcome"),
            )
        if last_agent_result_metadata is not _MISSING:
            next_session = replace(
                next_session,
                last_agent_result_metadata=None
                if last_agent_result_metadata is None
                else _validate_mapping(last_agent_result_metadata, source="last_agent_result_metadata"),
            )
        next_session = replace(next_session, updated_at=updated_at or _utc_now())
        return self.write_session(next_session)

    def finalize_session(
        self,
        session_id: str,
        *,
        overall_outcome: str,
        ended_at: datetime | None = None,
    ) -> RunSession:
        session = self.load_session(session_id)
        if session.is_terminal:
            raise BookkeepingValidationError(f"Cannot finalize terminal session: {session_id}")
        terminal_outcome = _validate_outcome(overall_outcome, source="overall_outcome")
        if terminal_outcome is None:
            raise BookkeepingValidationError(f"Session outcome must be terminal: {overall_outcome!r}")
        finished_at = ended_at or _utc_now()

        next_session = replace(
            session,
            overall_outcome=terminal_outcome,
            ended_at=finished_at,
            updated_at=finished_at,
        )
        return self.write_session(next_session)

    def session_path(self, session_id: str) -> Path:
        session_id = _validate_session_id(session_id, source="session_id")
        return self.sessions_dir / f"{session_id}.json"

    def _validate_session_for_store(self, session: RunSession) -> None:
        if session.feature_dir != self.config.feature_dir:
            raise BookkeepingValidationError(
                f"Session belongs to a different feature directory: {session.feature_dir} != {self.config.feature_dir}"
            )
        if not session.current_phase:
            raise BookkeepingValidationError(f"Session has an empty phase name: {session.session_id}")
        if session.iteration_count < 0:
            raise BookkeepingValidationError(f"Session has a negative iteration count: {session.session_id}")
        if session.overall_outcome is not None and session.overall_outcome not in TERMINAL_RUN_OUTCOMES:
            raise BookkeepingValidationError(f"Invalid terminal outcome for session {session.session_id}: {session.overall_outcome!r}")
        if session.last_phase_outcome is not None and not session.last_phase_outcome:
            raise BookkeepingValidationError(f"Invalid phase outcome for session {session.session_id}: {session.last_phase_outcome!r}")

    def _validate_lock_for_store(self, lock: RunLock) -> None:
        if not lock.session_id:
            raise BookkeepingValidationError("Lock session id cannot be empty")
        if lock.pid <= 0:
            raise BookkeepingValidationError(f"Lock pid must be positive: {lock.pid}")
        if not lock.hostname:
            raise BookkeepingValidationError("Lock hostname cannot be empty")
        if lock.last_heartbeat_at < lock.started_at:
            raise BookkeepingValidationError(
                "Lock heartbeat cannot precede the lock start time"
            )

    def _write_session_record(self, session: RunSession) -> None:
        _atomic_write_json(self.session_path(session.session_id), session.to_dict())

    def _write_lock_record(self, lock: RunLock) -> None:
        _atomic_write_json(self.lock_path, lock.to_dict())

    def _write_lock_record_exclusive(self, lock: RunLock) -> None:
        payload = json.dumps(lock.to_dict(), indent=2, sort_keys=True) + "\n"
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(self.lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            raise BookkeepingValidationError(f"Cannot acquire lock while a lock already exists: {self.lock_path}") from exc

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        except Exception:
            try:
                self.lock_path.unlink()
            except FileNotFoundError:
                pass
            raise

    def _write_current_pointer(self, pointer: RunSessionPointer) -> None:
        _atomic_write_json(self.current_session_path, pointer.to_dict())


__all__ = [
    "DEFAULT_CURRENT_PHASE",
    "LOCK_SCHEMA_VERSION",
    "LOCK_STALE_AFTER",
    "LockInspection",
    "LockState",
    "POINTER_SCHEMA_VERSION",
    "RunLock",
    "RunSession",
    "RunSessionPointer",
    "RunSessionStore",
    "SESSION_SCHEMA_VERSION",
    "TERMINAL_RUN_OUTCOMES",
]
