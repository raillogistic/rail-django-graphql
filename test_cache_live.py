#!/usr/bin/env python
"""
Test du cache GraphQL en utilisant le serveur en cours d'exécution
"""

import requests
import json
import time

# URL du serveur GraphQL
GRAPHQL_URL = 'http://127.0.0.1:8000/graphql/'

def make_graphql_request(query, variables=None):
    """Effectue une requête GraphQL"""
    payload = {
        'query': query,
        'variables': variables or {}
    }
    
    headers = {
        'Content-Type': 'application/json',
    }
    
    try:
        response = requests.post(GRAPHQL_URL, 
                               data=json.dumps(payload), 
                               headers=headers,
                               timeout=10)
        return response.json()
    except Exception as e:
        print(f"Erreur lors de la requête: {e}")
        return None

def test_cache_behavior():
    """Test le comportement du cache avec des requêtes GraphQL réelles"""
    
    print("=== Test du comportement du cache GraphQL (Serveur Live) ===\n")
    
    # 1. Requête initiale pour les catégories
    query_categories = """
    query {
        categories {
            id
            name
            description
        }
    }
    """
    
    print("1. Requête initiale des catégories...")
    result1 = make_graphql_request(query_categories)
    
    if result1:
        categories_initial = result1.get('data', {}).get('categories', [])
        print(f"   Résultat: {len(categories_initial)} catégories trouvées")
        print(f"   Données: {categories_initial}")
        
        if 'errors' in result1:
            print(f"   Erreurs: {result1['errors']}")
    else:
        print("   Échec de la requête")
        return
    
    # 2. Créer une nouvelle catégorie via mutation
    create_mutation = """
    mutation CreateCategory($input: CategoryInput!) {
        createCategory(input: $input) {
            category {
                id
                name
                description
            }
        }
    }
    """
    
    variables = {
        "input": {
            "name": f"Test Category {int(time.time())}",
            "description": "Test Description for cache testing"
        }
    }
    
    print("\n2. Création d'une nouvelle catégorie...")
    result2 = make_graphql_request(create_mutation, variables)
    
    if result2:
        print(f"   Résultat: {result2}")
        if 'errors' in result2:
            print(f"   Erreurs: {result2['errors']}")
            return
        
        created_category = result2.get('data', {}).get('createCategory', {}).get('category')
        if created_category:
            print(f"   Catégorie créée: {created_category['name']} (ID: {created_category['id']})")
        else:
            print("   Échec de la création")
            return
    else:
        print("   Échec de la requête")
        return
    
    # 3. Requête immédiate après création (test cache invalidation)
    print("\n3. Requête immédiate après création...")
    result3 = make_graphql_request(query_categories)
    
    if result3:
        categories_after = result3.get('data', {}).get('categories', [])
        print(f"   Résultat: {len(categories_after)} catégories trouvées")
        
        # Vérifier si la nouvelle catégorie apparaît
        new_category_name = created_category['name']
        new_category_found = any(cat['name'] == new_category_name for cat in categories_after)
        print(f"   Nouvelle catégorie '{new_category_name}' trouvée: {new_category_found}")
        
        if new_category_found:
            print("   ✅ Cache invalidé correctement!")
        else:
            print("   ❌ Cache non invalidé - problème détecté!")
            print(f"   Catégories actuelles: {[cat['name'] for cat in categories_after]}")
    else:
        print("   Échec de la requête")
    
    # 4. Attendre et tester à nouveau
    print("\n4. Attente de 3 secondes et nouvelle requête...")
    time.sleep(3)
    
    result4 = make_graphql_request(query_categories)
    
    if result4:
        categories_delayed = result4.get('data', {}).get('categories', [])
        print(f"   Résultat: {len(categories_delayed)} catégories trouvées")
        
        # Vérifier à nouveau
        new_category_found_delayed = any(cat['name'] == new_category_name for cat in categories_delayed)
        print(f"   Nouvelle catégorie trouvée après délai: {new_category_found_delayed}")
        
        if new_category_found_delayed:
            print("   ✅ Données persistantes correctement!")
        else:
            print("   ❌ Problème de persistance des données!")
    
    # 5. Test avec les tags
    print("\n5. Test avec les tags...")
    
    query_tags = """
    query {
        tags {
            id
            name
            color
        }
    }
    """
    
    result_tags = make_graphql_request(query_tags)
    if result_tags:
        tags_initial = result_tags.get('data', {}).get('tags', [])
        print(f"   Tags initiaux: {len(tags_initial)} trouvés")
        
        # Créer un nouveau tag
        create_tag_mutation = """
        mutation CreateTag($input: TagInput!) {
            createTag(input: $input) {
                tag {
                    id
                    name
                    color
                }
            }
        }
        """
        
        tag_variables = {
            "input": {
                "name": f"Test Tag {int(time.time())}",
                "color": "#FF0000"
            }
        }
        
        result_create_tag = make_graphql_request(create_tag_mutation, tag_variables)
        if result_create_tag and not result_create_tag.get('errors'):
            created_tag = result_create_tag.get('data', {}).get('createTag', {}).get('tag')
            print(f"   Tag créé: {created_tag['name']}")
            
            # Vérifier immédiatement
            result_tags_after = make_graphql_request(query_tags)
            if result_tags_after:
                tags_after = result_tags_after.get('data', {}).get('tags', [])
                tag_found = any(tag['name'] == created_tag['name'] for tag in tags_after)
                print(f"   Nouveau tag trouvé immédiatement: {tag_found}")
                
                if tag_found:
                    print("   ✅ Cache des tags invalidé correctement!")
                else:
                    print("   ❌ Cache des tags non invalidé!")
    
    print("\n=== Fin du test ===")

if __name__ == '__main__':
    test_cache_behavior()