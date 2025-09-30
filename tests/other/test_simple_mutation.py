#!/usr/bin/env python
"""
Test simple pour vérifier les noms de mutations GraphQL
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from rail_django_graphql.schema import schema


def test_mutation_names():
    """Test simple des noms de mutations."""
    print("🔍 Test des noms de mutations GraphQL")
    print("=" * 50)

    # Vérifier le type Mutation
    mutation_type = schema.mutation
    if not mutation_type:
        print("❌ Aucun type Mutation trouvé")
        return False

    # Obtenir les champs de mutation
    mutation_fields = mutation_type._meta.fields
    print(f"📋 Nombre de mutations: {len(mutation_fields)}")

    # Chercher les mutations Category et Tag
    category_mutations = [
        name for name in mutation_fields.keys() if "category" in name.lower()
    ]
    tag_mutations = [name for name in mutation_fields.keys() if "tag" in name.lower()]

    print(f"\n🏷️ Mutations Category trouvées: {category_mutations}")
    print(f"🏷️ Mutations Tag trouvées: {tag_mutations}")

    # Vérifier la convention snake_case
    expected_category = ["create_category", "update_category", "delete_category"]
    expected_tag = ["create_tag", "update_tag", "delete_tag"]

    category_ok = all(name in category_mutations for name in expected_category)
    tag_ok = all(name in tag_mutations for name in expected_tag)

    print(f"\n✅ Mutations Category (snake_case): {'✓' if category_ok else '✗'}")
    print(f"✅ Mutations Tag (snake_case): {'✓' if tag_ok else '✗'}")

    return category_ok and tag_ok


if __name__ == "__main__":
    success = test_mutation_names()
    print(f"\n🎯 Résultat final: {'✅ SUCCÈS' if success else '❌ ÉCHEC'}")
    sys.exit(0 if success else 1)
