"""Development settings."""

from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

SECRET_KEY = env("DJANGO_SECRET_KEY", default="django-insecure-dev-only")

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
