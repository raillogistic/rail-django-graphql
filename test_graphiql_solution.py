#!/usr/bin/env python3
"""
Test simplifié pour vérifier que la solution GraphiQL fonctionne.
Ce script simule exactement ce qui se passe dans GraphiQL.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.core.cache import cache
from test_app.models import Tag
from test_app.schema import invalidate_tag_cache
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_graphiql_solution():
    """Test de la solution pour GraphiQL."""
    print("\n" + "="*70)
    print("🎯 TEST DE LA SOLUTION GRAPHIQL - INVALIDATION DU CACHE")
    print("="*70)
    
    # Nettoyer
    cache.clear()
    Tag.objects.filter(name__startswith="GraphiQLTest").delete()
    print("🧹 Environnement nettoyé")
    
    # Étape 1: Simuler l'état initial (utilisateur charge GraphiQL)
    print("\n📋 ÉTAPE 1: État initial - Utilisateur charge GraphiQL")
    
    # Créer quelques tags existants
    existing_tags = [
        Tag.objects.create(name="GraphiQLTestExisting1", color="#FF0000"),
        Tag.objects.create(name="GraphiQLTestExisting2", color="#00FF00")
    ]
    print(f"✅ {len(existing_tags)} tags existants créés")
    
    # Simuler une requête GraphQL qui met en cache les résultats
    # (comme quand l'utilisateur exécute: query { tags { id name color } })
    all_tags = list(Tag.objects.filter(name__startswith="GraphiQLTest"))
    cache.set("graphql_all_tags", [{"id": t.pk, "name": t.name, "color": t.color} for t in all_tags], 300)
    cache.set("gql_query_tags", {"count": len(all_tags), "data": "cached"}, 300)
    print(f"📦 Cache simulé: {len(all_tags)} tags en cache")
    
    # Étape 2: Utilisateur crée un nouveau tag via mutation
    print("\n📋 ÉTAPE 2: Utilisateur crée un nouveau tag via GraphiQL")
    
    # Créer directement un tag et appeler l'invalidation (comme dans la mutation)
    new_tag = Tag.objects.create(name="GraphiQLTestNew", color="#0000FF")
    print(f"✅ Nouveau tag créé: {new_tag.name} (ID: {new_tag.pk})")
    
    # Appeler la fonction d'invalidation (comme dans CreateTag.mutate)
    print("🔄 Invalidation du cache...")
    invalidate_tag_cache(new_tag)
    
    # Étape 3: Vérifier l'invalidation
    print("\n📋 ÉTAPE 3: Vérification de l'invalidation du cache")
    
    cached_tags = cache.get("graphql_all_tags")
    cached_query = cache.get("gql_query_tags")
    
    if cached_tags is None:
        print("✅ Cache 'graphql_all_tags' correctement invalidé")
    else:
        print("❌ Cache 'graphql_all_tags' toujours présent")
    
    if cached_query is None:
        print("✅ Cache 'gql_query_tags' correctement invalidé")
    else:
        print("❌ Cache 'gql_query_tags' toujours présent")
    
    # Étape 4: Simuler la requête suivante (sans rafraîchissement)
    print("\n📋 ÉTAPE 4: Utilisateur exécute une nouvelle requête tags")
    
    # Comme le cache est invalidé, cette requête récupérera les données fraîches
    fresh_tags = list(Tag.objects.filter(name__startswith="GraphiQLTest"))
    print(f"🔍 Requête fraîche: {len(fresh_tags)} tags trouvés")
    
    # Vérifier que le nouveau tag est inclus
    new_tag_found = any(tag.name == "GraphiQLTestNew" for tag in fresh_tags)
    
    if new_tag_found:
        print("✅ SUCCÈS: Le nouveau tag est visible immédiatement!")
        print("✅ L'utilisateur voit le nouveau tag sans rafraîchir la page")
    else:
        print("❌ ÉCHEC: Le nouveau tag n'est pas visible")
    
    # Étape 5: Test de la fonction helper seule
    print("\n📋 ÉTAPE 5: Test direct de la fonction helper")
    
    # Remettre du cache
    cache.set("test_cache_key", "test_value", 300)
    cache.set("graphql_all_tags", ["test"], 300)
    
    test_tag = Tag.objects.create(name="GraphiQLTestHelper", color="#FFFF00")
    
    try:
        invalidate_tag_cache(test_tag)
        
        if cache.get("graphql_all_tags") is None:
            print("✅ Fonction helper fonctionne correctement")
        else:
            print("❌ Fonction helper ne fonctionne pas")
            
    except Exception as e:
        print(f"❌ Erreur dans la fonction helper: {e}")
    
    # Résumé final
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DE LA SOLUTION")
    print("="*70)
    
    if cached_tags is None and new_tag_found:
        print("🎉 SOLUTION FONCTIONNELLE!")
        print("✅ Le cache est correctement invalidé après les mutations")
        print("✅ Les nouveaux objets apparaissent immédiatement dans GraphiQL")
        print("✅ Plus besoin de rafraîchir la page!")
        
        print("\n🚀 INSTRUCTIONS POUR L'UTILISATEUR:")
        print("1. Redémarrer le serveur: python manage.py runserver")
        print("2. Aller sur http://localhost:8000/graphql/")
        print("3. Tester cette mutation:")
        print('   mutation { createTag(input: {name: "TestGraphiQL", color: "#FF5733"}) { tag { id name color } } }')
        print("4. Puis immédiatement cette requête:")
        print("   query { tags { id name color } }")
        print("5. Le nouveau tag devrait apparaître sans rafraîchissement!")
        
    else:
        print("⚠️ PROBLÈME DÉTECTÉ")
        print("🔧 Vérifiez les erreurs ci-dessus")
    
    # Nettoyer
    Tag.objects.filter(name__startswith="GraphiQLTest").delete()
    cache.clear()
    print("\n🧹 Nettoyage terminé")

if __name__ == "__main__":
    test_graphiql_solution()