# Dockerfile pour Django GraphQL Auto System
FROM python:3.11-slim

# Définir les variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=rail_django_graphql.settings \
    PORT=8000

# Créer un utilisateur non-root pour la sécurité
RUN groupadd -r django && useradd -r -g django django

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Créer et définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .
COPY requirements-dev.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p /app/media/uploads /app/static /app/logs && \
    chown -R django:django /app

# Collecter les fichiers statiques
RUN python manage.py collectstatic --noinput

# Changer vers l'utilisateur non-root
USER django

# Exposer le port
EXPOSE $PORT

# Script de santé pour Docker
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health/ || exit 1

# Commande par défaut
CMD ["sh", "-c", "python manage.py migrate && gunicorn rail_django_graphql.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120"]