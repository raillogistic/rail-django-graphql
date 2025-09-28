#!/usr/bin/env python3
"""
Script de rollback pour le système Django GraphQL Auto
Gère les rollbacks de déploiement avec vérifications de sécurité.
"""

import os
import sys
import json
import logging
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rollback.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RollbackManager:
    """Gestionnaire de rollback pour les déploiements."""
    
    def __init__(self, config_file: str = 'rollback_config.json'):
        """Initialise le gestionnaire de rollback."""
        self.config_file = config_file
        self.config = self.load_config()
        self.backup_dir = Path(self.config.get('backup_directory', './backups'))
        self.backup_dir.mkdir(exist_ok=True)
        
    def load_config(self) -> Dict:
        """Charge la configuration de rollback."""
        default_config = {
            "database": {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", 5432)),
                "name": os.getenv("DB_NAME", "django_graphql_auto"),
                "user": os.getenv("DB_USER", "postgres"),
                "password": os.getenv("DB_PASSWORD", "")
            },
            "backup_directory": "./backups",
            "max_rollback_age_hours": 72,
            "safety_checks": {
                "require_confirmation": True,
                "check_active_connections": True,
                "verify_backup_integrity": True,
                "test_rollback_first": False
            },
            "notification": {
                "slack_webhook": os.getenv("SLACK_WEBHOOK_URL"),
                "email_recipients": []
            },
            "docker": {
                "compose_file": "docker-compose.yml",
                "service_name": "web"
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Fusionner avec la configuration par défaut
                    default_config.update(config)
            except Exception as e:
                logger.warning(f"Erreur lors du chargement de la configuration: {e}")
                logger.info("Utilisation de la configuration par défaut")
        
        return default_config
    
    def list_available_backups(self) -> List[Dict]:
        """Liste les sauvegardes disponibles pour le rollback."""
        backups = []
        
        try:
            for backup_file in self.backup_dir.glob("backup_*.json"):
                with open(backup_file, 'r') as f:
                    backup_info = json.load(f)
                    
                # Vérifier l'âge de la sauvegarde
                backup_time = datetime.fromisoformat(backup_info['timestamp'])
                age_hours = (datetime.now() - backup_time).total_seconds() / 3600
                
                if age_hours <= self.config['max_rollback_age_hours']:
                    backup_info['age_hours'] = round(age_hours, 2)
                    backup_info['backup_file'] = str(backup_file)
                    backups.append(backup_info)
                    
        except Exception as e:
            logger.error(f"Erreur lors de la liste des sauvegardes: {e}")
        
        # Trier par timestamp décroissant
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        return backups
    
    def verify_backup_integrity(self, backup_info: Dict) -> bool:
        """Vérifie l'intégrité d'une sauvegarde."""
        try:
            # Vérifier que tous les fichiers existent
            required_files = ['database_dump', 'static_files', 'media_files', 'schema_version']
            
            for file_key in required_files:
                if file_key in backup_info['files']:
                    file_path = Path(backup_info['files'][file_key])
                    if not file_path.exists():
                        logger.error(f"Fichier de sauvegarde manquant: {file_path}")
                        return False
            
            # Vérifier la taille du dump de base de données
            db_dump_path = Path(backup_info['files']['database_dump'])
            if db_dump_path.stat().st_size < 1024:  # Moins de 1KB
                logger.error("Le dump de base de données semble trop petit")
                return False
            
            # Vérifier le hash si disponible
            if 'checksums' in backup_info:
                for file_key, expected_hash in backup_info['checksums'].items():
                    if file_key in backup_info['files']:
                        file_path = Path(backup_info['files'][file_key])
                        actual_hash = self.calculate_file_hash(file_path)
                        if actual_hash != expected_hash:
                            logger.error(f"Hash invalide pour {file_key}")
                            return False
            
            logger.info("Intégrité de la sauvegarde vérifiée avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification d'intégrité: {e}")
            return False
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calcule le hash SHA-256 d'un fichier."""
        import hashlib
        
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def check_active_connections(self) -> Tuple[bool, int]:
        """Vérifie les connexions actives à la base de données."""
        try:
            conn = psycopg2.connect(**self.config['database'])
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Compter les connexions actives
            cursor.execute("""
                SELECT count(*) as active_connections
                FROM pg_stat_activity 
                WHERE datname = %s AND state = 'active' AND pid != pg_backend_pid()
            """, (self.config['database']['name'],))
            
            result = cursor.fetchone()
            active_connections = result['active_connections']
            
            cursor.close()
            conn.close()
            
            # Considérer comme sûr si moins de 5 connexions actives
            is_safe = active_connections < 5
            
            return is_safe, active_connections
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des connexions: {e}")
            return False, -1
    
    def create_pre_rollback_backup(self) -> Optional[str]:
        """Crée une sauvegarde avant le rollback."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"pre_rollback_{timestamp}"
            
            logger.info("Création d'une sauvegarde pré-rollback...")
            
            # Utiliser le script de déploiement pour créer la sauvegarde
            result = subprocess.run([
                sys.executable, 'deploy.py', 'backup', '--name', backup_name
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Sauvegarde pré-rollback créée: {backup_name}")
                return backup_name
            else:
                logger.error(f"Erreur lors de la sauvegarde pré-rollback: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de la création de la sauvegarde pré-rollback: {e}")
            return None
    
    def stop_application_services(self) -> bool:
        """Arrête les services de l'application."""
        try:
            logger.info("Arrêt des services de l'application...")
            
            # Arrêter les services Docker Compose
            result = subprocess.run([
                'docker-compose', '-f', self.config['docker']['compose_file'],
                'stop', self.config['docker']['service_name']
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Services arrêtés avec succès")
                return True
            else:
                logger.error(f"Erreur lors de l'arrêt des services: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt des services: {e}")
            return False
    
    def restore_database(self, backup_info: Dict) -> bool:
        """Restaure la base de données depuis une sauvegarde."""
        try:
            db_dump_path = backup_info['files']['database_dump']
            logger.info(f"Restauration de la base de données depuis {db_dump_path}...")
            
            # Commande de restauration PostgreSQL
            restore_cmd = [
                'pg_restore',
                '--host', self.config['database']['host'],
                '--port', str(self.config['database']['port']),
                '--username', self.config['database']['user'],
                '--dbname', self.config['database']['name'],
                '--clean',
                '--if-exists',
                '--no-owner',
                '--no-privileges',
                '--verbose',
                db_dump_path
            ]
            
            # Définir le mot de passe via variable d'environnement
            env = os.environ.copy()
            env['PGPASSWORD'] = self.config['database']['password']
            
            result = subprocess.run(restore_cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Base de données restaurée avec succès")
                return True
            else:
                logger.error(f"Erreur lors de la restauration: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la restauration de la base de données: {e}")
            return False
    
    def restore_static_files(self, backup_info: Dict) -> bool:
        """Restaure les fichiers statiques."""
        try:
            if 'static_files' not in backup_info['files']:
                logger.info("Aucun fichier statique à restaurer")
                return True
            
            static_backup_path = backup_info['files']['static_files']
            static_dir = Path('./staticfiles')
            
            logger.info(f"Restauration des fichiers statiques depuis {static_backup_path}...")
            
            # Supprimer les fichiers statiques existants
            if static_dir.exists():
                subprocess.run(['rm', '-rf', str(static_dir)], check=True)
            
            # Extraire l'archive
            subprocess.run(['tar', '-xzf', static_backup_path, '-C', '.'], check=True)
            
            logger.info("Fichiers statiques restaurés avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la restauration des fichiers statiques: {e}")
            return False
    
    def restore_media_files(self, backup_info: Dict) -> bool:
        """Restaure les fichiers média."""
        try:
            if 'media_files' not in backup_info['files']:
                logger.info("Aucun fichier média à restaurer")
                return True
            
            media_backup_path = backup_info['files']['media_files']
            media_dir = Path('./media')
            
            logger.info(f"Restauration des fichiers média depuis {media_backup_path}...")
            
            # Supprimer les fichiers média existants
            if media_dir.exists():
                subprocess.run(['rm', '-rf', str(media_dir)], check=True)
            
            # Extraire l'archive
            subprocess.run(['tar', '-xzf', media_backup_path, '-C', '.'], check=True)
            
            logger.info("Fichiers média restaurés avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la restauration des fichiers média: {e}")
            return False
    
    def restore_schema_version(self, backup_info: Dict) -> bool:
        """Restaure la version du schéma GraphQL."""
        try:
            if 'schema_version' not in backup_info:
                logger.info("Aucune version de schéma à restaurer")
                return True
            
            schema_version = backup_info['schema_version']
            logger.info(f"Restauration de la version de schéma: {schema_version}")
            
            # Utiliser la commande Django pour activer la version
            result = subprocess.run([
                sys.executable, 'manage.py', 'manage_schema_versions',
                'activate', schema_version
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Version de schéma {schema_version} activée")
                return True
            else:
                logger.error(f"Erreur lors de l'activation de la version: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la restauration de la version de schéma: {e}")
            return False
    
    def start_application_services(self) -> bool:
        """Redémarre les services de l'application."""
        try:
            logger.info("Redémarrage des services de l'application...")
            
            # Redémarrer les services Docker Compose
            result = subprocess.run([
                'docker-compose', '-f', self.config['docker']['compose_file'],
                'up', '-d', self.config['docker']['service_name']
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Services redémarrés avec succès")
                return True
            else:
                logger.error(f"Erreur lors du redémarrage: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors du redémarrage des services: {e}")
            return False
    
    def verify_rollback_success(self) -> bool:
        """Vérifie que le rollback s'est bien déroulé."""
        try:
            logger.info("Vérification du succès du rollback...")
            
            # Vérifier la connectivité de la base de données
            conn = psycopg2.connect(**self.config['database'])
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            
            # Vérifier que l'application répond
            import requests
            response = requests.get('http://localhost:8000/health/', timeout=30)
            if response.status_code != 200:
                logger.error("L'application ne répond pas correctement")
                return False
            
            logger.info("Rollback vérifié avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du rollback: {e}")
            return False
    
    def send_notification(self, message: str, success: bool = True):
        """Envoie une notification de rollback."""
        try:
            # Notification Slack
            if self.config['notification']['slack_webhook']:
                import requests
                
                color = "good" if success else "danger"
                payload = {
                    "attachments": [{
                        "color": color,
                        "title": "Rollback Django GraphQL Auto",
                        "text": message,
                        "ts": int(datetime.now().timestamp())
                    }]
                }
                
                requests.post(self.config['notification']['slack_webhook'], json=payload)
            
            # Notification par email (implémentation basique)
            if self.config['notification']['email_recipients']:
                logger.info(f"Notification email à envoyer: {message}")
                # Ici, vous pourriez intégrer un service d'email
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification: {e}")
    
    def perform_rollback(self, backup_id: str, force: bool = False) -> bool:
        """Effectue le rollback complet."""
        try:
            # Trouver la sauvegarde
            backups = self.list_available_backups()
            backup_info = None
            
            for backup in backups:
                if backup['backup_id'] == backup_id:
                    backup_info = backup
                    break
            
            if not backup_info:
                logger.error(f"Sauvegarde {backup_id} non trouvée")
                return False
            
            logger.info(f"Début du rollback vers {backup_id}")
            
            # Vérifications de sécurité
            if self.config['safety_checks']['verify_backup_integrity']:
                if not self.verify_backup_integrity(backup_info):
                    logger.error("Échec de la vérification d'intégrité")
                    return False
            
            if self.config['safety_checks']['check_active_connections']:
                is_safe, connections = self.check_active_connections()
                if not is_safe and not force:
                    logger.error(f"Trop de connexions actives ({connections}). Utilisez --force pour ignorer.")
                    return False
            
            # Demander confirmation
            if self.config['safety_checks']['require_confirmation'] and not force:
                confirm = input(f"Confirmer le rollback vers {backup_id}? (oui/non): ")
                if confirm.lower() not in ['oui', 'o', 'yes', 'y']:
                    logger.info("Rollback annulé par l'utilisateur")
                    return False
            
            # Créer une sauvegarde pré-rollback
            pre_rollback_backup = self.create_pre_rollback_backup()
            if not pre_rollback_backup:
                logger.warning("Impossible de créer une sauvegarde pré-rollback")
                if not force:
                    return False
            
            # Arrêter les services
            if not self.stop_application_services():
                logger.error("Impossible d'arrêter les services")
                return False
            
            try:
                # Restaurer la base de données
                if not self.restore_database(backup_info):
                    raise Exception("Échec de la restauration de la base de données")
                
                # Restaurer les fichiers statiques
                if not self.restore_static_files(backup_info):
                    raise Exception("Échec de la restauration des fichiers statiques")
                
                # Restaurer les fichiers média
                if not self.restore_media_files(backup_info):
                    raise Exception("Échec de la restauration des fichiers média")
                
                # Restaurer la version du schéma
                if not self.restore_schema_version(backup_info):
                    raise Exception("Échec de la restauration de la version de schéma")
                
                # Redémarrer les services
                if not self.start_application_services():
                    raise Exception("Échec du redémarrage des services")
                
                # Vérifier le succès
                if not self.verify_rollback_success():
                    raise Exception("Échec de la vérification du rollback")
                
                logger.info(f"Rollback vers {backup_id} terminé avec succès")
                self.send_notification(f"Rollback vers {backup_id} terminé avec succès", True)
                return True
                
            except Exception as e:
                logger.error(f"Erreur pendant le rollback: {e}")
                
                # Tentative de redémarrage des services en cas d'échec
                self.start_application_services()
                
                self.send_notification(f"Échec du rollback vers {backup_id}: {e}", False)
                return False
                
        except Exception as e:
            logger.error(f"Erreur critique pendant le rollback: {e}")
            self.send_notification(f"Erreur critique pendant le rollback: {e}", False)
            return False


def main():
    """Point d'entrée principal du script."""
    parser = argparse.ArgumentParser(description='Script de rollback pour Django GraphQL Auto')
    
    subparsers = parser.add_subparsers(dest='command', help='Commandes disponibles')
    
    # Commande list
    list_parser = subparsers.add_parser('list', help='Lister les sauvegardes disponibles')
    list_parser.add_argument('--format', choices=['table', 'json'], default='table', help='Format de sortie')
    
    # Commande rollback
    rollback_parser = subparsers.add_parser('rollback', help='Effectuer un rollback')
    rollback_parser.add_argument('backup_id', help='ID de la sauvegarde cible')
    rollback_parser.add_argument('--force', action='store_true', help='Forcer le rollback sans vérifications')
    rollback_parser.add_argument('--config', default='rollback_config.json', help='Fichier de configuration')
    
    # Commande verify
    verify_parser = subparsers.add_parser('verify', help='Vérifier une sauvegarde')
    verify_parser.add_argument('backup_id', help='ID de la sauvegarde à vérifier')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    rollback_manager = RollbackManager(getattr(args, 'config', 'rollback_config.json'))
    
    if args.command == 'list':
        backups = rollback_manager.list_available_backups()
        
        if args.format == 'json':
            print(json.dumps(backups, indent=2, default=str))
        else:
            print(f"\n{'='*80}")
            print(f"{'ID':<20} {'Timestamp':<20} {'Version':<15} {'Âge (h)':<10} {'Description'}")
            print(f"{'='*80}")
            
            for backup in backups:
                print(f"{backup['backup_id']:<20} {backup['timestamp']:<20} "
                      f"{backup.get('schema_version', 'N/A'):<15} {backup['age_hours']:<10} "
                      f"{backup.get('description', '')}")
            
            print(f"{'='*80}\n")
    
    elif args.command == 'rollback':
        success = rollback_manager.perform_rollback(args.backup_id, args.force)
        sys.exit(0 if success else 1)
    
    elif args.command == 'verify':
        backups = rollback_manager.list_available_backups()
        backup_info = None
        
        for backup in backups:
            if backup['backup_id'] == args.backup_id:
                backup_info = backup
                break
        
        if not backup_info:
            print(f"Sauvegarde {args.backup_id} non trouvée")
            sys.exit(1)
        
        if rollback_manager.verify_backup_integrity(backup_info):
            print(f"Sauvegarde {args.backup_id} vérifiée avec succès")
            sys.exit(0)
        else:
            print(f"Échec de la vérification de la sauvegarde {args.backup_id}")
            sys.exit(1)


if __name__ == '__main__':
    main()