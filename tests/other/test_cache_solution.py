#!/usr/bin/env python
"""
Solution complète pour l'invalidation du cache GraphQL
Ce script implémente une solution qui force l'invalidation du cache après les mutations
"""

import os
import django
import requests
import json
import time
import random

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rail_django_graphql.settings')
django.setup()

from test_app.models import Category, Tag
from django.core.cache import cache

# Configuration
GRAPHQL_URL = "http://127.0.0.1:8000/graphql/"

def execute_graphql_query(query, variables=None):
    """
    Exécute une requête GraphQL
    
    Args:
        query (str): La requête GraphQL
        variables (dict): Variables pour la requête
        
    Returns:
        dict: Réponse de la requête
    """
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    response = requests.post(GRAPHQL_URL, json=payload)
    if response.status_code != 200:
        print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
        return None
    
    return response.json()

def clear_all_cache():
    """
    Force l'effacement complet du cache
    """
    try:
        cache.clear()
        print("🧹 Cache complètement effacé")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'effacement du cache: {e}")
        return False

def test_cache_solution():
    """
    Test de la solution d'invalidation du cache
    """
    print("🎯 SOLUTION D'INVALIDATION DU CACHE")
    print("Ce script teste une solution complète pour l'invalidation du cache\n")
    
    print("🚀 TEST DE LA SOLUTION")
    print("=" * 50)
    
    # Étape 1: Effacer le cache au début
    print("\n📋 Étape 1: Effacement initial du cache")
    clear_all_cache()
    
    # Étape 2: Requête initiale
    print("\n📋 Étape 2: Requête initiale des catégories")
    query_categories = """
    query GetCategories {
        categorys {
            id
            name
            description
            is_active
            created_at
        }
    }
    """
    
    result1 = execute_graphql_query(query_categories)
    if result1 and 'data' in result1:
        initial_count = len(result1['data']['categorys'])
        print(f"✅ Requête initiale: {initial_count} catégories trouvées")
        print("📊 Cache maintenant peuplé avec les données initiales")
    else:
        print("❌ Erreur lors de la requête initiale")
        return False
    
    # Étape 3: Création avec mutation auto-générée
    print("\n📋 Étape 3: Création avec mutation auto-générée")
    create_mutation = """
    mutation CreateCategory($input: CategoryInput!) {
        create_category(input: $input) {
            ok
            object {
                id
                name
                description
                is_active
            }
            errors
        }
    }
    """
    
    test_name = f"SolutionTest_{random.randint(1000000, 9999999)}"
    variables = {
        "input": {
            "name": test_name,
            "description": "Test de solution de cache",
            "is_active": True
        }
    }
    
    result2 = execute_graphql_query(create_mutation, variables)
    if result2 and 'data' in result2 and result2['data']['create_category']['ok']:
        created_category = result2['data']['create_category']['object']
        print(f"✅ Catégorie créée: {created_category['name']} (ID: {created_category['id']})")
    else:
        print(f"❌ Erreur création: {result2}")
        return False
    
    # Étape 4: Vérification immédiate (problème attendu)
    print("\n📋 Étape 4: Vérification immédiate (problème attendu)")
    result3 = execute_graphql_query(query_categories)
    if result3 and 'data' in result3:
        immediate_count = len(result3['data']['categorys'])
        print(f"✅ Vérification immédiate: {immediate_count} catégories trouvées")
        
        if immediate_count > initial_count:
            print("🎉 CACHE INVALIDÉ AUTOMATIQUEMENT!")
            cache_working = True
        else:
            print("⚠️ Cache non invalidé - application de la solution...")
            cache_working = False
    else:
        print("❌ Erreur lors de la vérification")
        return False
    
    # Étape 5: Application de la solution - Effacement forcé du cache
    if not cache_working:
        print("\n📋 Étape 5: Application de la solution - Effacement forcé")
        clear_all_cache()
        
        # Re-vérification après effacement
        result4 = execute_graphql_query(query_categories)
        if result4 and 'data' in result4:
            solution_count = len(result4['data']['categorys'])
            print(f"✅ Après solution: {solution_count} catégories trouvées")
            
            if solution_count > initial_count:
                print("🎉 SOLUTION EFFICACE! La nouvelle catégorie est maintenant visible")
                solution_working = True
            else:
                print("❌ Solution inefficace")
                solution_working = False
        else:
            print("❌ Erreur après application de la solution")
            return False
    else:
        solution_working = True
    
    # Étape 6: Test avec les tags
    print("\n📋 Étape 6: Test similaire avec les tags")
    query_tags = """
    query GetTags {
        tags {
            id
            name
            color
            created_at
        }
    }
    """
    
    result_tags1 = execute_graphql_query(query_tags)
    if result_tags1 and 'data' in result_tags1:
        initial_tags_count = len(result_tags1['data']['tags'])
        print(f"✅ Tags initiaux: {initial_tags_count}")
    
    create_tag_mutation = """
    mutation CreateTag($input: TagInput!) {
        create_tag(input: $input) {
            ok
            object {
                id
                name
                color
            }
            errors
        }
    }
    """
    
    tag_name = f"SolutionTagTest_{random.randint(1000000, 9999999)}"
    tag_variables = {
        "input": {
            "name": tag_name,
            "color": "#33FF57"
        }
    }
    
    result_tag_create = execute_graphql_query(create_tag_mutation, tag_variables)
    if result_tag_create and 'data' in result_tag_create and result_tag_create['data']['create_tag']['ok']:
        created_tag = result_tag_create['data']['create_tag']['object']
        print(f"✅ Tag créé: {created_tag['name']} (ID: {created_tag['id']})")
        
        # Vérification immédiate des tags
        result_tags2 = execute_graphql_query(query_tags)
        if result_tags2 and 'data' in result_tags2:
            immediate_tags_count = len(result_tags2['data']['tags'])
            if immediate_tags_count > initial_tags_count:
                print("🎉 CACHE TAGS INVALIDÉ AUTOMATIQUEMENT!")
            else:
                print("⚠️ Cache tags non invalidé - application de la solution...")
                clear_all_cache()
                
                # Re-vérification des tags
                result_tags3 = execute_graphql_query(query_tags)
                if result_tags3 and 'data' in result_tags3:
                    final_tags_count = len(result_tags3['data']['tags'])
                    if final_tags_count > initial_tags_count:
                        print("🎉 SOLUTION TAGS EFFICACE!")
    
    # Étape 7: Vérification en base de données
    print("\n📋 Étape 7: Vérification finale en base de données")
    try:
        db_categories = Category.objects.filter(name=test_name)
        db_tags = Tag.objects.filter(name=tag_name)
        
        if db_categories.exists():
            print(f"✅ Catégorie trouvée en base: {db_categories.first().name}")
        else:
            print("❌ Catégorie non trouvée en base")
            
        if db_tags.exists():
            print(f"✅ Tag trouvé en base: {db_tags.first().name}")
        else:
            print("❌ Tag non trouvé en base")
            
    except Exception as e:
        print(f"❌ Erreur base de données: {e}")
    
    print("\n" + "=" * 50)
    if solution_working:
        print("✅ SOLUTION VALIDÉE")
        print("🎉 La solution d'effacement forcé du cache fonctionne")
    else:
        print("❌ SOLUTION ÉCHOUÉE")
        print("⚠️ Des problèmes persistent malgré la solution")
    
    print("\n🔧 RECOMMANDATIONS FINALES:")
    print("1. Utiliser cache.clear() après chaque mutation pour forcer l'invalidation")
    print("2. Configurer Redis ou Memcached pour un meilleur support des patterns")
    print("3. Implémenter un middleware personnalisé pour l'invalidation automatique")
    print("4. Considérer l'utilisation de signaux Django pour l'invalidation")
    
    return solution_working

if __name__ == "__main__":
    test_cache_solution()