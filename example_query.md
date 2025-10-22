# GraphQL Metadata Query Examples

This document provides comprehensive examples of GraphQL queries for retrieving model metadata and form metadata from the Django GraphQL schema.

## Table of Contents
1. [Model Form Metadata Query](#model-form-metadata-query)
2. [Model Metadata Query](#model-metadata-query)
3. [Sample Results](#sample-results)

---

## Model Form Metadata Query

The `model_form_metadata` query provides comprehensive form-specific metadata for Django models, including field configurations, relationships, validation rules, and UI settings.

### Complete Query with All Fields

```graphql
query GetModelFormMetadata($appName: String!, $modelName: String!, $nestedFields: [String]) {
  modelFormMetadata(
    appName: $appName
    modelName: $modelName
    nestedFields: $nestedFields
  ) {
    # Basic model information
    appName
    modelName
    verboseName
    verboseNamePlural
    formTitle
    formDescription
    
    # Form fields
    fields {
      name
      fieldType
      isRequired
      verboseName
      helpText
      widgetType
      placeholder
      defaultValue
      choices {
        value
        label
      }
      maxLength
      minLength
      decimalPlaces
      maxDigits
      minValue
      maxValue
      autoNow
      autoNowAdd
      blank
      null
      unique
      editable
      validators
      errorMessages
      disabled
      readonly
      cssClasses
      dataAttributes
      hasPermission
    }
    
    # Relationship fields
    relationships {
      name
      relationshipType
      verboseName
      helpText
      widgetType
      isRequired
      relatedModel
      relatedApp
      toField
      fromField
      manyToMany
      oneToOne
      foreignKey
      isReverse
      multiple
      querysetFilters
      emptyLabel
      limitChoicesTo
      disabled
      readonly
      cssClasses
      dataAttributes
      hasPermission
    }
    
    # Nested form metadata
    nested {
      appName
      modelName
      verboseName
      verboseNamePlural
      formTitle
      formDescription
      fields {
        name
        fieldType
        isRequired
        verboseName
        helpText
        widgetType
      }
      relationships {
        name
        relationshipType
        verboseName
        relatedModel
        relatedApp
      }
    }
    
    # Form configuration
    fieldOrder
    excludeFields
    readonlyFields
    requiredPermissions
    formValidationRules
    formLayout
    cssClasses
    formAttributes
  }
}
```

### Query Variables Example

```json
{
  "appName": "myapp",
  "modelName": "User",
  "nestedFields": ["profile", "department"]
}
```

---

## Model Metadata Query

The `model_metadata` query provides comprehensive structural metadata for Django models, including database schema information, relationships, permissions, and filtering options.

### Complete Query with All Fields

```graphql
query GetModelMetadata(
  $appName: String!
  $modelName: String!
  $nestedFields: Boolean
  $permissionsIncluded: Boolean
  $maxDepth: Int
) {
  modelMetadata(
    appName: $appName
    modelName: $modelName
    nestedFields: $nestedFields
    permissionsIncluded: $permissionsIncluded
    maxDepth: $maxDepth
  ) {
    # Basic model information
    appName
    modelName
    verboseName
    verboseNamePlural
    tableName
    primaryKeyField
    
    # Model configuration
    abstract
    proxy
    managed
    ordering
    uniqueTogether
    
    # Fields metadata
    fields {
      name
      fieldType
      isRequired
      isNullable
      null
      defaultValue
      helpText
      maxLength
      choices {
        value
        label
      }
      isPrimaryKey
      isForeignKey
      isUnique
      isIndexed
      hasAutoNow
      hasAutoNowAdd
      blank
      editable
      verboseName
      hasPermission
    }
    
    # Relationships metadata
    relationships {
      name
      relationshipType
      relatedModel {
        appName
        modelName
        verboseName
        verboseNamePlural
        tableName
        primaryKeyField
        abstract
        proxy
        managed
        ordering
        uniqueTogether
        fields {
          name
          fieldType
          isRequired
          verboseName
          isPrimaryKey
          isForeignKey
          isUnique
        }
      }
      relatedApp
      toField
      fromField
      isReverse
      isRequired
      manyToMany
      oneToOne
      foreignKey
      onDelete
      relatedName
      hasPermission
      verboseName
    }
    
    # Permissions and security
    permissions
    
    # Database indexes
    indexes
    
    # Filtering capabilities
    filters {
      fieldName
      isNested
      relatedModel
      isCustom
      options {
        name
        lookupExpr
        helpText
        filterType
      }
    }
    
    # Available mutations
    mutations {
      name
      description
      inputFields {
        name
        fieldType
        required
        defaultValue
        description
        choices
        validationRules
        widgetType
        placeholder
        helpText
        minLength
        maxLength
        minValue
        maxValue
        pattern
        relatedModel
        multiple
      }
      returnType
      requiresAuthentication
      requiredPermissions
      mutationType
      modelName
      formConfig
      validationSchema
      successMessage
      errorMessages
    }
  }
}
```

### Query Variables Example

```json
{
  "appName": "myapp",
  "modelName": "User",
  "nestedFields": true,
  "permissionsIncluded": true,
  "maxDepth": 2
}
```

---

## Sample Results

### Model Form Metadata Sample Result

```json
{
  "data": {
    "modelFormMetadata": {
      "appName": "myapp",
      "modelName": "User",
      "verboseName": "User",
      "verboseNamePlural": "Users",
      "formTitle": "Form for User",
      "formDescription": "Create or edit user",
      "fields": [
        {
          "name": "username",
          "fieldType": "CharField",
          "isRequired": true,
          "verboseName": "Username",
          "helpText": "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
          "widgetType": "TextInput",
          "placeholder": "Enter username",
          "defaultValue": null,
          "choices": null,
          "maxLength": 150,
          "minLength": 1,
          "decimalPlaces": null,
          "maxDigits": null,
          "minValue": null,
          "maxValue": null,
          "autoNow": false,
          "autoNowAdd": false,
          "blank": false,
          "null": false,
          "unique": true,
          "editable": true,
          "validators": ["validate_username"],
          "errorMessages": {
            "unique": "A user with that username already exists."
          },
          "disabled": false,
          "readonly": false,
          "cssClasses": "form-control",
          "dataAttributes": {
            "validation": "username"
          },
          "hasPermission": true
        },
        {
          "name": "email",
          "fieldType": "EmailField",
          "isRequired": true,
          "verboseName": "Email address",
          "helpText": "Enter a valid email address",
          "widgetType": "EmailInput",
          "placeholder": "user@example.com",
          "defaultValue": null,
          "choices": null,
          "maxLength": 254,
          "minLength": null,
          "decimalPlaces": null,
          "maxDigits": null,
          "minValue": null,
          "maxValue": null,
          "autoNow": false,
          "autoNowAdd": false,
          "blank": false,
          "null": false,
          "unique": true,
          "editable": true,
          "validators": ["validate_email"],
          "errorMessages": {
            "invalid": "Enter a valid email address.",
            "unique": "A user with that email already exists."
          },
          "disabled": false,
          "readonly": false,
          "cssClasses": "form-control",
          "dataAttributes": {
            "validation": "email"
          },
          "hasPermission": true
        }
      ],
      "relationships": [
        {
          "name": "profile",
          "relationshipType": "OneToOneField",
          "verboseName": "Profile",
          "helpText": "User profile information",
          "widgetType": "Select",
          "isRequired": false,
          "relatedModel": "UserProfile",
          "relatedApp": "myapp",
          "toField": "id",
          "fromField": "profile_id",
          "manyToMany": false,
          "oneToOne": true,
          "foreignKey": false,
          "isReverse": false,
          "multiple": false,
          "querysetFilters": null,
          "emptyLabel": "Select profile",
          "limitChoicesTo": null,
          "disabled": false,
          "readonly": false,
          "cssClasses": "form-select",
          "dataAttributes": null,
          "hasPermission": true
        },
        {
          "name": "groups",
          "relationshipType": "ManyToManyField",
          "verboseName": "Groups",
          "helpText": "The groups this user belongs to",
          "widgetType": "CheckboxSelectMultiple",
          "isRequired": false,
          "relatedModel": "Group",
          "relatedApp": "auth",
          "toField": null,
          "fromField": "",
          "manyToMany": true,
          "oneToOne": false,
          "foreignKey": false,
          "isReverse": false,
          "multiple": true,
          "querysetFilters": null,
          "emptyLabel": null,
          "limitChoicesTo": null,
          "disabled": false,
          "readonly": false,
          "cssClasses": "form-check-input",
          "dataAttributes": null,
          "hasPermission": true
        }
      ],
      "nested": [
        {
          "appName": "myapp",
          "modelName": "UserProfile",
          "verboseName": "User Profile",
          "verboseNamePlural": "User Profiles",
          "formTitle": "Form for User Profile",
          "formDescription": "Create or edit user profile",
          "fields": [
            {
              "name": "bio",
              "fieldType": "TextField",
              "isRequired": false,
              "verboseName": "Biography",
              "helpText": "Tell us about yourself",
              "widgetType": "Textarea"
            }
          ],
          "relationships": []
        }
      ],
      "fieldOrder": ["username", "email", "first_name", "last_name"],
      "excludeFields": ["id", "password", "last_login", "date_joined"],
      "readonlyFields": ["id", "date_joined", "last_login"],
      "requiredPermissions": ["myapp.add_user", "myapp.change_user"],
      "formValidationRules": {
        "username": {
          "required": true,
          "minLength": 1,
          "maxLength": 150,
          "pattern": "^[\\w.@+-]+$"
        },
        "email": {
          "required": true,
          "type": "email"
        }
      },
      "formLayout": {
        "sections": [
          {
            "title": "Basic Information",
            "fields": ["username", "email", "first_name", "last_name"]
          },
          {
            "title": "Permissions",
            "fields": ["groups", "user_permissions"]
          }
        ]
      },
      "cssClasses": "user-form",
      "formAttributes": {
        "enctype": "multipart/form-data",
        "method": "POST"
      }
    }
  }
}
```

### Model Metadata Sample Result

```json
{
  "data": {
    "modelMetadata": {
      "appName": "myapp",
      "modelName": "User",
      "verboseName": "User",
      "verboseNamePlural": "Users",
      "tableName": "myapp_user",
      "primaryKeyField": "id",
      "abstract": false,
      "proxy": false,
      "managed": true,
      "ordering": ["username"],
      "uniqueTogether": [],
      "fields": [
        {
          "name": "id",
          "fieldType": "AutoField",
          "isRequired": true,
          "isNullable": false,
          "null": false,
          "defaultValue": null,
          "helpText": "",
          "maxLength": null,
          "choices": null,
          "isPrimaryKey": true,
          "isForeignKey": false,
          "isUnique": true,
          "isIndexed": true,
          "hasAutoNow": false,
          "hasAutoNowAdd": false,
          "blank": false,
          "editable": false,
          "verboseName": "ID",
          "hasPermission": true
        },
        {
          "name": "username",
          "fieldType": "CharField",
          "isRequired": true,
          "isNullable": false,
          "null": false,
          "defaultValue": null,
          "helpText": "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
          "maxLength": 150,
          "choices": null,
          "isPrimaryKey": false,
          "isForeignKey": false,
          "isUnique": true,
          "isIndexed": true,
          "hasAutoNow": false,
          "hasAutoNowAdd": false,
          "blank": false,
          "editable": true,
          "verboseName": "Username",
          "hasPermission": true
        }
      ],
      "relationships": [
        {
          "name": "profile",
          "relationshipType": "OneToOneField",
          "relatedModel": {
            "appName": "myapp",
            "modelName": "UserProfile",
            "verboseName": "User Profile",
            "verboseNamePlural": "User Profiles",
            "tableName": "myapp_userprofile",
            "primaryKeyField": "id",
            "abstract": false,
            "proxy": false,
            "managed": true,
            "ordering": [],
            "uniqueTogether": [],
            "fields": [
              {
                "name": "id",
                "fieldType": "AutoField",
                "isRequired": true,
                "verboseName": "ID",
                "isPrimaryKey": true,
                "isForeignKey": false,
                "isUnique": true
              }
            ]
          },
          "relatedApp": "myapp",
          "toField": "id",
          "fromField": "profile_id",
          "isReverse": false,
          "isRequired": false,
          "manyToMany": false,
          "oneToOne": true,
          "foreignKey": false,
          "onDelete": "CASCADE",
          "relatedName": "user",
          "hasPermission": true,
          "verboseName": "Profile"
        }
      ],
      "permissions": [
        "myapp.add_user",
        "myapp.change_user",
        "myapp.delete_user",
        "myapp.view_user"
      ],
      "indexes": [
        {
          "fields": ["username"],
          "name": "myapp_user_username_idx",
          "unique": true
        }
      ],
      "filters": [
        {
          "fieldName": "username",
          "isNested": false,
          "relatedModel": null,
          "isCustom": false,
          "options": [
            {
              "name": "username",
              "lookupExpr": "exact",
              "helpText": "Nom d'utilisateur exact",
              "filterType": "CharFilter"
            },
            {
              "name": "username__icontains",
              "lookupExpr": "icontains",
              "helpText": "Nom d'utilisateur contient (insensible à la casse)",
              "filterType": "CharFilter"
            }
          ]
        }
      ],
      "mutations": [
        {
          "name": "createUser",
          "description": "Create a new user",
          "inputFields": [
            {
              "name": "username",
              "fieldType": "String",
              "required": true,
              "defaultValue": null,
              "description": "Username for the user",
              "choices": null,
              "validationRules": {
                "maxLength": 150,
                "pattern": "^[\\w.@+-]+$"
              },
              "widgetType": "TextInput",
              "placeholder": "Enter username",
              "helpText": "Required. 150 characters or fewer.",
              "minLength": 1,
              "maxLength": 150,
              "minValue": null,
              "maxValue": null,
              "pattern": "^[\\w.@+-]+$",
              "relatedModel": null,
              "multiple": false
            }
          ],
          "returnType": "User",
          "requiresAuthentication": true,
          "requiredPermissions": ["myapp.add_user"],
          "mutationType": "create",
          "modelName": "User",
          "formConfig": {
            "layout": "vertical",
            "submitText": "Create User"
          },
          "validationSchema": {
            "username": {
              "required": true,
              "type": "string",
              "maxLength": 150
            }
          },
          "successMessage": "User created successfully",
          "errorMessages": {
            "username": {
              "required": "Username is required",
              "unique": "Username already exists"
            }
          }
        }
      ]
    }
  }
}
```

---

## Usage Notes

### Key Differences Between Queries

1. **Model Form Metadata**: Focuses on form rendering, validation, and UI components
   - Field widgets and form controls
   - Validation rules and error messages
   - Form layout and styling
   - User permissions for form fields

2. **Model Metadata**: Focuses on database structure and business logic
   - Database schema information
   - Relationship definitions
   - Available mutations and operations
   - Filtering and querying capabilities

### Best Practices

1. **Use nested fields sparingly** to avoid deep recursion and performance issues
2. **Cache results** when possible, as metadata extraction can be expensive
3. **Filter permissions** based on user context for security
4. **Limit max_depth** in model_metadata queries to prevent excessive nesting

### Common Use Cases

- **Frontend Form Generation**: Use `model_form_metadata` to dynamically create forms
- **API Documentation**: Use `model_metadata` to generate API documentation
- **Admin Interfaces**: Combine both queries for comprehensive admin panels
- **Data Validation**: Use field metadata for client-side validation rules