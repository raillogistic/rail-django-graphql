"""
Test models for GraphQL schema generation testing.
These models represent a simple blog system with various field types and relationships.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MaxLengthValidator, MinValueValidator


class Category(models.Model):
    """Blog post category with basic fields."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def get_post_count(self):
        """Get the number of posts in this category."""
        return self.posts.count()


class Tag(models.Model):
    """Tags for blog posts with minimal fields."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    """
    Blog post model with various field types and relationships.
    Tests different field types, validators, and relationship types.
    """
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    # Basic fields
    title = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(5), MaxLengthValidator(200)]
    )
    slug = models.SlugField(unique=True, max_length=200)
    content = models.TextField()
    excerpt = models.CharField(max_length=500, blank=True)
    
    # Numeric fields
    view_count = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True
    )
    
    # Date fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Boolean and choice fields
    is_featured = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft"
    )
    
    # File fields
    featured_image = models.ImageField(
        upload_to="blog/posts/",
        null=True,
        blank=True
    )
    attachment = models.FileField(
        upload_to="blog/attachments/",
        null=True,
        blank=True
    )
    
    # Relationships
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="posts"
    )
    tags = models.ManyToManyField(Tag, related_name="posts", blank=True)
    related_posts = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="related_to"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Get the absolute URL for the post."""
        return f"/blog/{self.slug}/"

    @property
    def reading_time(self):
        """Estimate reading time in minutes."""
        words_per_minute = 200
        word_count = len(self.content.split())
        return max(1, round(word_count / words_per_minute))


class Comment(models.Model):
    """
    Blog comment model with a recursive relationship.
    Tests recursive relationships and timestamp fields.
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"

    @property
    def reply_count(self):
        """Get the number of replies to this comment."""
        return self.replies.count()
