# 🚀 rclone Remote Control (RC) Implementation Guide

**Status:** Ready for Implementation
**Priority:** P0 (Critical)
**Estimated Time:** 3 weeks
**Created:** November 17, 2025

---

## 📋 Overview

This guide provides a step-by-step implementation plan for integrating **rclone's Remote Control API** into BackupGenie. This will enable 100% Web GUI configuration for ALL cloud storage providers without requiring CLI access.

### Why rclone RC?

✅ **Universal:** Works for ALL 40+ rclone providers
✅ **OAuth2 Built-in:** Handles authentication automatically
✅ **Maintained:** Provider updates handled by rclone team
✅ **Secure:** Battle-tested OAuth2 implementation
✅ **Complete:** Config, test, browse, sync all included
✅ **Zero Setup:** No provider app registration needed

---

## 🎯 Implementation Phases

### **Phase 1: Backend Foundation (Week 1)**

#### 1.1 Create Directory Structure

```bash
mkdir -p backend/app/rclone
touch backend/app/rclone/__init__.py
touch backend/app/rclone/rc_server.py
touch backend/app/rclone/rc_client.py
```

#### 1.2 Implement RC Server Manager

**File:** `backend/app/rclone/rc_server.py`

```python
"""rclone Remote Control Server Manager"""
import subprocess
import logging
import time
import requests
from pathlib import Path

logger = logging.getLogger(__name__)


class RcloneRCServer:
    """Manages rclone Remote Control server lifecycle"""

    def __init__(self, port=5572, config_path='/app/config/rclone.conf'):
        self.port = port
        self.config_path = config_path
        self.process = None
        self.base_url = f"http://127.0.0.1:{port}"

    def start(self):
        """Start rclone RC server"""
        if self.is_running():
            logger.info("rclone RC server already running")
            return True

        try:
            # Ensure config directory exists
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)

            # Start rclone rcd
            self.process = subprocess.Popen(
                [
                    'rclone', 'rcd',
                    '--rc-addr', f'127.0.0.1:{self.port}',
                    '--rc-no-auth',  # Auth handled by BackupGenie
                    '--config', self.config_path,
                    '--rc-allow-origin', '*',  # Allow CORS for frontend
                    '--log-level', 'INFO'
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for server to start
            for _ in range(10):
                if self.is_running():
                    logger.info(f"rclone RC server started on port {self.port}")
                    return True
                time.sleep(0.5)

            logger.error("rclone RC server failed to start")
            return False

        except Exception as e:
            logger.error(f"Failed to start rclone RC server: {e}")
            return False

    def stop(self):
        """Stop rclone RC server"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                logger.info("rclone RC server stopped")
            except subprocess.TimeoutExpired:
                self.process.kill()
                logger.warning("rclone RC server killed (timeout)")
            except Exception as e:
                logger.error(f"Error stopping rclone RC server: {e}")

    def is_running(self):
        """Check if rclone RC server is running"""
        try:
            response = requests.get(f"{self.base_url}/core/stats", timeout=2)
            return response.status_code == 200
        except:
            return False

    def restart(self):
        """Restart rclone RC server"""
        self.stop()
        time.sleep(1)
        return self.start()
```

#### 1.3 Implement RC Client Wrapper

**File:** `backend/app/rclone/rc_client.py`

```python
"""rclone Remote Control API Client"""
import requests
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class RcloneRC:
    """Client for rclone Remote Control API"""

    def __init__(self, base_url="http://127.0.0.1:5572"):
        self.base_url = base_url

    def _call(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make API call to rclone RC server"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.post(url, json=data or {}, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"rclone RC API error: {e}")
            raise

    # Config Management

    def list_remotes(self) -> List[str]:
        """List all configured remotes"""
        result = self._call('config/listremotes')
        return result.get('remotes', [])

    def get_remote(self, name: str) -> Dict:
        """Get remote configuration"""
        result = self._call('config/get', {'name': name})
        return result

    def create_remote(self, name: str, type: str, parameters: Dict) -> Dict:
        """Create new remote"""
        data = {
            'name': name,
            'type': type,
            'parameters': parameters
        }
        return self._call('config/create', data)

    def update_remote(self, name: str, parameters: Dict) -> Dict:
        """Update existing remote"""
        data = {
            'name': name,
            'parameters': parameters
        }
        return self._call('config/update', data)

    def delete_remote(self, name: str) -> Dict:
        """Delete remote"""
        return self._call('config/delete', {'name': name})

    # OAuth2 Authorization

    def authorize(self, type: str) -> Dict:
        """Start OAuth2 authorization flow"""
        data = {'type': type}
        return self._call('config/authorize', data)

    # Operations

    def test_remote(self, remote: str) -> Dict:
        """Test remote connection and get info"""
        try:
            result = self._call('operations/about', {'fs': f'{remote}:'})
            return {
                'success': True,
                'total': result.get('total', 0),
                'used': result.get('used', 0),
                'free': result.get('free', 0)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def list_dir(self, remote: str, path: str = "") -> List[Dict]:
        """List files and folders in remote"""
        result = self._call('operations/list', {
            'fs': f'{remote}:',
            'remote': path
        })
        return result.get('list', [])

    def mkdir(self, remote: str, path: str) -> Dict:
        """Create directory in remote"""
        return self._call('operations/mkdir', {
            'fs': f'{remote}:',
            'remote': path
        })

    # System

    def get_stats(self) -> Dict:
        """Get rclone transfer stats"""
        return self._call('core/stats')

    def version(self) -> Dict:
        """Get rclone version"""
        return self._call('core/version')
```

#### 1.4 Integrate RC Server into Flask App

**File:** `backend/app/__init__.py`

Add to the `create_app()` function:

```python
from app.rclone.rc_server import RcloneRCServer

def create_app():
    app = Flask(__name__)

    # ... existing initialization ...

    # Start rclone RC server
    rc_server = RcloneRCServer(
        port=5572,
        config_path='/app/config/rclone.conf'
    )

    if rc_server.start():
        app.rc_server = rc_server
        app.logger.info("✅ rclone Remote Control server started")
    else:
        app.logger.error("❌ Failed to start rclone RC server")

    # Ensure server stops on shutdown
    @app.teardown_appcontext
    def shutdown_rc_server(exception=None):
        if hasattr(app, 'rc_server'):
            app.rc_server.stop()

    # ... rest of initialization ...

    return app
```

---

### **Phase 2: Backend API Endpoints (Week 1-2)**

#### 2.1 Create rclone API Blueprint

**File:** `backend/app/api/rclone.py`

```python
"""rclone Management API Endpoints"""
from flask import Blueprint, request, jsonify, current_app
from app.api.auth import token_required
from app.rclone.rc_client import RcloneRC
import logging

logger = logging.getLogger(__name__)

rclone_bp = Blueprint('rclone', __name__, url_prefix='/api/v1/rclone')


def get_rc_client():
    """Get rclone RC client instance"""
    return RcloneRC()


# Remote Management

@rclone_bp.route('/remotes', methods=['GET'])
@token_required
def list_remotes(current_user):
    """List all rclone remotes"""
    try:
        rc = get_rc_client()
        remotes = rc.list_remotes()
        return jsonify({'remotes': remotes}), 200
    except Exception as e:
        logger.error(f"Error listing remotes: {e}")
        return jsonify({'error': str(e)}), 500


@rclone_bp.route('/remotes/<name>', methods=['GET'])
@token_required
def get_remote(current_user, name):
    """Get remote configuration"""
    try:
        rc = get_rc_client()
        config = rc.get_remote(name)
        return jsonify(config), 200
    except Exception as e:
        logger.error(f"Error getting remote {name}: {e}")
        return jsonify({'error': str(e)}), 404


@rclone_bp.route('/remotes', methods=['POST'])
@token_required
def create_remote(current_user):
    """Create new rclone remote"""
    try:
        data = request.get_json()

        if not data or not data.get('name') or not data.get('type'):
            return jsonify({'error': 'name and type are required'}), 400

        rc = get_rc_client()
        result = rc.create_remote(
            name=data['name'],
            type=data['type'],
            parameters=data.get('parameters', {})
        )

        return jsonify({
            'message': f"Remote {data['name']} created successfully",
            'result': result
        }), 201

    except Exception as e:
        logger.error(f"Error creating remote: {e}")
        return jsonify({'error': str(e)}), 500


@rclone_bp.route('/remotes/<name>', methods=['PUT'])
@token_required
def update_remote(current_user, name):
    """Update existing remote"""
    try:
        data = request.get_json()

        if not data or not data.get('parameters'):
            return jsonify({'error': 'parameters are required'}), 400

        rc = get_rc_client()
        result = rc.update_remote(name, data['parameters'])

        return jsonify({
            'message': f"Remote {name} updated successfully",
            'result': result
        }), 200

    except Exception as e:
        logger.error(f"Error updating remote {name}: {e}")
        return jsonify({'error': str(e)}), 500


@rclone_bp.route('/remotes/<name>', methods=['DELETE'])
@token_required
def delete_remote(current_user, name):
    """Delete remote"""
    try:
        rc = get_rc_client()
        rc.delete_remote(name)

        return jsonify({'message': f"Remote {name} deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Error deleting remote {name}: {e}")
        return jsonify({'error': str(e)}), 500


# OAuth2 Authorization

@rclone_bp.route('/authorize/<provider>', methods=['POST'])
@token_required
def authorize_oauth(current_user, provider):
    """Start OAuth2 authorization flow"""
    try:
        rc = get_rc_client()
        result = rc.authorize(provider)

        return jsonify({
            'message': f"Authorization started for {provider}",
            'auth_url': result.get('auth_url'),
            'result': result
        }), 200

    except Exception as e:
        logger.error(f"Error starting OAuth for {provider}: {e}")
        return jsonify({'error': str(e)}), 500


# Operations

@rclone_bp.route('/remotes/<name>/test', methods=['POST'])
@token_required
def test_remote(current_user, name):
    """Test remote connection"""
    try:
        rc = get_rc_client()
        result = rc.test_remote(name)

        if result['success']:
            return jsonify({
                'message': f"Connection to {name} successful",
                'stats': result
            }), 200
        else:
            return jsonify({
                'error': f"Connection failed: {result.get('error')}"
            }), 400

    except Exception as e:
        logger.error(f"Error testing remote {name}: {e}")
        return jsonify({'error': str(e)}), 500


@rclone_bp.route('/remotes/<name>/browse', methods=['POST'])
@token_required
def browse_remote(current_user, name):
    """Browse folders in remote"""
    try:
        data = request.get_json() or {}
        path = data.get('path', '')

        rc = get_rc_client()
        files = rc.list_dir(name, path)

        return jsonify({
            'path': path,
            'files': files
        }), 200

    except Exception as e:
        logger.error(f"Error browsing remote {name}: {e}")
        return jsonify({'error': str(e)}), 500


@rclone_bp.route('/remotes/<name>/mkdir', methods=['POST'])
@token_required
def create_directory(current_user, name):
    """Create directory in remote"""
    try:
        data = request.get_json()

        if not data or not data.get('path'):
            return jsonify({'error': 'path is required'}), 400

        rc = get_rc_client()
        result = rc.mkdir(name, data['path'])

        return jsonify({
            'message': f"Directory created: {data['path']}",
            'result': result
        }), 201

    except Exception as e:
        logger.error(f"Error creating directory in {name}: {e}")
        return jsonify({'error': str(e)}), 500


# System Info

@rclone_bp.route('/version', methods=['GET'])
@token_required
def get_version(current_user):
    """Get rclone version"""
    try:
        rc = get_rc_client()
        version = rc.version()
        return jsonify(version), 200
    except Exception as e:
        logger.error(f"Error getting rclone version: {e}")
        return jsonify({'error': str(e)}), 500
```

#### 2.2 Register Blueprint

**File:** `backend/app/__init__.py`

```python
from app.api.rclone import rclone_bp

def create_app():
    # ... existing code ...

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(backup_bp)
    app.register_blueprint(sources_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(rclone_bp)  # Add this

    return app
```

---

### **Phase 3: Frontend Components (Week 2)**

#### 3.1 Add rclone API Client

**File:** `frontend/src/services/api.js`

Add after existing API exports:

```javascript
// rclone Management API
export const rcloneAPI = {
  // Remotes
  listRemotes: () => api.get('/rclone/remotes'),
  getRemote: (name) => api.get(`/rclone/remotes/${name}`),
  createRemote: (data) => api.post('/rclone/remotes', data),
  updateRemote: (name, data) => api.put(`/rclone/remotes/${name}`, data),
  deleteRemote: (name) => api.delete(`/rclone/remotes/${name}`),

  // OAuth2
  authorize: (provider) => api.post(`/rclone/authorize/${provider}`),

  // Operations
  testRemote: (name) => api.post(`/rclone/remotes/${name}/test`),
  browseRemote: (name, path = '') =>
    api.post(`/rclone/remotes/${name}/browse`, { path }),
  createDirectory: (name, path) =>
    api.post(`/rclone/remotes/${name}/mkdir`, { path }),

  // System
  getVersion: () => api.get('/rclone/version'),
}
```

#### 3.2 Create RcloneConfigManager Component

**File:** `frontend/src/components/RcloneConfigManager.jsx`

```jsx
import { useState } from 'react'
import { rcloneAPI } from '../services/api'
import toast from 'react-hot-toast'
import { Cloud, Check, AlertCircle, Loader } from 'lucide-react'

export default function RcloneConfigManager({ type, onConfigured }) {
  const [remoteName, setRemoteName] = useState('')
  const [isConnecting, setIsConnecting] = useState(false)
  const [isConnected, setIsConnected] = useState(false)

  const handleOAuthConnect = async () => {
    if (!remoteName.trim()) {
      toast.error('Please enter a remote name')
      return
    }

    setIsConnecting(true)
    const loadingToast = toast.loading('Starting OAuth flow...')

    try {
      // Start OAuth2 flow
      const result = await rcloneAPI.authorize(type)

      if (result.auth_url) {
        // Open OAuth consent in popup
        const popup = window.open(
          result.auth_url,
          'OAuth Authorization',
          'width=600,height=700,toolbar=no,location=no,status=no,menubar=no'
        )

        // Poll for popup close
        const pollTimer = setInterval(() => {
          if (popup.closed) {
            clearInterval(pollTimer)
            checkConnection()
          }
        }, 500)
      }

      toast.success('Please complete authorization in the popup window', {
        id: loadingToast
      })

    } catch (error) {
      console.error('OAuth error:', error)
      toast.error(error.response?.data?.error || 'Failed to start OAuth flow', {
        id: loadingToast
      })
      setIsConnecting(false)
    }
  }

  const checkConnection = async () => {
    try {
      // Test if remote was created
      const result = await rcloneAPI.testRemote(remoteName)

      if (result.message) {
        setIsConnected(true)
        toast.success(`✅ Connected to ${type}!`)
        onConfigured(remoteName)
      }
    } catch (error) {
      toast.error('Authorization may have failed. Please try again.')
    } finally {
      setIsConnecting(false)
    }
  }

  return (
    <div className="space-y-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
      <div className="flex items-start gap-3">
        <Cloud className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className="font-semibold text-blue-900 mb-1">
            Connect to {type}
          </p>
          <p className="text-sm text-blue-800 mb-4">
            Click the button below to authorize BackupGenie to access your {type} account.
            A popup window will open for you to sign in.
          </p>

          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Remote Name
              </label>
              <input
                type="text"
                value={remoteName}
                onChange={(e) => setRemoteName(e.target.value)}
                placeholder={`my-${type.toLowerCase()}`}
                disabled={isConnected}
                className="input w-full"
              />
              <p className="text-xs text-gray-500 mt-1">
                Choose a unique name for this connection
              </p>
            </div>

            {!isConnected ? (
              <button
                onClick={handleOAuthConnect}
                disabled={isConnecting || !remoteName.trim()}
                className="btn btn-primary w-full flex items-center justify-center gap-2"
              >
                {isConnecting ? (
                  <>
                    <Loader className="w-4 h-4 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <Cloud className="w-4 h-4" />
                    Connect to {type}
                  </>
                )}
              </button>
            ) : (
              <div className="flex items-center gap-2 p-3 bg-green-100 text-green-800 rounded-lg">
                <Check className="w-5 h-5" />
                <span className="font-medium">Connected successfully!</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
```

#### 3.3 Integrate into SourceModal

**File:** `frontend/src/components/SourceModal.jsx`

Import the component:

```jsx
import RcloneConfigManager from './RcloneConfigManager'
```

Replace the OAuth2 instructions section with:

```jsx
{needsOAuth ? (
  <RcloneConfigManager
    type={type}
    onConfigured={(remoteName) => {
      handleChange('remote_name', remoteName)
      toast.success(`${type} connected! You can now select folders.`)
    }}
  />
) : (
  // Existing fields for non-OAuth sources (S3, SFTP, etc.)
  <>
    {/* ... existing form fields ... */}
  </>
)}
```

---

### **Phase 4: Folder Browser (Week 3)**

#### 4.1 Create FolderBrowser Component

**File:** `frontend/src/components/FolderBrowser.jsx`

```jsx
import { useState, useEffect } from 'react'
import { rcloneAPI } from '../services/api'
import toast from 'react-hot-toast'
import { Folder, ChevronRight, Home, Loader, X } from 'lucide-react'

export default function FolderBrowser({ remoteName, onSelect, onClose }) {
  const [folders, setFolders] = useState([])
  const [currentPath, setCurrentPath] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [pathHistory, setPathHistory] = useState([''])

  useEffect(() => {
    loadFolders('')
  }, [remoteName])

  const loadFolders = async (path) => {
    setIsLoading(true)
    try {
      const result = await rcloneAPI.browseRemote(remoteName, path)

      // Filter to show only directories
      const dirs = result.files.filter(f => f.IsDir)
      setFolders(dirs)
      setCurrentPath(path)

    } catch (error) {
      console.error('Error loading folders:', error)
      toast.error('Failed to load folders')
    } finally {
      setIsLoading(false)
    }
  }

  const navigateToFolder = (folder) => {
    const newPath = currentPath ? `${currentPath}/${folder.Name}` : folder.Name
    setPathHistory([...pathHistory, newPath])
    loadFolders(newPath)
  }

  const navigateBack = () => {
    if (pathHistory.length > 1) {
      const newHistory = pathHistory.slice(0, -1)
      const previousPath = newHistory[newHistory.length - 1]
      setPathHistory(newHistory)
      loadFolders(previousPath)
    }
  }

  const navigateToRoot = () => {
    setPathHistory([''])
    loadFolders('')
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-bold">Browse Folders</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Breadcrumb */}
        <div className="flex items-center gap-2 p-4 bg-gray-50 border-b">
          <button
            onClick={navigateToRoot}
            className="p-1 hover:bg-gray-200 rounded"
            title="Go to root"
          >
            <Home className="w-4 h-4" />
          </button>
          <span className="text-gray-600">/</span>
          <span className="text-sm text-gray-800">
            {currentPath || 'root'}
          </span>
          {pathHistory.length > 1 && (
            <button
              onClick={navigateBack}
              className="ml-auto text-sm text-blue-600 hover:underline"
            >
              ← Back
            </button>
          )}
        </div>

        {/* Folder List */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader className="w-8 h-8 animate-spin text-blue-600" />
            </div>
          ) : folders.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Folder className="w-12 h-12 mx-auto mb-2 text-gray-300" />
              <p>No folders found</p>
            </div>
          ) : (
            <div className="space-y-1">
              {folders.map((folder) => (
                <button
                  key={folder.Path}
                  onClick={() => navigateToFolder(folder)}
                  className="w-full flex items-center gap-3 p-3 hover:bg-gray-100 rounded-lg transition-colors text-left"
                >
                  <Folder className="w-5 h-5 text-blue-600 shrink-0" />
                  <span className="flex-1 text-sm font-medium text-gray-900">
                    {folder.Name}
                  </span>
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t bg-gray-50">
          <div className="text-sm text-gray-600">
            Current: <span className="font-mono">{currentPath || '/'}</span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              onClick={() => onSelect(currentPath)}
              className="btn btn-primary"
            >
              Select This Folder
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
```

#### 4.2 Add Browse Button to SourceModal

In `SourceModal.jsx`, after the remote name field:

```jsx
{formData.remote_name && (
  <div>
    <button
      type="button"
      onClick={() => setShowFolderBrowser(true)}
      className="btn btn-secondary flex items-center gap-2"
    >
      <Folder className="w-4 h-4" />
      Browse Folders
    </button>
  </div>
)}

{showFolderBrowser && (
  <FolderBrowser
    remoteName={formData.remote_name}
    onSelect={(path) => {
      handleChange('folder_path', path)
      setShowFolderBrowser(false)
      toast.success(`Selected folder: ${path || '/'}`)
    }}
    onClose={() => setShowFolderBrowser(false)}
  />
)}
```

---

### **Phase 5: Testing & Deployment (Week 3)**

#### 5.1 Backend Testing

Create test file: `backend/tests/test_rclone.py`

```python
import pytest
from app.rclone.rc_client import RcloneRC

def test_list_remotes():
    rc = RcloneRC()
    remotes = rc.list_remotes()
    assert isinstance(remotes, list)

def test_create_remote():
    rc = RcloneRC()
    result = rc.create_remote(
        name='test-remote',
        type='s3',
        parameters={'provider': 'AWS'}
    )
    assert 'name' in result

# Add more tests...
```

#### 5.2 Manual Testing Checklist

- [ ] **Start RC Server:** Verify server starts on app launch
- [ ] **List Remotes:** GET /api/v1/rclone/remotes returns empty array
- [ ] **OAuth2 Flow:**
  - [ ] Google Drive: Click "Connect", popup opens, authorize, closes automatically
  - [ ] OneDrive: Same flow
  - [ ] Dropbox: Same flow
- [ ] **Test Connection:** POST /api/v1/rclone/remotes/{name}/test returns stats
- [ ] **Browse Folders:** POST /api/v1/rclone/remotes/{name}/browse returns file list
- [ ] **Create Remote (S3):** Non-OAuth provider with API keys
- [ ] **Delete Remote:** DELETE removes remote from config

#### 5.3 Docker Configuration

Update `docker-compose.yml` to expose RC port (optional for debugging):

```yaml
backend:
  # ... existing config ...
  ports:
    - "${API_PORT:-5000}:5000"
    # - "5572:5572"  # Uncomment for debugging rclone RC
```

#### 5.4 Documentation

Create user guide: `docs/RCLONE_SETUP.md`

```markdown
# Setting up Cloud Storage with rclone

BackupGenie uses rclone to connect to 40+ cloud storage providers.

## Supported Providers

- Google Drive
- OneDrive (Personal & Business)
- Dropbox
- Amazon S3
- Backblaze B2
- ... and 35+ more!

## Connecting a Provider

1. Go to **Sources** page
2. Click **Add Source**
3. Select your cloud provider (e.g., Google Drive)
4. Enter a name for this connection
5. Click **Connect to [Provider]**
6. A popup will open - sign in and authorize access
7. Once authorized, you can browse and select folders!

## Troubleshooting

### Popup Blocked
If the authorization popup doesn't open, check your browser's popup blocker.

### Authorization Failed
Try again or check your account permissions.

### Connection Test Fails
Verify your credentials and network connection.
```

---

## 🎯 Success Criteria

Implementation is complete when:

- [ ] rclone RC server starts automatically with backend
- [ ] All API endpoints respond correctly
- [ ] OAuth2 flow works for Google Drive, OneDrive, Dropbox
- [ ] Non-OAuth sources (S3, SFTP) can be configured with forms
- [ ] Folder browser displays directories correctly
- [ ] Connection test provides meaningful feedback
- [ ] Users can configure cloud sources without terminal access
- [ ] Documentation is complete

---

## 📚 References

- [rclone RC API Documentation](https://rclone.org/rc/)
- [rclone Config Documentation](https://rclone.org/docs/)
- [rclone OAuth2 Guide](https://rclone.org/remote_setup/)

---

**Next Steps:** Begin Phase 1 implementation! 🚀
