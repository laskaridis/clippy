import os

from django.contrib.auth import get_user_model


def _is_production_environment() -> bool:
    for env_name in ("DJANGO_ENV", "ENVIRONMENT"):
        declared_env = os.environ.get(env_name, "").strip().lower()
        if declared_env in {"prod", "production"}:
            return True

    return False


def ensure_admin_user_from_env() -> str:
    """Ensure a local superuser exists using env var overrides."""
    if _is_production_environment():
        return "skipped:production"

    username = os.environ.get("DJANGO_ADMIN_USERNAME", "admin")
    email = os.environ.get("DJANGO_ADMIN_EMAIL", "admin@clippy.local")
    password = os.environ.get("DJANGO_ADMIN_PASSWORD", "admin")

    user_model = get_user_model()
    admin_user = user_model.objects.filter(username=username).first()

    if admin_user:
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
            return f"updated:{username}"
        return f"exists:{username}"

    user_model.objects.create_superuser(
        username=username,
        email=email,
        password=password,
    )
    return f"created:{username}"
