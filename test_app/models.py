from re import I
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from rail_django_graphql.decorators import (
    mutation,
    business_logic,
    custom_mutation_name,
)


class Category(models.Model):
    name = models.CharField("Nom de la catégorie", max_length=100)
    description = models.TextField("Description", blank=True)
    is_active = models.BooleanField("Actif", default=True)
    created_at = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

    @property
    def uppercase_name(self) -> str:
        """Retourne le nom de la catégorie en majuscules"""
        return self.name.upper()

    @property
    def post_count(self) -> int:
        """Retourne le nombre de posts dans cette catégorie"""
        return self.post_set.count()

    def __str__(self):
        return self.name

    @mutation(description="Activate category")
    def activate_category(self):
        """Activate this category."""
        self.is_active = True
        self.save()
        return True

    @mutation(description="Deactivate category")
    def deactivate_category(self, reason: str = "Manual deactivation"):
        """Deactivate this category with optional reason."""
        self.is_active = False
        self.save()
        return {"status": "deactivated", "reason": reason}


class Tag(models.Model):
    name = models.CharField("Nom du tag", max_length=50, unique=True)
    color = models.CharField("Couleur", max_length=7, default="#000000")
    created_at = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return self.name

    def update_color(self, new_color: str):
        """Update tag color."""
        self.color = new_color
        self.save()
        return self.color


class Post(models.Model):
    title = models.CharField("Titre", max_length=200)
    content = models.TextField("Contenu")
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, verbose_name="Catégorie"
    )
    tags = models.ManyToManyField("Tag", blank=True, verbose_name="Tags")
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    updated_at = models.DateTimeField("Date de modification", auto_now=True)
    is_published = models.BooleanField("Publié", default=False)

    @property
    def title_with_category(self) -> str:
        """Retourne le titre avec le nom de la catégorie"""
        return f"{self.title} - {self.category.name}"

    @property
    def word_count(self) -> int:
        """Retourne le nombre de mots dans le contenu"""
        return len(self.content.split())

    @property
    def tag_names(self) -> list:
        """Retourne la liste des noms des tags"""
        return [tag.name for tag in self.tags.all()]

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ["-created_at"]

    @business_logic(category="publishing", requires_permission="can_publish_posts")
    def publish_post(self, publish_notes: str = ""):
        """Publish this post."""
        self.status = "published"
        self.published_at = timezone.now()
        self.save()
        return {
            "status": "published",
            "published_at": self.published_at,
            "notes": publish_notes,
        }

    @business_logic(category="workflow")
    def archive_post(self, archive_reason: str = "Manual archival"):
        """Archive this post."""
        self.status = "archived"
        self.save()
        return {"status": "archived", "reason": archive_reason}

    @custom_mutation_name("addTagToPost")
    def add_tag(self, tag_id: int):
        """Add a tag to this post."""
        try:
            tag = Tag.objects.get(id=tag_id)
            self.tags.add(tag)
            return {"success": True, "tag_name": tag.name}
        except Tag.DoesNotExist:
            return {"success": False, "error": "Tag not found"}

    def calculate_reading_time(self):
        """Calculate estimated reading time in minutes."""
        word_count = len(self.content.split())
        reading_time = max(1, word_count // 200)  # Assume 200 words per minute
        return reading_time


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments", verbose_name="Article"
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Auteur")
    content = models.TextField("Contenu")
    is_approved = models.BooleanField("Approuvé", default=False)
    created_at = models.DateTimeField("Créé le", auto_now_add=True)
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="Tags")

    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"

    @business_logic(category="moderation", requires_permission="can_moderate_comments")
    def approve_comment(self, approved_by: str, moderation_notes: str = ""):
        """Approve this comment."""
        self.is_approved = True
        self.save()
        return {
            "status": "approved",
            "approved_by": approved_by,
            "notes": moderation_notes,
            "approved_at": timezone.now(),
        }

    def reject_comment(self, rejection_reason: str):
        """Reject this comment by deleting it."""
        self.delete()
        return {"status": "rejected", "reason": rejection_reason}


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, verbose_name="Utilisateur"
    )
    bio = models.TextField("Biographie", blank=True)
    avatar = models.URLField("Avatar", blank=True)
    website = models.URLField("Site web", blank=True)
    is_verified = models.BooleanField("Vérifié", default=False)
    created_at = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profils"

    def __str__(self):
        return f"Profile of {self.user.username}"

    @business_logic(category="verification", requires_permission="can_verify_profiles")
    def verify_profile(self, verified_by: str, verification_notes: str = ""):
        """Verify this user profile."""
        self.is_verified = True
        self.save()
        return {
            "status": "verified",
            "verified_by": verified_by,
            "notes": verification_notes,
            "verified_at": timezone.now(),
        }

    def update_bio(self, new_bio: str):
        """Update user bio."""
        self.bio = new_bio
        self.save()
        return self.bio


from polymorphic.models import PolymorphicModel


class Client(PolymorphicModel):
    raison = models.CharField("Nom", max_length=255)

    @property
    def uppercase_raison(self) -> str:
        return self.raison.upper()


class LocalClient(Client):
    test = models.CharField("Test", max_length=255)


class ClientInformation(models.Model):
    client = models.OneToOneField(
        Client, on_delete=models.CASCADE, verbose_name="Client", related_name="info"
    )
    adresse = models.CharField("Adresse", max_length=255)
    ville = models.CharField("Ville", max_length=255)
    code_postal = models.CharField("Code postal", max_length=20)
    pays = models.CharField("Pays", max_length=255)
    paysx = models.CharField("Pays", max_length=255)


# Additional models for nested field filtering tests
class Country(models.Model):
    name = models.CharField("Nom du pays", max_length=100)
    code = models.CharField("Code du pays", max_length=3)

    class Meta:
        verbose_name = "Pays"
        verbose_name_plural = "Pays"

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField("Nom de la marque", max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, verbose_name="Pays")
    founded_year = models.IntegerField("Année de fondation")

    class Meta:
        verbose_name = "Marque"
        verbose_name_plural = "Marques"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField("Nom du produit", max_length=200)
    price = models.DecimalField("Prix", max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, verbose_name="Catégorie"
    )
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, verbose_name="Marque")
    is_active = models.BooleanField("Actif", default=True)

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"

    def __str__(self):
        return self.name
