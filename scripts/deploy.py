#!/usr/bin/env python3
"""
Script de déploiement automatisé pour Django GraphQL Auto System
Gère les migrations de base de données, les vérifications de santé et le déploiement sécurisé.
"""

import os
import sys
import subprocess
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DeploymentManager:
    """Gestionnaire de déploiement avec migrations et vérifications de sécurité."""
    
    def __init__(self, environment: str = 'production'):
        self.environment = environment
        self.backup_dir = Path('backups')
        self.backup_dir.mkdir(exist_ok=True)
        self.deployment_config = self._load_deployment_config()
        
    def _load_deployment_config(self) -> Dict:
        """Charge la configuration de déploiement."""
        config_file = f'deployment-{self.environment}.json'
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        
        # Configuration par défaut
        return {
            'database_backup': True,
            'run_tests': True,
            'health_check_timeout': 300,
            'rollback_on_failure': True,
            'maintenance_mode': True,
            'static_files': True,
            'cache_clear': True
        }
    
    def run_command(self, command: str, check: bool = True) -> Tuple[int, str, str]:
        """Exécute une commande système et retourne le résultat."""
        logger.info(f"Exécution: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if check and result.returncode != 0:
                logger.error(f"Erreur dans la commande: {command}")
                logger.error(f"Sortie d'erreur: {result.stderr}")
                raise subprocess.CalledProcessError(result.returncode, command)
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout pour la commande: {command}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de {command}: {e}")
            raise
    
    def create_database_backup(self) -> str:
        """Crée une sauvegarde de la base de données."""
        if not self.deployment_config.get('database_backup', True):
            logger.info("Sauvegarde de base de données désactivée")
            return ""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f"db_backup_{timestamp}.sql"
        
        logger.info("Création de la sauvegarde de base de données...")
        
        # Récupérer l'URL de la base de données
        db_url = os.environ.get('DATABASE_URL', '')
        if not db_url:
            logger.warning("DATABASE_URL non définie, sauvegarde ignorée")
            return ""
        
        # Commande de sauvegarde PostgreSQL
        if 'postgresql' in db_url:
            cmd = f"pg_dump {db_url} > {backup_file}"
        elif 'mysql' in db_url:
            cmd = f"mysqldump --single-transaction {db_url} > {backup_file}"
        else:
            logger.warning("Type de base de données non supporté pour la sauvegarde")
            return ""
        
        try:
            self.run_command(cmd)
            logger.info(f"Sauvegarde créée: {backup_file}")
            return str(backup_file)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            raise
    
    def enable_maintenance_mode(self):
        """Active le mode maintenance."""
        if not self.deployment_config.get('maintenance_mode', True):
            return
        
        logger.info("Activation du mode maintenance...")
        maintenance_file = Path('maintenance.html')
        
        maintenance_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Maintenance en cours</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                .container { max-width: 600px; margin: 0 auto; }
                h1 { color: #333; }
                p { color: #666; line-height: 1.6; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔧 Maintenance en cours</h1>
                <p>Notre système est actuellement en cours de mise à jour.</p>
                <p>Nous serons de retour dans quelques minutes.</p>
                <p>Merci pour votre patience.</p>
            </div>
        </body>
        </html>
        """
        
        with open(maintenance_file, 'w', encoding='utf-8') as f:
            f.write(maintenance_content)
        
        # Configurer le serveur web pour servir la page de maintenance
        # (Cette partie dépend de votre configuration serveur)
        logger.info("Mode maintenance activé")
    
    def disable_maintenance_mode(self):
        """Désactive le mode maintenance."""
        if not self.deployment_config.get('maintenance_mode', True):
            return
        
        logger.info("Désactivation du mode maintenance...")
        maintenance_file = Path('maintenance.html')
        if maintenance_file.exists():
            maintenance_file.unlink()
        logger.info("Mode maintenance désactivé")
    
    def run_database_migrations(self):
        """Exécute les migrations de base de données."""
        logger.info("Exécution des migrations de base de données...")
        
        # Vérifier les migrations en attente
        returncode, stdout, stderr = self.run_command(
            "python manage.py showmigrations --plan",
            check=False
        )
        
        if "[ ]" in stdout:
            logger.info("Migrations en attente détectées")
            
            # Exécuter les migrations
            self.run_command("python manage.py migrate --noinput")
            logger.info("Migrations appliquées avec succès")
        else:
            logger.info("Aucune migration en attente")
    
    def collect_static_files(self):
        """Collecte les fichiers statiques."""
        if not self.deployment_config.get('static_files', True):
            return
        
        logger.info("Collection des fichiers statiques...")
        self.run_command("python manage.py collectstatic --noinput --clear")
        logger.info("Fichiers statiques collectés")
    
    def clear_cache(self):
        """Vide le cache."""
        if not self.deployment_config.get('cache_clear', True):
            return
        
        logger.info("Vidage du cache...")
        try:
            self.run_command("python manage.py clear_cache", check=False)
        except:
            logger.warning("Impossible de vider le cache (commande non disponible)")
    
    def run_tests(self):
        """Exécute les tests avant le déploiement."""
        if not self.deployment_config.get('run_tests', True):
            return
        
        logger.info("Exécution des tests...")
        try:
            self.run_command("python -m pytest tests/ -x --tb=short")
            logger.info("Tous les tests sont passés")
        except subprocess.CalledProcessError:
            logger.error("Échec des tests - arrêt du déploiement")
            raise
    
    def health_check(self) -> bool:
        """Vérifie la santé de l'application après déploiement."""
        logger.info("Vérification de santé de l'application...")
        
        timeout = self.deployment_config.get('health_check_timeout', 300)
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Vérifier l'endpoint de santé
                returncode, stdout, stderr = self.run_command(
                    "curl -f http://localhost:8000/health/ -m 10",
                    check=False
                )
                
                if returncode == 0:
                    logger.info("Vérification de santé réussie")
                    return True
                
                logger.info("En attente de la disponibilité de l'application...")
                time.sleep(10)
                
            except Exception as e:
                logger.warning(f"Erreur lors de la vérification de santé: {e}")
                time.sleep(10)
        
        logger.error("Échec de la vérification de santé")
        return False
    
    def rollback_database(self, backup_file: str):
        """Effectue un rollback de la base de données."""
        if not backup_file or not os.path.exists(backup_file):
            logger.error("Fichier de sauvegarde non disponible pour le rollback")
            return False
        
        logger.info(f"Rollback de la base de données depuis {backup_file}...")
        
        try:
            db_url = os.environ.get('DATABASE_URL', '')
            
            if 'postgresql' in db_url:
                # Restaurer PostgreSQL
                self.run_command(f"psql {db_url} < {backup_file}")
            elif 'mysql' in db_url:
                # Restaurer MySQL
                self.run_command(f"mysql {db_url} < {backup_file}")
            
            logger.info("Rollback de la base de données terminé")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du rollback: {e}")
            return False
    
    def deploy(self) -> bool:
        """Exécute le processus de déploiement complet."""
        logger.info(f"Début du déploiement en environnement {self.environment}")
        backup_file = ""
        
        try:
            # 1. Créer une sauvegarde
            backup_file = self.create_database_backup()
            
            # 2. Activer le mode maintenance
            self.enable_maintenance_mode()
            
            # 3. Exécuter les tests
            self.run_tests()
            
            # 4. Exécuter les migrations
            self.run_database_migrations()
            
            # 5. Collecter les fichiers statiques
            self.collect_static_files()
            
            # 6. Vider le cache
            self.clear_cache()
            
            # 7. Redémarrer l'application (dépend de votre setup)
            logger.info("Redémarrage de l'application...")
            # self.run_command("systemctl restart django-app")
            
            # 8. Désactiver le mode maintenance
            self.disable_maintenance_mode()
            
            # 9. Vérification de santé
            if not self.health_check():
                if self.deployment_config.get('rollback_on_failure', True):
                    logger.error("Échec de la vérification - rollback en cours...")
                    self.rollback_database(backup_file)
                    return False
                else:
                    logger.warning("Vérification échouée mais rollback désactivé")
            
            logger.info("Déploiement terminé avec succès!")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du déploiement: {e}")
            
            # Rollback en cas d'erreur
            if self.deployment_config.get('rollback_on_failure', True):
                logger.info("Rollback en cours...")
                self.disable_maintenance_mode()
                self.rollback_database(backup_file)
            
            return False


def main():
    """Point d'entrée principal du script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Script de déploiement Django GraphQL Auto')
    parser.add_argument(
        '--environment',
        choices=['development', 'staging', 'production'],
        default='production',
        help='Environnement de déploiement'
    )
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Ignorer les tests'
    )
    parser.add_argument(
        '--skip-backup',
        action='store_true',
        help='Ignorer la sauvegarde'
    )
    
    args = parser.parse_args()
    
    # Créer le gestionnaire de déploiement
    deployment_manager = DeploymentManager(args.environment)
    
    # Modifier la configuration selon les arguments
    if args.skip_tests:
        deployment_manager.deployment_config['run_tests'] = False
    if args.skip_backup:
        deployment_manager.deployment_config['database_backup'] = False
    
    # Exécuter le déploiement
    success = deployment_manager.deploy()
    
    if success:
        logger.info("🎉 Déploiement réussi!")
        sys.exit(0)
    else:
        logger.error("❌ Échec du déploiement")
        sys.exit(1)


if __name__ == '__main__':
    main()