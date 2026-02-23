import os

from django.contrib.auth.hashers import make_password
from django.db import migrations


def seed_single_superuser(apps, schema_editor):
    User = apps.get_model("auth", "User")

    username = os.getenv("SUPERUSER_USERNAME", "").strip()
    email = os.getenv("SUPERUSER_EMAIL", "").strip()
    password = os.getenv("SUPERUSER_PASSWORD", "")

    if not username or not email or not password:
        # Env vars not set: skip safely.
        return

    user = User.objects.filter(username=username).first()
    hashed_password = make_password(password)

    if user is None:
        user = User.objects.create(
            username=username,
            email=email,
            password=hashed_password,
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
    else:
        user.email = email
        user.password = hashed_password
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

    # Enforce at most one superuser.
    User.objects.filter(is_superuser=True).exclude(pk=user.pk).update(
        is_superuser=False,
        is_staff=False,
    )


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(seed_single_superuser, noop_reverse),
    ]
