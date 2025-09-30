# Intégration CI/CD - Tests Django GraphQL Auto

Ce guide détaille l'intégration des tests dans les pipelines CI/CD pour assurer la qualité et la fiabilité du projet Django GraphQL Auto.

## 📋 Table des Matières

- [Vue d'Ensemble](#vue-densemble)
- [GitHub Actions](#github-actions)
- [Configuration des Workflows](#configuration-des-workflows)
- [Tests Automatisés](#tests-automatisés)
- [Déploiement Continu](#déploiement-continu)
- [Monitoring et Alertes](#monitoring-et-alertes)
- [Optimisation des Performances](#optimisation-des-performances)
- [Sécurité](#sécurité)

## 🎯 Vue d'Ensemble

### Stratégie CI/CD

```yaml
# Flux de développement
Développement → Tests Locaux → Pull Request → Tests CI → Review → Merge → Déploiement

# Environnements
- development: Tests complets + déploiement automatique
- staging: Tests de régression + validation manuelle
- production: Tests de fumée + déploiement contrôlé
```

### Objectifs de Qualité

```yaml
quality_gates:
  test_coverage: ">= 80%"
  performance_threshold: "< 2s pour les tests unitaires"
  security_scan: "Aucune vulnérabilité critique"
  code_quality: "Grade A (SonarQube)"
  documentation: "100% des API publiques documentées"
```

## 🔄 GitHub Actions

### 1. Workflow Principal

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    # Tests nocturnes à 2h00 UTC
    - cron: "0 2 * * *"

env:
  PYTHON_VERSION: "3.11"
  NODE_VERSION: "18"
  DJANGO_SETTINGS_MODULE: "tests.settings"
  TESTING: "true"

jobs:
  # ===== TESTS DE BASE =====
  test:
    name: Tests (${{ matrix.python-version }}, ${{ matrix.django-version }})
    runs-on: ubuntu-latest

    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]
        django-version: ["4.2", "5.0", "5.1"]
        exclude:
          # Django 5.0+ nécessite Python 3.10+
          - python-version: "3.9"
            django-version: "5.0"
          - python-version: "3.9"
            django-version: "5.1"

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - name: Checkout du code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0 # Nécessaire pour SonarQube

      - name: Configuration Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
          cache: "pip"

      - name: Installation des dépendances
        run: |
          python -m pip install --upgrade pip
          pip install Django==${{ matrix.django-version }}
          pip install -r requirements-test.txt
          pip install -e .

      - name: Vérification du code (linting)
        run: |
          flake8 rail_django_graphql tests
          black --check rail_django_graphql tests
          isort --check-only rail_django_graphql tests
          mypy rail_django_graphql

      - name: Tests de sécurité
        run: |
          bandit -r rail_django_graphql
          safety check

      - name: Tests unitaires et d'intégration
        run: |
          pytest \
            --cov=rail_django_graphql \
            --cov-report=xml \
            --cov-report=html \
            --cov-report=term-missing \
            --cov-fail-under=80 \
            --junitxml=test-results.xml \
            --durations=10 \
            -v
        env:
          DATABASE_URL: postgres://postgres:postgres@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0

      - name: Tests de performance
        run: |
          pytest tests/performance/ \
            --benchmark-only \
            --benchmark-json=benchmark.json

      - name: Upload des résultats de couverture
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

      - name: Upload des artefacts de test
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results-${{ matrix.python-version }}-${{ matrix.django-version }}
          path: |
            test-results.xml
            htmlcov/
            benchmark.json
          retention-days: 30

  # ===== ANALYSE DE QUALITÉ =====
  quality:
    name: Analyse de qualité
    runs-on: ubuntu-latest
    needs: test

    steps:
      - name: Checkout du code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Configuration Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Installation des dépendances
        run: |
          pip install -r requirements-test.txt
          pip install -e .

      - name: Génération du rapport de couverture
        run: |
          pytest --cov=rail_django_graphql --cov-report=xml

      - name: Analyse SonarQube
        uses: sonarqube-quality-gate-action@master
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
        with:
          scanMetadataReportFile: .scannerwork/report-task.txt

      - name: Analyse de complexité
        run: |
          radon cc rail_django_graphql --json > complexity.json
          radon mi rail_django_graphql --json > maintainability.json

      - name: Upload des métriques
        uses: actions/upload-artifact@v3
        with:
          name: quality-metrics
          path: |
            complexity.json
            maintainability.json
            coverage.xml

  # ===== TESTS E2E =====
  e2e:
    name: Tests End-to-End
    runs-on: ubuntu-latest
    needs: test

    steps:
      - name: Checkout du code
        uses: actions/checkout@v4

      - name: Configuration Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Configuration Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "18"
          cache: "npm"

      - name: Installation des dépendances
        run: |
          pip install -r requirements-test.txt
          pip install -e .
          npm install

      - name: Démarrage du serveur de test
        run: |
          python manage.py runserver 8000 &
          sleep 10  # Attendre que le serveur démarre
        env:
          DJANGO_SETTINGS_MODULE: "tests.settings"

      - name: Tests E2E avec Playwright
        run: |
          npx playwright test

      - name: Upload des rapports E2E
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: e2e-results
          path: |
            test-results/
            playwright-report/

  # ===== TESTS DE SÉCURITÉ =====
  security:
    name: Tests de sécurité
    runs-on: ubuntu-latest

    steps:
      - name: Checkout du code
        uses: actions/checkout@v4

      - name: Scan de sécurité avec Trivy
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: "fs"
          scan-ref: "."
          format: "sarif"
          output: "trivy-results.sarif"

      - name: Upload des résultats vers GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: "trivy-results.sarif"

      - name: Scan des dépendances
        run: |
          pip install safety
          safety check --json --output safety-report.json

      - name: Tests de pénétration OWASP ZAP
        uses: zaproxy/action-baseline@v0.7.0
        with:
          target: "http://localhost:8000"
          rules_file_name: ".zap/rules.tsv"

  # ===== BUILD ET PACKAGING =====
  build:
    name: Build et packaging
    runs-on: ubuntu-latest
    needs: [test, quality, security]

    steps:
      - name: Checkout du code
        uses: actions/checkout@v4

      - name: Configuration Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Installation des outils de build
        run: |
          pip install build twine

      - name: Build du package
        run: |
          python -m build

      - name: Vérification du package
        run: |
          twine check dist/*

      - name: Upload des artefacts
        uses: actions/upload-artifact@v3
        with:
          name: dist
          path: dist/

  # ===== DÉPLOIEMENT =====
  deploy:
    name: Déploiement
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'

    environment:
      name: production
      url: https://django-graphql-auto.example.com

    steps:
      - name: Téléchargement des artefacts
        uses: actions/download-artifact@v3
        with:
          name: dist
          path: dist/

      - name: Publication sur PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
          skip_existing: true

      - name: Création du tag de release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: v${{ github.run_number }}
          release_name: Release v${{ github.run_number }}
          draft: false
          prerelease: false
```

### 2. Workflow de Tests Nocturnes

```yaml
# .github/workflows/nightly.yml
name: Tests Nocturnes

on:
  schedule:
    - cron: "0 2 * * *" # 2h00 UTC chaque jour
  workflow_dispatch: # Déclenchement manuel

jobs:
  comprehensive-tests:
    name: Tests complets nocturnes
    runs-on: ubuntu-latest

    strategy:
      matrix:
        test-suite:
          - unit
          - integration
          - performance
          - security
          - compatibility

    steps:
      - name: Checkout du code
        uses: actions/checkout@v4

      - name: Configuration de l'environnement
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Installation des dépendances
        run: |
          pip install -r requirements-test.txt
          pip install -e .

      - name: Exécution des tests ${{ matrix.test-suite }}
        run: |
          case "${{ matrix.test-suite }}" in
            "unit")
              pytest tests/unit/ -v --durations=0
              ;;
            "integration")
              pytest tests/integration/ -v --durations=0
              ;;
            "performance")
              pytest tests/performance/ --benchmark-only --benchmark-sort=mean
              ;;
            "security")
              pytest tests/security/ -v
              bandit -r rail_django_graphql
              ;;
            "compatibility")
              pytest tests/compatibility/ -v
              ;;
          esac

      - name: Génération du rapport
        run: |
          echo "## Rapport de Tests ${{ matrix.test-suite }}" > report.md
          echo "Date: $(date)" >> report.md
          echo "Commit: ${{ github.sha }}" >> report.md
          # Ajouter les résultats des tests

      - name: Notification Slack en cas d'échec
        if: failure()
        uses: 8398a7/action-slack@v3
        with:
          status: failure
          channel: "#dev-alerts"
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### 3. Workflow de Performance

```yaml
# .github/workflows/performance.yml
name: Tests de Performance

on:
  pull_request:
    paths:
      - "rail_django_graphql/**"
      - "tests/performance/**"
  schedule:
    - cron: "0 4 * * 1" # Lundi 4h00 UTC

jobs:
  performance-baseline:
    name: Baseline de performance
    runs-on: ubuntu-latest

    steps:
      - name: Checkout du code
        uses: actions/checkout@v4
        with:
          fetch-depth: 2 # Pour comparer avec le commit précédent

      - name: Configuration Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Installation des dépendances
        run: |
          pip install -r requirements-test.txt
          pip install -e .

      - name: Tests de performance (commit actuel)
        run: |
          pytest tests/performance/ \
            --benchmark-only \
            --benchmark-json=current-benchmark.json \
            --benchmark-sort=mean

      - name: Checkout du commit précédent
        run: |
          git checkout HEAD~1
          pip install -e .

      - name: Tests de performance (commit précédent)
        run: |
          pytest tests/performance/ \
            --benchmark-only \
            --benchmark-json=previous-benchmark.json \
            --benchmark-sort=mean

      - name: Comparaison des performances
        run: |
          python scripts/compare_benchmarks.py \
            previous-benchmark.json \
            current-benchmark.json \
            --threshold=10  # 10% de régression acceptable

      - name: Commentaire PR avec résultats
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const comparison = fs.readFileSync('benchmark-comparison.md', 'utf8');

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## 📊 Rapport de Performance\n\n${comparison}`
            });
```

## 🔧 Configuration des Workflows

### 1. Variables d'Environnement

```yaml
# .github/workflows/env.yml
env:
  # Configuration Python
  PYTHON_VERSION: "3.11"
  PIP_CACHE_DIR: ~/.cache/pip

  # Configuration Django
  DJANGO_SETTINGS_MODULE: "tests.settings"
  SECRET_KEY: "test-secret-key-not-for-production"

  # Configuration de test
  TESTING: "true"
  COVERAGE_THRESHOLD: "80"

  # Configuration de base de données
  DATABASE_URL: "sqlite:///:memory:"

  # Configuration de cache
  CACHE_URL: "locmem://"

  # Configuration de logging
  LOG_LEVEL: "INFO"

  # Configuration de performance
  BENCHMARK_THRESHOLD: "10" # % de régression acceptable
```

### 2. Secrets GitHub

```yaml
# Secrets requis dans GitHub Settings > Secrets
secrets:
  # PyPI
  PYPI_API_TOKEN: "pypi-token-for-publishing"

  # SonarQube
  SONAR_TOKEN: "sonar-analysis-token"
  SONAR_HOST_URL: "https://sonarcloud.io"

  # Notifications
  SLACK_WEBHOOK: "https://hooks.slack.com/services/..."

  # Sécurité
  SNYK_TOKEN: "snyk-security-token"

  # Déploiement
  DEPLOY_KEY: "ssh-private-key-for-deployment"
```

### 3. Configuration des Caches

```yaml
# Configuration du cache pour optimiser les builds
cache_strategy:
  pip_cache:
    key: pip-${{ runner.os }}-${{ hashFiles('requirements*.txt') }}
    paths:
      - ~/.cache/pip

  node_cache:
    key: node-${{ runner.os }}-${{ hashFiles('package-lock.json') }}
    paths:
      - ~/.npm

  pytest_cache:
    key: pytest-${{ runner.os }}-${{ hashFiles('pytest.ini') }}
    paths:
      - .pytest_cache
```

## 📊 Tests Automatisés

### 1. Configuration des Tests par Environnement

```python
# tests/ci_settings.py
"""Configuration spécifique pour les tests CI."""

from .settings import *

# Configuration optimisée pour CI
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test_db',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'MAX_CONNS': 20,
        }
    }
}

# Cache Redis pour les tests d'intégration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://localhost:6379/0',
        'OPTIONS': {
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 20,
            }
        }
    }
}

# Logging optimisé pour CI
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'test.log',
            'formatter': 'verbose',
        },
    },
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name}: {message}',
            'style': '{',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# Configuration spécifique CI
CI_SPECIFIC_SETTINGS = {
    'PARALLEL_TESTING': True,
    'TEST_RUNNER': 'django.test.runner.DiscoverRunner',
    'TEST_PROCESSES': 4,
}
```

### 2. Scripts de Test Personnalisés

```python
# scripts/run_ci_tests.py
"""Script pour exécuter les tests en environnement CI."""

import os
import sys
import subprocess
import json
from pathlib import Path


class CITestRunner:
    """Gestionnaire des tests pour l'environnement CI."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_results = {}

    def setup_environment(self):
        """Configure l'environnement de test."""

        env_vars = {
            'DJANGO_SETTINGS_MODULE': 'tests.ci_settings',
            'TESTING': 'true',
            'PYTHONPATH': str(self.project_root),
        }

        for key, value in env_vars.items():
            os.environ[key] = value

        print(f"✅ Environnement configuré: {env_vars}")

    def run_test_suite(self, suite_name, command):
        """Exécute une suite de tests."""

        print(f"\n🧪 Exécution de la suite: {suite_name}")
        print(f"Commande: {command}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            self.test_results[suite_name] = {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
            }

            if result.returncode == 0:
                print(f"✅ {suite_name}: SUCCÈS")
            else:
                print(f"❌ {suite_name}: ÉCHEC")
                print(f"Erreur: {result.stderr}")

            return result.returncode == 0

        except Exception as e:
            print(f"❌ Erreur lors de l'exécution de {suite_name}: {e}")
            self.test_results[suite_name] = {
                'success': False,
                'error': str(e),
            }
            return False

    def run_all_tests(self):
        """Exécute toutes les suites de tests."""

        test_suites = {
            'linting': 'flake8 rail_django_graphql tests',
            'formatting': 'black --check rail_django_graphql tests',
            'imports': 'isort --check-only rail_django_graphql tests',
            'typing': 'mypy rail_django_graphql',
            'security': 'bandit -r rail_django_graphql',
            'unit_tests': 'pytest tests/unit/ -v --tb=short',
            'integration_tests': 'pytest tests/integration/ -v --tb=short',
            'performance_tests': 'pytest tests/performance/ --benchmark-only',
        }

        all_passed = True

        for suite_name, command in test_suites.items():
            success = self.run_test_suite(suite_name, command)
            if not success:
                all_passed = False

        return all_passed

    def generate_report(self):
        """Génère un rapport de test."""

        report = {
            'timestamp': datetime.now().isoformat(),
            'environment': 'CI',
            'results': self.test_results,
            'summary': {
                'total_suites': len(self.test_results),
                'passed': sum(1 for r in self.test_results.values() if r.get('success')),
                'failed': sum(1 for r in self.test_results.values() if not r.get('success')),
            }
        }

        # Sauvegarder le rapport
        report_file = self.project_root / 'test_reports' / 'ci_report.json'
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📊 Rapport généré: {report_file}")

        # Afficher le résumé
        summary = report['summary']
        print(f"\n📈 RÉSUMÉ:")
        print(f"  Total: {summary['total_suites']}")
        print(f"  Succès: {summary['passed']}")
        print(f"  Échecs: {summary['failed']}")

        return report


def main():
    """Point d'entrée principal."""

    runner = CITestRunner()

    # Configuration
    runner.setup_environment()

    # Exécution des tests
    all_passed = runner.run_all_tests()

    # Génération du rapport
    report = runner.generate_report()

    # Code de sortie
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
```

## 🚀 Déploiement Continu

### 1. Stratégie de Déploiement

```yaml
# Configuration de déploiement par environnement
deployment_strategy:
  development:
    trigger: "push to develop branch"
    tests: "unit + integration"
    deployment: "automatic"
    rollback: "automatic on failure"

  staging:
    trigger: "push to main branch"
    tests: "full test suite"
    deployment: "automatic"
    approval: "optional"
    rollback: "manual"

  production:
    trigger: "manual or scheduled"
    tests: "full test suite + security scan"
    deployment: "manual approval required"
    rollback: "manual with confirmation"
```

### 2. Scripts de Déploiement

```bash
#!/bin/bash
# scripts/deploy.sh

set -e  # Arrêter en cas d'erreur

ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}

echo "🚀 Déploiement vers $ENVIRONMENT (version: $VERSION)"

# Vérifications pré-déploiement
echo "🔍 Vérifications pré-déploiement..."

# Vérifier que les tests passent
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Exécution des tests complets..."
    python scripts/run_ci_tests.py

    if [ $? -ne 0 ]; then
        echo "❌ Les tests ont échoué. Déploiement annulé."
        exit 1
    fi
fi

# Vérifier la connectivité
echo "Vérification de la connectivité..."
curl -f https://api.$ENVIRONMENT.example.com/health || {
    echo "❌ Impossible de joindre l'environnement $ENVIRONMENT"
    exit 1
}

# Sauvegarde pré-déploiement
echo "💾 Sauvegarde pré-déploiement..."
./scripts/backup.sh $ENVIRONMENT

# Déploiement
echo "📦 Déploiement en cours..."

case $ENVIRONMENT in
    "development")
        # Déploiement simple pour dev
        rsync -av --delete ./ dev-server:/app/
        ssh dev-server "cd /app && pip install -e . && systemctl restart django-app"
        ;;

    "staging")
        # Déploiement avec validation pour staging
        docker build -t django-graphql-auto:$VERSION .
        docker push registry.example.com/django-graphql-auto:$VERSION
        kubectl set image deployment/django-app app=registry.example.com/django-graphql-auto:$VERSION -n staging
        kubectl rollout status deployment/django-app -n staging
        ;;

    "production")
        # Déploiement blue-green pour production
        echo "🔵 Déploiement Blue-Green..."

        # Déployer sur l'environnement inactif
        CURRENT_ENV=$(kubectl get service django-app-service -o jsonpath='{.spec.selector.version}')
        NEW_ENV=$([ "$CURRENT_ENV" = "blue" ] && echo "green" || echo "blue")

        echo "Environnement actuel: $CURRENT_ENV"
        echo "Nouvel environnement: $NEW_ENV"

        # Déployer la nouvelle version
        kubectl set image deployment/django-app-$NEW_ENV app=registry.example.com/django-graphql-auto:$VERSION
        kubectl rollout status deployment/django-app-$NEW_ENV

        # Tests de fumée
        echo "💨 Tests de fumée..."
        ./scripts/smoke_tests.sh $NEW_ENV

        if [ $? -eq 0 ]; then
            # Basculer le trafic
            echo "🔄 Basculement du trafic..."
            kubectl patch service django-app-service -p '{"spec":{"selector":{"version":"'$NEW_ENV'"}}}'

            echo "✅ Déploiement réussi sur $NEW_ENV"

            # Attendre avant de supprimer l'ancien environnement
            echo "⏳ Attente de 5 minutes avant nettoyage..."
            sleep 300

            # Arrêter l'ancien environnement
            kubectl scale deployment django-app-$CURRENT_ENV --replicas=0

        else
            echo "❌ Tests de fumée échoués. Rollback..."
            exit 1
        fi
        ;;
esac

# Tests post-déploiement
echo "🧪 Tests post-déploiement..."
./scripts/post_deploy_tests.sh $ENVIRONMENT

if [ $? -eq 0 ]; then
    echo "✅ Déploiement terminé avec succès!"

    # Notification
    curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"✅ Déploiement réussi sur '$ENVIRONMENT' (version: '$VERSION')"}' \
        $SLACK_WEBHOOK
else
    echo "❌ Tests post-déploiement échoués!"
    exit 1
fi
```

## 📈 Monitoring et Alertes

### 1. Configuration des Alertes

```yaml
# .github/workflows/monitoring.yml
name: Monitoring et Alertes

on:
  workflow_run:
    workflows: ["CI/CD Pipeline"]
    types: [completed]

jobs:
  notify-results:
    runs-on: ubuntu-latest

    steps:
      - name: Notification Slack - Succès
        if: ${{ github.event.workflow_run.conclusion == 'success' }}
        uses: 8398a7/action-slack@v3
        with:
          status: success
          channel: "#ci-cd"
          message: |
            ✅ Pipeline CI/CD réussi
            Branche: ${{ github.event.workflow_run.head_branch }}
            Commit: ${{ github.event.workflow_run.head_sha }}
            Auteur: ${{ github.event.workflow_run.head_commit.author.name }}
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}

      - name: Notification Slack - Échec
        if: ${{ github.event.workflow_run.conclusion == 'failure' }}
        uses: 8398a7/action-slack@v3
        with:
          status: failure
          channel: "#ci-cd-alerts"
          message: |
            ❌ Pipeline CI/CD échoué
            Branche: ${{ github.event.workflow_run.head_branch }}
            Commit: ${{ github.event.workflow_run.head_sha }}
            Auteur: ${{ github.event.workflow_run.head_commit.author.name }}

            🔗 Voir les détails: ${{ github.event.workflow_run.html_url }}
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}

      - name: Création d'issue pour échec récurrent
        if: ${{ github.event.workflow_run.conclusion == 'failure' }}
        uses: actions/github-script@v6
        with:
          script: |
            // Vérifier s'il y a eu des échecs récents
            const { data: runs } = await github.rest.actions.listWorkflowRuns({
              owner: context.repo.owner,
              repo: context.repo.repo,
              workflow_id: context.payload.workflow_run.workflow_id,
              per_page: 5
            });

            const recentFailures = runs.workflow_runs.filter(run => 
              run.conclusion === 'failure'
            ).length;

            if (recentFailures >= 3) {
              await github.rest.issues.create({
                owner: context.repo.owner,
                repo: context.repo.repo,
                title: '🚨 Échecs récurrents du pipeline CI/CD',
                body: `Le pipeline CI/CD a échoué ${recentFailures} fois récemment.
                
                Dernière exécution: ${context.payload.workflow_run.html_url}
                
                **Action requise:** Investigation et correction nécessaires.`,
                labels: ['bug', 'ci-cd', 'high-priority']
              });
            }
```

### 2. Métriques et Tableaux de Bord

```python
# scripts/collect_metrics.py
"""Collecte des métriques CI/CD."""

import json
import requests
from datetime import datetime, timedelta


class CIMetricsCollector:
    """Collecteur de métriques CI/CD."""

    def __init__(self, github_token, repo):
        self.github_token = github_token
        self.repo = repo
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

    def collect_workflow_metrics(self, days=30):
        """Collecte les métriques des workflows."""

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        url = f'https://api.github.com/repos/{self.repo}/actions/runs'
        params = {
            'created': f'{start_date.isoformat()}..{end_date.isoformat()}',
            'per_page': 100
        }

        response = requests.get(url, headers=self.headers, params=params)
        runs = response.json()['workflow_runs']

        metrics = {
            'total_runs': len(runs),
            'successful_runs': len([r for r in runs if r['conclusion'] == 'success']),
            'failed_runs': len([r for r in runs if r['conclusion'] == 'failure']),
            'average_duration': self._calculate_average_duration(runs),
            'success_rate': 0,
            'failure_rate': 0,
        }

        if metrics['total_runs'] > 0:
            metrics['success_rate'] = metrics['successful_runs'] / metrics['total_runs'] * 100
            metrics['failure_rate'] = metrics['failed_runs'] / metrics['total_runs'] * 100

        return metrics

    def _calculate_average_duration(self, runs):
        """Calcule la durée moyenne des workflows."""

        durations = []

        for run in runs:
            if run['created_at'] and run['updated_at']:
                created = datetime.fromisoformat(run['created_at'].replace('Z', '+00:00'))
                updated = datetime.fromisoformat(run['updated_at'].replace('Z', '+00:00'))
                duration = (updated - created).total_seconds()
                durations.append(duration)

        return sum(durations) / len(durations) if durations else 0

    def generate_report(self):
        """Génère un rapport de métriques."""

        metrics = self.collect_workflow_metrics()

        report = f"""
# 📊 Rapport de Métriques CI/CD

## Période: 30 derniers jours

### Statistiques Générales
- **Total d'exécutions**: {metrics['total_runs']}
- **Succès**: {metrics['successful_runs']} ({metrics['success_rate']:.1f}%)
- **Échecs**: {metrics['failed_runs']} ({metrics['failure_rate']:.1f}%)
- **Durée moyenne**: {metrics['average_duration']/60:.1f} minutes

### Objectifs de Performance
- ✅ Taux de succès > 95%: {'✅' if metrics['success_rate'] > 95 else '❌'}
- ✅ Durée moyenne < 10 min: {'✅' if metrics['average_duration'] < 600 else '❌'}

### Recommandations
"""

        if metrics['success_rate'] < 95:
            report += "- 🔧 Améliorer la stabilité des tests\n"

        if metrics['average_duration'] > 600:
            report += "- ⚡ Optimiser la durée des workflows\n"

        return report


# Utilisation
if __name__ == '__main__':
    import os

    collector = CIMetricsCollector(
        github_token=os.environ['GITHUB_TOKEN'],
        repo='owner/django-graphql-auto'
    )

    report = collector.generate_report()
    print(report)

    # Sauvegarder le rapport
    with open('ci_metrics_report.md', 'w') as f:
        f.write(report)
```

Ce guide d'intégration CI/CD fournit une base solide pour automatiser les tests, le déploiement et le monitoring du projet Django GraphQL Auto, garantissant ainsi la qualité et la fiabilité du code en production.
