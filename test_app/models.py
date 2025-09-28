from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django_graphql_auto.decorators import mutation, business_logic, custom_mutation_name


class Category(models.Model):
    name = models.CharField("Nom de la catégorie", max_length=100)
    description = models.TextField("Description", blank=True)
    is_active = models.BooleanField("Actif", default=True)
    created_at = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

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
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('published', 'Publié'),
        ('archived', 'Archivé'),
    ]

    title = models.CharField("Titre", max_length=200)
    content = models.TextField("Contenu")
    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default='draft')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Auteur")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Catégorie")
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="Tags")
    created_at = models.DateTimeField("Créé le", auto_now_add=True)
    updated_at = models.DateTimeField("Modifié le", auto_now=True)
    published_at = models.DateTimeField("Publié le", null=True, blank=True)

    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"

    def __str__(self):
        return self.title

    @business_logic(category="publishing", requires_permission="can_publish_posts")
    def publish_post(self, publish_notes: str = ""):
        """Publish this post."""
        self.status = 'published'
        self.published_at = timezone.now()
        self.save()
        return {"status": "published", "published_at": self.published_at, "notes": publish_notes}

    @business_logic(category="workflow")
    def archive_post(self, archive_reason: str = "Manual archival"):
        """Archive this post."""
        self.status = 'archived'
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
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name="Article")
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
            "approved_at": timezone.now()
        }

    def reject_comment(self, rejection_reason: str):
        """Reject this comment by deleting it."""
        self.delete()
        return {"status": "rejected", "reason": rejection_reason}


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
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
            "verified_at": timezone.now()
        }

    def update_bio(self, new_bio: str):
        """Update user bio."""
        self.bio = new_bio
        self.save()
        return self.bio


class Client(models.Model):
    raison = models.CharField("Nom", max_length=255)
    
    @mutation
    def ppppp(self):
        return self.raison

class ClientInformation(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE, verbose_name="Client",related_name="info")
    adresse = models.CharField("Adresse", max_length=255)
    ville = models.CharField("Ville", max_length=255)
    code_postal = models.CharField("Code postal", max_length=20)
    pays = models.CharField("Pays", max_length=255)
    paysx = models.CharField("Pays", max_length=255)
    