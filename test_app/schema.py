import graphene
from graphene_django import DjangoObjectType
from .models import Category, Tag, Post, Comment

# Define GraphQL types for our models
class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = "__all__"

class TagType(DjangoObjectType):
    class Meta:
        model = Tag
        fields = "__all__"

class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = "__all__"

class CommentType(DjangoObjectType):
    class Meta:
        model = Comment
        fields = "__all__"

# Define Query class
class Query(graphene.ObjectType):
    # Single object queries
    category = graphene.Field(CategoryType, id=graphene.ID())
    tag = graphene.Field(TagType, id=graphene.ID())
    post = graphene.Field(PostType, id=graphene.ID())
    comment = graphene.Field(CommentType, id=graphene.ID())
    
    # List queries
    categories = graphene.List(CategoryType)
    tags = graphene.List(TagType)
    posts = graphene.List(PostType)
    comments = graphene.List(CommentType)
    
    def resolve_category(self, info, id):
        try:
            return Category.objects.get(pk=id)
        except Category.DoesNotExist:
            return None
    
    def resolve_tag(self, info, id):
        try:
            return Tag.objects.get(pk=id)
        except Tag.DoesNotExist:
            return None
    
    def resolve_post(self, info, id):
        try:
            return Post.objects.get(pk=id)
        except Post.DoesNotExist:
            return None
    
    def resolve_comment(self, info, id):
        try:
            return Comment.objects.get(pk=id)
        except Comment.DoesNotExist:
            return None
    
    def resolve_categories(self, info):
        return Category.objects.all()
    
    def resolve_tags(self, info):
        return Tag.objects.all()
    
    def resolve_posts(self, info):
        return Post.objects.all()
    
    def resolve_comments(self, info):
        return Comment.objects.all()

# Define input types for mutations
class CategoryInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    description = graphene.String()

class TagInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    color = graphene.String()

class PostInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    content = graphene.String(required=True)
    category_id = graphene.ID()
    tag_ids = graphene.List(graphene.ID)
    status = graphene.String()

class CommentInput(graphene.InputObjectType):
    content = graphene.String(required=True)
    post_id = graphene.ID(required=True)
    author_name = graphene.String(required=True)
    author_email = graphene.String(required=True)

# Define mutations
class CreateCategory(graphene.Mutation):
    class Arguments:
        input = CategoryInput(required=True)
    
    category = graphene.Field(CategoryType)
    
    def mutate(self, info, input):
        category = Category.objects.create(**input)
        return CreateCategory(category=category)

class CreateTag(graphene.Mutation):
    class Arguments:
        input = TagInput(required=True)
    
    tag = graphene.Field(TagType)
    
    def mutate(self, info, input):
        tag = Tag.objects.create(**input)
        return CreateTag(tag=tag)

class CreatePost(graphene.Mutation):
    class Arguments:
        input = PostInput(required=True)
    
    post = graphene.Field(PostType)
    
    def mutate(self, info, input):
        tag_ids = input.pop('tag_ids', [])
        post = Post.objects.create(**input)
        if tag_ids:
            post.tags.set(tag_ids)
        return CreatePost(post=post)

class CreateComment(graphene.Mutation):
    class Arguments:
        input = CommentInput(required=True)
    
    comment = graphene.Field(CommentType)
    
    def mutate(self, info, input):
        comment = Comment.objects.create(**input)
        return CreateComment(comment=comment)

# Define Mutation class
class Mutation(graphene.ObjectType):
    create_category = CreateCategory.Field()
    create_tag = CreateTag.Field()
    create_post = CreatePost.Field()
    create_comment = CreateComment.Field()

# Create schema
test_app_schema = graphene.Schema(query=Query, mutation=Mutation)