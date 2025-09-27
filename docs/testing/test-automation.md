# Automatisation des Tests - Django GraphQL Auto

Ce guide détaille les stratégies et outils d'automatisation des tests pour les applications Django GraphQL, couvrant l'exécution automatisée, les rapports, et l'intégration continue.

## 📋 Table des Matières

- [Vue d'Ensemble](#vue-densemble)
- [Configuration de l'Automatisation](#configuration-de-lautomatisation)
- [Exécution Automatisée](#exécution-automatisée)
- [Rapports et Métriques](#rapports-et-métriques)
- [Tests Parallèles](#tests-parallèles)
- [Tests de Régression](#tests-de-régression)
- [Surveillance Continue](#surveillance-continue)
- [Intégration CI/CD](#intégration-cicd)
- [Outils et Scripts](#outils-et-scripts)

## 🎯 Vue d'Ensemble

### Architecture de l'Automatisation

```python
# tests/automation/core.py
"""Core de l'automatisation des tests."""

import os
import sys
import time
import json
import subprocess
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


@dataclass
class TestConfig:
    """Configuration pour l'automatisation des tests."""
    
    # Chemins et fichiers
    test_directory: str = "tests"
    output_directory: str = "test_reports"
    coverage_directory: str = "htmlcov"
    
    # Exécution
    parallel_workers: int = 4
    timeout_seconds: int = 300
    retry_failed_tests: int = 2
    fail_fast: bool = False
    
    # Filtres
    test_patterns: List[str] = None
    exclude_patterns: List[str] = None
    test_tags: List[str] = None
    
    # Rapports
    generate_html_report: bool = True
    generate_json_report: bool = True
    generate_junit_xml: bool = True
    coverage_threshold: float = 80.0
    
    # Notifications
    send_notifications: bool = False
    notification_emails: List[str] = None
    slack_webhook: Optional[str] = None
    
    # Surveillance
    monitor_performance: bool = True
    performance_threshold_ms: int = 1000
    memory_threshold_mb: int = 512


@dataclass
class TestResult:
    """Résultat d'exécution de test."""
    
    test_name: str
    status: str  # passed, failed, skipped, error
    duration: float
    error_message: Optional[str] = None
    traceback: Optional[str] = None
    output: Optional[str] = None
    memory_usage: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TestSuiteResult:
    """Résultat d'exécution d'une suite de tests."""
    
    suite_name: str
    start_time: datetime
    end_time: datetime
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    coverage_percentage: float
    results: List[TestResult]
    
    @property
    def duration(self) -> timedelta:
        return self.end_time - self.start_time
    
    @property
    def success_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'suite_name': self.suite_name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_seconds': self.duration.total_seconds(),
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'skipped_tests': self.skipped_tests,
            'error_tests': self.error_tests,
            'success_rate': self.success_rate,
            'coverage_percentage': self.coverage_percentage,
            'results': [result.to_dict() for result in self.results]
        }


class TestAutomationEngine:
    """Moteur principal d'automatisation des tests."""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.results_history = []
        
        # Créer les répertoires nécessaires
        Path(self.config.output_directory).mkdir(parents=True, exist_ok=True)
        Path(self.config.coverage_directory).mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self) -> logging.Logger:
        """Configure le logging pour l'automatisation."""
        
        logger = logging.getLogger('test_automation')
        logger.setLevel(logging.INFO)
        
        # Handler pour fichier
        file_handler = logging.FileHandler(
            Path(self.config.output_directory) / 'automation.log'
        )
        file_handler.setLevel(logging.INFO)
        
        # Handler pour console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def run_test_suite(self, suite_name: str = "full") -> TestSuiteResult:
        """Exécute une suite de tests complète."""
        
        self.logger.info(f"Démarrage de la suite de tests: {suite_name}")
        start_time = datetime.now()
        
        try:
            # Préparer l'environnement
            self._prepare_test_environment()
            
            # Exécuter les tests
            test_results = self._execute_tests()
            
            # Générer le rapport de couverture
            coverage_percentage = self._generate_coverage_report()
            
            # Créer le résultat de la suite
            end_time = datetime.now()
            suite_result = self._create_suite_result(
                suite_name, start_time, end_time, test_results, coverage_percentage
            )
            
            # Générer les rapports
            self._generate_reports(suite_result)
            
            # Envoyer les notifications
            if self.config.send_notifications:
                self._send_notifications(suite_result)
            
            # Sauvegarder l'historique
            self.results_history.append(suite_result)
            
            self.logger.info(f"Suite de tests terminée: {suite_result.success_rate:.1f}% de réussite")
            
            return suite_result
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'exécution de la suite: {e}")
            raise
    
    def _prepare_test_environment(self):
        """Prépare l'environnement de test."""
        
        self.logger.info("Préparation de l'environnement de test")
        
        # Nettoyer les anciens rapports
        self._cleanup_old_reports()
        
        # Vérifier les dépendances
        self._check_dependencies()
        
        # Configurer les variables d'environnement
        os.environ['TESTING'] = 'true'
        os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'
        
        # Initialiser la base de données de test
        self._setup_test_database()
    
    def _execute_tests(self) -> List[TestResult]:
        """Exécute les tests et retourne les résultats."""
        
        self.logger.info("Exécution des tests")
        
        # Construire la commande pytest
        cmd = self._build_pytest_command()
        
        # Exécuter les tests
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path.cwd()
        )
        
        # Surveiller l'exécution avec timeout
        try:
            stdout, stderr = process.communicate(timeout=self.config.timeout_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            raise TimeoutError(f"Tests timeout après {self.config.timeout_seconds}s")
        
        # Parser les résultats
        return self._parse_test_results(stdout, stderr, process.returncode)
    
    def _build_pytest_command(self) -> List[str]:
        """Construit la commande pytest."""
        
        cmd = [
            sys.executable, '-m', 'pytest',
            self.config.test_directory,
            '--verbose',
            '--tb=short',
            f'--workers={self.config.parallel_workers}',
            '--cov=.',
            f'--cov-report=html:{self.config.coverage_directory}',
            '--cov-report=json',
            '--cov-report=term-missing',
            '--junit-xml=test_results.xml'
        ]
        
        # Ajouter les patterns de test
        if self.config.test_patterns:
            for pattern in self.config.test_patterns:
                cmd.extend(['-k', pattern])
        
        # Ajouter les exclusions
        if self.config.exclude_patterns:
            for pattern in self.config.exclude_patterns:
                cmd.extend(['--ignore', pattern])
        
        # Ajouter les tags
        if self.config.test_tags:
            for tag in self.config.test_tags:
                cmd.extend(['-m', tag])
        
        # Options supplémentaires
        if self.config.fail_fast:
            cmd.append('--maxfail=1')
        
        return cmd
    
    def _parse_test_results(self, stdout: str, stderr: str, 
                           return_code: int) -> List[TestResult]:
        """Parse les résultats des tests depuis la sortie pytest."""
        
        results = []
        
        # Parser la sortie pytest (format verbose)
        lines = stdout.split('\n')
        current_test = None
        
        for line in lines:
            line = line.strip()
            
            # Détecter le début d'un test
            if '::' in line and ('PASSED' in line or 'FAILED' in line or 'SKIPPED' in line):
                parts = line.split()
                test_name = parts[0]
                status = parts[-1].lower()
                
                # Extraire la durée si disponible
                duration = 0.0
                for part in parts:
                    if 's' in part and part.replace('.', '').replace('s', '').isdigit():
                        duration = float(part.replace('s', ''))
                        break
                
                result = TestResult(
                    test_name=test_name,
                    status=status,
                    duration=duration
                )
                
                results.append(result)
        
        # Si aucun résultat parsé, créer un résultat d'erreur
        if not results and return_code != 0:
            results.append(TestResult(
                test_name="test_execution",
                status="error",
                duration=0.0,
                error_message="Failed to execute tests",
                output=stderr
            ))
        
        return results
    
    def _generate_coverage_report(self) -> float:
        """Génère le rapport de couverture et retourne le pourcentage."""
        
        try:
            # Lire le rapport de couverture JSON
            coverage_file = Path('coverage.json')
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                
                total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0.0)
                return total_coverage
            
        except Exception as e:
            self.logger.warning(f"Impossible de lire le rapport de couverture: {e}")
        
        return 0.0
    
    def _create_suite_result(self, suite_name: str, start_time: datetime,
                           end_time: datetime, test_results: List[TestResult],
                           coverage_percentage: float) -> TestSuiteResult:
        """Crée le résultat de la suite de tests."""
        
        # Compter les résultats par statut
        status_counts = {
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'error': 0
        }
        
        for result in test_results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1
        
        return TestSuiteResult(
            suite_name=suite_name,
            start_time=start_time,
            end_time=end_time,
            total_tests=len(test_results),
            passed_tests=status_counts['passed'],
            failed_tests=status_counts['failed'],
            skipped_tests=status_counts['skipped'],
            error_tests=status_counts['error'],
            coverage_percentage=coverage_percentage,
            results=test_results
        )
    
    def _generate_reports(self, suite_result: TestSuiteResult):
        """Génère les différents rapports."""
        
        self.logger.info("Génération des rapports")
        
        # Rapport JSON
        if self.config.generate_json_report:
            self._generate_json_report(suite_result)
        
        # Rapport HTML
        if self.config.generate_html_report:
            self._generate_html_report(suite_result)
        
        # Rapport JUnit XML (déjà généré par pytest)
        if self.config.generate_junit_xml:
            self._process_junit_xml()
    
    def _generate_json_report(self, suite_result: TestSuiteResult):
        """Génère un rapport JSON détaillé."""
        
        report_file = Path(self.config.output_directory) / f'test_report_{suite_result.start_time.strftime("%Y%m%d_%H%M%S")}.json'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(suite_result.to_dict(), f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Rapport JSON généré: {report_file}")
    
    def _generate_html_report(self, suite_result: TestSuiteResult):
        """Génère un rapport HTML."""
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Rapport de Tests - {suite_name}</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .metric {{ text-align: center; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
                .metric h3 {{ margin: 0; color: #333; }}
                .metric .value {{ font-size: 24px; font-weight: bold; }}
                .passed {{ color: #28a745; }}
                .failed {{ color: #dc3545; }}
                .skipped {{ color: #ffc107; }}
                .error {{ color: #fd7e14; }}
                .tests-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                .tests-table th, .tests-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .tests-table th {{ background-color: #f2f2f2; }}
                .status-passed {{ background-color: #d4edda; }}
                .status-failed {{ background-color: #f8d7da; }}
                .status-skipped {{ background-color: #fff3cd; }}
                .status-error {{ background-color: #f5c6cb; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Rapport de Tests - {suite_name}</h1>
                <p><strong>Date:</strong> {start_time}</p>
                <p><strong>Durée:</strong> {duration}</p>
                <p><strong>Couverture:</strong> {coverage:.1f}%</p>
            </div>
            
            <div class="summary">
                <div class="metric">
                    <h3>Total</h3>
                    <div class="value">{total_tests}</div>
                </div>
                <div class="metric">
                    <h3 class="passed">Réussis</h3>
                    <div class="value passed">{passed_tests}</div>
                </div>
                <div class="metric">
                    <h3 class="failed">Échoués</h3>
                    <div class="value failed">{failed_tests}</div>
                </div>
                <div class="metric">
                    <h3 class="skipped">Ignorés</h3>
                    <div class="value skipped">{skipped_tests}</div>
                </div>
                <div class="metric">
                    <h3 class="error">Erreurs</h3>
                    <div class="value error">{error_tests}</div>
                </div>
                <div class="metric">
                    <h3>Taux de Réussite</h3>
                    <div class="value">{success_rate:.1f}%</div>
                </div>
            </div>
            
            <h2>Détail des Tests</h2>
            <table class="tests-table">
                <thead>
                    <tr>
                        <th>Test</th>
                        <th>Statut</th>
                        <th>Durée (s)</th>
                        <th>Message d'Erreur</th>
                    </tr>
                </thead>
                <tbody>
                    {test_rows}
                </tbody>
            </table>
        </body>
        </html>
        """
        
        # Générer les lignes de tests
        test_rows = []
        for result in suite_result.results:
            error_msg = result.error_message or ""
            if len(error_msg) > 100:
                error_msg = error_msg[:100] + "..."
            
            row = f"""
                <tr class="status-{result.status}">
                    <td>{result.test_name}</td>
                    <td>{result.status.upper()}</td>
                    <td>{result.duration:.3f}</td>
                    <td>{error_msg}</td>
                </tr>
            """
            test_rows.append(row)
        
        # Remplir le template
        html_content = html_template.format(
            suite_name=suite_result.suite_name,
            start_time=suite_result.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            duration=str(suite_result.duration),
            coverage=suite_result.coverage_percentage,
            total_tests=suite_result.total_tests,
            passed_tests=suite_result.passed_tests,
            failed_tests=suite_result.failed_tests,
            skipped_tests=suite_result.skipped_tests,
            error_tests=suite_result.error_tests,
            success_rate=suite_result.success_rate,
            test_rows="".join(test_rows)
        )
        
        # Sauvegarder le rapport
        report_file = Path(self.config.output_directory) / f'test_report_{suite_result.start_time.strftime("%Y%m%d_%H%M%S")}.html'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Rapport HTML généré: {report_file}")
    
    def _send_notifications(self, suite_result: TestSuiteResult):
        """Envoie les notifications de résultats."""
        
        self.logger.info("Envoi des notifications")
        
        # Email
        if self.config.notification_emails:
            self._send_email_notification(suite_result)
        
        # Slack
        if self.config.slack_webhook:
            self._send_slack_notification(suite_result)
    
    def _send_email_notification(self, suite_result: TestSuiteResult):
        """Envoie une notification par email."""
        
        try:
            # Créer le message
            msg = MIMEMultipart()
            msg['From'] = 'test-automation@example.com'
            msg['To'] = ', '.join(self.config.notification_emails)
            msg['Subject'] = f'Résultats Tests - {suite_result.suite_name} - {suite_result.success_rate:.1f}%'
            
            # Corps du message
            body = f"""
            Résultats de la suite de tests: {suite_result.suite_name}
            
            Date: {suite_result.start_time.strftime("%Y-%m-%d %H:%M:%S")}
            Durée: {suite_result.duration}
            
            Résultats:
            - Total: {suite_result.total_tests}
            - Réussis: {suite_result.passed_tests}
            - Échoués: {suite_result.failed_tests}
            - Ignorés: {suite_result.skipped_tests}
            - Erreurs: {suite_result.error_tests}
            
            Taux de réussite: {suite_result.success_rate:.1f}%
            Couverture: {suite_result.coverage_percentage:.1f}%
            
            {'✅ Tous les tests sont passés!' if suite_result.failed_tests == 0 else '❌ Des tests ont échoué.'}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Envoyer l'email (configuration SMTP nécessaire)
            # server = smtplib.SMTP('localhost')
            # server.send_message(msg)
            # server.quit()
            
            self.logger.info("Notification email envoyée")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi de l'email: {e}")
    
    def _send_slack_notification(self, suite_result: TestSuiteResult):
        """Envoie une notification Slack."""
        
        try:
            import requests
            
            # Déterminer la couleur du message
            if suite_result.failed_tests == 0:
                color = "good"
                emoji = ":white_check_mark:"
            else:
                color = "danger"
                emoji = ":x:"
            
            # Créer le payload
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"{emoji} Résultats Tests - {suite_result.suite_name}",
                        "fields": [
                            {
                                "title": "Taux de Réussite",
                                "value": f"{suite_result.success_rate:.1f}%",
                                "short": True
                            },
                            {
                                "title": "Couverture",
                                "value": f"{suite_result.coverage_percentage:.1f}%",
                                "short": True
                            },
                            {
                                "title": "Tests Réussis",
                                "value": str(suite_result.passed_tests),
                                "short": True
                            },
                            {
                                "title": "Tests Échoués",
                                "value": str(suite_result.failed_tests),
                                "short": True
                            }
                        ],
                        "footer": f"Durée: {suite_result.duration}",
                        "ts": int(suite_result.start_time.timestamp())
                    }
                ]
            }
            
            # Envoyer la notification
            response = requests.post(self.config.slack_webhook, json=payload)
            response.raise_for_status()
            
            self.logger.info("Notification Slack envoyée")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi de la notification Slack: {e}")
    
    def _cleanup_old_reports(self):
        """Nettoie les anciens rapports."""
        
        output_dir = Path(self.config.output_directory)
        
        # Supprimer les rapports de plus de 30 jours
        cutoff_date = datetime.now() - timedelta(days=30)
        
        for file_path in output_dir.glob('test_report_*'):
            if file_path.stat().st_mtime < cutoff_date.timestamp():
                file_path.unlink()
                self.logger.info(f"Ancien rapport supprimé: {file_path}")
    
    def _check_dependencies(self):
        """Vérifie que toutes les dépendances sont installées."""
        
        required_packages = [
            'pytest',
            'pytest-cov',
            'pytest-xdist',
            'pytest-django'
        ]
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                raise ImportError(f"Package requis manquant: {package}")
    
    def _setup_test_database(self):
        """Configure la base de données de test."""
        
        try:
            # Exécuter les migrations de test
            subprocess.run([
                sys.executable, 'manage.py', 'migrate',
                '--settings=tests.settings',
                '--run-syncdb'
            ], check=True, capture_output=True)
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Erreur lors de la configuration de la base de données: {e}")
            raise
    
    def _process_junit_xml(self):
        """Traite le fichier JUnit XML généré par pytest."""
        
        junit_file = Path('test_results.xml')
        if junit_file.exists():
            # Déplacer vers le répertoire de rapports
            target_file = Path(self.config.output_directory) / 'junit_results.xml'
            junit_file.rename(target_file)
            self.logger.info(f"Rapport JUnit XML déplacé vers: {target_file}")


class ContinuousTestRunner:
    """Runner pour les tests en continu."""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.automation_engine = TestAutomationEngine(config)
        self.is_running = False
        self.watch_thread = None
    
    def start_continuous_testing(self, watch_directories: List[str] = None):
        """Démarre les tests en continu."""
        
        watch_directories = watch_directories or ['src', 'tests']
        
        self.is_running = True
        self.watch_thread = threading.Thread(
            target=self._watch_files,
            args=(watch_directories,)
        )
        self.watch_thread.start()
        
        print("Tests en continu démarrés. Appuyez sur Ctrl+C pour arrêter.")
    
    def stop_continuous_testing(self):
        """Arrête les tests en continu."""
        
        self.is_running = False
        if self.watch_thread:
            self.watch_thread.join()
    
    def _watch_files(self, watch_directories: List[str]):
        """Surveille les changements de fichiers."""
        
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class TestHandler(FileSystemEventHandler):
                def __init__(self, runner):
                    self.runner = runner
                    self.last_run = 0
                
                def on_modified(self, event):
                    if event.is_directory:
                        return
                    
                    # Éviter les exécutions trop fréquentes
                    now = time.time()
                    if now - self.last_run < 5:  # 5 secondes minimum
                        return
                    
                    # Filtrer les fichiers Python
                    if event.src_path.endswith('.py'):
                        print(f"Changement détecté: {event.src_path}")
                        self.runner.run_affected_tests(event.src_path)
                        self.last_run = now
            
            observer = Observer()
            handler = TestHandler(self)
            
            for directory in watch_directories:
                if Path(directory).exists():
                    observer.schedule(handler, directory, recursive=True)
            
            observer.start()
            
            try:
                while self.is_running:
                    time.sleep(1)
            finally:
                observer.stop()
                observer.join()
                
        except ImportError:
            print("watchdog non installé. Utilisation du polling...")
            self._poll_files(watch_directories)
    
    def _poll_files(self, watch_directories: List[str]):
        """Surveillance par polling (fallback)."""
        
        file_times = {}
        
        while self.is_running:
            for directory in watch_directories:
                dir_path = Path(directory)
                if not dir_path.exists():
                    continue
                
                for file_path in dir_path.rglob('*.py'):
                    mtime = file_path.stat().st_mtime
                    
                    if str(file_path) not in file_times:
                        file_times[str(file_path)] = mtime
                    elif file_times[str(file_path)] < mtime:
                        print(f"Changement détecté: {file_path}")
                        self.run_affected_tests(str(file_path))
                        file_times[str(file_path)] = mtime
            
            time.sleep(2)  # Vérifier toutes les 2 secondes
    
    def run_affected_tests(self, changed_file: str):
        """Exécute les tests affectés par un changement de fichier."""
        
        # Logique simple: si c'est un fichier de test, l'exécuter
        # sinon, exécuter tous les tests
        
        if 'test_' in Path(changed_file).name:
            # Exécuter ce test spécifique
            config = TestConfig(
                test_patterns=[changed_file],
                parallel_workers=1,
                generate_html_report=False
            )
            engine = TestAutomationEngine(config)
            result = engine.run_test_suite(f"affected_{int(time.time())}")
            
            print(f"Résultat: {result.success_rate:.1f}% de réussite")
        else:
            # Exécuter tous les tests (version rapide)
            config = TestConfig(
                parallel_workers=2,
                generate_html_report=False,
                fail_fast=True
            )
            engine = TestAutomationEngine(config)
            result = engine.run_test_suite(f"quick_{int(time.time())}")
            
            print(f"Tests rapides: {result.success_rate:.1f}% de réussite")


# Scripts d'automatisation
class AutomationScripts:
    """Scripts utilitaires pour l'automatisation."""
    
    @staticmethod
    def create_nightly_test_script():
        """Crée un script pour les tests nocturnes."""
        
        script_content = '''#!/usr/bin/env python3
"""Script de tests nocturnes automatisés."""

import sys
from pathlib import Path

# Ajouter le répertoire du projet au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.automation.core import TestAutomationEngine, TestConfig

def main():
    """Exécute les tests nocturnes complets."""
    
    config = TestConfig(
        parallel_workers=8,
        timeout_seconds=1800,  # 30 minutes
        coverage_threshold=85.0,
        send_notifications=True,
        notification_emails=['dev-team@example.com'],
        generate_html_report=True,
        generate_json_report=True
    )
    
    engine = TestAutomationEngine(config)
    result = engine.run_test_suite("nightly")
    
    # Vérifier les seuils de qualité
    if result.success_rate < 95.0:
        print(f"ATTENTION: Taux de réussite faible: {result.success_rate:.1f}%")
        sys.exit(1)
    
    if result.coverage_percentage < config.coverage_threshold:
        print(f"ATTENTION: Couverture insuffisante: {result.coverage_percentage:.1f}%")
        sys.exit(1)
    
    print("Tests nocturnes réussis!")
    sys.exit(0)

if __name__ == "__main__":
    main()
'''
        
        script_path = Path('scripts/nightly_tests.py')
        script_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Rendre exécutable sur Unix
        if sys.platform != 'win32':
            script_path.chmod(0o755)
        
        return script_path
    
    @staticmethod
    def create_performance_test_script():
        """Crée un script pour les tests de performance."""
        
        script_content = '''#!/usr/bin/env python3
"""Script de tests de performance automatisés."""

import sys
from pathlib import Path

# Ajouter le répertoire du projet au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.automation.core import TestAutomationEngine, TestConfig

def main():
    """Exécute les tests de performance."""
    
    config = TestConfig(
        test_patterns=['*performance*', '*benchmark*'],
        parallel_workers=1,  # Tests de performance en série
        timeout_seconds=3600,  # 1 heure
        monitor_performance=True,
        performance_threshold_ms=2000,
        generate_html_report=True
    )
    
    engine = TestAutomationEngine(config)
    result = engine.run_test_suite("performance")
    
    # Analyser les résultats de performance
    slow_tests = [
        test for test in result.results
        if test.duration > (config.performance_threshold_ms / 1000)
    ]
    
    if slow_tests:
        print(f"ATTENTION: {len(slow_tests)} tests lents détectés:")
        for test in slow_tests:
            print(f"  - {test.test_name}: {test.duration:.3f}s")
    
    print(f"Tests de performance terminés: {result.success_rate:.1f}% de réussite")

if __name__ == "__main__":
    main()
'''
        
        script_path = Path('scripts/performance_tests.py')
        script_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Rendre exécutable sur Unix
        if sys.platform != 'win32':
            script_path.chmod(0o755)
        
        return script_path
    
    @staticmethod
    def create_regression_test_script():
        """Crée un script pour les tests de régression."""
        
        script_content = '''#!/usr/bin/env python3
"""Script de tests de régression automatisés."""

import sys
import json
from pathlib import Path

# Ajouter le répertoire du projet au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.automation.core import TestAutomationEngine, TestConfig

def main():
    """Exécute les tests de régression."""
    
    # Charger les résultats de référence
    baseline_file = Path('test_reports/baseline_results.json')
    baseline_results = {}
    
    if baseline_file.exists():
        with open(baseline_file, 'r') as f:
            baseline_results = json.load(f)
    
    # Exécuter les tests actuels
    config = TestConfig(
        test_tags=['regression'],
        parallel_workers=4,
        generate_json_report=True
    )
    
    engine = TestAutomationEngine(config)
    result = engine.run_test_suite("regression")
    
    # Comparer avec la baseline
    if baseline_results:
        baseline_success_rate = baseline_results.get('success_rate', 0)
        current_success_rate = result.success_rate
        
        if current_success_rate < baseline_success_rate - 5.0:  # Tolérance de 5%
            print(f"RÉGRESSION DÉTECTÉE!")
            print(f"Baseline: {baseline_success_rate:.1f}%")
            print(f"Actuel: {current_success_rate:.1f}%")
            sys.exit(1)
    
    print(f"Tests de régression: {result.success_rate:.1f}% de réussite")

if __name__ == "__main__":
    main()
'''
        
        script_path = Path('scripts/regression_tests.py')
        script_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Rendre exécutable sur Unix
        if sys.platform != 'win32':
            script_path.chmod(0o755)
        
        return script_path


# Exemple d'utilisation
def example_usage():
    """Exemple d'utilisation de l'automatisation des tests."""
    
    # Configuration pour tests complets
    config = TestConfig(
        parallel_workers=4,
        coverage_threshold=80.0,
        send_notifications=True,
        notification_emails=['team@example.com'],
        generate_html_report=True
    )
    
    # Exécuter les tests
    engine = TestAutomationEngine(config)
    result = engine.run_test_suite("example")
    
    print(f"Tests terminés: {result.success_rate:.1f}% de réussite")
    
    # Tests en continu
    continuous_runner = ContinuousTestRunner(config)
    # continuous_runner.start_continuous_testing(['src', 'tests'])
```

Ce guide d'automatisation des tests fournit une infrastructure complète pour l'exécution automatisée, la génération de rapports, et la surveillance continue de la qualité du code dans le projet Django GraphQL Auto.