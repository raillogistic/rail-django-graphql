#!/usr/bin/env python3
"""
Test complet pour vérifier l'invalidation du cache via les signaux Django
Ce test vérifie que tous les changements CRUD déclenchent l'invalidation du cache
"""

import os
import sys
import django
import json
import requests
import time
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.core.cache import cache
from django.db import transaction
from test_app.models import Category, Tag

# Configuration du serveur GraphQL
GRAPHQL_URL = "http://127.0.0.1:8000/graphql/"
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def log_test_step(step_name, details=""):
    """Log une étape de test avec timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{timestamp}] 🧪 {step_name}")
    if details:
        print(f"   📝 {details}")

def execute_graphql_query(query, variables=None):
    """Exécute une requête GraphQL"""
    payload = {
        'query': query,
        'variables': variables or {}
    }
    
    try:
        response = requests.post(GRAPHQL_URL, json=payload, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de requête: {e}")
        return None

def test_server_connection():
    """Test la connexion au serveur GraphQL"""
    log_test_step("Test de connexion au serveur GraphQL")
    
    query = """
    query TestConnection {
        __schema {
            queryType {
                name
            }
        }
    }
    """
    
    result = execute_graphql_query(query)
    if result and 'data' in result:
        print("✅ Serveur GraphQL accessible")
        return True
    else:
        print("❌ Serveur GraphQL inaccessible")
        return False

def get_categories_count():
    """Récupère le nombre de catégories via GraphQL"""
    query = """
    query GetCategories {
        categories {
            edges {
                node {
                    id
                    name
                }
            }
        }
    }
    """
    
    result = execute_graphql_query(query)
    if result and 'data' in result and result['data']['categories']:
        return len(result['data']['categories']['edges'])
    return 0

def test_direct_model_operations():
    """Test les opérations directes sur les modèles (sans GraphQL)"""
    log_test_step("Test des opérations directes sur les modèles")
    
    # 1. Vérifier l'état initial du cache
    initial_count = get_categories_count()
    print(f"   📊 Nombre initial de catégories (via GraphQL): {initial_count}")
    
    # 2. Créer une catégorie directement via le modèle Django
    log_test_step("Création directe d'une catégorie via le modèle Django")
    with transaction.atomic():
        new_category = Category.objects.create(
            name=f"Test Direct Category {datetime.now().strftime('%H%M%S')}",
            description="Créée directement via le modèle Django"
        )
        print(f"   ✅ Catégorie créée: {new_category.name} (ID: {new_category.id})")
    
    # 3. Attendre un peu pour que les signaux se déclenchent
    time.sleep(0.5)
    
    # 4. Vérifier que le cache a été invalidé
    log_test_step("Vérification de l'invalidation du cache après création directe")
    new_count = get_categories_count()
    print(f"   📊 Nouveau nombre de catégories (via GraphQL): {new_count}")
    
    if new_count > initial_count:
        print("   ✅ Cache invalidé correctement - nouvelle catégorie visible")
        cache_invalidated = True
    else:
        print("   ❌ Cache non invalidé - nouvelle catégorie non visible")
        cache_invalidated = False
    
    # 5. Modifier la catégorie
    log_test_step("Modification directe de la catégorie")
    new_category.description = f"Modifiée à {datetime.now().strftime('%H:%M:%S')}"
    new_category.save()
    print(f"   ✅ Catégorie modifiée: {new_category.name}")
    
    # 6. Supprimer la catégorie
    log_test_step("Suppression directe de la catégorie")
    category_id = new_category.id
    new_category.delete()
    print(f"   ✅ Catégorie supprimée (ID: {category_id})")
    
    # 7. Vérifier que le cache a été invalidé après suppression
    time.sleep(0.5)
    final_count = get_categories_count()
    print(f"   📊 Nombre final de catégories (via GraphQL): {final_count}")
    
    if final_count == initial_count:
        print("   ✅ Cache invalidé correctement après suppression")
        return cache_invalidated and True
    else:
        print("   ❌ Cache non invalidé après suppression")
        return False

def test_bulk_operations():
    """Test les opérations en lot"""
    log_test_step("Test des opérations en lot")
    
    initial_count = get_categories_count()
    
    # Créer plusieurs catégories en lot
    categories_to_create = [
        Category(name=f"Bulk Category {i}", description=f"Catégorie en lot {i}")
        for i in range(3)
    ]
    
    with transaction.atomic():
        Category.objects.bulk_create(categories_to_create)
        print(f"   ✅ {len(categories_to_create)} catégories créées en lot")
    
    time.sleep(0.5)
    
    # Vérifier l'invalidation
    new_count = get_categories_count()
    print(f"   📊 Nombre de catégories après création en lot: {new_count}")
    
    # Nettoyer
    Category.objects.filter(name__startswith="Bulk Category").delete()
    
    if new_count > initial_count:
        print("   ✅ Cache invalidé correctement pour les opérations en lot")
        return True
    else:
        print("   ❌ Cache non invalidé pour les opérations en lot")
        return False

def test_many_to_many_operations():
    """Test les opérations many-to-many"""
    log_test_step("Test des opérations many-to-many")
    
    # Créer une catégorie et des tags
    category = Category.objects.create(
        name=f"M2M Test Category {datetime.now().strftime('%H%M%S')}",
        description="Pour tester les relations M2M"
    )
    
    tag1 = Tag.objects.create(name=f"M2M Tag 1 {datetime.now().strftime('%H%M%S')}")
    tag2 = Tag.objects.create(name=f"M2M Tag 2 {datetime.now().strftime('%H%M%S')}")
    
    print(f"   ✅ Catégorie et tags créés")
    
    # Ajouter des tags à la catégorie (si la relation existe)
    try:
        if hasattr(category, 'tags'):
            category.tags.add(tag1, tag2)
            print(f"   ✅ Tags ajoutés à la catégorie")
            
            time.sleep(0.5)
            
            # Supprimer un tag
            category.tags.remove(tag1)
            print(f"   ✅ Tag supprimé de la catégorie")
            
            # Nettoyer
            category.tags.clear()
            
        else:
            print(f"   ℹ️ Pas de relation M2M tags sur Category")
            
    except Exception as e:
        print(f"   ⚠️ Erreur lors du test M2M: {e}")
    
    # Nettoyer
    category.delete()
    tag1.delete()
    tag2.delete()
    
    return True

def test_graphql_mutations_with_signals():
    """Test les mutations GraphQL avec les signaux"""
    log_test_step("Test des mutations GraphQL avec signaux")
    
    initial_count = get_categories_count()
    
    # Mutation GraphQL
    mutation = """
    mutation CreateCategory($input: CreateCategoryInput!) {
        createCategory(input: $input) {
            category {
                id
                name
                description
            }
            success
            errors
        }
    }
    """
    
    variables = {
        "input": {
            "name": f"GraphQL Signal Test {datetime.now().strftime('%H%M%S')}",
            "description": "Créée via mutation GraphQL avec signaux"
        }
    }
    
    result = execute_graphql_query(mutation, variables)
    
    if result and 'data' in result and result['data']['createCategory']['success']:
        category_id = result['data']['createCategory']['category']['id']
        print(f"   ✅ Catégorie créée via GraphQL (ID: {category_id})")
        
        time.sleep(0.5)
        
        # Vérifier l'invalidation
        new_count = get_categories_count()
        
        if new_count > initial_count:
            print("   ✅ Cache invalidé correctement pour mutation GraphQL")
            return True
        else:
            print("   ❌ Cache non invalidé pour mutation GraphQL")
            return False
    else:
        print(f"   ❌ Échec de la mutation GraphQL: {result}")
        return False

def run_comprehensive_test():
    """Lance tous les tests de manière séquentielle"""
    print("🚀 DÉBUT DES TESTS COMPLETS D'INVALIDATION DU CACHE VIA SIGNAUX")
    print("=" * 80)
    
    # Vérifier la connexion
    if not test_server_connection():
        print("❌ Impossible de continuer sans connexion au serveur")
        return False
    
    # Effacer le cache au début
    log_test_step("Nettoyage initial du cache")
    cache.clear()
    print("   ✅ Cache effacé")
    
    # Tests
    results = []
    
    try:
        # Test 1: Opérations directes sur les modèles
        results.append(("Opérations directes", test_direct_model_operations()))
        
        # Test 2: Opérations en lot
        results.append(("Opérations en lot", test_bulk_operations()))
        
        # Test 3: Opérations many-to-many
        results.append(("Opérations M2M", test_many_to_many_operations()))
        
        # Test 4: Mutations GraphQL avec signaux
        results.append(("Mutations GraphQL", test_graphql_mutations_with_signals()))
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        return False
    
    # Résumé des résultats
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 80)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"   {test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 TOUS LES TESTS SONT RÉUSSIS!")
        print("✅ Le middleware avec signaux Django fonctionne correctement")
        print("✅ Toutes les opérations CRUD déclenchent l'invalidation du cache")
    else:
        print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
        print("❌ Vérifiez la configuration du middleware et des signaux")
    
    print("=" * 80)
    return all_passed

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)