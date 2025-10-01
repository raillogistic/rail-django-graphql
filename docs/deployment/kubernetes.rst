Kubernetes Deployment
====================

This guide covers deploying Django GraphQL Auto applications on Kubernetes clusters.

.. contents:: Table of Contents
   :local:
   :depth: 2

Kubernetes Fundamentals
----------------------

Why Kubernetes for Django GraphQL Auto?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Scalability**: Automatic horizontal and vertical scaling
* **High Availability**: Built-in redundancy and failover
* **Service Discovery**: Automatic load balancing and service routing
* **Rolling Updates**: Zero-downtime deployments
* **Resource Management**: Efficient resource allocation and limits
* **Self-healing**: Automatic restart of failed containers

Basic Kubernetes Resources
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # namespace.yaml
   apiVersion: v1
   kind: Namespace
   metadata:
     name: django-graphql-auto
     labels:
       name: django-graphql-auto

Application Deployment
---------------------

Django Application Deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: django-app
     namespace: django-graphql-auto
     labels:
       app: django-app
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: django-app
     template:
       metadata:
         labels:
           app: django-app
       spec:
         containers:
         - name: django
           image: your-registry/django-graphql-auto:latest
           ports:
           - containerPort: 8000
           env:
           - name: DJANGO_SETTINGS_MODULE
             value: "myproject.settings.production"
           - name: DB_HOST
             value: "postgres-service"
           - name: REDIS_URL
             value: "redis://redis-service:6379/1"
           - name: SECRET_KEY
             valueFrom:
               secretKeyRef:
                 name: django-secrets
                 key: secret-key
           - name: DB_PASSWORD
             valueFrom:
               secretKeyRef:
                 name: postgres-secrets
                 key: password
           resources:
             requests:
               memory: "256Mi"
               cpu: "250m"
             limits:
               memory: "512Mi"
               cpu: "500m"
           livenessProbe:
             httpGet:
               path: /health/
               port: 8000
             initialDelaySeconds: 30
             periodSeconds: 10
           readinessProbe:
             httpGet:
               path: /health/
               port: 8000
             initialDelaySeconds: 5
             periodSeconds: 5
           volumeMounts:
           - name: static-volume
             mountPath: /app/staticfiles
           - name: media-volume
             mountPath: /app/media
         volumes:
         - name: static-volume
           persistentVolumeClaim:
             claimName: static-pvc
         - name: media-volume
           persistentVolumeClaim:
             claimName: media-pvc
         imagePullSecrets:
         - name: registry-secret

Service Configuration
~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # service.yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: django-service
     namespace: django-graphql-auto
     labels:
       app: django-app
   spec:
     selector:
       app: django-app
     ports:
     - protocol: TCP
       port: 80
       targetPort: 8000
     type: ClusterIP

Database Setup
-------------

PostgreSQL Deployment
~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # postgres-deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: postgres
     namespace: django-graphql-auto
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: postgres
     template:
       metadata:
         labels:
           app: postgres
       spec:
         containers:
         - name: postgres
           image: postgres:15
           env:
           - name: POSTGRES_DB
             value: "django_graphql_auto"
           - name: POSTGRES_USER
             value: "postgres"
           - name: POSTGRES_PASSWORD
             valueFrom:
               secretKeyRef:
                 name: postgres-secrets
                 key: password
           - name: PGDATA
             value: "/var/lib/postgresql/data/pgdata"
           ports:
           - containerPort: 5432
           volumeMounts:
           - name: postgres-storage
             mountPath: /var/lib/postgresql/data
           resources:
             requests:
               memory: "256Mi"
               cpu: "250m"
             limits:
               memory: "1Gi"
               cpu: "500m"
         volumes:
         - name: postgres-storage
           persistentVolumeClaim:
             claimName: postgres-pvc

PostgreSQL Service
~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # postgres-service.yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: postgres-service
     namespace: django-graphql-auto
   spec:
     selector:
       app: postgres
     ports:
     - protocol: TCP
       port: 5432
       targetPort: 5432
     type: ClusterIP

Redis Deployment
~~~~~~~~~~~~~~~

.. code-block:: yaml

   # redis-deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: redis
     namespace: django-graphql-auto
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: redis
     template:
       metadata:
         labels:
           app: redis
       spec:
         containers:
         - name: redis
           image: redis:7-alpine
           command: ["redis-server", "--appendonly", "yes"]
           ports:
           - containerPort: 6379
           volumeMounts:
           - name: redis-storage
             mountPath: /data
           resources:
             requests:
               memory: "128Mi"
               cpu: "100m"
             limits:
               memory: "256Mi"
               cpu: "200m"
         volumes:
         - name: redis-storage
           persistentVolumeClaim:
             claimName: redis-pvc

Redis Service
~~~~~~~~~~~

.. code-block:: yaml

   # redis-service.yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: redis-service
     namespace: django-graphql-auto
   spec:
     selector:
       app: redis
     ports:
     - protocol: TCP
       port: 6379
       targetPort: 6379
     type: ClusterIP

Storage Configuration
--------------------

Persistent Volume Claims
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # storage.yaml
   apiVersion: v1
   kind: PersistentVolumeClaim
   metadata:
     name: postgres-pvc
     namespace: django-graphql-auto
   spec:
     accessModes:
       - ReadWriteOnce
     resources:
       requests:
         storage: 10Gi
     storageClassName: fast-ssd
   
   ---
   apiVersion: v1
   kind: PersistentVolumeClaim
   metadata:
     name: redis-pvc
     namespace: django-graphql-auto
   spec:
     accessModes:
       - ReadWriteOnce
     resources:
       requests:
         storage: 5Gi
     storageClassName: fast-ssd
   
   ---
   apiVersion: v1
   kind: PersistentVolumeClaim
   metadata:
     name: static-pvc
     namespace: django-graphql-auto
   spec:
     accessModes:
       - ReadWriteMany
     resources:
       requests:
         storage: 1Gi
     storageClassName: shared-storage
   
   ---
   apiVersion: v1
   kind: PersistentVolumeClaim
   metadata:
     name: media-pvc
     namespace: django-graphql-auto
   spec:
     accessModes:
       - ReadWriteMany
     resources:
       requests:
         storage: 5Gi
     storageClassName: shared-storage

Secrets Management
-----------------

Kubernetes Secrets
~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # secrets.yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: django-secrets
     namespace: django-graphql-auto
   type: Opaque
   data:
     secret-key: <base64-encoded-secret-key>
     db-password: <base64-encoded-db-password>
   
   ---
   apiVersion: v1
   kind: Secret
   metadata:
     name: postgres-secrets
     namespace: django-graphql-auto
   type: Opaque
   data:
     password: <base64-encoded-password>
   
   ---
   apiVersion: v1
   kind: Secret
   metadata:
     name: registry-secret
     namespace: django-graphql-auto
   type: kubernetes.io/dockerconfigjson
   data:
     .dockerconfigjson: <base64-encoded-docker-config>

ConfigMaps
~~~~~~~~~

.. code-block:: yaml

   # configmap.yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: django-config
     namespace: django-graphql-auto
   data:
     ALLOWED_HOSTS: "your-domain.com,www.your-domain.com"
     GRAPHQL_MAX_QUERY_COMPLEXITY: "1000"
     GRAPHQL_MAX_QUERY_DEPTH: "10"
     GRAPHQL_ENABLE_INTROSPECTION: "false"

External Secrets Operator
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # external-secret.yaml
   apiVersion: external-secrets.io/v1beta1
   kind: ExternalSecret
   metadata:
     name: django-external-secrets
     namespace: django-graphql-auto
   spec:
     refreshInterval: 1h
     secretStoreRef:
       name: vault-secret-store
       kind: SecretStore
     target:
       name: django-secrets
       creationPolicy: Owner
     data:
     - secretKey: secret-key
       remoteRef:
         key: django/secret-key
     - secretKey: db-password
       remoteRef:
         key: postgres/password

Ingress and Load Balancing
-------------------------

Nginx Ingress
~~~~~~~~~~~~

.. code-block:: yaml

   # ingress.yaml
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     name: django-ingress
     namespace: django-graphql-auto
     annotations:
       kubernetes.io/ingress.class: "nginx"
       cert-manager.io/cluster-issuer: "letsencrypt-prod"
       nginx.ingress.kubernetes.io/ssl-redirect: "true"
       nginx.ingress.kubernetes.io/proxy-body-size: "10m"
       nginx.ingress.kubernetes.io/rate-limit: "100"
       nginx.ingress.kubernetes.io/rate-limit-window: "1m"
   spec:
     tls:
     - hosts:
       - your-domain.com
       - www.your-domain.com
       secretName: django-tls
     rules:
     - host: your-domain.com
       http:
         paths:
         - path: /
           pathType: Prefix
           backend:
             service:
               name: django-service
               port:
                 number: 80
     - host: www.your-domain.com
       http:
         paths:
         - path: /
           pathType: Prefix
           backend:
             service:
               name: django-service
               port:
                 number: 80

SSL Certificates
~~~~~~~~~~~~~~

.. code-block:: yaml

   # cert-manager.yaml
   apiVersion: cert-manager.io/v1
   kind: ClusterIssuer
   metadata:
     name: letsencrypt-prod
   spec:
     acme:
       server: https://acme-v02.api.letsencrypt.org/directory
       email: your-email@domain.com
       privateKeySecretRef:
         name: letsencrypt-prod
       solvers:
       - http01:
           ingress:
             class: nginx

Horizontal Pod Autoscaler
------------------------

HPA Configuration
~~~~~~~~~~~~~~~

.. code-block:: yaml

   # hpa.yaml
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: django-hpa
     namespace: django-graphql-auto
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: django-app
     minReplicas: 3
     maxReplicas: 10
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70
     - type: Resource
       resource:
         name: memory
         target:
           type: Utilization
           averageUtilization: 80
     behavior:
       scaleDown:
         stabilizationWindowSeconds: 300
         policies:
         - type: Percent
           value: 10
           periodSeconds: 60
       scaleUp:
         stabilizationWindowSeconds: 60
         policies:
         - type: Percent
           value: 50
           periodSeconds: 60

Vertical Pod Autoscaler
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # vpa.yaml
   apiVersion: autoscaling.k8s.io/v1
   kind: VerticalPodAutoscaler
   metadata:
     name: django-vpa
     namespace: django-graphql-auto
   spec:
     targetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: django-app
     updatePolicy:
       updateMode: "Auto"
     resourcePolicy:
       containerPolicies:
       - containerName: django
         maxAllowed:
           cpu: 1
           memory: 2Gi
         minAllowed:
           cpu: 100m
           memory: 128Mi

Monitoring and Observability
---------------------------

Prometheus Monitoring
~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # servicemonitor.yaml
   apiVersion: monitoring.coreos.com/v1
   kind: ServiceMonitor
   metadata:
     name: django-metrics
     namespace: django-graphql-auto
     labels:
       app: django-app
   spec:
     selector:
       matchLabels:
         app: django-app
     endpoints:
     - port: metrics
       interval: 30s
       path: /metrics

Grafana Dashboard
~~~~~~~~~~~~~~~

.. code-block:: yaml

   # grafana-dashboard.yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: django-dashboard
     namespace: monitoring
     labels:
       grafana_dashboard: "1"
   data:
     django-graphql-auto.json: |
       {
         "dashboard": {
           "title": "Django GraphQL Auto",
           "panels": [
             {
               "title": "Request Rate",
               "type": "graph",
               "targets": [
                 {
                   "expr": "rate(django_http_requests_total[5m])"
                 }
               ]
             }
           ]
         }
       }

Logging with Fluentd
~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # fluentd-configmap.yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: fluentd-config
     namespace: kube-system
   data:
     fluent.conf: |
       <source>
         @type tail
         path /var/log/containers/*django-app*.log
         pos_file /var/log/fluentd-containers.log.pos
         tag kubernetes.*
         format json
         time_format %Y-%m-%dT%H:%M:%S.%NZ
       </source>
       
       <match kubernetes.**>
         @type elasticsearch
         host elasticsearch.logging.svc.cluster.local
         port 9200
         index_name django-logs
       </match>

Job and CronJob Management
-------------------------

Database Migrations
~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # migration-job.yaml
   apiVersion: batch/v1
   kind: Job
   metadata:
     name: django-migrate
     namespace: django-graphql-auto
   spec:
     template:
       spec:
         containers:
         - name: migrate
           image: your-registry/django-graphql-auto:latest
           command: ["python", "manage.py", "migrate"]
           env:
           - name: DJANGO_SETTINGS_MODULE
             value: "myproject.settings.production"
           - name: DB_HOST
             value: "postgres-service"
           - name: DB_PASSWORD
             valueFrom:
               secretKeyRef:
                 name: postgres-secrets
                 key: password
         restartPolicy: OnFailure
     backoffLimit: 3

Scheduled Tasks
~~~~~~~~~~~~~

.. code-block:: yaml

   # cronjob.yaml
   apiVersion: batch/v1
   kind: CronJob
   metadata:
     name: django-cleanup
     namespace: django-graphql-auto
   spec:
     schedule: "0 2 * * *"  # Daily at 2 AM
     jobTemplate:
       spec:
         template:
           spec:
             containers:
             - name: cleanup
               image: your-registry/django-graphql-auto:latest
               command: ["python", "manage.py", "clearsessions"]
               env:
               - name: DJANGO_SETTINGS_MODULE
                 value: "myproject.settings.production"
               - name: DB_HOST
                 value: "postgres-service"
               - name: DB_PASSWORD
                 valueFrom:
                   secretKeyRef:
                     name: postgres-secrets
                     key: password
             restartPolicy: OnFailure

Backup Strategy
--------------

Database Backups
~~~~~~~~~~~~~~~

.. code-block:: yaml

   # backup-cronjob.yaml
   apiVersion: batch/v1
   kind: CronJob
   metadata:
     name: postgres-backup
     namespace: django-graphql-auto
   spec:
     schedule: "0 1 * * *"  # Daily at 1 AM
     jobTemplate:
       spec:
         template:
           spec:
             containers:
             - name: backup
               image: postgres:15
               command:
               - /bin/bash
               - -c
               - |
                 DATE=$(date +%Y%m%d_%H%M%S)
                 pg_dump -h postgres-service -U postgres django_graphql_auto | gzip > /backup/backup_$DATE.sql.gz
                 # Upload to S3 or other storage
                 aws s3 cp /backup/backup_$DATE.sql.gz s3://your-backup-bucket/
                 # Cleanup old backups
                 find /backup -name "backup_*.sql.gz" -mtime +7 -delete
               env:
               - name: PGPASSWORD
                 valueFrom:
                   secretKeyRef:
                     name: postgres-secrets
                     key: password
               volumeMounts:
               - name: backup-storage
                 mountPath: /backup
             volumes:
             - name: backup-storage
               persistentVolumeClaim:
                 claimName: backup-pvc
             restartPolicy: OnFailure

Disaster Recovery
~~~~~~~~~~~~~~~

.. code-block:: yaml

   # restore-job.yaml
   apiVersion: batch/v1
   kind: Job
   metadata:
     name: postgres-restore
     namespace: django-graphql-auto
   spec:
     template:
       spec:
         containers:
         - name: restore
           image: postgres:15
           command:
           - /bin/bash
           - -c
           - |
             # Download backup from S3
             aws s3 cp s3://your-backup-bucket/backup_20231201_010000.sql.gz /tmp/
             # Restore database
             gunzip -c /tmp/backup_20231201_010000.sql.gz | psql -h postgres-service -U postgres django_graphql_auto
           env:
           - name: PGPASSWORD
             valueFrom:
               secretKeyRef:
                 name: postgres-secrets
                 key: password
         restartPolicy: Never

Security Hardening
-----------------

Network Policies
~~~~~~~~~~~~~~

.. code-block:: yaml

   # network-policy.yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: django-network-policy
     namespace: django-graphql-auto
   spec:
     podSelector:
       matchLabels:
         app: django-app
     policyTypes:
     - Ingress
     - Egress
     ingress:
     - from:
       - namespaceSelector:
           matchLabels:
             name: ingress-nginx
       ports:
       - protocol: TCP
         port: 8000
     egress:
     - to:
       - podSelector:
           matchLabels:
             app: postgres
       ports:
       - protocol: TCP
         port: 5432
     - to:
       - podSelector:
           matchLabels:
             app: redis
       ports:
       - protocol: TCP
         port: 6379

Pod Security Policy
~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # pod-security-policy.yaml
   apiVersion: policy/v1beta1
   kind: PodSecurityPolicy
   metadata:
     name: django-psp
   spec:
     privileged: false
     allowPrivilegeEscalation: false
     requiredDropCapabilities:
       - ALL
     volumes:
       - 'configMap'
       - 'emptyDir'
       - 'projected'
       - 'secret'
       - 'downwardAPI'
       - 'persistentVolumeClaim'
     runAsUser:
       rule: 'MustRunAsNonRoot'
     seLinux:
       rule: 'RunAsAny'
     fsGroup:
       rule: 'RunAsAny'

RBAC Configuration
~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # rbac.yaml
   apiVersion: v1
   kind: ServiceAccount
   metadata:
     name: django-service-account
     namespace: django-graphql-auto
   
   ---
   apiVersion: rbac.authorization.k8s.io/v1
   kind: Role
   metadata:
     name: django-role
     namespace: django-graphql-auto
   rules:
   - apiGroups: [""]
     resources: ["pods", "services"]
     verbs: ["get", "list"]
   
   ---
   apiVersion: rbac.authorization.k8s.io/v1
   kind: RoleBinding
   metadata:
     name: django-role-binding
     namespace: django-graphql-auto
   subjects:
   - kind: ServiceAccount
     name: django-service-account
     namespace: django-graphql-auto
   roleRef:
     kind: Role
     name: django-role
     apiGroup: rbac.authorization.k8s.io

CI/CD Integration
----------------

GitLab CI/CD
~~~~~~~~~~~

.. code-block:: yaml

   # .gitlab-ci.yml
   stages:
     - test
     - build
     - deploy
   
   variables:
     DOCKER_DRIVER: overlay2
     DOCKER_TLS_CERTDIR: "/certs"
   
   test:
     stage: test
     image: python:3.11
     services:
       - postgres:15
     variables:
       POSTGRES_DB: test_db
       POSTGRES_USER: postgres
       POSTGRES_PASSWORD: postgres
     script:
       - pip install -r requirements.txt
       - python manage.py test
   
   build:
     stage: build
     image: docker:latest
     services:
       - docker:dind
     script:
       - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
       - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
   
   deploy:
     stage: deploy
     image: bitnami/kubectl:latest
     script:
       - kubectl set image deployment/django-app django=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA -n django-graphql-auto
       - kubectl rollout status deployment/django-app -n django-graphql-auto

ArgoCD GitOps
~~~~~~~~~~~~

.. code-block:: yaml

   # argocd-application.yaml
   apiVersion: argoproj.io/v1alpha1
   kind: Application
   metadata:
     name: django-graphql-auto
     namespace: argocd
   spec:
     project: default
     source:
       repoURL: https://github.com/your-org/django-graphql-auto-k8s
       targetRevision: HEAD
       path: manifests
     destination:
       server: https://kubernetes.default.svc
       namespace: django-graphql-auto
     syncPolicy:
       automated:
         prune: true
         selfHeal: true
       syncOptions:
       - CreateNamespace=true

Helm Charts
----------

Chart Structure
~~~~~~~~~~~~~

.. code-block:: bash

   django-graphql-auto/
   ├── Chart.yaml
   ├── values.yaml
   ├── templates/
   │   ├── deployment.yaml
   │   ├── service.yaml
   │   ├── ingress.yaml
   │   ├── configmap.yaml
   │   ├── secrets.yaml
   │   └── hpa.yaml
   └── charts/

Chart.yaml
~~~~~~~~~

.. code-block:: yaml

   # Chart.yaml
   apiVersion: v2
   name: django-graphql-auto
   description: A Helm chart for Django GraphQL Auto
   type: application
   version: 0.1.0
   appVersion: "1.0.0"
   dependencies:
   - name: postgresql
     version: 12.1.2
     repository: https://charts.bitnami.com/bitnami
   - name: redis
     version: 17.3.7
     repository: https://charts.bitnami.com/bitnami

Values.yaml
~~~~~~~~~

.. code-block:: yaml

   # values.yaml
   replicaCount: 3
   
   image:
     repository: your-registry/django-graphql-auto
     pullPolicy: IfNotPresent
     tag: "latest"
   
   service:
     type: ClusterIP
     port: 80
   
   ingress:
     enabled: true
     className: "nginx"
     annotations:
       cert-manager.io/cluster-issuer: letsencrypt-prod
     hosts:
       - host: your-domain.com
         paths:
           - path: /
             pathType: Prefix
     tls:
       - secretName: django-tls
         hosts:
           - your-domain.com
   
   resources:
     limits:
       cpu: 500m
       memory: 512Mi
     requests:
       cpu: 250m
       memory: 256Mi
   
   autoscaling:
     enabled: true
     minReplicas: 3
     maxReplicas: 10
     targetCPUUtilizationPercentage: 70
   
   postgresql:
     enabled: true
     auth:
       postgresPassword: "your-password"
       database: "django_graphql_auto"
   
   redis:
     enabled: true
     auth:
       enabled: false

Troubleshooting
--------------

Common Issues
~~~~~~~~~~~

**Pod Startup Issues**

.. code-block:: bash

   # Check pod status
   kubectl get pods -n django-graphql-auto
   
   # Describe pod for events
   kubectl describe pod <pod-name> -n django-graphql-auto
   
   # Check logs
   kubectl logs <pod-name> -n django-graphql-auto

**Service Discovery Issues**

.. code-block:: bash

   # Test service connectivity
   kubectl exec -it <pod-name> -n django-graphql-auto -- nslookup postgres-service
   
   # Check service endpoints
   kubectl get endpoints -n django-graphql-auto

**Resource Issues**

.. code-block:: bash

   # Check resource usage
   kubectl top pods -n django-graphql-auto
   kubectl top nodes
   
   # Check resource quotas
   kubectl describe resourcequota -n django-graphql-auto

Debugging Commands
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Interactive debugging
   kubectl exec -it <pod-name> -n django-graphql-auto -- /bin/bash
   
   # Port forwarding for local access
   kubectl port-forward service/django-service 8000:80 -n django-graphql-auto
   
   # Check cluster events
   kubectl get events --sort-by=.metadata.creationTimestamp -n django-graphql-auto

Best Practices Summary
---------------------

1. **Resource Management**: Set appropriate requests and limits
2. **Health Checks**: Implement liveness and readiness probes
3. **Security**: Use RBAC, network policies, and security contexts
4. **Monitoring**: Implement comprehensive observability
5. **Scaling**: Use HPA and VPA for automatic scaling
6. **Storage**: Use appropriate storage classes and backup strategies
7. **Secrets**: Never store secrets in plain text
8. **Networking**: Use service mesh for complex networking requirements
9. **GitOps**: Implement GitOps workflows for deployments
10. **Testing**: Test in staging environments that mirror production