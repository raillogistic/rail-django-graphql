# Inheritance Support

This document explains how the Django GraphQL Auto-Generation Library handles Django model inheritance, including abstract base classes, multi-table inheritance, and proxy models.

## 📚 Table of Contents

- [Overview](#overview)
- [Abstract Base Classes](#abstract-base-classes)
- [Multi-Table Inheritance](#multi-table-inheritance)
- [Proxy Models](#proxy-models)
- [Polymorphic Queries](#polymorphic-queries)
- [Union Types](#union-types)
- [Interface Implementation](#interface-implementation)
- [Configuration](#configuration)
- [Examples](#examples)

## 🔍 Overview

The inheritance system provides:

- **Abstract base class support** with shared fields and methods
- **Multi-table inheritance** with proper relationship handling
- **Proxy model support** with specialized behavior
- **Polymorphic queries** for querying across inheritance hierarchies
- **Union types** for returning different model types
- **Interface implementation** for shared GraphQL contracts

## 🎯 Abstract Base Classes

### Basic Abstract Model

```python
# Django Models
class BaseContent(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def get_absolute_url(self):
        """Returns the absolute URL for this content."""
        return f"/{self.slug}/"

    @property
    def is_recent(self) -> bool:
        """Check if content was created recently."""
        from datetime import timedelta
        return self.created_at > timezone.now() - timedelta(days=7)

class Article(BaseContent):
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=100)

    def get_word_count(self) -> int:
        """Returns word count of the article."""
        return len(self.content.split())

class Video(BaseContent):
    video_file = models.FileField(upload_to='videos/')
    duration = models.DurationField()
    thumbnail = models.ImageField(upload_to='thumbnails/')

    def get_duration_minutes(self) -> float:
        """Returns duration in minutes."""
        return self.duration.total_seconds() / 60

class Podcast(BaseContent):
    audio_file = models.FileField(upload_to='podcasts/')
    duration = models.DurationField()
    episode_number = models.PositiveIntegerField()

    def get_episode_info(self) -> dict:
        """Returns episode information."""
        return {
            'episode': self.episode_number,
            'duration_minutes': self.duration.total_seconds() / 60,
            'file_size': self.audio_file.size if self.audio_file else 0
        }
```

### Generated GraphQL Schema

The library automatically generates shared interfaces and individual types:

```graphql
# Shared interface for all content types
interface ContentInterface {
  id: ID!
  title: String!
  slug: String!
  createdAt: DateTime!
  updatedAt: DateTime!
  isPublished: Boolean!
  absoluteUrl: String! # From get_absolute_url method
  isRecent: Boolean! # From is_recent property
}

# Individual types implementing the interface
type Article implements ContentInterface {
  id: ID!
  title: String!
  slug: String!
  createdAt: DateTime!
  updatedAt: DateTime!
  isPublished: Boolean!
  absoluteUrl: String!
  isRecent: Boolean!

  # Article-specific fields
  content: String!
  author: User!
  category: String!
  wordCount: Int! # From get_word_count method
}

type Video implements ContentInterface {
  id: ID!
  title: String!
  slug: String!
  createdAt: DateTime!
  updatedAt: DateTime!
  isPublished: Boolean!
  absoluteUrl: String!
  isRecent: Boolean!

  # Video-specific fields
  videoFile: String!
  duration: Duration!
  thumbnail: String!
  durationMinutes: Float! # From get_duration_minutes method
}

type Podcast implements ContentInterface {
  id: ID!
  title: String!
  slug: String!
  createdAt: DateTime!
  updatedAt: DateTime!
  isPublished: Boolean!
  absoluteUrl: String!
  isRecent: Boolean!

  # Podcast-specific fields
  audioFile: String!
  duration: Duration!
  episodeNumber: Int!
  episodeInfo: JSON! # From get_episode_info method
}

# Union type for polymorphic queries
union Content = Article | Video | Podcast

# Queries
type Query {
  # Individual type queries
  articles: [Article!]!
  videos: [Video!]!
  podcasts: [Podcast!]!

  # Polymorphic queries
  allContent: [Content!]!
  publishedContent: [Content!]!
  recentContent: [Content!]!
}
```

## 🏗️ Multi-Table Inheritance

### Parent-Child Relationships

```python
# Django Models
class Place(models.Model):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=80)

    def get_coordinates(self) -> dict:
        """Returns GPS coordinates."""
        # Simulate geocoding
        return {'lat': 40.7128, 'lng': -74.0060}

class Restaurant(Place):
    serves_hot_dogs = models.BooleanField(default=False)
    serves_pizza = models.BooleanField(default=False)
    cuisine_type = models.CharField(max_length=50)

    def get_menu_info(self) -> dict:
        """Returns menu information."""
        return {
            'has_hot_dogs': self.serves_hot_dogs,
            'has_pizza': self.serves_pizza,
            'cuisine': self.cuisine_type,
            'specialties': self.get_specialties()
        }

    def get_specialties(self) -> list:
        """Returns list of specialties."""
        specialties = []
        if self.serves_hot_dogs:
            specialties.append('Hot Dogs')
        if self.serves_pizza:
            specialties.append('Pizza')
        return specialties

class Hotel(Place):
    star_rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    room_count = models.PositiveIntegerField()
    has_pool = models.BooleanField(default=False)

    def get_amenities(self) -> list:
        """Returns list of amenities."""
        amenities = ['WiFi', 'Parking']
        if self.has_pool:
            amenities.append('Swimming Pool')
        if self.star_rating >= 4:
            amenities.extend(['Concierge', 'Room Service'])
        return amenities

    @property
    def is_luxury(self) -> bool:
        """Check if hotel is luxury class."""
        return self.star_rating >= 4
```

### Generated Schema with Inheritance

```graphql
# Base interface
interface PlaceInterface {
  id: ID!
  name: String!
  address: String!
  coordinates: JSON! # From get_coordinates method
}

# Child types
type Restaurant implements PlaceInterface {
  id: ID!
  name: String!
  address: String!
  coordinates: JSON!

  # Restaurant-specific fields
  servesHotDogs: Boolean!
  servesPizza: Boolean!
  cuisineType: String!
  menuInfo: JSON! # From get_menu_info method
  specialties: [String!]! # From get_specialties method
  # Parent relationship
  place: Place!
}

type Hotel implements PlaceInterface {
  id: ID!
  name: String!
  address: String!
  coordinates: JSON!

  # Hotel-specific fields
  starRating: Int!
  roomCount: Int!
  hasPool: Boolean!
  amenities: [String!]! # From get_amenities method
  isLuxury: Boolean! # From is_luxury property
  # Parent relationship
  place: Place!
}

# Union for polymorphic queries
union PlaceType = Restaurant | Hotel

# Queries
type Query {
  places: [PlaceInterface!]!
  restaurants: [Restaurant!]!
  hotels: [Hotel!]!

  # Polymorphic queries
  allPlaces: [PlaceType!]!
  luxuryPlaces: [PlaceType!]!
}
```

## 👥 Proxy Models

### Specialized Behavior Models

```python
# Django Models
class Person(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    birth_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def get_full_name(self) -> str:
        """Returns full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self) -> int:
        """Calculate age from birth date."""
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

class Employee(Person):
    """Proxy model for employees with specialized methods."""

    class Meta:
        proxy = True

    def get_employee_info(self) -> dict:
        """Returns employee-specific information."""
        return {
            'employee_id': self.id,
            'full_name': self.get_full_name(),
            'email': self.email,
            'is_active': self.is_active,
            'age': self.age
        }

    def get_work_email(self) -> str:
        """Generate work email address."""
        return f"{self.first_name.lower()}.{self.last_name.lower()}@company.com"

    @property
    def is_senior(self) -> bool:
        """Check if employee is senior (age >= 40)."""
        return self.age >= 40

class Customer(Person):
    """Proxy model for customers with specialized methods."""

    class Meta:
        proxy = True

    def get_customer_info(self) -> dict:
        """Returns customer-specific information."""
        return {
            'customer_id': self.id,
            'full_name': self.get_full_name(),
            'contact_email': self.email,
            'age_group': self.get_age_group()
        }

    def get_age_group(self) -> str:
        """Returns age group category."""
        if self.age < 25:
            return 'Young Adult'
        elif self.age < 40:
            return 'Adult'
        elif self.age < 60:
            return 'Middle Age'
        else:
            return 'Senior'

    @property
    def marketing_segment(self) -> str:
        """Determine marketing segment."""
        age_group = self.get_age_group()
        return f"{age_group}_Customer"
```

### Generated Schema for Proxy Models

```graphql
# Base type (shared by all proxy models)
type Person {
  id: ID!
  firstName: String!
  lastName: String!
  email: String!
  birthDate: Date!
  isActive: Boolean!
  fullName: String! # From get_full_name method
  age: Int! # From age property
}

# Proxy model types with specialized methods
type Employee {
  id: ID!
  firstName: String!
  lastName: String!
  email: String!
  birthDate: Date!
  isActive: Boolean!
  fullName: String!
  age: Int!

  # Employee-specific methods
  employeeInfo: JSON! # From get_employee_info method
  workEmail: String! # From get_work_email method
  isSenior: Boolean! # From is_senior property
}

type Customer {
  id: ID!
  firstName: String!
  lastName: String!
  email: String!
  birthDate: Date!
  isActive: Boolean!
  fullName: String!
  age: Int!

  # Customer-specific methods
  customerInfo: JSON! # From get_customer_info method
  ageGroup: String! # From get_age_group method
  marketingSegment: String! # From marketing_segment property
}

# Queries
type Query {
  people: [Person!]!
  employees: [Employee!]!
  customers: [Customer!]!

  # Filtered queries
  activeEmployees: [Employee!]!
  seniorEmployees: [Employee!]!
  customersByAgeGroup(ageGroup: String!): [Customer!]!
}
```

## 🔄 Polymorphic Queries

### Advanced Query Patterns

```python
from rail_django_graphql.generators.queries import PolymorphicQueryGenerator

class PolymorphicQueryGenerator:
    """Generates polymorphic queries for inheritance hierarchies."""

    def generate_polymorphic_queries(self, base_model, child_models):
        """Generate queries that can return multiple model types."""

        # Union type for all child models
        union_name = f"{base_model.__name__}Union"
        union_type = type(union_name, (graphene.Union,), {
            'Meta': type('Meta', (), {
                'types': tuple(child_models)
            })
        })

        # Polymorphic query fields
        queries = {
            # All instances across all child models
            f'all_{base_model.__name__.lower()}s': graphene.List(
                union_type,
                description=f"Get all {base_model.__name__} instances"
            ),

            # Filtered polymorphic queries
            f'published_{base_model.__name__.lower()}s': graphene.List(
                union_type,
                description=f"Get published {base_model.__name__} instances"
            ),

            # Search across all types
            f'search_{base_model.__name__.lower()}s': graphene.List(
                union_type,
                query=graphene.String(required=True),
                description=f"Search {base_model.__name__} instances"
            ),
        }

        return queries
```

### Example Polymorphic Queries

```graphql
# Query all content types
query {
  allContent {
    __typename
    ... on Article {
      id
      title
      content
      author {
        username
      }
      wordCount
    }
    ... on Video {
      id
      title
      videoFile
      duration
      durationMinutes
    }
    ... on Podcast {
      id
      title
      episodeNumber
      episodeInfo
    }
  }
}

# Search across all content types
query {
  searchContent(query: "technology") {
    __typename
    ... on ContentInterface {
      id
      title
      slug
      isPublished
      isRecent
    }
    ... on Article {
      category
      wordCount
    }
    ... on Video {
      durationMinutes
    }
    ... on Podcast {
      episodeNumber
    }
  }
}

# Filter by shared interface fields
query {
  publishedContent {
    __typename
    ... on ContentInterface {
      title
      createdAt
      absoluteUrl
    }
  }
}
```

## 🔗 Union Types

### Custom Union Definitions

```python
from rail_django_graphql.generators.unions import UnionGenerator

class MediaUnion(graphene.Union):
    """Union type for different media types."""

    class Meta:
        types = (Article, Video, Podcast)

    @classmethod
    def resolve_type(cls, instance, info):
        """Resolve the actual type of the instance."""
        if isinstance(instance, Article):
            return Article
        elif isinstance(instance, Video):
            return Video
        elif isinstance(instance, Podcast):
            return Podcast
        return None

class PlaceUnion(graphene.Union):
    """Union type for different place types."""

    class Meta:
        types = (Restaurant, Hotel)

    @classmethod
    def resolve_type(cls, instance, info):
        """Resolve the actual type of the instance."""
        if hasattr(instance, 'serves_hot_dogs'):
            return Restaurant
        elif hasattr(instance, 'star_rating'):
            return Hotel
        return None

# Usage in queries
class Query(graphene.ObjectType):
    mixed_media = graphene.List(MediaUnion)
    nearby_places = graphene.List(PlaceUnion, lat=graphene.Float(), lng=graphene.Float())

    def resolve_mixed_media(self, info):
        """Return mixed media content."""
        from itertools import chain
        return list(chain(
            Article.objects.filter(is_published=True)[:5],
            Video.objects.filter(is_published=True)[:5],
            Podcast.objects.filter(is_published=True)[:5],
        ))

    def resolve_nearby_places(self, info, lat=None, lng=None):
        """Return nearby places of different types."""
        # Simulate location-based filtering
        restaurants = Restaurant.objects.all()[:10]
        hotels = Hotel.objects.all()[:10]
        return list(chain(restaurants, hotels))
```

## 🎭 Interface Implementation

### Shared GraphQL Interfaces

```python
from rail_django_graphql.generators.interfaces import InterfaceGenerator

class ContentInterface(graphene.Interface):
    """Shared interface for all content types."""

    id = graphene.ID(required=True)
    title = graphene.String(required=True)
    slug = graphene.String(required=True)
    created_at = graphene.DateTime(required=True)
    updated_at = graphene.DateTime(required=True)
    is_published = graphene.Boolean(required=True)
    absolute_url = graphene.String(required=True)
    is_recent = graphene.Boolean(required=True)

    @classmethod
    def resolve_type(cls, instance, info):
        """Resolve the concrete type implementing this interface."""
        if isinstance(instance, Article):
            return ArticleType
        elif isinstance(instance, Video):
            return VideoType
        elif isinstance(instance, Podcast):
            return PodcastType
        return None

class TimestampedInterface(graphene.Interface):
    """Interface for models with timestamp fields."""

    created_at = graphene.DateTime(required=True)
    updated_at = graphene.DateTime(required=True)

    def resolve_created_at(self, info):
        return self.created_at

    def resolve_updated_at(self, info):
        return self.updated_at

class PublishableInterface(graphene.Interface):
    """Interface for publishable content."""

    is_published = graphene.Boolean(required=True)
    published_at = graphene.DateTime()

    def resolve_is_published(self, info):
        return self.is_published

    def resolve_published_at(self, info):
        return getattr(self, 'published_at', None)
```

## ⚙️ Configuration

### Inheritance Settings

```python
# settings.py
rail_django_graphql = {
    'INHERITANCE': {
        # Enable inheritance support
        'ENABLE_INHERITANCE': True,

        # Generate interfaces for abstract models
        'GENERATE_INTERFACES': True,

        # Generate union types for polymorphic queries
        'GENERATE_UNIONS': True,

        # Include parent fields in child types
        'INCLUDE_PARENT_FIELDS': True,

        # Generate polymorphic queries
        'GENERATE_POLYMORPHIC_QUERIES': True,

        # Interface naming convention
        'INTERFACE_SUFFIX': 'Interface',

        # Union naming convention
        'UNION_SUFFIX': 'Union',

        # Proxy model handling
        'HANDLE_PROXY_MODELS': True,
        'PROXY_MODEL_SUFFIX': '',
    },

    'POLYMORPHIC_QUERIES': {
        # Query naming patterns
        'ALL_QUERY_PREFIX': 'all_',
        'SEARCH_QUERY_PREFIX': 'search_',
        'FILTER_QUERY_PREFIX': 'filter_',

        # Enable specific query types
        'ENABLE_ALL_QUERIES': True,
        'ENABLE_SEARCH_QUERIES': True,
        'ENABLE_FILTER_QUERIES': True,
    }
}
```

### Per-Model Configuration

```python
# models.py
class BaseContent(models.Model):
    title = models.CharField(max_length=200)

    class Meta:
        abstract = True

    class GraphQLMeta:
        # Generate interface for this abstract model
        generate_interface = True
        interface_name = 'ContentInterface'

        # Include these fields in the interface
        interface_fields = ['title', 'slug', 'is_published']

        # Exclude these fields from child types
        exclude_from_children = []

class Article(BaseContent):
    content = models.TextField()

    class GraphQLMeta:
        # Implement the parent interface
        implements_interfaces = ['ContentInterface']

        # Include in union types
        include_in_unions = ['ContentUnion', 'MediaUnion']

        # Custom type name
        type_name = 'ArticleType'
```

## 📊 Usage Examples

### Complex Inheritance Query

```graphql
query ComplexInheritanceQuery {
  # Query all content with shared fields
  allContent {
    __typename
    ... on ContentInterface {
      id
      title
      slug
      isPublished
      createdAt
      isRecent
    }

    # Type-specific fields
    ... on Article {
      content
      author {
        username
        email
      }
      category
      wordCount
    }

    ... on Video {
      videoFile
      duration
      thumbnail
      durationMinutes
    }

    ... on Podcast {
      audioFile
      episodeNumber
      episodeInfo
    }
  }

  # Query specific types
  articles(first: 5, isPublished: true) {
    edges {
      node {
        title
        content
        wordCount
        author {
          fullName
        }
      }
    }
  }

  # Polymorphic search
  searchContent(query: "technology") {
    __typename
    ... on ContentInterface {
      title
      absoluteUrl
    }
  }
}
```

### Multi-Table Inheritance Query

```graphql
query PlacesQuery {
  # All places with shared interface
  places {
    __typename
    ... on PlaceInterface {
      id
      name
      address
      coordinates
    }
  }

  # Specific place types
  restaurants {
    name
    address
    cuisineType
    menuInfo
    specialties

    # Access parent fields
    place {
      coordinates
    }
  }

  hotels {
    name
    starRating
    roomCount
    amenities
    isLuxury

    # Access parent fields
    place {
      coordinates
    }
  }

  # Union query
  allPlaces {
    __typename
    ... on Restaurant {
      cuisineType
      specialties
    }
    ... on Hotel {
      starRating
      isLuxury
    }
  }
}
```

### Proxy Model Query

```graphql
query ProxyModelQuery {
  # Base model
  people {
    id
    fullName
    age
    email
  }

  # Proxy models with specialized methods
  employees {
    fullName
    workEmail
    isSenior
    employeeInfo
  }

  customers {
    fullName
    ageGroup
    marketingSegment
    customerInfo
  }

  # Filtered proxy queries
  seniorEmployees {
    fullName
    employeeInfo
  }

  customersByAgeGroup(ageGroup: "Adult") {
    fullName
    marketingSegment
  }
}
```

## 🚀 Next Steps

Now that you understand inheritance support:

1. [Learn About Nested Operations](nested-operations.md) - Complex nested create/update operations
2. [Explore Performance Optimization](../development/performance.md) - Optimization techniques
3. [Check Testing Guide](../development/testing.md) - Testing inheritance patterns
4. [Review Advanced Examples](../examples/advanced-examples.md) - Complex inheritance scenarios

## 🤝 Need Help?

- Check the [Troubleshooting Guide](../development/troubleshooting.md)
- Review [API Reference](../api/core-classes.md)
- Join our [Community Discussions](https://github.com/your-repo/django-graphql-auto/discussions)
