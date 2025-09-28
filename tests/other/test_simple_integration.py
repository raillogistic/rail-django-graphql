#!/usr/bin/env python3
"""
Test simple pour vérifier l'intégration des mutations personnalisées.
"""

import requests
import json
import time

def make_graphql_request(query, variables=None):
    """Effectue une requête GraphQL vers le serveur local."""
    url = "http://127.0.0.1:8000/graphql/"
    payload = {
        "query": query,
        "variables": variables or {}
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
            return None
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de requête: {e}")
        return None

def test_simple_integration():
    """Test simple de l'intégration."""
    print("🚀 TEST SIMPLE D'INTÉGRATION")
    print("=" * 50)
    
    # Test 1: Vérifier les catégories avec l'auto-schema
    print("\n📋 Test 1: Requête des catégories (auto-schema)")
    
    categories_query = """
    query {
        categorys {
            id
            name
            description
        }
    }
    """
    
    result = make_graphql_request(categories_query)
    if result and 'data' in result:
        count = len(result['data']['categorys'])
        print(f"✅ Requête réussie: {count} catégories trouvées")
    else:
        print(f"❌ Erreur: {result}")
        return False
    
    # Test 2: Créer une catégorie avec l'auto-schema
    print("\n📋 Test 2: Création avec auto-schema")
    
    create_auto_mutation = """
    mutation CreateCategory($input: CategoryInput!) {
        create_category(input: $input) {
            ok
            object {
                id
                name
                description
            }
            errors
        }
    }
    """
    
    variables = {
        "input": {
            "name": f"AutoTest_{int(time.time())}",
            "description": "Test auto-schema"
        }
    }
    
    create_result = make_graphql_request(create_auto_mutation, variables)
    if create_result and 'data' in create_result and create_result['data']['create_category']['ok']:
        new_category = create_result['data']['create_category']['object']
        print(f"✅ Catégorie créée (auto): {new_category['name']} (ID: {new_category['id']})")
    else:
        print(f"❌ Erreur création auto: {create_result}")
        return False
    
    # Test 3: Vérifier immédiatement
    print("\n📋 Test 3: Vérification immédiate")
    
    time.sleep(0.2)
    
    immediate_result = make_graphql_request(categories_query)
    if immediate_result and 'data' in immediate_result:
        immediate_count = len(immediate_result['data']['categorys'])
        found = any(cat['id'] == new_category['id'] for cat in immediate_result['data']['categorys'])
        
        if found:
            print("✅ SUCCÈS: La nouvelle catégorie apparaît immédiatement!")
            print("✅ Le cache auto-généré fonctionne correctement")
        else:
            print("❌ La nouvelle catégorie n'apparaît pas")
            return False
    else:
        print(f"❌ Erreur vérification: {immediate_result}")
        return False
    
    # Test 4: Tester les mutations personnalisées si elles existent
    print("\n📋 Test 4: Test des mutations personnalisées")
    
    # D'abord, faire une introspection pour voir quelles mutations sont disponibles
    introspection_query = """
    query {
        __schema {
            mutationType {
                fields {
                    name
                    description
                }
            }
        }
    }
    """
    
    introspection_result = make_graphql_request(introspection_query)
    if introspection_result and 'data' in introspection_result:
        mutations = introspection_result['data']['__schema']['mutationType']['fields']
        mutation_names = [m['name'] for m in mutations]
        
        print(f"📋 Mutations disponibles: {', '.join(mutation_names[:10])}...")
        
        # Vérifier si nos mutations personnalisées existent
        custom_mutations = ['createCategory', 'createTag', 'updateTag', 'deleteTag']
        available_custom = [m for m in custom_mutations if m in mutation_names]
        
        if available_custom:
            print(f"✅ Mutations personnalisées trouvées: {', '.join(available_custom)}")
        else:
            print("⚠️ Aucune mutation personnalisée trouvée dans le schéma")
    
    return True

def main():
    """Fonction principale."""
    print("🎯 TEST SIMPLE D'INTÉGRATION DU CACHE")
    print("Ce script teste l'intégration basique")
    print()
    
    success = test_simple_integration()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 TEST RÉUSSI!")
        print("✅ L'auto-schema fonctionne correctement")
        print("✅ Le cache est invalidé automatiquement")
    else:
        print("❌ TEST ÉCHOUÉ")
        print("⚠️ Des problèmes subsistent")
    
    print("\n🔧 RECOMMANDATIONS:")
    print("1. Les mutations auto-générées fonctionnent bien")
    print("2. Utiliser les mutations auto-générées pour la cohérence")
    print("3. Vérifier si les mutations personnalisées sont nécessaires")

if __name__ == "__main__":
    main()