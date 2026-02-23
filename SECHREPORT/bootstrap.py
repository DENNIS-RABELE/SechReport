import os

from django.contrib.auth import get_user_model
from django.db import IntegrityError, OperationalError, connection, transaction
from django.db.utils import ProgrammingError


def _env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


def ensure_single_superuser_from_env():
    if not _env_bool("AUTO_CREATE_SUPERUSER", False):
        return

    username = os.getenv("SUPERUSER_USERNAME", "").strip()
    email = os.getenv("SUPERUSER_EMAIL", "").strip()
    password = os.getenv("SUPERUSER_PASSWORD", "")

    if not username or not password or not email:
        return

    user_model = get_user_model()

    # Serialize startup creation attempts across workers/processes.
    lock_key = 97421031
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_lock(%s)", [lock_key])

        with transaction.atomic():
            superusers = list(
                user_model.objects.filter(is_superuser=True).order_by("id")
            )

            if len(superusers) == 0:
                try:
                    user_model.objects.create_superuser(
                        username=username,
                        email=email,
                        password=password,
                    )
                except IntegrityError:
                    # Another process may have created a user with same username.
                    pass
                return

            if len(superusers) == 1:
                # Keep a single admin account and sync it to configured credentials.
                user = superusers[0]
                user.username = username
                user.email = email
                user.is_staff = True
                user.is_superuser = True
                user.is_active = True
                user.set_password(password)
                try:
                    user.save(
                        update_fields=[
                            "username",
                            "email",
                            "is_staff",
                            "is_superuser",
                            "is_active",
                            "password",
                        ]
                    )
                except IntegrityError:
                    pass
    except (OperationalError, ProgrammingError):
        # Database/tables might be unavailable during startup.
        return
    finally:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s)", [lock_key])
        except Exception:
            pass
