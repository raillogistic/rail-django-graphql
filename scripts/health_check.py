#!/usr/bin/env python3
"""
Système de vérification de santé pour Django GraphQL Auto
Effectue des contrôles complets de l'état du système.
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import redis
from psycopg2.extras import RealDictCursor

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthCheckResult:
    """Résultat d'un contrôle de santé."""
    
    def __init__(self, name: str, status: str, message: str = "", details: Dict = None, duration_ms: float = 0):
        self.name = name
        self.status = status  # 'healthy', 'warning', 'critical'
        self.message = message
        self.details = details or {}
        self.duration_ms = duration_ms
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convertit le résultat en dictionnaire."""
        return {
            'name': self.name,
            'status': self.status,
            'message': self.message,
            'details': self.details,
            'duration_ms': self.duration_ms,
            'timestamp': self.timestamp
        }


class HealthChecker:
    """Système de vérification de santé."""
    
    def __init__(self, config_file: str = 'health_check_config.json'):
        """Initialise le vérificateur de santé."""
        self.config = self.load_config(config_file)
        self.results: List[HealthCheckResult] = []
        
    def load_config(self, config_file: str) -> Dict:
        """Charge la configuration des contrôles de santé."""
        default_config = {
            "database": {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", 5432)),
                "name": os.getenv("DB_NAME", "django_graphql_auto"),
                "user": os.getenv("DB_USER", "postgres"),
                "password": os.getenv("DB_PASSWORD", ""),
                "timeout": 5
            },
            "redis": {
                "host": os.getenv("REDIS_HOST", "localhost"),
                "port": int(os.getenv("REDIS_PORT", 6379)),
                "db": int(os.getenv("REDIS_DB", 0)),
                "password": os.getenv("REDIS_PASSWORD"),
                "timeout": 5
            },
            "application": {
                "url": os.getenv("APP_URL", "http://localhost:8000"),
                "timeout": 10,
                "expected_status": 200
            },
            "graphql": {
                "endpoint": "/graphql/",
                "timeout": 10,
                "test_query": "query { __schema { types { name } } }"
            },
            "filesystem": {
                "check_disk_space": True,
                "min_free_space_gb": 1.0,
                "check_permissions": True,
                "required_directories": ["./media", "./staticfiles", "./logs"]
            },
            "performance": {
                "max_response_time_ms": 2000,
                "max_db_connections": 100,
                "max_memory_usage_percent": 80
            },
            "thresholds": {
                "warning_response_time_ms": 1000,
                "critical_response_time_ms": 5000,
                "warning_db_connections": 50,
                "critical_db_connections": 80
            }
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    # Fusionner avec la configuration par défaut
                    default_config.update(config)
            except Exception as e:
                logger.warning(f"Erreur lors du chargement de la configuration: {e}")
        
        return default_config
    
    def check_database_connectivity(self) -> HealthCheckResult:
        """Vérifie la connectivité de la base de données."""
        start_time = time.time()
        
        try:
            conn = psycopg2.connect(
                **self.config['database'],
                connect_timeout=self.config['database']['timeout']
            )
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Test de base
            cursor.execute("SELECT version(), current_database(), current_user")
            db_info = cursor.fetchone()
            
            # Vérifier les connexions actives
            cursor.execute("""
                SELECT count(*) as active_connections,
                       max(extract(epoch from (now() - query_start))) as longest_query_seconds
                FROM pg_stat_activity 
                WHERE datname = %s AND state = 'active'
            """, (self.config['database']['name'],))
            
            conn_info = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Évaluer le statut
            active_connections = conn_info['active_connections']
            if active_connections >= self.config['thresholds']['critical_db_connections']:
                status = 'critical'
                message = f"Trop de connexions actives: {active_connections}"
            elif active_connections >= self.config['thresholds']['warning_db_connections']:
                status = 'warning'
                message = f"Nombre élevé de connexions: {active_connections}"
            else:
                status = 'healthy'
                message = "Base de données accessible"
            
            details = {
                'database_version': db_info['version'].split()[0:2],
                'database_name': db_info['current_database'],
                'current_user': db_info['current_user'],
                'active_connections': active_connections,
                'longest_query_seconds': float(conn_info['longest_query_seconds'] or 0)
            }
            
            return HealthCheckResult('database', status, message, details, duration_ms)
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                'database', 'critical', f"Erreur de connexion: {e}", 
                {'error': str(e)}, duration_ms
            )
    
    def check_redis_connectivity(self) -> HealthCheckResult:
        """Vérifie la connectivité Redis."""
        start_time = time.time()
        
        try:
            redis_config = self.config['redis'].copy()
            timeout = redis_config.pop('timeout', 5)
            
            r = redis.Redis(
                socket_connect_timeout=timeout,
                socket_timeout=timeout,
                **redis_config
            )
            
            # Test de base
            r.ping()
            
            # Informations Redis
            info = r.info()
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Évaluer la mémoire utilisée
            used_memory_percent = (info['used_memory'] / info['maxmemory']) * 100 if info.get('maxmemory', 0) > 0 else 0
            
            if used_memory_percent > 90:
                status = 'critical'
                message = f"Mémoire Redis critique: {used_memory_percent:.1f}%"
            elif used_memory_percent > 70:
                status = 'warning'
                message = f"Mémoire Redis élevée: {used_memory_percent:.1f}%"
            else:
                status = 'healthy'
                message = "Redis accessible"
            
            details = {
                'redis_version': info['redis_version'],
                'connected_clients': info['connected_clients'],
                'used_memory_human': info['used_memory_human'],
                'used_memory_percent': round(used_memory_percent, 2),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0)
            }
            
            return HealthCheckResult('redis', status, message, details, duration_ms)
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                'redis', 'critical', f"Erreur de connexion Redis: {e}",
                {'error': str(e)}, duration_ms
            )
    
    def check_application_health(self) -> HealthCheckResult:
        """Vérifie la santé de l'application Django."""
        start_time = time.time()
        
        try:
            url = f"{self.config['application']['url']}/health/"
            timeout = self.config['application']['timeout']
            
            response = requests.get(url, timeout=timeout)
            duration_ms = (time.time() - start_time) * 1000
            
            # Évaluer le temps de réponse
            if duration_ms > self.config['thresholds']['critical_response_time_ms']:
                status = 'critical'
                message = f"Temps de réponse critique: {duration_ms:.0f}ms"
            elif duration_ms > self.config['thresholds']['warning_response_time_ms']:
                status = 'warning'
                message = f"Temps de réponse élevé: {duration_ms:.0f}ms"
            elif response.status_code == self.config['application']['expected_status']:
                status = 'healthy'
                message = "Application accessible"
            else:
                status = 'warning'
                message = f"Code de statut inattendu: {response.status_code}"
            
            details = {
                'status_code': response.status_code,
                'response_time_ms': round(duration_ms, 2),
                'content_length': len(response.content),
                'headers': dict(response.headers)
            }
            
            # Analyser la réponse JSON si disponible
            try:
                json_response = response.json()
                details['response_data'] = json_response
            except:
                pass
            
            return HealthCheckResult('application', status, message, details, duration_ms)
            
        except requests.exceptions.Timeout:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                'application', 'critical', "Timeout de l'application",
                {'timeout_seconds': timeout}, duration_ms
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                'application', 'critical', f"Erreur d'accès à l'application: {e}",
                {'error': str(e)}, duration_ms
            )
    
    def check_graphql_endpoint(self) -> HealthCheckResult:
        """Vérifie l'endpoint GraphQL."""
        start_time = time.time()
        
        try:
            url = f"{self.config['application']['url']}{self.config['graphql']['endpoint']}"
            timeout = self.config['graphql']['timeout']
            
            # Requête GraphQL de test
            payload = {
                'query': self.config['graphql']['test_query']
            }
            
            response = requests.post(
                url,
                json=payload,
                timeout=timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                try:
                    json_response = response.json()
                    if 'errors' in json_response:
                        status = 'warning'
                        message = f"Erreurs GraphQL: {len(json_response['errors'])}"
                        details = {'errors': json_response['errors']}
                    else:
                        status = 'healthy'
                        message = "Endpoint GraphQL fonctionnel"
                        details = {
                            'schema_types_count': len(json_response.get('data', {}).get('__schema', {}).get('types', []))
                        }
                except Exception as e:
                    status = 'warning'
                    message = f"Réponse GraphQL invalide: {e}"
                    details = {'response_text': response.text[:500]}
            else:
                status = 'critical'
                message = f"Endpoint GraphQL inaccessible: {response.status_code}"
                details = {'status_code': response.status_code}
            
            details.update({
                'response_time_ms': round(duration_ms, 2),
                'content_length': len(response.content)
            })
            
            return HealthCheckResult('graphql', status, message, details, duration_ms)
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                'graphql', 'critical', f"Erreur endpoint GraphQL: {e}",
                {'error': str(e)}, duration_ms
            )
    
    def check_filesystem(self) -> HealthCheckResult:
        """Vérifie l'état du système de fichiers."""
        start_time = time.time()
        
        try:
            issues = []
            details = {}
            
            # Vérifier l'espace disque
            if self.config['filesystem']['check_disk_space']:
                import shutil
                total, used, free = shutil.disk_usage('.')
                free_gb = free / (1024**3)
                
                details['disk_space'] = {
                    'total_gb': round(total / (1024**3), 2),
                    'used_gb': round(used / (1024**3), 2),
                    'free_gb': round(free_gb, 2),
                    'used_percent': round((used / total) * 100, 2)
                }
                
                if free_gb < self.config['filesystem']['min_free_space_gb']:
                    issues.append(f"Espace disque faible: {free_gb:.2f}GB")
            
            # Vérifier les répertoires requis
            missing_dirs = []
            permission_issues = []
            
            for dir_path in self.config['filesystem']['required_directories']:
                path = Path(dir_path)
                
                if not path.exists():
                    missing_dirs.append(str(path))
                elif self.config['filesystem']['check_permissions']:
                    # Vérifier les permissions de lecture/écriture
                    if not os.access(path, os.R_OK | os.W_OK):
                        permission_issues.append(str(path))
            
            if missing_dirs:
                issues.append(f"Répertoires manquants: {', '.join(missing_dirs)}")
                details['missing_directories'] = missing_dirs
            
            if permission_issues:
                issues.append(f"Problèmes de permissions: {', '.join(permission_issues)}")
                details['permission_issues'] = permission_issues
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Déterminer le statut
            if issues:
                if missing_dirs or (details.get('disk_space', {}).get('free_gb', float('inf')) < 0.1):
                    status = 'critical'
                    message = f"Problèmes critiques: {'; '.join(issues)}"
                else:
                    status = 'warning'
                    message = f"Avertissements: {'; '.join(issues)}"
            else:
                status = 'healthy'
                message = "Système de fichiers OK"
            
            return HealthCheckResult('filesystem', status, message, details, duration_ms)
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                'filesystem', 'critical', f"Erreur système de fichiers: {e}",
                {'error': str(e)}, duration_ms
            )
    
    def check_system_resources(self) -> HealthCheckResult:
        """Vérifie les ressources système."""
        start_time = time.time()
        
        try:
            import psutil
            
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Mémoire
            memory = psutil.virtual_memory()
            
            # Processus
            process_count = len(psutil.pids())
            
            details = {
                'cpu_percent': cpu_percent,
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'used_percent': memory.percent
                },
                'process_count': process_count,
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Évaluer le statut
            issues = []
            
            if cpu_percent > 90:
                issues.append(f"CPU élevé: {cpu_percent}%")
            
            if memory.percent > self.config['performance']['max_memory_usage_percent']:
                issues.append(f"Mémoire élevée: {memory.percent}%")
            
            if issues:
                if cpu_percent > 95 or memory.percent > 95:
                    status = 'critical'
                    message = f"Ressources critiques: {'; '.join(issues)}"
                else:
                    status = 'warning'
                    message = f"Ressources élevées: {'; '.join(issues)}"
            else:
                status = 'healthy'
                message = "Ressources système OK"
            
            return HealthCheckResult('system_resources', status, message, details, duration_ms)
            
        except ImportError:
            return HealthCheckResult(
                'system_resources', 'warning', "Module psutil non disponible",
                {'error': 'psutil not installed'}, 0
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                'system_resources', 'critical', f"Erreur ressources système: {e}",
                {'error': str(e)}, duration_ms
            )
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Exécute tous les contrôles de santé."""
        logger.info("Début des contrôles de santé...")
        
        checks = [
            self.check_database_connectivity,
            self.check_redis_connectivity,
            self.check_application_health,
            self.check_graphql_endpoint,
            self.check_filesystem,
            self.check_system_resources
        ]
        
        self.results = []
        
        for check in checks:
            try:
                result = check()
                self.results.append(result)
                logger.info(f"{result.name}: {result.status} - {result.message}")
            except Exception as e:
                error_result = HealthCheckResult(
                    check.__name__, 'critical', f"Erreur lors du contrôle: {e}",
                    {'error': str(e)}
                )
                self.results.append(error_result)
                logger.error(f"Erreur lors du contrôle {check.__name__}: {e}")
        
        # Calculer le statut global
        statuses = [result.status for result in self.results]
        
        if 'critical' in statuses:
            overall_status = 'critical'
        elif 'warning' in statuses:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
        
        # Statistiques
        total_duration = sum(result.duration_ms for result in self.results)
        
        summary = {
            'overall_status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'total_checks': len(self.results),
            'healthy_checks': len([r for r in self.results if r.status == 'healthy']),
            'warning_checks': len([r for r in self.results if r.status == 'warning']),
            'critical_checks': len([r for r in self.results if r.status == 'critical']),
            'total_duration_ms': round(total_duration, 2),
            'checks': [result.to_dict() for result in self.results]
        }
        
        logger.info(f"Contrôles terminés - Statut global: {overall_status}")
        
        return summary
    
    def save_results(self, filename: str = None):
        """Sauvegarde les résultats dans un fichier."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"health_check_{timestamp}.json"
        
        summary = self.run_all_checks()
        
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Résultats sauvegardés dans {filename}")
        return filename


def main():
    """Point d'entrée principal du script."""
    parser = argparse.ArgumentParser(description='Contrôles de santé pour Django GraphQL Auto')
    
    parser.add_argument('--config', default='health_check_config.json', help='Fichier de configuration')
    parser.add_argument('--output', help='Fichier de sortie pour les résultats')
    parser.add_argument('--format', choices=['json', 'table'], default='table', help='Format de sortie')
    parser.add_argument('--save', action='store_true', help='Sauvegarder les résultats dans un fichier')
    parser.add_argument('--exit-code', action='store_true', help='Utiliser le code de sortie pour indiquer le statut')
    
    args = parser.parse_args()
    
    health_checker = HealthChecker(args.config)
    
    if args.save or args.output:
        filename = health_checker.save_results(args.output)
        if args.format == 'table':
            print(f"Résultats sauvegardés dans {filename}")
    else:
        summary = health_checker.run_all_checks()
        
        if args.format == 'json':
            print(json.dumps(summary, indent=2))
        else:
            # Format tableau
            print(f"\n{'='*80}")
            print(f"Rapport de santé - {summary['timestamp']}")
            print(f"Statut global: {summary['overall_status'].upper()}")
            print(f"{'='*80}")
            
            for check in summary['checks']:
                status_symbol = {
                    'healthy': '✓',
                    'warning': '⚠',
                    'critical': '✗'
                }.get(check['status'], '?')
                
                print(f"{status_symbol} {check['name']:<20} {check['status']:<10} "
                      f"{check['duration_ms']:>6.0f}ms  {check['message']}")
            
            print(f"{'='*80}")
            print(f"Total: {summary['total_checks']} contrôles en {summary['total_duration_ms']:.0f}ms")
            print(f"Sains: {summary['healthy_checks']}, "
                  f"Avertissements: {summary['warning_checks']}, "
                  f"Critiques: {summary['critical_checks']}")
            print(f"{'='*80}\n")
    
    # Code de sortie basé sur le statut
    if args.exit_code:
        if not hasattr(health_checker, 'results') or not health_checker.results:
            summary = health_checker.run_all_checks()
        
        statuses = [result.status for result in health_checker.results]
        
        if 'critical' in statuses:
            sys.exit(2)  # Critique
        elif 'warning' in statuses:
            sys.exit(1)  # Avertissement
        else:
            sys.exit(0)  # Sain


if __name__ == '__main__':
    main()