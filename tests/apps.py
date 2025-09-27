"""
Configuration de l'application de tests Django.

Ce module configure:
- Application Django pour les tests
- Configuration des modèles de test
- Signaux et hooks de test
"""

from django.apps import AppConfig


class TestsConfig(AppConfig):
    """Configuration de l'application de tests."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tests'
    verbose_name = 'Tests GraphQL Auto'
    
    def ready(self):
        """Initialisation de l'application de tests."""
        # Importer les signaux si nécessaire
        try:
            from . import signals  # noqa
        except ImportError:
            pass
        
        # Configuration spécifique aux tests
        self._configure_test_environment()
    
    def _configure_test_environment(self):
        """Configure l'environnement de test."""
        import os
        
        # S'assurer que nous sommes en mode test
        if not os.environ.get('TESTING'):
            os.environ['TESTING'] = 'True'
        
        # Configuration des logs pour les tests
        import logging
        
        # Réduire le niveau de log pour certains modules pendant les tests
        logging.getLogger('django.db.backends').setLevel(logging.WARNING)
        logging.getLogger('graphene').setLevel(logging.WARNING)
