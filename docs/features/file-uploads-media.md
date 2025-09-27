# 📁 File Uploads & Media Management

Comprehensive file upload and media management system with advanced security, processing, and storage capabilities.

## 🌟 Overview

The File Uploads & Media Management system provides a complete solution for handling file uploads in GraphQL applications with:

- **Secure File Uploads** - Multi-layered validation and virus scanning
- **Media Processing** - Automatic image processing and thumbnail generation
- **Flexible Storage** - Support for local, cloud, and CDN storage backends
- **Performance Optimization** - Efficient file handling and caching
- **Comprehensive Security** - Virus scanning, quarantine, and threat detection

## 🚀 Key Features

### 1. File Upload System
- **Multiple Upload Methods**: Single file, multiple files, and batch uploads
- **Format Support**: Images, documents, videos, and custom file types
- **Size Management**: Configurable file size limits and validation
- **Progress Tracking**: Real-time upload progress and status monitoring

### 2. Security & Validation
- **Virus Scanning**: ClamAV integration with real-time threat detection
- **File Validation**: MIME type, extension, and content validation
- **Quarantine System**: Automatic isolation of suspicious files
- **Access Control**: Permission-based file access and sharing

### 3. Media Processing
- **Image Processing**: Automatic resizing, format conversion, and optimization
- **Thumbnail Generation**: Multiple thumbnail sizes and formats
- **Metadata Extraction**: EXIF data and file information extraction
- **Format Conversion**: Support for various image and document formats

### 4. Storage Backends
- **Local Storage**: File system-based storage with configurable paths
- **Cloud Storage**: AWS S3, Google Cloud Storage, Azure Blob Storage
- **CDN Integration**: CloudFront, CloudFlare, and custom CDN support
- **Hybrid Storage**: Multi-tier storage with automatic migration

## 📋 Configuration

### Basic Configuration
```python
# settings.py
GRAPHQL_FILE_UPLOADS = {
    'ENABLE_FILE_UPLOADS': True,
    'MAX_FILE_SIZE': 10 * 1024 * 1024,  # 10MB
    'ALLOWED_EXTENSIONS': ['.jpg', '.png', '.pdf', '.txt'],
    'UPLOAD_PATH': 'uploads/',
    'ENABLE_VIRUS_SCANNING': True,
}
```

### Advanced Configuration
```python
GRAPHQL_FILE_UPLOADS = {
    # Basic Settings
    'ENABLE_FILE_UPLOADS': True,
    'MAX_FILE_SIZE': 50 * 1024 * 1024,  # 50MB
    'MAX_FILES_PER_REQUEST': 10,
    'UPLOAD_PATH': 'uploads/',
    
    # File Validation
    'ALLOWED_EXTENSIONS': [
        '.jpg', '.jpeg', '.png', '.gif', '.webp',
        '.pdf', '.doc', '.docx', '.txt', '.csv'
    ],
    'ALLOWED_MIME_TYPES': [
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf', 'text/plain', 'text/csv'
    ],
    'VALIDATE_FILE_CONTENT': True,
    
    # Security Settings
    'ENABLE_VIRUS_SCANNING': True,
    'VIRUS_SCANNER_TYPE': 'clamav',
    'VIRUS_SCAN_TIMEOUT': 30,
    'QUARANTINE_PATH': '/var/quarantine/',
    'SCAN_RESULT_RETENTION_DAYS': 30,
    
    # Media Processing
    'ENABLE_IMAGE_PROCESSING': True,
    'THUMBNAIL_SIZES': [(150, 150), (300, 300), (600, 600)],
    'IMAGE_QUALITY': 85,
    'AUTO_OPTIMIZE_IMAGES': True,
    
    # Storage Backend
    'STORAGE_BACKEND': 'local',  # 'local', 's3', 'gcs', 'azure'
    'STORAGE_SETTINGS': {
        'local': {
            'BASE_PATH': '/var/uploads/',
            'BASE_URL': '/media/',
        },
        's3': {
            'BUCKET_NAME': 'my-uploads-bucket',
            'REGION': 'us-east-1',
            'ACCESS_KEY_ID': 'your-access-key',
            'SECRET_ACCESS_KEY': 'your-secret-key',
        }
    },
    
    # Performance
    'ENABLE_CACHING': True,
    'CACHE_TIMEOUT': 3600,
    'ENABLE_CDN': False,
    'CDN_BASE_URL': 'https://cdn.example.com/',
}
```

## 🔧 GraphQL Operations

### File Upload Mutations

#### Single File Upload
```graphql
mutation UploadSingleFile {
  uploadFile(input: {
    file: "base64EncodedContent"
    filename: "document.pdf"
    mimeType: "application/pdf"
  }) {
    ok
    file {
      id
      filename
      size
      mimeType
      url
      uploadedAt
      scanResult {
        status
        scanTime
      }
    }
    errors
  }
}
```

#### Multiple File Upload
```graphql
mutation UploadMultipleFiles {
  uploadFiles(input: {
    files: [
      {
        file: "base64EncodedContent1"
        filename: "image1.jpg"
        mimeType: "image/jpeg"
      },
      {
        file: "base64EncodedContent2"
        filename: "document.pdf"
        mimeType: "application/pdf"
      }
    ]
  }) {
    ok
    files {
      id
      filename
      size
      url
      thumbnails {
        size
        url
      }
    }
    errors
  }
}
```

### File Management Queries

#### Get File Information
```graphql
query GetFileInfo($fileId: ID!) {
  file(id: $fileId) {
    id
    filename
    size
    mimeType
    url
    uploadedAt
    scanResult {
      status
      threats
      scanTime
      scannerVersion
    }
    thumbnails {
      size
      url
      width
      height
    }
    metadata {
      width
      height
      exifData
      duration
    }
  }
}
```

#### List Files with Filtering
```graphql
query ListFiles($filters: FileFilterInput) {
  files(filters: $filters) {
    edges {
      node {
        id
        filename
        size
        mimeType
        url
        uploadedAt
        scanResult {
          status
        }
      }
    }
    pageInfo {
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
    }
  }
}
```

### Media Processing Operations

#### Generate Thumbnails
```graphql
mutation GenerateThumbnails {
  generateThumbnails(input: {
    fileId: "file-id"
    sizes: [
      { width: 150, height: 150 },
      { width: 300, height: 300 }
    ]
  }) {
    ok
    thumbnails {
      size
      url
      width
      height
    }
    errors
  }
}
```

#### Process Image
```graphql
mutation ProcessImage {
  processImage(input: {
    fileId: "file-id"
    operations: [
      { type: RESIZE, width: 800, height: 600 },
      { type: OPTIMIZE, quality: 85 },
      { type: CONVERT, format: WEBP }
    ]
  }) {
    ok
    processedFile {
      id
      url
      size
      format
    }
    errors
  }
}
```

## 🛡️ Security Features

### Virus Scanning
- **Real-time Scanning**: All uploaded files are scanned immediately
- **ClamAV Integration**: Industry-standard antivirus engine
- **Threat Detection**: Comprehensive malware and virus detection
- **Quarantine System**: Automatic isolation of infected files

### File Validation
- **Content Validation**: Deep file content analysis beyond extensions
- **MIME Type Checking**: Whitelist-based MIME type validation
- **Size Limits**: Configurable maximum file size restrictions
- **Extension Filtering**: Allowed file extension validation

### Access Control
- **Permission-based Access**: Integration with GraphQL permissions
- **User-based Isolation**: Files isolated by user/tenant
- **Secure URLs**: Time-limited and signed URLs for file access
- **Audit Logging**: Comprehensive file access and modification logs

## 🎯 Performance Optimization

### Caching Strategy
- **File Metadata Caching**: Cache file information for faster access
- **Thumbnail Caching**: Cache generated thumbnails
- **CDN Integration**: Serve files through CDN for global performance
- **Smart Cache Invalidation**: Automatic cache updates on file changes

### Storage Optimization
- **Compression**: Automatic file compression for supported formats
- **Deduplication**: Prevent duplicate file storage
- **Tiered Storage**: Move old files to cheaper storage tiers
- **Cleanup Jobs**: Automatic cleanup of temporary and orphaned files

### Upload Optimization
- **Chunked Uploads**: Support for large file uploads in chunks
- **Resume Capability**: Resume interrupted uploads
- **Parallel Processing**: Process multiple files simultaneously
- **Background Jobs**: Move heavy processing to background tasks

## 📊 Monitoring & Analytics

### File Upload Statistics
```graphql
query FileUploadStats {
  fileUploadStats {
    totalFiles
    totalSize
    uploadsByType {
      mimeType
      count
      totalSize
    }
    uploadsByDate {
      date
      count
      totalSize
    }
    scanResults {
      clean
      infected
      suspicious
      errors
    }
  }
}
```

### Storage Usage
```graphql
query StorageUsage {
  storageUsage {
    totalUsed
    totalAvailable
    usageByType {
      type
      size
      percentage
    }
    usageByUser {
      userId
      username
      totalSize
      fileCount
    }
  }
}
```

## 🔄 Storage Backends

### Local Storage
```python
STORAGE_SETTINGS = {
    'local': {
        'BASE_PATH': '/var/uploads/',
        'BASE_URL': '/media/',
        'PERMISSIONS': 0o644,
        'DIRECTORY_PERMISSIONS': 0o755,
    }
}
```

### AWS S3
```python
STORAGE_SETTINGS = {
    's3': {
        'BUCKET_NAME': 'my-uploads-bucket',
        'REGION': 'us-east-1',
        'ACCESS_KEY_ID': 'your-access-key',
        'SECRET_ACCESS_KEY': 'your-secret-key',
        'CUSTOM_DOMAIN': 'cdn.example.com',
        'ENCRYPTION': 'AES256',
    }
}
```

### Google Cloud Storage
```python
STORAGE_SETTINGS = {
    'gcs': {
        'BUCKET_NAME': 'my-uploads-bucket',
        'PROJECT_ID': 'my-project-id',
        'CREDENTIALS_PATH': '/path/to/credentials.json',
        'CUSTOM_DOMAIN': 'cdn.example.com',
    }
}
```

## 🧪 Testing

### Unit Tests
```python
# Test file upload functionality
def test_file_upload():
    """Test basic file upload functionality"""
    # Test implementation
    pass

def test_virus_scanning():
    """Test virus scanning integration"""
    # Test implementation
    pass

def test_thumbnail_generation():
    """Test thumbnail generation"""
    # Test implementation
    pass
```

### Integration Tests
```python
# Test complete file upload workflow
def test_complete_upload_workflow():
    """Test end-to-end file upload process"""
    # Test implementation
    pass
```

## 📚 Examples

### Basic File Upload
```python
# Python client example
import requests
import base64

# Read file and encode
with open('document.pdf', 'rb') as f:
    file_content = base64.b64encode(f.read()).decode()

# GraphQL mutation
mutation = """
mutation UploadFile($input: FileUploadInput!) {
  uploadFile(input: $input) {
    ok
    file {
      id
      filename
      url
    }
    errors
  }
}
"""

variables = {
    "input": {
        "file": file_content,
        "filename": "document.pdf",
        "mimeType": "application/pdf"
    }
}

response = requests.post(
    'http://localhost:8000/graphql/',
    json={'query': mutation, 'variables': variables}
)
```

### JavaScript File Upload
```javascript
// JavaScript client example
const uploadFile = async (file) => {
  const reader = new FileReader();
  
  return new Promise((resolve, reject) => {
    reader.onload = async () => {
      const base64Content = reader.result.split(',')[1];
      
      const mutation = `
        mutation UploadFile($input: FileUploadInput!) {
          uploadFile(input: $input) {
            ok
            file {
              id
              filename
              url
            }
            errors
          }
        }
      `;
      
      const variables = {
        input: {
          file: base64Content,
          filename: file.name,
          mimeType: file.type
        }
      };
      
      try {
        const response = await fetch('/graphql/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ query: mutation, variables })
        });
        
        const result = await response.json();
        resolve(result);
      } catch (error) {
        reject(error);
      }
    };
    
    reader.readAsDataURL(file);
  });
};
```

## 🔧 Troubleshooting

### Common Issues

#### Upload Fails with Size Error
```python
# Check file size limits
GRAPHQL_FILE_UPLOADS = {
    'MAX_FILE_SIZE': 50 * 1024 * 1024,  # Increase to 50MB
}
```

#### Virus Scanner Not Working
```bash
# Install ClamAV
sudo apt-get install clamav clamav-daemon

# Update virus definitions
sudo freshclam

# Start ClamAV daemon
sudo systemctl start clamav-daemon
```

#### Thumbnails Not Generated
```python
# Install Pillow with all features
pip install Pillow[all]

# Check image processing settings
GRAPHQL_FILE_UPLOADS = {
    'ENABLE_IMAGE_PROCESSING': True,
    'THUMBNAIL_SIZES': [(150, 150), (300, 300)],
}
```

### Debug Mode
```python
# Enable debug mode for detailed logging
GRAPHQL_FILE_UPLOADS = {
    'DEBUG_MODE': True,
    'LOG_LEVEL': 'DEBUG',
}
```

## 📖 Additional Resources

- [File Upload Examples](../examples/file-upload-examples.md)
- [Security Configuration](../setup/security-configuration.md)
- [Performance Optimization](../development/performance.md)
- [Storage Backend Setup](../deployment/storage-backends.md)
- [API Reference](../api-reference.md#file-upload-operations)