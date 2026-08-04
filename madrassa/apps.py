from django.apps import AppConfig


class MadrassaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'madrassa'
    verbose_name = 'Madrassa'

    def ready(self):
        from . import signals  # noqa: F401
