#!/usr/bin/env python
"""
Script pour introspecter le schéma GraphQL et découvrir les champs disponibles
"""

import requests
import json

# URL du serveur GraphQL
GRAPHQL_URL = 'http://127.0.0.1:8000/graphql/'

def introspect_schema():
    """Introspection du schéma GraphQL"""
    
    introspection_query = """
    query IntrospectionQuery {
        __schema {
            queryType { name }
            mutationType { name }
            types {
                ...FullType
            }
        }
    }

    fragment FullType on __Type {
        kind
        name
        description
        fields(includeDeprecated: true) {
            name
            description
            args {
                ...InputValue
            }
            type {
                ...TypeRef
            }
            isDeprecated
            deprecationReason
        }
        inputFields {
            ...InputValue
        }
        interfaces {
            ...TypeRef
        }
        enumValues(includeDeprecated: true) {
            name
            description
            isDeprecated
            deprecationReason
        }
        possibleTypes {
            ...TypeRef
        }
    }

    fragment InputValue on __InputValue {
        name
        description
        type { ...TypeRef }
        defaultValue
    }

    fragment TypeRef on __Type {
        kind
        name
        ofType {
            kind
            name
            ofType {
                kind
                name
                ofType {
                    kind
                    name
                    ofType {
                        kind
                        name
                        ofType {
                            kind
                            name
                            ofType {
                                kind
                                name
                                ofType {
                                    kind
                                    name
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """
    
    payload = {
        'query': introspection_query
    }
    
    headers = {
        'Content-Type': 'application/json',
    }
    
    try:
        response = requests.post(GRAPHQL_URL, 
                               data=json.dumps(payload), 
                               headers=headers,
                               timeout=30)
        return response.json()
    except Exception as e:
        print(f"Erreur lors de l'introspection: {e}")
        return None

def analyze_schema(schema_data):
    """Analyse les données du schéma"""
    
    if not schema_data or 'data' not in schema_data:
        print("Pas de données de schéma disponibles")
        return
    
    schema = schema_data['data']['__schema']
    types = schema['types']
    
    print("=== Analyse du schéma GraphQL ===\n")
    
    # Trouver le type Query
    query_type = None
    mutation_type = None
    
    for type_info in types:
        if type_info['name'] == schema['queryType']['name']:
            query_type = type_info
        if schema.get('mutationType') and type_info['name'] == schema['mutationType']['name']:
            mutation_type = type_info
    
    # Analyser les queries
    if query_type and query_type.get('fields'):
        print("=== QUERIES DISPONIBLES ===")
        for field in query_type['fields']:
            field_name = field['name']
            field_type = field['type']
            
            # Extraire le type de retour
            return_type = extract_type_name(field_type)
            
            print(f"  {field_name}: {return_type}")
            if field.get('description'):
                print(f"    Description: {field['description']}")
        print()
    
    # Analyser les mutations
    if mutation_type and mutation_type.get('fields'):
        print("=== MUTATIONS DISPONIBLES ===")
        for field in mutation_type['fields']:
            field_name = field['name']
            field_type = field['type']
            
            # Extraire le type de retour
            return_type = extract_type_name(field_type)
            
            print(f"  {field_name}: {return_type}")
            if field.get('description'):
                print(f"    Description: {field['description']}")
        print()
    
    # Analyser les types spécifiques
    print("=== TYPES SPÉCIFIQUES ===")
    
    # Chercher les types Category, Tag, etc.
    relevant_types = ['CategoryType', 'TagType', 'PostType', 'CommentType', 
                     'CreateCategory', 'CreateTag', 'UpdateTag', 'DeleteTag']
    
    for type_name in relevant_types:
        type_info = next((t for t in types if t['name'] == type_name), None)
        if type_info and type_info.get('fields'):
            print(f"--- {type_name} ---")
            for field in type_info['fields']:
                field_type = extract_type_name(field['type'])
                print(f"  {field['name']}: {field_type}")
            print()

def extract_type_name(type_info):
    """Extrait le nom du type depuis la structure de type GraphQL"""
    if not type_info:
        return "Unknown"
    
    if type_info['kind'] == 'NON_NULL':
        return extract_type_name(type_info['ofType']) + "!"
    elif type_info['kind'] == 'LIST':
        return "[" + extract_type_name(type_info['ofType']) + "]"
    else:
        return type_info.get('name', 'Unknown')

def simple_query_test():
    """Test simple pour découvrir les champs disponibles"""
    
    print("\n=== TEST SIMPLE DES QUERIES ===\n")
    
    # Test des queries simples
    simple_queries = [
        "query { __typename }",
        "query { categorys { __typename } }",
        "query { category { __typename } }",
        "query { tags { __typename } }",
        "query { tag { __typename } }"
    ]
    
    for query in simple_queries:
        print(f"Test: {query}")
        payload = {'query': query}
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(GRAPHQL_URL, 
                                   data=json.dumps(payload), 
                                   headers=headers,
                                   timeout=10)
            result = response.json()
            
            if 'errors' in result:
                print(f"  Erreur: {result['errors'][0]['message']}")
            else:
                print(f"  Succès: {result}")
        except Exception as e:
            print(f"  Exception: {e}")
        print()

if __name__ == '__main__':
    print("Introspection du schéma GraphQL...\n")
    
    # Introspection complète
    schema_data = introspect_schema()
    if schema_data:
        analyze_schema(schema_data)
    
    # Tests simples
    simple_query_test()