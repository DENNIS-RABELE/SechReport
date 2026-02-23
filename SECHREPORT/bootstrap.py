import os
import logging

from django.contrib.auth import get_user_model
from django.db import IntegrityError, OperationalError, connection, transaction
from django.db.utils import ProgrammingError

logger = logging.getLogger(__name__)


def _env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


def ensure_single_superuser_from_env():
    if not _env_bool("AUTO_CREATE_SUPERUSER", False):
        logger.info("superuser-bootstrap: disabled (AUTO_CREATE_SUPERUSER=false)")
        return

    username = os.getenv("SUPERUSER_USERNAME", "").strip()
    email = os.getenv("SUPERUSER_EMAIL", "").strip()
    password = os.getenv("SUPERUSER_PASSWORD", "")

    if not username or not password or not email:
        logger.warning(
            "superuser-bootstrap: skipped (missing SUPERUSER_USERNAME/SUPERUSER_EMAIL/SUPERUSER_PASSWORD)"
        )
        return

    user_model = get_user_model()

    # Serialize startup creation attempts across workers/processes.
    lock_key = 97421031
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_lock(%s)", [lock_key])

        with transaction.atomic():
            user = user_model.objects.filter(username=username).first()
            if user is None:
                user = user_model.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                )
                logger.info(
                    "superuser-bootstrap: created target user '%s' from env",
                    username,
                )
            else:
                user.email = email
                user.set_password(password)
                logger.info(
                    "superuser-bootstrap: updated credentials for existing user '%s'",
                    username,
                )

            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save(
                update_fields=[
                    "email",
                    "password",
                    "is_staff",
                    "is_superuser",
                    "is_active",
                ]
            )

            demoted = (
                user_model.objects.filter(is_superuser=True).exclude(pk=user.pk).update(
                    is_superuser=False,
                    is_staff=False,
                )
            )
            logger.info(
                "superuser-bootstrap: enforced single superuser '%s' (demoted=%s)",
                username,
                demoted,
            )
    except (OperationalError, ProgrammingError):
        # Database/tables might be unavailable during startup.
        logger.exception(
            "superuser-bootstrap: skipped due to database not ready or tables missing"
        )
        return
    except IntegrityError:
        logger.exception("superuser-bootstrap: failed due to integrity error")
        return
    finally:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s)", [lock_key])
        except Exception:
            pass
