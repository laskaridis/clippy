import os

from django.contrib.auth import get_user_model

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_EMAIL = "admin@clippy.local"
DEFAULT_ADMIN_PASSWORD = "admin"
PRODUCTION_ENVIRONMENTS = {"prod", "production"}


def _is_production_environment() -> bool:
    for env_name in ("DJANGO_ENV", "ENVIRONMENT"):
        declared_env = os.environ.get(env_name, "").strip().lower()
        if declared_env in PRODUCTION_ENVIRONMENTS:
            return True

    return False


def _admin_config() -> tuple[str, str, str]:
    return (
        os.environ.get("DJANGO_ADMIN_USERNAME", DEFAULT_ADMIN_USERNAME),
        os.environ.get("DJANGO_ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL),
        os.environ.get("DJANGO_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD),
    )


def _sync_existing_admin(admin_user, email: str) -> bool:
    changed = False
    if not admin_user.is_staff:
        admin_user.is_staff = True
        changed = True
    if not admin_user.is_superuser:
        admin_user.is_superuser = True
        changed = True
    if email and admin_user.email != email:
        admin_user.email = email
        changed = True
    if changed:
        admin_user.save(update_fields=["is_staff", "is_superuser", "email"])
    return changed


def ensure_admin_user_from_env() -> str:
    """Ensure a local superuser exists using env var overrides."""
    if _is_production_environment():
        return "skipped:production"

    username, email, password = _admin_config()

    user_model = get_user_model()
    admin_user = user_model.objects.filter(username=username).first()

    if admin_user:
        if _sync_existing_admin(admin_user, email):
            return f"updated:{username}"
        return f"exists:{username}"

    user_model.objects.create_superuser(
        username=username,
        email=email,
        password=password,
    )
    return f"created:{username}"
