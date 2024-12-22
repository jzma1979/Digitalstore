from django.apps import AppConfig

class DigikeyoutletConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'digikeyoutlet'

    def ready(self):
        import digikeyoutlet.signals  # Import your signals module here
