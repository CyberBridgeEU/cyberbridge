# Authentication Architecture - Global Middleware Pattern

## 🏗️ Architecture Overview

This application uses **Global Middleware Authentication** - an enterprise-grade pattern where authentication runs automatically on ALL routes.

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                     Incoming Request                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    CORS Middleware                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              🔐 AUTH MIDDLEWARE (Global)                     │
│                                                              │
│  1. Is route public? → Allow                                │
│  2. Has JWT token?   → Set principal.type = "user"          │
│  3. Has API key?     → Set principal.type = "service"       │
│  4. Neither?         → Reject 401                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  request.state.principal                     │
│  {                                                           │
│    "type": "user" or "service",                             │
│    "user": User object,                                      │
│    "user_id": "uuid",                                        │
│    "email": "user@example.com",                             │
│    "role": "admin" or "user",                               │
│    "auth_method": "jwt" or "api_key"                        │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Your Endpoint Logic                       │
│                                                              │
│  @app.post("/scan")                                         │
│  async def scan(request: Request):                          │
│      principal = get_principal(request)                     │
│      if principal["type"] == "user":                        │
│          # Human user via web UI                            │
│      else:  # "service"                                     │
│          # Automated service via API                        │
└─────────────────────────────────────────────────────────────┘
```

## 🔑 Principal Types

### Type: "user" (Human Users)
- **Authentication**: JWT Bearer token
- **Source**: Web UI, mobile app, interactive sessions
- **Use Case**: Manual scans, dashboard usage, configuration
- **Expiration**: 15 minutes (access token), 7 days (refresh token)

**Example:**
```json
{
  "type": "user",
  "user": <User object>,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john@example.com",
  "role": "admin",
  "auth_method": "jwt"
}
```

### Type: "service" (Automated Services)
- **Authentication**: API Key (X-API-Key header)
- **Source**: Scripts, CI/CD, automation tools, integrations
- **Use Case**: Scheduled scans, batch processing, integrations
- **Expiration**: Custom (or never expires)

**Example:**
```json
{
  "type": "service",
  "user": <User object>,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "automation@example.com",
  "role": "user",
  "auth_method": "api_key"
}
```

## 📋 Public Routes (No Authentication Required)

The following routes are accessible without authentication:

```python
PUBLIC_ROUTES = {
    "/auth/login",      # Login to get JWT token
    "/auth/register",   # Register new user (admin only internally)
    "/auth/refresh",    # Refresh JWT token
    "/auth/info",       # Get authentication configuration
    "/health",          # Health check
    "/docs",            # OpenAPI documentation
    "/redoc",           # ReDoc documentation
    "/openapi.json",    # OpenAPI schema
}
```

## 🔒 Protected Routes (All Others)

**All other routes** automatically require authentication via:
- JWT Bearer token (Authorization: Bearer <token>), OR
- API Key (X-API-Key: <key>)

Examples:
- `/scan` - Create new scan
- `/scans` - List scans
- `/scan/json/{scan_id}` - Get scan status
- `/download/pdf/{scan_id}` - Download report
- `/api-keys/*` - Manage API keys
- `/users/*` - User management (admin only)

## 💻 Implementation Details

### 1. Middleware Location
```
backend/app/middleware/auth_middleware.py
```

### 2. Registration in main.py
```python
from app.middleware.auth_middleware import AuthMiddleware

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, ...)  # First
app.add_middleware(AuthMiddleware)       # Second (order matters!)
```

### 3. Accessing Principal in Endpoints

**Method 1: Get full principal object**
```python
from app.api.deps import get_principal

@app.post("/scan")
async def scan(request: Request):
    principal = get_principal(request)
    
    # Access principal data
    user = principal["user"]
    auth_type = principal["type"]  # "user" or "service"
    email = principal["email"]
    
    # Different logging based on type
    if auth_type == "user":
        logger.info(f"👤 User {email} started scan")
    else:
        logger.info(f"🤖 Service {email} started automated scan")
```

**Method 2: Get just the user (simplified)**
```python
from app.api.deps import get_current_user_from_principal

@app.post("/scan")
async def scan(user: User = Depends(get_current_user_from_principal)):
    # user is already loaded, ready to use
    logger.info(f"Scan by {user.email}")
```

## 🎯 Use Cases & Examples

### Use Case 1: Different Behavior for Users vs Services

```python
@app.post("/scan")
async def scan(request: Request, keyword: str):
    principal = get_principal(request)
    
    if principal["type"] == "user":
        # User from web UI - send real-time notifications
        notify_websocket(principal["user_id"], "Scan started")
    else:  # service
        # Automated service - just log
        logger.info(f"Automated scan: {keyword}")
    
    # Continue with scan logic...
```

### Use Case 2: Audit Logging

```python
@app.delete("/users/{user_id}")
async def delete_user(request: Request, user_id: str):
    principal = get_principal(request)
    
    # Log who deleted what
    audit_log.create({
        "action": "DELETE_USER",
        "target": user_id,
        "performed_by": principal["email"],
        "principal_type": principal["type"],  # user or service
        "auth_method": principal["auth_method"],  # jwt or api_key
        "timestamp": datetime.utcnow()
    })
    
    # Perform deletion...
```

### Use Case 3: Rate Limiting

```python
@app.post("/scan")
async def scan(request: Request):
    principal = get_principal(request)
    
    # Different rate limits for users vs services
    if principal["type"] == "user":
        limit = 10  # 10 scans per hour for users
    else:  # service
        limit = 100  # 100 scans per hour for services
    
    check_rate_limit(principal["user_id"], limit)
```

## 🔧 Configuration

### JWT Token Expiration

Edit `backend/app/core/config.py`:

```python
class Settings(BaseSettings):
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # JWT expires in 15 min
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7     # Refresh valid for 7 days
```

### Add/Remove Public Routes

Edit `backend/app/middleware/auth_middleware.py`:

```python
class AuthMiddleware(BaseHTTPMiddleware):
    PUBLIC_ROUTES = {
        "/auth/login",
        "/health",
        "/your-new-public-route",  # Add here
    }
```

## 📊 Logging & Monitoring

The middleware automatically logs all authentication attempts:

**Successful JWT:**
```
✅ JWT Auth: admin@example.com (type=user) → POST /scan
```

**Successful API Key:**
```
✅ API Key Auth: automation@example.com (type=service) → POST /scan
```

**Failed:**
```
❌ Unauthorized: POST /scan (no valid JWT or API key)
```

## 🧪 Testing

### Test with JWT:
```bash
# Login
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Use token (marked as type="user")
curl http://localhost:8001/scans \
  -H "Authorization: Bearer <token>"
```

### Test with API Key:
```bash
# Use API key (marked as type="service")
curl http://localhost:8001/scans \
  -H "X-API-Key: dk_prod_AbCdEfGhIjKlMn..."
```

### Test Authentication Test Script:
```bash
cd backend
python test_authentication.py
```

## 🎓 Benefits of This Architecture

1. **Automatic Protection**: All routes protected by default
2. **Principal Tracking**: Know if request is from user or service
3. **Centralized Logic**: All auth code in one place
4. **Better Auditing**: Track human vs automated actions
5. **Enterprise Pattern**: Used by major platforms (AWS, Google Cloud, etc.)
6. **Flexible**: Easy to add new auth methods
7. **No Boilerplate**: Don't need `Depends()` on every endpoint

## 🔐 Security Best Practices

1. **JWT Tokens** (for users):
   - ✅ Short expiration (15 minutes)
   - ✅ Auto-refresh on frontend
   - ✅ Revocable via logout

2. **API Keys** (for services):
   - ✅ Set expiration dates
   - ✅ One key per service/integration
   - ✅ Rotate periodically
   - ✅ Revoke immediately if compromised

3. **General**:
   - ✅ All routes protected by default
   - ✅ Different tracking for users vs services
   - ✅ Comprehensive audit logging
   - ✅ HTTPS only in production

## 🚀 Migration from Dependency Injection

If you had old code like this:

```python
# OLD (dependency injection per endpoint)
@app.post("/scan")
async def scan(current_user: User = Depends(get_current_user)):
    logger.info(f"Scan by {current_user.email}")
```

Now it's:

```python
# NEW (global middleware)
@app.post("/scan")
async def scan(request: Request):
    principal = get_principal(request)
    user = principal["user"]
    
    if principal["type"] == "user":
        logger.info(f"👤 User scan by {user.email}")
    else:
        logger.info(f"🤖 Service scan by {user.email}")
```

---

**This architecture is production-ready and follows industry best practices used by major platforms!**
