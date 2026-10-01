# 📂 CleanLoop Storage & Static Assets Guide (`media/` & `staticfiles/`)

This document explains the purpose, architecture, configuration, and security rules for file storage in CleanLoop, specifically detailing why **`media/`** and **`staticfiles/`** are critical for runtime operations and production deployment.

---

## 📸 1. Media Files Directory (`media/`)

### Purpose & Functionality
- **Location**: `media/` (configured as `MEDIA_ROOT = PROJECT_ROOT / 'media'`).
- **URL Path**: `/media/` (configured as `MEDIA_URL = '/media/'`).
- **Role**: Serves as the persistent storage directory for user-uploaded media files (e.g. photos of reported waste issues taken by citizens).
- **Subdirectory Structure**:
  - `media/complaints/YYYY/MM/DD/`: Automatically organized by Django when a user attaches an image during waste reporting on `/citizen/` or via AI Assistant `/ai/`.

### Configuration in `backend/smartwaste_project/settings.py`:
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = PROJECT_ROOT / 'media'
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB upload limit per image
```

### Why it is MANDATORY:
If `media/` is removed, any photo attached during waste reporting will raise `FileNotFoundError` / `PermissionError` on save, and images displayed in Complaint Detail views (`/complaints/<id>/`) and Admin Dashboard (`/admin-dashboard/`) will fail to render.

---

## 📦 2. Static Files Directory (`staticfiles/`)

### Purpose & Functionality
- **Location**: `staticfiles/` (configured as `STATIC_ROOT = PROJECT_ROOT / 'staticfiles'`).
- **URL Path**: `/static/` (configured as `STATIC_URL = '/static/'`).
- **Role**: Serves as the compiled production directory for all static web assets (CSS stylesheets, JavaScript files, CleanLoop SVG brand logos, favicons, social OpenGraph banner images).
- **Collection Source**: Configured via `STATICFILES_DIRS = [ PROJECT_ROOT / 'frontend' ]`.

### Production Deployment Workflow (AWS EC2 & Nginx):
When deploying to AWS EC2, the deployment script (`deployment/deploy.sh`) executes:
```bash
python backend/manage.py collectstatic --noinput
```
This gathers all assets from `frontend/` and compiles them into `staticfiles/`.

### Nginx Integration:
In production, Nginx bypasses Python/Gunicorn for static requests and directly serves `/static/` files from `staticfiles/` at native kernel speeds with HTTP caching headers:
```nginx
location /static/ {
    alias /home/ubuntu/spectrum/staticfiles/;
    expires 30d;
    add_header Cache-Control "public, no-transform";
}
```

### Why it is MANDATORY:
If `staticfiles/` is deleted, Nginx will fail to serve SVG logos (`cleanloop-mark.svg`), favicons, and CSS styles on the production domain (`https://cleanloop.sarthakml.in/`), causing 404 static asset errors.

---

## 🛡️ Git & Security Rules

1. **Upload Size Validation**: Restricted to a maximum of 5MB per upload (`FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880`).
2. **Git Ignore Configuration**:
   - `media/complaints/` is git-ignored to prevent test photo bloat in the git repository while keeping the directory structure intact.
   - `staticfiles/` is git-ignored because it is dynamically generated on target deployment environments during continuous integration/deployment (`collectstatic`).
