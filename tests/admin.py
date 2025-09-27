"""
Configuration de l'administration Django pour les tests.

Ce module configure:
- Interface d'administration pour les modèles de test
- Filtres et recherche pour les tests
- Actions personnalisées pour les tests
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    TestPerformanceModel,
    TestConcurrencyModel,
    TestCacheModel,
    TestSecurityModel,
    TestUserProfile,
    TestLogEntry
)


@admin.register(TestPerformanceModel)
class TestPerformanceModelAdmin(admin.ModelAdmin):
    """Administration pour les tests de performance."""
    
    list_display = [
        'name',
        'execution_time_display',
        'memory_usage_display',
        'created_at'
    ]
    list_filter = [
        'created_at',
        ('execution_time', admin.EmptyFieldListFilter),
        ('memory_usage', admin.EmptyFieldListFilter),
    ]
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description')
        }),
        ('Métriques de performance', {
            'fields': ('execution_time', 'memory_usage')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def execution_time_display(self, obj):
        """Affiche le temps d'exécution formaté."""
        if obj.execution_time is not None:
            if obj.execution_time < 1000:
                return format_html(
                    '<span style="color: green;">{:.2f} ms</span>',
                    obj.execution_time
                )
            elif obj.execution_time < 5000:
                return format_html(
                    '<span style="color: orange;">{:.2f} ms</span>',
                    obj.execution_time
                )
            else:
                return format_html(
                    '<span style="color: red;">{:.2f} ms</span>',
                    obj.execution_time
                )
        return '-'
    execution_time_display.short_description = 'Temps d\'exécution'
    
    def memory_usage_display(self, obj):
        """Affiche l'utilisation mémoire formatée."""
        if obj.memory_usage is not None:
            if obj.memory_usage < 1024 * 1024:  # < 1MB
                return f"{obj.memory_usage / 1024:.1f} KB"
            elif obj.memory_usage < 1024 * 1024 * 1024:  # < 1GB
                return f"{obj.memory_usage / (1024 * 1024):.1f} MB"
            else:
                return f"{obj.memory_usage / (1024 * 1024 * 1024):.1f} GB"
        return '-'
    memory_usage_display.short_description = 'Utilisation mémoire'


@admin.register(TestConcurrencyModel)
class TestConcurrencyModelAdmin(admin.ModelAdmin):
    """Administration pour les tests de concurrence."""
    
    list_display = [
        'name',
        'thread_count',
        'concurrent_operations',
        'success_rate_display',
        'average_response_time_display',
        'created_at'
    ]
    list_filter = [
        'thread_count',
        'created_at',
        ('average_response_time', admin.EmptyFieldListFilter),
    ]
    search_fields = ['name']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Configuration du test', {
            'fields': ('name', 'thread_count', 'concurrent_operations')
        }),
        ('Résultats', {
            'fields': ('success_count', 'error_count', 'average_response_time')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def success_rate_display(self, obj):
        """Affiche le taux de succès."""
        total = obj.success_count + obj.error_count
        if total > 0:
            rate = (obj.success_count / total) * 100
            if rate >= 95:
                color = 'green'
            elif rate >= 80:
                color = 'orange'
            else:
                color = 'red'
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color, rate
            )
        return '-'
    success_rate_display.short_description = 'Taux de succès'
    
    def average_response_time_display(self, obj):
        """Affiche le temps de réponse moyen formaté."""
        if obj.average_response_time is not None:
            return f"{obj.average_response_time:.2f} ms"
        return '-'
    average_response_time_display.short_description = 'Temps de réponse moyen'


@admin.register(TestCacheModel)
class TestCacheModelAdmin(admin.ModelAdmin):
    """Administration pour les tests de cache."""
    
    list_display = [
        'key',
        'value_preview',
        'ttl_display',
        'hit_count',
        'updated_at'
    ]
    list_filter = [
        'created_at',
        'updated_at',
        ('ttl', admin.EmptyFieldListFilter),
    ]
    search_fields = ['key', 'value']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def value_preview(self, obj):
        """Affiche un aperçu de la valeur."""
        if len(obj.value) > 50:
            return obj.value[:50] + '...'
        return obj.value
    value_preview.short_description = 'Valeur'
    
    def ttl_display(self, obj):
        """Affiche le TTL formaté."""
        if obj.ttl is not None:
            if obj.ttl < 60:
                return f"{obj.ttl}s"
            elif obj.ttl < 3600:
                return f"{obj.ttl // 60}m {obj.ttl % 60}s"
            else:
                hours = obj.ttl // 3600
                minutes = (obj.ttl % 3600) // 60
                return f"{hours}h {minutes}m"
        return 'Permanent'
    ttl_display.short_description = 'Durée de vie'


@admin.register(TestSecurityModel)
class TestSecurityModelAdmin(admin.ModelAdmin):
    """Administration pour les tests de sécurité."""
    
    list_display = [
        'test_type',
        'payload_preview',
        'expected_result',
        'actual_result',
        'vulnerability_status',
        'created_at'
    ]
    list_filter = [
        'test_type',
        'expected_result',
        'actual_result',
        'is_vulnerable',
        'created_at',
    ]
    search_fields = ['payload']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Configuration du test', {
            'fields': ('test_type', 'payload')
        }),
        ('Résultats', {
            'fields': ('expected_result', 'actual_result', 'is_vulnerable')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def payload_preview(self, obj):
        """Affiche un aperçu du payload."""
        if len(obj.payload) > 30:
            return obj.payload[:30] + '...'
        return obj.payload
    payload_preview.short_description = 'Charge utile'
    
    def vulnerability_status(self, obj):
        """Affiche le statut de vulnérabilité."""
        if obj.is_vulnerable:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ Vulnérable</span>'
            )
        else:
            return format_html(
                '<span style="color: green;">✅ Sécurisé</span>'
            )
    vulnerability_status.short_description = 'Statut de sécurité'


@admin.register(TestUserProfile)
class TestUserProfileAdmin(admin.ModelAdmin):
    """Administration pour les profils utilisateur de test."""
    
    list_display = [
        'user',
        'test_role',
        'permissions_count',
        'created_at'
    ]
    list_filter = [
        'test_role',
        'created_at',
    ]
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def permissions_count(self, obj):
        """Affiche le nombre de permissions."""
        return len(obj.permissions) if obj.permissions else 0
    permissions_count.short_description = 'Nombre de permissions'


@admin.register(TestLogEntry)
class TestLogEntryAdmin(admin.ModelAdmin):
    """Administration pour les entrées de log de test."""
    
    list_display = [
        'test_name',
        'test_type',
        'status_display',
        'duration_display',
        'created_at'
    ]
    list_filter = [
        'test_type',
        'status',
        'created_at',
        ('duration', admin.EmptyFieldListFilter),
    ]
    search_fields = ['test_name', 'error_message']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informations du test', {
            'fields': ('test_name', 'test_type', 'status', 'duration')
        }),
        ('Erreurs', {
            'fields': ('error_message', 'traceback'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('metadata', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        """Affiche le statut avec couleur."""
        colors = {
            'passed': 'green',
            'failed': 'red',
            'skipped': 'orange',
            'error': 'darkred',
        }
        icons = {
            'passed': '✅',
            'failed': '❌',
            'skipped': '⏭️',
            'error': '💥',
        }
        
        color = colors.get(obj.status, 'black')
        icon = icons.get(obj.status, '❓')
        
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_display.short_description = 'Statut'
    
    def duration_display(self, obj):
        """Affiche la durée formatée."""
        if obj.duration is not None:
            if obj.duration < 1:
                return f"{obj.duration * 1000:.0f} ms"
            else:
                return f"{obj.duration:.2f} s"
        return '-'
    duration_display.short_description = 'Durée'
    
    actions = ['clear_old_logs']
    
    def clear_old_logs(self, request, queryset):
        """Action pour supprimer les anciens logs."""
        from datetime import datetime, timedelta
        
        old_date = datetime.now() - timedelta(days=30)
        old_logs = TestLogEntry.objects.filter(created_at__lt=old_date)
        count = old_logs.count()
        old_logs.delete()
        
        self.message_user(
            request,
            f"{count} anciens logs supprimés (plus de 30 jours)."
        )
    clear_old_logs.short_description = "Supprimer les logs de plus de 30 jours"


# Configuration globale de l'admin
admin.site.site_header = "Administration des Tests GraphQL Auto"
admin.site.site_title = "Tests GraphQL Auto"
admin.site.index_title = "Gestion des Tests"
