# 📁 File Upload Examples

Practical examples for implementing file uploads and media management with Django GraphQL Auto.

## 🚀 Quick Start Examples

### Basic File Upload

#### Python Client
```python
import requests
import base64
from pathlib import Path

def upload_file(file_path, graphql_endpoint):
    """Upload a single file using GraphQL mutation"""
    
    # Read and encode file
    file_path = Path(file_path)
    with open(file_path, 'rb') as f:
        file_content = base64.b64encode(f.read()).decode()
    
    # GraphQL mutation
    mutation = """
    mutation UploadFile($input: FileUploadInput!) {
      uploadFile(input: $input) {
        ok
        file {
          id
          filename
          size
          url
          mimeType
          uploadedAt
          scanResult {
            status
            scanTime
          }
        }
        errors
      }
    }
    """
    
    variables = {
        "input": {
            "file": file_content,
            "filename": file_path.name,
            "mimeType": "application/octet-stream"  # Auto-detect or specify
        }
    }
    
    response = requests.post(
        graphql_endpoint,
        json={'query': mutation, 'variables': variables},
        headers={'Content-Type': 'application/json'}
    )
    
    return response.json()

# Usage
result = upload_file('document.pdf', 'http://localhost:8000/graphql/')
if result['data']['uploadFile']['ok']:
    file_info = result['data']['uploadFile']['file']
    print(f"File uploaded: {file_info['url']}")
else:
    print(f"Upload failed: {result['data']['uploadFile']['errors']}")
```

#### JavaScript/React Client
```javascript
import React, { useState } from 'react';

const FileUploadComponent = () => {
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);

  const uploadFile = async (file) => {
    setUploading(true);
    
    try {
      // Convert file to base64
      const base64Content = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = () => {
          const base64 = reader.result.split(',')[1];
          resolve(base64);
        };
        reader.readAsDataURL(file);
      });

      const mutation = `
        mutation UploadFile($input: FileUploadInput!) {
          uploadFile(input: $input) {
            ok
            file {
              id
              filename
              size
              url
              mimeType
              uploadedAt
              scanResult {
                status
                scanTime
              }
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

      const response = await fetch('/graphql/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: mutation, variables })
      });

      const result = await response.json();
      setUploadResult(result.data.uploadFile);
      
    } catch (error) {
      console.error('Upload failed:', error);
      setUploadResult({ ok: false, errors: [error.message] });
    } finally {
      setUploading(false);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      uploadFile(file);
    }
  };

  return (
    <div>
      <input 
        type="file" 
        onChange={handleFileSelect}
        disabled={uploading}
      />
      
      {uploading && <p>Uploading...</p>}
      
      {uploadResult && (
        <div>
          {uploadResult.ok ? (
            <div>
              <p>✅ Upload successful!</p>
              <p>File: {uploadResult.file.filename}</p>
              <p>Size: {uploadResult.file.size} bytes</p>
              <p>URL: <a href={uploadResult.file.url} target="_blank" rel="noopener noreferrer">
                {uploadResult.file.url}
              </a></p>
              <p>Scan Status: {uploadResult.file.scanResult.status}</p>
            </div>
          ) : (
            <div>
              <p>❌ Upload failed</p>
              <ul>
                {uploadResult.errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FileUploadComponent;
```

## 📚 Advanced Examples

### Multiple File Upload

#### Python - Batch Upload
```python
import requests
import base64
from pathlib import Path
from typing import List

def upload_multiple_files(file_paths: List[str], graphql_endpoint: str):
    """Upload multiple files in a single request"""
    
    files_data = []
    
    for file_path in file_paths:
        file_path = Path(file_path)
        with open(file_path, 'rb') as f:
            file_content = base64.b64encode(f.read()).decode()
        
        files_data.append({
            "file": file_content,
            "filename": file_path.name,
            "mimeType": "application/octet-stream"
        })
    
    mutation = """
    mutation UploadMultipleFiles($input: MultipleFileUploadInput!) {
      uploadFiles(input: $input) {
        ok
        files {
          id
          filename
          size
          url
          mimeType
          scanResult {
            status
            threats
          }
        }
        errors
      }
    }
    """
    
    variables = {
        "input": {
            "files": files_data
        }
    }
    
    response = requests.post(
        graphql_endpoint,
        json={'query': mutation, 'variables': variables}
    )
    
    return response.json()

# Usage
file_paths = ['image1.jpg', 'document.pdf', 'data.csv']
result = upload_multiple_files(file_paths, 'http://localhost:8000/graphql/')

if result['data']['uploadFiles']['ok']:
    for file_info in result['data']['uploadFiles']['files']:
        print(f"Uploaded: {file_info['filename']} -> {file_info['url']}")
else:
    print(f"Upload failed: {result['data']['uploadFiles']['errors']}")
```

#### React - Drag & Drop Multiple Files
```javascript
import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

const MultipleFileUpload = () => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState([]);

  const uploadFiles = async (filesToUpload) => {
    setUploading(true);
    
    try {
      // Convert all files to base64
      const filesData = await Promise.all(
        filesToUpload.map(file => 
          new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = () => {
              const base64 = reader.result.split(',')[1];
              resolve({
                file: base64,
                filename: file.name,
                mimeType: file.type
              });
            };
            reader.readAsDataURL(file);
          })
        )
      );

      const mutation = `
        mutation UploadMultipleFiles($input: MultipleFileUploadInput!) {
          uploadFiles(input: $input) {
            ok
            files {
              id
              filename
              size
              url
              scanResult {
                status
                threats
              }
            }
            errors
          }
        }
      `;

      const variables = {
        input: {
          files: filesData
        }
      };

      const response = await fetch('/graphql/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: mutation, variables })
      });

      const result = await response.json();
      setResults(result.data.uploadFiles);
      
    } catch (error) {
      console.error('Upload failed:', error);
      setResults({ ok: false, errors: [error.message] });
    } finally {
      setUploading(false);
    }
  };

  const onDrop = useCallback((acceptedFiles) => {
    setFiles(acceptedFiles);
    uploadFiles(acceptedFiles);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
    maxFiles: 10
  });

  return (
    <div>
      <div 
        {...getRootProps()} 
        style={{
          border: '2px dashed #ccc',
          padding: '20px',
          textAlign: 'center',
          cursor: 'pointer'
        }}
      >
        <input {...getInputProps()} />
        {isDragActive ? (
          <p>Drop the files here...</p>
        ) : (
          <p>Drag & drop files here, or click to select files</p>
        )}
      </div>

      {uploading && <p>Uploading {files.length} files...</p>}

      {results.ok && (
        <div>
          <h3>Upload Results:</h3>
          {results.files.map((file, index) => (
            <div key={index} style={{ margin: '10px 0', padding: '10px', border: '1px solid #ddd' }}>
              <p><strong>{file.filename}</strong></p>
              <p>Size: {file.size} bytes</p>
              <p>Scan Status: {file.scanResult.status}</p>
              <p>URL: <a href={file.url} target="_blank" rel="noopener noreferrer">
                View File
              </a></p>
            </div>
          ))}
        </div>
      )}

      {results.errors && (
        <div>
          <h3>Upload Errors:</h3>
          <ul>
            {results.errors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default MultipleFileUpload;
```

### Image Processing Examples

#### Generate Thumbnails
```python
def generate_thumbnails(file_id: str, graphql_endpoint: str):
    """Generate thumbnails for an uploaded image"""
    
    mutation = """
    mutation GenerateThumbnails($input: ThumbnailGenerationInput!) {
      generateThumbnails(input: $input) {
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
    """
    
    variables = {
        "input": {
            "fileId": file_id,
            "sizes": [
                {"width": 150, "height": 150},
                {"width": 300, "height": 300},
                {"width": 600, "height": 600}
            ]
        }
    }
    
    response = requests.post(
        graphql_endpoint,
        json={'query': mutation, 'variables': variables}
    )
    
    return response.json()

# Usage
result = generate_thumbnails("file-123", 'http://localhost:8000/graphql/')
if result['data']['generateThumbnails']['ok']:
    for thumbnail in result['data']['generateThumbnails']['thumbnails']:
        print(f"Thumbnail: {thumbnail['width']}x{thumbnail['height']} -> {thumbnail['url']}")
```

#### Image Processing Pipeline
```python
def process_image(file_id: str, graphql_endpoint: str):
    """Apply multiple processing operations to an image"""
    
    mutation = """
    mutation ProcessImage($input: ImageProcessingInput!) {
      processImage(input: $input) {
        ok
        processedFile {
          id
          url
          size
          format
          metadata {
            width
            height
            format
          }
        }
        errors
      }
    }
    """
    
    variables = {
        "input": {
            "fileId": file_id,
            "operations": [
                {"type": "RESIZE", "width": 800, "height": 600},
                {"type": "OPTIMIZE", "quality": 85},
                {"type": "CONVERT", "format": "WEBP"}
            ]
        }
    }
    
    response = requests.post(
        graphql_endpoint,
        json={'query': mutation, 'variables': variables}
    )
    
    return response.json()
```

## 🔍 File Management Examples

### List and Filter Files
```python
def list_files_with_filters(graphql_endpoint: str, filters: dict = None):
    """List files with optional filtering"""
    
    query = """
    query ListFiles($filters: FileFilterInput, $first: Int, $after: String) {
      files(filters: $filters, first: $first, after: $after) {
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
              threats
            }
            thumbnails {
              size
              url
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
    """
    
    variables = {
        "filters": filters or {},
        "first": 20
    }
    
    response = requests.post(
        graphql_endpoint,
        json={'query': query, 'variables': variables}
    )
    
    return response.json()

# Usage examples
# List all files
all_files = list_files_with_filters('http://localhost:8000/graphql/')

# Filter by MIME type
image_files = list_files_with_filters(
    'http://localhost:8000/graphql/',
    {"mimeType": "image/jpeg"}
)

# Filter by upload date
recent_files = list_files_with_filters(
    'http://localhost:8000/graphql/',
    {"uploadedAfter": "2024-01-01T00:00:00Z"}
)

# Filter by scan status
clean_files = list_files_with_filters(
    'http://localhost:8000/graphql/',
    {"scanStatus": "CLEAN"}
)
```

### File Search and Metadata
```python
def search_files(search_term: str, graphql_endpoint: str):
    """Search files by filename or metadata"""
    
    query = """
    query SearchFiles($search: String!, $first: Int) {
      searchFiles(search: $search, first: $first) {
        edges {
          node {
            id
            filename
            size
            mimeType
            url
            uploadedAt
            metadata {
              width
              height
              duration
              exifData
            }
            scanResult {
              status
            }
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
    """
    
    variables = {
        "search": search_term,
        "first": 10
    }
    
    response = requests.post(
        graphql_endpoint,
        json={'query': query, 'variables': variables}
    )
    
    return response.json()

# Usage
search_results = search_files("vacation", 'http://localhost:8000/graphql/')
for edge in search_results['data']['searchFiles']['edges']:
    file_info = edge['node']
    print(f"Found: {file_info['filename']} ({file_info['size']} bytes)")
```

## 🛡️ Security Examples

### Virus Scan Status Check
```python
def check_scan_status(file_id: str, graphql_endpoint: str):
    """Check the virus scan status of a file"""
    
    query = """
    query FileScanStatus($fileId: ID!) {
      fileScanStatus(fileId: $fileId) {
        status
        scanResult {
          status
          threats
          scanTime
          scannerVersion
        }
        quarantined
        quarantineReason
      }
    }
    """
    
    variables = {"fileId": file_id}
    
    response = requests.post(
        graphql_endpoint,
        json={'query': query, 'variables': variables}
    )
    
    return response.json()

# Usage
scan_status = check_scan_status("file-123", 'http://localhost:8000/graphql/')
status_info = scan_status['data']['fileScanStatus']

if status_info['quarantined']:
    print(f"⚠️ File is quarantined: {status_info['quarantineReason']}")
elif status_info['scanResult']['status'] == 'CLEAN':
    print("✅ File is clean and safe")
elif status_info['scanResult']['status'] == 'INFECTED':
    print(f"🦠 File is infected: {status_info['scanResult']['threats']}")
```

### Security Statistics
```python
def get_security_stats(graphql_endpoint: str):
    """Get file upload security statistics"""
    
    query = """
    query FileUploadSecurityStats {
      fileUploadStats {
        totalUploads
        cleanFiles
        infectedFiles
        quarantinedFiles
        scanFailures
        avgScanTime
        threatTypes {
          type
          count
        }
      }
    }
    """
    
    response = requests.post(
        graphql_endpoint,
        json={'query': query}
    )
    
    return response.json()

# Usage
stats = get_security_stats('http://localhost:8000/graphql/')
upload_stats = stats['data']['fileUploadStats']

print(f"Total uploads: {upload_stats['totalUploads']}")
print(f"Clean files: {upload_stats['cleanFiles']}")
print(f"Infected files: {upload_stats['infectedFiles']}")
print(f"Average scan time: {upload_stats['avgScanTime']}s")

if upload_stats['threatTypes']:
    print("Threat types detected:")
    for threat in upload_stats['threatTypes']:
        print(f"  - {threat['type']}: {threat['count']} occurrences")
```

## 📊 Storage and Performance Examples

### Storage Usage Monitoring
```python
def get_storage_usage(graphql_endpoint: str):
    """Monitor storage usage and statistics"""
    
    query = """
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
    """
    
    response = requests.post(
        graphql_endpoint,
        json={'query': query}
    )
    
    return response.json()

# Usage
usage = get_storage_usage('http://localhost:8000/graphql/')
storage_info = usage['data']['storageUsage']

print(f"Total used: {storage_info['totalUsed']} bytes")
print(f"Total available: {storage_info['totalAvailable']} bytes")

print("Usage by file type:")
for usage_type in storage_info['usageByType']:
    print(f"  {usage_type['type']}: {usage_type['size']} bytes ({usage_type['percentage']}%)")
```

### Cleanup Operations
```python
def cleanup_old_files(days_old: int, graphql_endpoint: str):
    """Clean up files older than specified days"""
    
    mutation = """
    mutation CleanupOldFiles($input: FileCleanupInput!) {
      cleanupOldFiles(input: $input) {
        ok
        deletedCount
        freedSpace
        errors
      }
    }
    """
    
    variables = {
        "input": {
            "olderThanDays": days_old,
            "includeQuarantined": True,
            "dryRun": False
        }
    }
    
    response = requests.post(
        graphql_endpoint,
        json={'query': mutation, 'variables': variables}
    )
    
    return response.json()

# Usage
cleanup_result = cleanup_old_files(30, 'http://localhost:8000/graphql/')
if cleanup_result['data']['cleanupOldFiles']['ok']:
    result = cleanup_result['data']['cleanupOldFiles']
    print(f"Deleted {result['deletedCount']} files")
    print(f"Freed {result['freedSpace']} bytes of storage")
```

## 🔧 Error Handling Examples

### Comprehensive Error Handling
```python
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class FileUploadError(Exception):
    """Custom exception for file upload errors"""
    pass

def safe_file_upload(file_path: str, graphql_endpoint: str) -> Optional[Dict[str, Any]]:
    """Upload file with comprehensive error handling"""
    
    try:
        # Validate file exists and is readable
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileUploadError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise FileUploadError(f"Path is not a file: {file_path}")
        
        # Check file size
        file_size = file_path.stat().st_size
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            raise FileUploadError(f"File too large: {file_size} bytes (max: {max_size})")
        
        # Read and encode file
        with open(file_path, 'rb') as f:
            file_content = base64.b64encode(f.read()).decode()
        
        mutation = """
        mutation UploadFile($input: FileUploadInput!) {
          uploadFile(input: $input) {
            ok
            file {
              id
              filename
              size
              url
              scanResult {
                status
                threats
              }
            }
            errors
          }
        }
        """
        
        variables = {
            "input": {
                "file": file_content,
                "filename": file_path.name,
                "mimeType": "application/octet-stream"
            }
        }
        
        response = requests.post(
            graphql_endpoint,
            json={'query': mutation, 'variables': variables},
            timeout=60  # 60 second timeout
        )
        
        # Check HTTP response
        response.raise_for_status()
        
        result = response.json()
        
        # Check for GraphQL errors
        if 'errors' in result:
            error_messages = [error['message'] for error in result['errors']]
            raise FileUploadError(f"GraphQL errors: {', '.join(error_messages)}")
        
        # Check upload result
        upload_result = result['data']['uploadFile']
        if not upload_result['ok']:
            error_messages = upload_result.get('errors', ['Unknown error'])
            raise FileUploadError(f"Upload failed: {', '.join(error_messages)}")
        
        # Check scan result
        file_info = upload_result['file']
        scan_status = file_info['scanResult']['status']
        
        if scan_status == 'INFECTED':
            threats = file_info['scanResult']['threats']
            logger.warning(f"Uploaded file is infected: {threats}")
            # You might want to handle this differently based on your requirements
        
        logger.info(f"File uploaded successfully: {file_info['filename']} -> {file_info['url']}")
        return file_info
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during upload: {e}")
        raise FileUploadError(f"Network error: {e}")
    
    except FileUploadError:
        # Re-raise our custom errors
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}")
        raise FileUploadError(f"Unexpected error: {e}")

# Usage with error handling
try:
    file_info = safe_file_upload('document.pdf', 'http://localhost:8000/graphql/')
    print(f"Upload successful: {file_info['url']}")
except FileUploadError as e:
    print(f"Upload failed: {e}")
```

## 📱 Mobile App Examples

### React Native File Upload
```javascript
import { launchImageLibrary } from 'react-native-image-picker';
import RNFS from 'react-native-fs';

const uploadFileFromMobile = async () => {
  try {
    // Pick image from library
    const result = await new Promise((resolve, reject) => {
      launchImageLibrary(
        {
          mediaType: 'mixed',
          quality: 0.8,
        },
        (response) => {
          if (response.didCancel || response.error) {
            reject(new Error(response.error || 'User cancelled'));
          } else {
            resolve(response.assets[0]);
          }
        }
      );
    });

    // Read file as base64
    const base64Content = await RNFS.readFile(result.uri, 'base64');

    const mutation = `
      mutation UploadFile($input: FileUploadInput!) {
        uploadFile(input: $input) {
          ok
          file {
            id
            filename
            url
            scanResult {
              status
            }
          }
          errors
        }
      }
    `;

    const variables = {
      input: {
        file: base64Content,
        filename: result.fileName || 'mobile_upload.jpg',
        mimeType: result.type
      }
    };

    const response = await fetch('http://your-server.com/graphql/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query: mutation, variables })
    });

    const uploadResult = await response.json();
    
    if (uploadResult.data.uploadFile.ok) {
      console.log('Upload successful:', uploadResult.data.uploadFile.file.url);
      return uploadResult.data.uploadFile.file;
    } else {
      throw new Error(uploadResult.data.uploadFile.errors.join(', '));
    }

  } catch (error) {
    console.error('Mobile upload failed:', error);
    throw error;
  }
};
```

## 🧪 Testing Examples

### Unit Test for File Upload
```python
import pytest
from unittest.mock import patch, mock_open
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

class FileUploadTestCase(TestCase):
    
    def setUp(self):
        self.graphql_endpoint = '/graphql/'
        self.test_file_content = b'Test file content'
        self.test_file = SimpleUploadedFile(
            "test.txt",
            self.test_file_content,
            content_type="text/plain"
        )
    
    def test_successful_file_upload(self):
        """Test successful file upload"""
        mutation = """
        mutation UploadFile($input: FileUploadInput!) {
          uploadFile(input: $input) {
            ok
            file {
              id
              filename
              size
            }
            errors
          }
        }
        """
        
        variables = {
            "input": {
                "file": base64.b64encode(self.test_file_content).decode(),
                "filename": "test.txt",
                "mimeType": "text/plain"
            }
        }
        
        response = self.client.post(
            self.graphql_endpoint,
            data={'query': mutation, 'variables': variables},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result['data']['uploadFile']['ok'])
        self.assertEqual(result['data']['uploadFile']['file']['filename'], 'test.txt')
    
    @patch('your_app.virus_scanner.scan_file')
    def test_virus_scan_integration(self, mock_scan):
        """Test virus scanning integration"""
        # Mock virus scanner to return infected result
        mock_scan.return_value = {
            'status': 'INFECTED',
            'threats': ['Test.Virus'],
            'scan_time': 0.5
        }
        
        mutation = """
        mutation UploadFile($input: FileUploadInput!) {
          uploadFile(input: $input) {
            ok
            file {
              scanResult {
                status
                threats
              }
            }
            errors
          }
        }
        """
        
        variables = {
            "input": {
                "file": base64.b64encode(self.test_file_content).decode(),
                "filename": "infected.txt",
                "mimeType": "text/plain"
            }
        }
        
        response = self.client.post(
            self.graphql_endpoint,
            data={'query': mutation, 'variables': variables},
            content_type='application/json'
        )
        
        result = response.json()
        # File should still upload but be marked as infected
        self.assertTrue(result['data']['uploadFile']['ok'])
        self.assertEqual(
            result['data']['uploadFile']['file']['scanResult']['status'],
            'INFECTED'
        )
```

## 📚 Additional Resources

- [File Upload Security Best Practices](../features/security.md#file-upload-security)
- [Performance Optimization Guide](../development/performance.md)
- [Storage Backend Configuration](../deployment/storage-backends.md)
- [API Reference](../api-reference.md#file-upload-operations)
- [Troubleshooting Guide](../development/troubleshooting.md)