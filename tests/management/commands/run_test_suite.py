"""
Commande de gestion Django pour exécuter la suite de tests complète.

Cette commande fournit:
- Exécution de tests avec configuration personnalisée
- Rapports détaillés de couverture
- Métriques de performance
- Nettoyage automatique
"""

import os
import sys
import time
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.test.utils import get_runner
from django.db import connection


class Command(BaseCommand):
    """Commande pour exécuter la suite de tests complète."""
    
    help = 'Exécute la suite de tests complète avec rapports détaillés'
    
    def add_arguments(self, parser):
        """Ajoute les arguments de la commande."""
        parser.add_argument(
            '--pattern',
            type=str,
            default='test_*.py',
            help='Motif des fichiers de test à exécuter'
        )
        
        parser.add_argument(
            '--coverage',
            action='store_true',
            help='Active le rapport de couverture'
        )
        
        parser.add_argument(
            '--performance',
            action='store_true',
            help='Active les tests de performance'
        )
        
        parser.add_argument(
            '--parallel',
            type=int,
            default=1,
            help='Nombre de processus parallèles'
        )
        
        parser.add_argument(
            '--failfast',
            action='store_true',
            help='Arrête à la première erreur'
        )
        
        parser.add_argument(
            '--keepdb',
            action='store_true',
            help='Conserve la base de données de test'
        )
        
        parser.add_argument(
            '--debug-mode',
            action='store_true',
            help='Active le mode debug'
        )
        
        parser.add_argument(
            '--output-dir',
            type=str,
            default='test_reports',
            help='Répertoire de sortie des rapports'
        )
        
        parser.add_argument(
            '--exclude-tags',
            type=str,
            nargs='*',
            default=[],
            help='Tags de tests à exclure'
        )
        
        parser.add_argument(
            '--include-tags',
            type=str,
            nargs='*',
            default=[],
            help='Tags de tests à inclure uniquement'
        )
    
    def handle(self, *args, **options):
        """Exécute la commande."""
        start_time = time.time()
        
        self.stdout.write(
            self.style.SUCCESS('🚀 Démarrage de la suite de tests complète')
        )
        
        # Configuration de l'environnement de test
        self._setup_test_environment(options)
        
        # Préparation des rapports
        self._prepare_reports_directory(options['output_dir'])
        
        # Exécution des tests
        try:
            results = self._run_tests(options)
            
            # Génération des rapports
            self._generate_reports(results, options)
            
            # Affichage du résumé
            self._display_summary(results, start_time)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors de l\'exécution des tests: {e}')
            )
            raise CommandError(f'Échec de l\'exécution des tests: {e}')
        
        finally:
            # Nettoyage
            if not options['keepdb']:
                self._cleanup_test_environment()
    
    def _setup_test_environment(self, options):
        """Configure l'environnement de test."""
        self.stdout.write('⚙️  Configuration de l\'environnement de test...')
        
        # Variables d'environnement
        os.environ['TESTING'] = 'True'
        os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'
        
        # Configuration du debug
        if options['debug_mode']:
            os.environ['DEBUG'] = 'True'
        
        # Configuration de la couverture
        if options['coverage']:
            try:
                import coverage
                self.coverage = coverage.Coverage(
                    source=['rail_django_graphql'],
                    omit=[
                        '*/tests/*',
                        '*/migrations/*',
                        '*/venv/*',
                        '*/env/*',
                    ]
                )
                self.coverage.start()
                self.stdout.write('✅ Couverture de code activée')
            except ImportError:
                self.stdout.write(
                    self.style.WARNING('⚠️  Module coverage non disponible')
                )
                options['coverage'] = False
    
    def _prepare_reports_directory(self, output_dir):
        """Prépare le répertoire des rapports."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            self.stdout.write(f'📁 Répertoire de rapports créé: {output_dir}')
    
    def _run_tests(self, options):
        """Exécute les tests."""
        self.stdout.write('🧪 Exécution des tests...')
        
        # Configuration du runner de tests
        test_runner_class = get_runner(settings)
        test_runner = test_runner_class(
            verbosity=2,
            interactive=False,
            failfast=options['failfast'],
            keepdb=options['keepdb'],
            parallel=options['parallel'] if options['parallel'] > 1 else 0,
        )
        
        # Labels de tests à exécuter
        test_labels = self._get_test_labels(options)
        
        # Exécution
        start_time = time.time()
        
        try:
            result = test_runner.run_tests(test_labels)
            execution_time = time.time() - start_time
            
            return {
                'result': result,
                'execution_time': execution_time,
                'test_count': getattr(test_runner, 'test_count', 0),
                'failure_count': getattr(test_runner, 'failure_count', 0),
                'error_count': getattr(test_runner, 'error_count', 0),
            }
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur pendant l\'exécution: {e}')
            )
            raise
    
    def _get_test_labels(self, options):
        """Détermine les labels de tests à exécuter."""
        labels = []
        
        # Tests de base
        labels.extend([
            'tests.test_core',
            'tests.test_generators',
            'tests.test_integration',
            'tests.test_business_methods',
        ])
        
        # Tests de performance si demandés
        if options['performance']:
            labels.extend([
                'tests.test_performance',
            ])
        
        # Filtrage par tags
        if options['include_tags']:
            # Logique pour inclure seulement certains tags
            pass
        
        if options['exclude_tags']:
            # Logique pour exclure certains tags
            pass
        
        return labels
    
    def _generate_reports(self, results, options):
        """Génère les rapports de test."""
        self.stdout.write('📊 Génération des rapports...')
        
        output_dir = options['output_dir']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Rapport de couverture
        if options['coverage'] and hasattr(self, 'coverage'):
            self.coverage.stop()
            
            # Rapport HTML
            html_dir = os.path.join(output_dir, f'coverage_html_{timestamp}')
            self.coverage.html_report(directory=html_dir)
            
            # Rapport XML
            xml_file = os.path.join(output_dir, f'coverage_{timestamp}.xml')
            self.coverage.xml_report(outfile=xml_file)
            
            self.stdout.write(f'✅ Rapport de couverture généré: {html_dir}')
        
        # Rapport de performance
        if options['performance']:
            self._generate_performance_report(results, output_dir, timestamp)
        
        # Rapport de résumé
        self._generate_summary_report(results, output_dir, timestamp)
    
    def _generate_performance_report(self, results, output_dir, timestamp):
        """Génère le rapport de performance."""
        try:
            from tests.models import TestPerformanceModel
            
            perf_data = TestPerformanceModel.objects.all().order_by('-created_at')[:100]
            
            report_file = os.path.join(output_dir, f'performance_{timestamp}.json')
            
            import json
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': timestamp,
                    'total_tests': len(perf_data),
                    'tests': [
                        {
                            'name': test.name,
                            'execution_time': test.execution_time,
                            'memory_usage': test.memory_usage,
                            'created_at': test.created_at.isoformat(),
                        }
                        for test in perf_data
                    ]
                }, f, indent=2, ensure_ascii=False)
            
            self.stdout.write(f'✅ Rapport de performance généré: {report_file}')
        
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Erreur génération rapport performance: {e}')
            )
    
    def _generate_summary_report(self, results, output_dir, timestamp):
        """Génère le rapport de résumé."""
        report_file = os.path.join(output_dir, f'summary_{timestamp}.json')
        
        summary = {
            'timestamp': timestamp,
            'execution_time': results['execution_time'],
            'test_result': results['result'],
            'test_count': results.get('test_count', 0),
            'failure_count': results.get('failure_count', 0),
            'error_count': results.get('error_count', 0),
            'success_rate': self._calculate_success_rate(results),
            'database_queries': len(connection.queries),
            'environment': {
                'python_version': sys.version,
                'django_version': self._get_django_version(),
                'testing_mode': os.environ.get('TESTING', 'False'),
            }
        }
        
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(f'✅ Rapport de résumé généré: {report_file}')
    
    def _calculate_success_rate(self, results):
        """Calcule le taux de succès."""
        total = results.get('test_count', 0)
        failures = results.get('failure_count', 0)
        errors = results.get('error_count', 0)
        
        if total == 0:
            return 0.0
        
        success = total - failures - errors
        return (success / total) * 100
    
    def _get_django_version(self):
        """Récupère la version de Django."""
        try:
            import django
            return django.get_version()
        except Exception:
            return 'Unknown'
    
    def _display_summary(self, results, start_time):
        """Affiche le résumé des résultats."""
        total_time = time.time() - start_time
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📋 RÉSUMÉ DE L\'EXÉCUTION DES TESTS'))
        self.stdout.write('='*60)
        
        # Résultats généraux
        self.stdout.write(f'⏱️  Temps total: {total_time:.2f} secondes')
        self.stdout.write(f'🧪 Tests exécutés: {results.get("test_count", 0)}')
        self.stdout.write(f'❌ Échecs: {results.get("failure_count", 0)}')
        self.stdout.write(f'💥 Erreurs: {results.get("error_count", 0)}')
        
        # Taux de succès
        success_rate = self._calculate_success_rate(results)
        if success_rate >= 95:
            style = self.style.SUCCESS
            icon = '✅'
        elif success_rate >= 80:
            style = self.style.WARNING
            icon = '⚠️'
        else:
            style = self.style.ERROR
            icon = '❌'
        
        self.stdout.write(f'{icon} Taux de succès: {style(f"{success_rate:.1f}%")}')
        
        # Requêtes base de données
        self.stdout.write(f'🗄️  Requêtes DB: {len(connection.queries)}')
        
        # Statut final
        if results['result'] == 0:
            self.stdout.write(self.style.SUCCESS('\n🎉 TOUS LES TESTS ONT RÉUSSI!'))
        else:
            self.stdout.write(self.style.ERROR('\n💥 CERTAINS TESTS ONT ÉCHOUÉ!'))
        
        self.stdout.write('='*60)
    
    def _cleanup_test_environment(self):
        """Nettoie l'environnement de test."""
        self.stdout.write('🧹 Nettoyage de l\'environnement de test...')
        
        # Arrêter la couverture si active
        if hasattr(self, 'coverage'):
            try:
                self.coverage.stop()
            except Exception:
                pass
        
        # Nettoyer les variables d'environnement
        env_vars_to_clean = ['TESTING', 'DEBUG']
        for var in env_vars_to_clean:
            if var in os.environ:
                del os.environ[var]
        
        self.stdout.write('✅ Nettoyage terminé')
