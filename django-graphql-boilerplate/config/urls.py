"""
URL configuration for django-graphql-boilerplate project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from graphene_django.views import GraphQLView
from rail_django_graphql.health_urls import health_urlpatterns
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    
    # GraphQL endpoint (library view)
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    
    # Health check endpoints
    path('health/', include(health_urlpatterns)),
    
    # App URLs
    path('users/', include('apps.users.urls')),
    path('blog/', include('apps.blog.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)