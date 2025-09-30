#!/usr/bin/env python3
"""
Test complet de l'invalidation du cache pour tous les modèles GraphQL.

Ce script teste l'invalidation du cache universelle pour:
- Category (Catégorie)
- Tag (Étiquette)
- Post (Article)
- Comment (Commentaire)
"""

import os
import sys
import django
import time
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_django():
    """Configure Django pour les tests."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
    django.setup()


def clean_environment():
    """Nettoie l'environnement de test."""
    from django.core.cache import cache
    from test_app.models import Category, Tag, Post, Comment

    logger.info("🧹 Nettoyage de l'environnement de test...")

    # Vider le cache
    cache.clear()

    # Supprimer les données de test existantes
    Comment.objects.filter(content__startswith="Test Comment").delete()
    Post.objects.filter(title__startswith="Test Post").delete()
    Tag.objects.filter(name__startswith="Test Tag").delete()
    Category.objects.filter(name__startswith="Test Category").delete()

    logger.info("✅ Environnement nettoyé")


def create_test_data():
    """Crée des données de test et les met en cache."""
    from django.core.cache import cache
    from test_app.models import Category, Tag, Post, Comment
    from django.contrib.auth.models import User

    logger.info("📝 Création des données de test...")

    # Créer une catégorie de test
    category = Category.objects.create(
        name="Test Category Original", description="Description originale"
    )

    # Créer un tag de test
    tag = Tag.objects.create(name="Test Tag Original", color="#FF0000")

    # Créer un utilisateur pour les posts et commentaires
    user, created = User.objects.get_or_create(
        username="test_user_original",
        defaults={
            "email": "test_original@example.com",
            "first_name": "Test",
            "last_name": "User",
        },
    )

    # Créer un post de test
    post = Post.objects.create(
        title="Test Post Original",
        content="Contenu original du post",
        category=category,
        author=user,
        status="published",
    )
    post.tags.add(tag)

    # Créer un commentaire de test
    comment = Comment.objects.create(
        content="Test Comment Original", post=post, author=user
    )

    # Mettre en cache les données
    cache_keys = [
        "graphql_categories_list",
        "graphql_tags_list",
        "graphql_posts_list",
        "graphql_comments_list",
        f"graphql_category_{category.pk}",
        f"graphql_tag_{tag.pk}",
        f"graphql_post_{post.pk}",
        f"graphql_comment_{comment.pk}",
    ]

    for key in cache_keys:
        cache.set(key, f"cached_data_for_{key}", 300)
        logger.info(f"✅ Clé mise en cache: {key}")

    return category, tag, post, comment


def test_category_cache_invalidation():
    """Teste l'invalidation du cache pour les catégories."""
    from test_app.schema import invalidate_universal_cache
    from test_app.models import Category
    from django.core.cache import cache

    logger.info("🔍 Test d'invalidation du cache pour Category...")

    # Créer une nouvelle catégorie
    new_category = Category.objects.create(
        name="Test Category New", description="Nouvelle description"
    )

    # Invalider le cache
    invalidate_universal_cache(model_instance=new_category)

    # Vérifier que le cache a été vidé
    test_keys = [
        "graphql_categories_list",
        f"graphql_category_{new_category.pk}",
        "graphql_schema_cache",
    ]

    cleared_count = 0
    for key in test_keys:
        if cache.get(key) is None:
            cleared_count += 1
            logger.info(f"✅ Clé invalidée: {key}")
        else:
            logger.warning(f"⚠️ Clé encore en cache: {key}")

    logger.info(f"📊 Category: {cleared_count}/{len(test_keys)} clés invalidées")
    return cleared_count == len(test_keys)


def test_tag_cache_invalidation():
    """Teste l'invalidation du cache pour les tags."""
    from test_app.schema import invalidate_universal_cache
    from test_app.models import Tag
    from django.core.cache import cache

    logger.info("🔍 Test d'invalidation du cache pour Tag...")

    # Créer un nouveau tag
    new_tag = Tag.objects.create(name="Test Tag New", color="#00FF00")

    # Invalider le cache
    invalidate_universal_cache(model_instance=new_tag)

    # Vérifier que le cache a été vidé
    test_keys = [
        "graphql_tags_list",
        f"graphql_tag_{new_tag.pk}",
        "graphql_schema_cache",
    ]

    cleared_count = 0
    for key in test_keys:
        if cache.get(key) is None:
            cleared_count += 1
            logger.info(f"✅ Clé invalidée: {key}")
        else:
            logger.warning(f"⚠️ Clé encore en cache: {key}")

    logger.info(f"📊 Tag: {cleared_count}/{len(test_keys)} clés invalidées")
    return cleared_count == len(test_keys)


def test_post_cache_invalidation():
    """Teste l'invalidation du cache pour les posts."""
    from test_app.schema import invalidate_universal_cache
    from test_app.models import Post, Category
    from django.contrib.auth.models import User
    from django.core.cache import cache

    logger.info("🔍 Test d'invalidation du cache pour Post...")

    # Créer une catégorie pour le post
    category = Category.objects.create(
        name="Test Category for Post", description="Catégorie pour test post"
    )

    # Créer un utilisateur pour le post
    user, created = User.objects.get_or_create(
        username="test_user_post",
        defaults={
            "email": "test_post@example.com",
            "first_name": "Test",
            "last_name": "User",
        },
    )

    # Créer un nouveau post
    new_post = Post.objects.create(
        title="Test Post New",
        content="Nouveau contenu du post",
        category=category,
        author=user,
        status="published",
    )

    # Invalider le cache
    invalidate_universal_cache(model_instance=new_post)

    # Vérifier que le cache a été vidé
    test_keys = [
        "graphql_posts_list",
        f"graphql_post_{new_post.pk}",
        "graphql_schema_cache",
    ]

    cleared_count = 0
    for key in test_keys:
        if cache.get(key) is None:
            cleared_count += 1
            logger.info(f"✅ Clé invalidée: {key}")
        else:
            logger.warning(f"⚠️ Clé encore en cache: {key}")

    logger.info(f"📊 Post: {cleared_count}/{len(test_keys)} clés invalidées")
    return cleared_count == len(test_keys)


def test_comment_cache_invalidation():
    """Teste l'invalidation du cache pour les commentaires."""
    from test_app.schema import invalidate_universal_cache
    from test_app.models import Comment, Post, Category
    from django.contrib.auth.models import User
    from django.core.cache import cache

    logger.info("🔍 Test d'invalidation du cache pour Comment...")

    # Créer les dépendances
    category = Category.objects.create(
        name="Test Category for Comment", description="Catégorie pour test commentaire"
    )

    # Créer un utilisateur pour le post
    user, created = User.objects.get_or_create(
        username="test_user_comment",
        defaults={
            "email": "test_comment@example.com",
            "first_name": "Test",
            "last_name": "User",
        },
    )

    post = Post.objects.create(
        title="Test Post for Comment",
        content="Post pour test commentaire",
        category=category,
        author=user,
        status="published",
    )

    # Créer un utilisateur pour le commentaire
    comment_user, created = User.objects.get_or_create(
        username="test_comment_author",
        defaults={
            "email": "comment_author@example.com",
            "first_name": "Comment",
            "last_name": "Author",
        },
    )

    # Créer un nouveau commentaire
    new_comment = Comment.objects.create(
        content="Test Comment New", post=post, author=comment_user
    )

    # Invalider le cache
    invalidate_universal_cache(model_instance=new_comment)

    # Vérifier que le cache a été vidé
    test_keys = [
        "graphql_comments_list",
        f"graphql_comment_{new_comment.pk}",
        "graphql_schema_cache",
    ]

    cleared_count = 0
    for key in test_keys:
        if cache.get(key) is None:
            cleared_count += 1
            logger.info(f"✅ Clé invalidée: {key}")
        else:
            logger.warning(f"⚠️ Clé encore en cache: {key}")

    logger.info(f"📊 Comment: {cleared_count}/{len(test_keys)} clés invalidées")
    return cleared_count == len(test_keys)


def test_fresh_queries():
    """Teste que les nouvelles requêtes retournent les données fraîches."""
    from test_app.models import Category, Tag, Post, Comment

    logger.info("🔍 Test des requêtes fraîches...")

    # Compter les objets créés pendant les tests
    categories_count = Category.objects.filter(name__startswith="Test Category").count()
    tags_count = Tag.objects.filter(name__startswith="Test Tag").count()
    posts_count = Post.objects.filter(title__startswith="Test Post").count()
    comments_count = Comment.objects.filter(content__startswith="Test Comment").count()

    logger.info(f"📊 Objets trouvés:")
    logger.info(f"   - Categories: {categories_count}")
    logger.info(f"   - Tags: {tags_count}")
    logger.info(f"   - Posts: {posts_count}")
    logger.info(f"   - Comments: {comments_count}")

    # Vérifier qu'on a bien créé des objets
    total_objects = categories_count + tags_count + posts_count + comments_count

    if total_objects > 0:
        logger.info("✅ Les requêtes fraîches retournent les nouvelles données")
        return True
    else:
        logger.error("❌ Aucun objet trouvé dans les requêtes fraîches")
        return False


def main():
    """Fonction principale du test."""
    logger.info("🚀 Début du test complet d'invalidation du cache")

    try:
        # Configuration
        setup_django()
        clean_environment()

        # Créer les données de test initiales
        category, tag, post, comment = create_test_data()

        # Tests d'invalidation pour chaque modèle
        results = {
            "category": test_category_cache_invalidation(),
            "tag": test_tag_cache_invalidation(),
            "post": test_post_cache_invalidation(),
            "comment": test_comment_cache_invalidation(),
        }

        # Test des requêtes fraîches
        fresh_queries_ok = test_fresh_queries()

        # Résultats finaux
        logger.info("📊 RÉSULTATS FINAUX:")
        success_count = 0
        total_tests = len(results) + 1  # +1 pour fresh_queries

        for model, success in results.items():
            status = "✅ SUCCÈS" if success else "❌ ÉCHEC"
            logger.info(f"   - {model.capitalize()}: {status}")
            if success:
                success_count += 1

        fresh_status = "✅ SUCCÈS" if fresh_queries_ok else "❌ ÉCHEC"
        logger.info(f"   - Requêtes fraîches: {fresh_status}")
        if fresh_queries_ok:
            success_count += 1

        # Conclusion
        if success_count == total_tests:
            logger.info(
                "🎉 SUCCÈS COMPLET: L'invalidation du cache fonctionne pour tous les modèles!"
            )
            logger.info(
                "✅ Recommandation: Testez maintenant manuellement dans GraphiQL"
            )
            logger.info("   1. Créez une catégorie, un tag, un post ou un commentaire")
            logger.info(
                "   2. Vérifiez qu'ils apparaissent immédiatement dans les listes"
            )
            logger.info("   3. Modifiez-les et vérifiez les changements")
            logger.info("   4. Supprimez-les et vérifiez qu'ils disparaissent")
        else:
            logger.error(
                f"❌ ÉCHEC PARTIEL: {success_count}/{total_tests} tests réussis"
            )
            logger.error("⚠️ Certains modèles ont encore des problèmes de cache")

        return success_count == total_tests

    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
