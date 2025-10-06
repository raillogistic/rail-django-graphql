# Guide de Sécurité Django GraphQL Auto-Generation

Ce guide détaille l'implémentation et la configuration des fonctionnalités de sécurité pour Django GraphQL Auto-Generation.

## 🛡️ Fonctionnalités de Sécurité Implémentées

### 1. Middleware d'Authentification Dédié
- **Validation JWT automatique** pour toutes les requêtes GraphQL
- **Injection du contexte utilisateur** dans les résolveurs
- **Gestion du cache utilisateur** pour optimiser les performances
- **Headers de sécurité HTTP** automatiques
- **Logging des événements d'authentification**

### 2. Limitation de Débit (Rate Limiting)
- **Protection contre les attaques par force brute** sur les connexions
- **Limitation des requêtes GraphQL** par IP et par utilisateur
- **Configuration flexible** des limites et fenêtres temporelles
- **Intégration avec le système de cache Django**

### 3. Authentification Multi-Facteurs (MFA)
- **Support TOTP** (Time-based One-Time Password) avec Google Authenticator
- **Codes de sauvegarde** pour la récupération de compte
- **Authentification SMS** via Twilio
- **Gestion des appareils de confiance**
- **Interface GraphQL** pour la configuration MFA

### 4. Audit Logging Complet
- **Logging de tous les événements d'authentification**
- **Détection d'activités suspectes**
- **Stockage en base de données et fichiers**
- **Intégration webhook** pour systèmes externes
- **Rapports de sécurité automatisés**

## 🚀 Installation et Configuration

### Étape 1: Installation Rapide

Utilisez la commande de configuration automatique :

```bash
python manage.py setup_security --enable-mfa --enable-audit --create-settings --migrate
```

### Étape 2: Configuration Manuelle

#### 2.1 Middlewares

Ajoutez les middlewares de sécurité à votre `MIDDLEWARE` dans `settings.py` :

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    
    # Middlewares de sécurité GraphQL
    'rail_django_graphql.middleware.GraphQLAuthenticationMiddleware',
    'rail_django_graphql.middleware.GraphQLRateLimitMiddleware',
    
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

#### 2.2 Configuration de Base

```python
# Désactiver les mutations de sécurité en production
DISABLE_SECURITY_MUTATIONS = False

# Configuration JWT
JWT_AUTH_HEADER_PREFIX = 'Bearer'
JWT_AUTH_HEADER_NAME = 'HTTP_AUTHORIZATION'
JWT_USER_CACHE_TIMEOUT = 300  # 5 minutes

# Audit Logging
GRAPHQL_ENABLE_AUDIT_LOGGING = True
AUDIT_STORE_IN_DATABASE = True
AUDIT_STORE_IN_FILE = True
AUDIT_RETENTION_DAYS = 90

# Limitation de Débit
GRAPHQL_ENABLE_AUTH_RATE_LIMITING = True
AUTH_LOGIN_ATTEMPTS_LIMIT = 5
AUTH_LOGIN_ATTEMPTS_WINDOW = 900  # 15 minutes
GRAPHQL_REQUESTS_LIMIT = 100
GRAPHQL_REQUESTS_WINDOW = 3600  # 1 heure
```

#### 2.3 Configuration du Cache

**Redis (Recommandé) :**

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'graphql_security',
        'TIMEOUT': 3600,
    }
}
```

**Memcached :**

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': '127.0.0.1:11211',
        'KEY_PREFIX': 'graphql_security',
        'TIMEOUT': 3600,
    }
}
```

#### 2.4 Configuration MFA (Optionnel)

```python
# Activer MFA
MFA_ENABLED = True
MFA_ISSUER_NAME = 'Mon Application'
MFA_TOTP_VALIDITY_WINDOW = 1
MFA_BACKUP_CODES_COUNT = 10
MFA_TRUSTED_DEVICE_DURATION = 30  # jours

# Configuration SMS (Twilio)
MFA_SMS_PROVIDER = 'twilio'
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER')
```

#### 2.5 Configuration du Logging

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'security': {
            'format': '[SECURITY] {asctime} {name} {levelname} {message}',
            'style': '{',
        },
        'audit': {
            'format': '[AUDIT] {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/security.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'security',
        },
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/audit.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 10,
            'formatter': 'audit',
        },
    },
    'loggers': {
        'rail_django_graphql.middleware': {
            'handlers': ['security_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'audit': {
            'handlers': ['audit_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### Étape 3: Variables d'Environnement

Créez un fichier `.env` avec les variables suivantes :

```env
# Sécurité Django
SECRET_KEY=your-very-long-and-random-secret-key-here
DEBUG=False

# Configuration Twilio (pour MFA SMS)
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_FROM_NUMBER=your-twilio-phone-number

# Webhook d'audit (optionnel)
AUDIT_WEBHOOK_URL=https://your-audit-webhook-url.com/webhook
```

### Étape 4: Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## 🔧 Utilisation

### Authentification GraphQL

```graphql
# Connexion
mutation {
  login(username: "user@example.com", password: "password") {
    success
    token
    refreshToken
    user {
      id
      username
      email
    }
  }
}

# Utilisation du token
# Headers: Authorization: Bearer <token>
query {
  me {
    id
    username
    email
  }
}
```

### Configuration MFA

```graphql
# Configurer TOTP
mutation {
  setupTotp {
    success
    qrCodeUrl
    backupCodes
  }
}

# Vérifier TOTP
mutation {
  verifyTotp(token: "123456") {
    success
    message
  }
}

# Configurer SMS
mutation {
  setupSms(phoneNumber: "+33123456789") {
    success
    message
  }
}
```

### Gestion des Appareils de Confiance

```graphql
# Marquer un appareil comme de confiance
mutation {
  trustDevice(deviceName: "Mon iPhone") {
    success
    deviceId
  }
}

# Lister les appareils de confiance
query {
  trustedDevices {
    id
    deviceName
    createdAt
    lastUsed
  }
}
```

## 🔍 Monitoring et Maintenance

### Vérification de Sécurité

```bash
# Vérification complète
python manage.py security_check

# Vérification avec détails
python manage.py security_check --verbose

# Format JSON pour intégration
python manage.py security_check --format json
```

### Surveillance des Logs

Les logs de sécurité sont stockés dans :
- `logs/security.log` - Événements de sécurité généraux
- `logs/audit.log` - Événements d'audit détaillés

### Rapports d'Audit

```python
from rail_django_graphql.extensions.audit import audit_logger

# Générer un rapport de sécurité
report = audit_logger.generate_security_report(days=7)
print(report)
```

## ⚠️ Considérations de Sécurité

### Production

1. **HTTPS Obligatoire** :
   ```python
   SECURE_SSL_REDIRECT = True
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   ```

2. **Headers de Sécurité** :
   ```python
   SECURE_BROWSER_XSS_FILTER = True
   SECURE_CONTENT_TYPE_NOSNIFF = True
   SECURE_HSTS_SECONDS = 31536000
   X_FRAME_OPTIONS = 'DENY'
   ```

3. **Cache Persistant** :
   - Utilisez Redis ou Memcached en production
   - Évitez le cache en mémoire locale

### Surveillance

1. **Alertes Automatiques** :
   - Configurez des webhooks pour les événements critiques
   - Surveillez les tentatives de connexion échouées
   - Alertes sur les activités suspectes

2. **Rotation des Logs** :
   - Les logs sont automatiquement rotés (10MB max)
   - Archivage automatique des anciens logs
   - Rétention configurable (90 jours par défaut)

### Sauvegarde

1. **Codes de Sauvegarde MFA** :
   - Stockés de manière sécurisée en base
   - Hachés avec bcrypt
   - Utilisables une seule fois

2. **Récupération de Compte** :
   - Processus de récupération sécurisé
   - Validation par email et SMS
   - Audit complet des récupérations

## 🐛 Dépannage

### Problèmes Courants

1. **Cache Non Configuré** :
   ```
   Erreur: 'default' cache not configured
   ```
   Solution: Configurez un backend de cache dans `CACHES`

2. **Middlewares Manquants** :
   ```
   Erreur: GraphQLAuthenticationMiddleware not found
   ```
   Solution: Ajoutez les middlewares à `MIDDLEWARE`

3. **Migrations Manquantes** :
   ```
   Erreur: Table doesn't exist
   ```
   Solution: `python manage.py migrate`

### Debug

Activez le logging détaillé :

```python
LOGGING['loggers']['rail_django_graphql.middleware']['level'] = 'DEBUG'
```

### Support

Pour obtenir de l'aide :
1. Vérifiez les logs de sécurité
2. Exécutez `python manage.py security_check --verbose`
3. Consultez la documentation des erreurs dans les logs

## 📚 Références

- [Documentation Django Security](https://docs.djangoproject.com/en/stable/topics/security/)
- [GraphQL Security Best Practices](https://graphql.org/learn/security/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [JWT Best Practices](https://auth0.com/blog/a-look-at-the-latest-draft-for-jwt-bcp/)

## 🔄 Mises à Jour

Pour mettre à jour les fonctionnalités de sécurité :

1. Sauvegardez votre configuration actuelle
2. Mettez à jour le package
3. Exécutez `python manage.py security_check`
4. Appliquez les nouvelles recommandations
5. Testez en environnement de développement

---

**Note** : Ce guide couvre les fonctionnalités de sécurité avancées. Pour une utilisation basique, utilisez la commande `setup_security` qui configure automatiquement la plupart des paramètres.