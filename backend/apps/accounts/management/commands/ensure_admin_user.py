import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Ensure a superuser exists for local development workflows."

    def handle(self, *args, **options):
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
                self.stdout.write(self.style.SUCCESS(f"Updated existing admin user '{username}'."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Admin user '{username}' already exists."))
            return

        user_model.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        self.stdout.write(self.style.SUCCESS(f"Created admin user '{username}'."))
