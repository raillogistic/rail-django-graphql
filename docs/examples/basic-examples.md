# Basic Examples

This document provides practical examples of using the Django GraphQL Auto-Generation Library in common scenarios. These examples build upon the [Basic Usage Guide](../usage/basic-usage.md) with real-world use cases.

## 📚 Table of Contents

- [Blog System Example](#blog-system-example)
- [E-commerce Example](#e-commerce-example)
- [User Management Example](#user-management-example)
- [File Upload Example](#file-upload-example)
- [Frontend Integration Examples](#frontend-integration-examples)

## 📝 Blog System Example

### Models

```python
# blog/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "categories"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#007bff')
    
    def __str__(self):
        return self.name

class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    content = models.TextField()
    excerpt = models.TextField(max_length=300, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='posts')
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    featured_image = models.ImageField(upload_to='posts/', blank=True, null=True)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='replies')
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f'Comment by {self.author.username} on {self.post.title}'
```

### GraphQL Queries

#### Get All Published Posts

```graphql
query GetPublishedPosts {
  posts(filters: { status: "published" }, orderBy: "-published_at") {
    id
    title
    slug
    excerpt
    author {
      id
      username
      firstName
      lastName
    }
    category {
      id
      name
      slug
    }
    tags {
      id
      name
      color
    }
    featuredImage
    viewCount
    publishedAt
    createdAt
  }
}
```

#### Get Single Post with Comments

```graphql
query GetPostDetail($slug: String!) {
  posts(filters: { slug: $slug, status: "published" }) {
    id
    title
    slug
    content
    excerpt
    author {
      id
      username
      firstName
      lastName
    }
    category {
      id
      name
      slug
    }
    tags {
      id
      name
      color
    }
    featuredImage
    viewCount
    publishedAt
    comments(filters: { isApproved: true, parent_Isnull: true }) {
      id
      content
      author {
        username
      }
      createdAt
      replies(filters: { isApproved: true }) {
        id
        content
        author {
          username
        }
        createdAt
      }
    }
  }
}
```

#### Get Posts by Category

```graphql
query GetPostsByCategory($categorySlug: String!, $first: Int = 10) {
  postPages(
    first: $first
    filters: { 
      category_Slug: $categorySlug
      status: "published" 
    }
    orderBy: "-published_at"
  ) {
    edges {
      node {
        id
        title
        slug
        excerpt
        author {
          username
        }
        tags {
          name
          color
        }
        publishedAt
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
  }
}
```

### GraphQL Mutations

#### Create a New Post

```graphql
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ok
    post {
      id
      title
      slug
      status
      author {
        username
      }
      category {
        name
      }
      tags {
        name
      }
    }
    errors
  }
}

# Variables:
{
  "input": {
    "title": "Getting Started with Django GraphQL",
    "content": "In this post, we'll explore how to build GraphQL APIs with Django...",
    "excerpt": "Learn the basics of Django GraphQL integration",
    "categoryId": 1,
    "tagIds": [1, 2, 3],
    "status": "draft"
  }
}
```

#### Publish a Post

```graphql
mutation PublishPost($id: ID!) {
  updatePost(id: $id, input: { 
    status: "published"
    publishedAt: "2024-01-15T10:00:00Z"
  }) {
    ok
    post {
      id
      title
      status
      publishedAt
    }
    errors
  }
}
```

#### Add Comment to Post

```graphql
mutation AddComment($input: CreateCommentInput!) {
  createComment(input: $input) {
    ok
    comment {
      id
      content
      author {
        username
      }
      post {
        title
      }
      createdAt
    }
    errors
  }
}

# Variables:
{
  "input": {
    "postId": 1,
    "content": "Great post! Very informative.",
    "isApproved": false
  }
}
```

## 🛒 E-commerce Example

### Models

```python
# shop/models.py
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='children')
    image = models.ImageField(upload_to='categories/', blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    sku = models.CharField(max_length=50, unique=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    @property
    def is_on_sale(self):
        return self.compare_price and self.compare_price > self.price
    
    @property
    def discount_percentage(self):
        if self.is_on_sale:
            return int(((self.compare_price - self.price) / self.compare_price) * 100)
        return 0

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Image for {self.product.name}"

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def total_amount(self):
        return sum(item.total_price for item in self.items.all())
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['cart', 'product']
    
    @property
    def total_price(self):
        return self.product.price * self.quantity
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order {self.order_number}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order
    
    @property
    def total_price(self):
        return self.price * self.quantity
```

### GraphQL Queries

#### Get Products with Filtering

```graphql
query GetProducts(
  $categorySlug: String
  $minPrice: Float
  $maxPrice: Float
  $search: String
  $first: Int = 12
) {
  productPages(
    first: $first
    filters: {
      isActive: true
      AND: [
        { category_Slug: $categorySlug }
        { price_Gte: $minPrice }
        { price_Lte: $maxPrice }
        {
          OR: [
            { name_Icontains: $search }
            { description_Icontains: $search }
          ]
        }
      ]
    }
    orderBy: "-created_at"
  ) {
    edges {
      node {
        id
        name
        slug
        price
        comparePrice
        isOnSale
        discountPercentage
        category {
          name
          slug
        }
        images(filters: { isPrimary: true }) {
          image
          altText
        }
        stockQuantity
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
  }
}
```

#### Get Product Detail

```graphql
query GetProductDetail($slug: String!) {
  products(filters: { slug: $slug, isActive: true }) {
    id
    name
    slug
    description
    price
    comparePrice
    isOnSale
    discountPercentage
    sku
    stockQuantity
    category {
      id
      name
      slug
      parent {
        name
        slug
      }
    }
    images {
      id
      image
      altText
      isPrimary
    }
  }
}
```

#### Get User's Cart

```graphql
query GetCart {
  carts(filters: { user: $userId }) {
    id
    totalAmount
    totalItems
    items {
      id
      quantity
      totalPrice
      product {
        id
        name
        slug
        price
        images(filters: { isPrimary: true }) {
          image
          altText
        }
        stockQuantity
      }
      addedAt
    }
    updatedAt
  }
}
```

### GraphQL Mutations

#### Add Product to Cart

```graphql
mutation AddToCart($input: CreateCartItemInput!) {
  createCartItem(input: $input) {
    ok
    cartItem {
      id
      quantity
      totalPrice
      product {
        name
        price
      }
      cart {
        totalAmount
        totalItems
      }
    }
    errors
  }
}

# Variables:
{
  "input": {
    "cartId": 1,
    "productId": 5,
    "quantity": 2
  }
}
```

#### Update Cart Item Quantity

```graphql
mutation UpdateCartItem($id: ID!, $quantity: Int!) {
  updateCartItem(id: $id, input: { quantity: $quantity }) {
    ok
    cartItem {
      id
      quantity
      totalPrice
      cart {
        totalAmount
        totalItems
      }
    }
    errors
  }
}
```

#### Create Order from Cart

```graphql
mutation CreateOrder($input: CreateOrderInput!) {
  createOrder(input: $input) {
    ok
    order {
      id
      orderNumber
      status
      totalAmount
      items {
        product {
          name
        }
        quantity
        price
        totalPrice
      }
      createdAt
    }
    errors
  }
}

# Variables:
{
  "input": {
    "shippingAddress": "123 Main St, City, State 12345",
    "totalAmount": "99.99"
  }
}
```

## 👥 User Management Example

### Extended User Profile

```python
# accounts/models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    birth_date = models.DateField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"

class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['follower', 'following']
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"
```

### GraphQL Queries

#### Get User Profile

```graphql
query GetUserProfile($username: String!) {
  users(filters: { username: $username }) {
    id
    username
    firstName
    lastName
    email
    dateJoined
    profile {
      bio
      avatar
      birthDate
      phoneNumber
      website
      location
      isVerified
    }
    posts {
      id
      title
      slug
      createdAt
    }
    followers {
      follower {
        username
        profile {
          avatar
        }
      }
    }
    following {
      following {
        username
        profile {
          avatar
        }
      }
    }
  }
}
```

### GraphQL Mutations

#### Update User Profile

```graphql
mutation UpdateProfile($input: UpdateUserProfileInput!) {
  updateUserProfile(input: $input) {
    ok
    userProfile {
      bio
      avatar
      website
      location
      updatedAt
      user {
        username
        firstName
        lastName
      }
    }
    errors
  }
}

# Variables:
{
  "input": {
    "bio": "Full-stack developer passionate about GraphQL and Django",
    "website": "https://johndoe.dev",
    "location": "San Francisco, CA"
  }
}
```

#### Follow/Unfollow User

```graphql
mutation FollowUser($userId: ID!) {
  createFollow(input: { followingId: $userId }) {
    ok
    follow {
      follower {
        username
      }
      following {
        username
      }
      createdAt
    }
    errors
  }
}

mutation UnfollowUser($followId: ID!) {
  deleteFollow(id: $followId) {
    ok
    follow {
      follower {
        username
      }
      following {
        username
      }
    }
    errors
  }
}
```

## 📁 File Upload Example

### GraphQL Mutation for File Upload

```graphql
mutation UploadFile($file: Upload!) {
  uploadFile(file: $file) {
    ok
    file {
      id
      name
      url
      size
      contentType
      uploadedAt
    }
    errors
  }
}
```

### Frontend Implementation (JavaScript)

```javascript
// Using Apollo Client
import { useMutation } from '@apollo/client';
import { UPLOAD_FILE } from './mutations';

function FileUploadComponent() {
  const [uploadFile, { loading, error }] = useMutation(UPLOAD_FILE);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      const { data } = await uploadFile({
        variables: { file }
      });

      if (data.uploadFile.ok) {
        console.log('File uploaded:', data.uploadFile.file);
      } else {
        console.error('Upload errors:', data.uploadFile.errors);
      }
    } catch (err) {
      console.error('Upload failed:', err);
    }
  };

  return (
    <div>
      <input
        type="file"
        onChange={handleFileUpload}
        disabled={loading}
      />
      {loading && <p>Uploading...</p>}
      {error && <p>Error: {error.message}</p>}
    </div>
  );
}
```

## 🌐 Frontend Integration Examples

### React with Apollo Client

```javascript
// apollo-client.js
import { ApolloClient, InMemoryCache, createHttpLink } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';

const httpLink = createHttpLink({
  uri: 'http://localhost:8000/graphql/',
});

const authLink = setContext((_, { headers }) => {
  const token = localStorage.getItem('token');
  return {
    headers: {
      ...headers,
      authorization: token ? `Bearer ${token}` : "",
    }
  }
});

const client = new ApolloClient({
  link: authLink.concat(httpLink),
  cache: new InMemoryCache()
});

export default client;
```

```javascript
// PostList.js
import React from 'react';
import { useQuery } from '@apollo/client';
import { GET_POSTS } from './queries';

function PostList() {
  const { loading, error, data, fetchMore } = useQuery(GET_POSTS, {
    variables: { first: 10 }
  });

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;

  const loadMore = () => {
    fetchMore({
      variables: {
        first: 10,
        after: data.postPages.pageInfo.endCursor
      },
      updateQuery: (prev, { fetchMoreResult }) => {
        if (!fetchMoreResult) return prev;
        return {
          postPages: {
            ...fetchMoreResult.postPages,
            edges: [...prev.postPages.edges, ...fetchMoreResult.postPages.edges]
          }
        };
      }
    });
  };

  return (
    <div>
      {data.postPages.edges.map(({ node: post }) => (
        <article key={post.id}>
          <h2>{post.title}</h2>
          <p>{post.excerpt}</p>
          <small>By {post.author.username} in {post.category.name}</small>
        </article>
      ))}
      
      {data.postPages.pageInfo.hasNextPage && (
        <button onClick={loadMore}>Load More</button>
      )}
    </div>
  );
}

export default PostList;
```

### Vue.js with Apollo

```javascript
// main.js
import { createApp } from 'vue';
import { ApolloClient, InMemoryCache } from '@apollo/client/core';
import { DefaultApolloClient } from '@vue/apollo-composable';
import App from './App.vue';

const apolloClient = new ApolloClient({
  uri: 'http://localhost:8000/graphql/',
  cache: new InMemoryCache()
});

const app = createApp(App);
app.provide(DefaultApolloClient, apolloClient);
app.mount('#app');
```

```vue
<!-- PostList.vue -->
<template>
  <div>
    <div v-if="loading">Loading...</div>
    <div v-else-if="error">Error: {{ error.message }}</div>
    <div v-else>
      <article v-for="post in posts" :key="post.id">
        <h2>{{ post.title }}</h2>
        <p>{{ post.excerpt }}</p>
        <small>By {{ post.author.username }}</small>
      </article>
    </div>
  </div>
</template>

<script>
import { useQuery } from '@vue/apollo-composable';
import { GET_POSTS } from './queries';

export default {
  name: 'PostList',
  setup() {
    const { result, loading, error } = useQuery(GET_POSTS);
    
    const posts = computed(() => 
      result.value?.postPages?.edges?.map(edge => edge.node) || []
    );

    return {
      posts,
      loading,
      error
    };
  }
};
</script>
```

## 🚀 Next Steps

These examples demonstrate the power and flexibility of the Django GraphQL Auto-Generation Library. To continue learning:

1. [Explore Advanced Features](../advanced/custom-scalars.md) - Custom scalars and complex types
2. [Check Advanced Examples](advanced-examples.md) - More complex scenarios
3. [Review API Reference](../api/core-classes.md) - Detailed API documentation
4. [Learn About Security](../features/security.md) - Authentication and permissions

## 🤝 Need Help?

- Check the [Troubleshooting Guide](../development/troubleshooting.md)
- Review [Common Patterns](../development/patterns.md)
- Join our [Community](https://github.com/your-repo/django-graphql-auto/discussions)