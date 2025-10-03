Deployment Guide

This boilerplate includes a production-ready deployment pack under `django-graphql-boilerplate/deploy`.

Prerequisites
- Docker and Docker Compose
- Set `.env.production` with secure values

Services
- `db`: PostgreSQL 15 with tuned configuration and init SQL
- `redis`: Redis 7 with persistence and LRU policy
- `web`: Django app served by Gunicorn
- `nginx`: Reverse proxy and static/media hosting
- `prometheus`: Metrics collection
- `grafana`: Dashboards and provisioning

Quick Start
1. Copy env: `cp django-graphql-boilerplate/deploy/.env.production.example django-graphql-boilerplate/deploy/.env.production` and set `SECRET_KEY`, `POSTGRES_PASSWORD`, `ALLOWED_HOSTS`
2. Compose up: `docker compose -f django-graphql-boilerplate/deploy/docker-compose.production.yml --env-file django-graphql-boilerplate/deploy/.env.production up -d --build`
3. Migrate: `docker compose -f django-graphql-boilerplate/deploy/docker-compose.production.yml exec web python manage.py migrate`
4. Static: `docker compose -f django-graphql-boilerplate/deploy/docker-compose.production.yml exec web python manage.py collectstatic --noinput`
5. Superuser: `docker compose -f django-graphql-boilerplate/deploy/docker-compose.production.yml exec web python manage.py createsuperuser`

Notes
- Static and media are volume-mounted and served by Nginx.
- SSL can be enabled by adding certs and exposing 443; update Nginx site config accordingly.
- Redis cache is configured via `REDIS_URL` and integrated with Django `CACHES`.
- Postgres extensions and example role are applied by `init-db.sql`; adapt for your environment.