# Plugin-Backend Authentication Integration Analysis

## Current Architecture Overview

### Backend Authentication System
The backend has a complete JWT-based authentication system:
- **FastAPI** with clean architecture (controllers, services, repositories)
- **JWT tokens** with 24-hour expiration
- **User roles**: admin, user, business_admin, business_user
- **Business association**: Users can be linked to business entities
- **Password reset** with OTP via email
- **Database models**: User, Business, PasswordResetOTP

### Zoho Plugin Structure  
The current plugin is minimal:
- **Zoho Books widget** in invoice.creation.sidebar location
- **Basic HTML/JS** with ZFAPPS SDK integration
- **Development server** with HTTPS support
- **Manifest configuration** for Finance service

## Authentication Challenge

### The Problem
The plugin runs inside Zoho Books (iframe/widget context) and needs to authenticate users with the external backend API. This creates several challenges:

1. **Cross-Origin Requests**: Plugin → Backend API calls
2. **Token Storage**: Secure JWT storage in widget context
3. **User Experience**: Seamless login without leaving Zoho interface
4. **Session Management**: Token refresh and expiration handling
5. **Business Context**: Linking Zoho org to backend business

## Solution Architecture

### 1. Plugin-Side Authentication Flow

```javascript
// In plugin widget (widget.html + extension.js)
class AuthenticationManager {
    constructor() {
        this.apiBaseUrl = 'https://your-backend.com/api/v1';
        this.token = localStorage.getItem('ebm_jwt_token');
    }
    
    async login(username, password) {
        const response = await this.makeApiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        
        if (response.access_token) {
            this.token = response.access_token;
            localStorage.setItem('ebm_jwt_token', this.token);
            return response.user;
        }
        throw new Error('Login failed');
    }
    
    async makeApiRequest(endpoint, options = {}) {
        const url = `${this.apiBaseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        const response = await fetch(url, {
            ...options,
            headers
        });
        
        if (response.status === 401) {
            // Token expired, redirect to login
            this.logout();
            throw new Error('Authentication required');
        }
        
        return response.json();
    }
    
    logout() {
        this.token = null;
        localStorage.removeItem('ebm_jwt_token');
        this.showLoginForm();
    }
    
    isAuthenticated() {
        return !!this.token;
    }
}
```

### 2. Backend Modifications Needed

#### A. CORS Configuration
```python
# main.py - Update CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://books.zoho.com",
        "https://books.zoho.eu", 
        "https://books.zoho.in",
        "https://127.0.0.1:5000",  # Local development
        "https://localhost:5000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

#### B. Business-Plugin Association Endpoint
```python
# controllers/v1/auth_controller.py - Add new endpoint
async def associate_zoho_business(
    self, 
    zoho_org_id: str,
    business_data: BusinessAssociationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Associate Zoho organization with business"""
    business_repo = BusinessRepository(db)
    
    # Find or create business
    business = business_repo.get_by_zoho_org_id(zoho_org_id)
    if not business:
        business = business_repo.create_from_zoho_data(zoho_org_id, business_data)
    
    # Associate user with business
    user_repo = UserRepository(db)
    user_repo.update_business_association(current_user.id, business.id)
    
    return {"message": "Business associated successfully", "business_id": business.id}
```

### 3. Plugin UI Integration

#### A. Login Form Component
```html
<!-- widget.html - Add login UI -->
<div id="auth-container">
    <!-- Login Form -->
    <div id="login-form" style="display: none;">
        <h3>EBM Service Login</h3>
        <form id="loginForm">
            <input type="text" id="username" placeholder="Username" required>
            <input type="password" id="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <div id="login-error" class="error"></div>
    </div>
    
    <!-- Main Plugin Interface -->
    <div id="main-interface" style="display: none;">
        <div id="user-info">
            Logged in as: <span id="current-username"></span>
            <button id="logout-btn">Logout</button>
        </div>
        <div id="plugin-content">
            <!-- Main plugin functionality here -->
        </div>
    </div>
</div>
```

#### B. Business Setup Integration
```javascript
// extension.js - Business setup
class BusinessSetupManager {
    constructor(authManager) {
        this.auth = authManager;
    }
    
    async initializeBusinessSetup() {
        // Get Zoho organization data
        const zohoBooksData = await ZFAPPS.get('organization');
        const orgId = zohoBooksData.organization.organization_id;
        
        // Check if business already exists
        try {
            const business = await this.auth.makeApiRequest(`/business/by-zoho-org/${orgId}`);
            return business;
        } catch (error) {
            // Business doesn't exist, create it
            return this.createBusinessFromZohoData(orgId, zohoBooksData.organization);
        }
    }
    
    async createBusinessFromZohoData(zohoOrgId, zohoOrg) {
        const businessData = {
            business_name: zohoOrg.name,
            email: zohoOrg.email,
            location: zohoOrg.address,
            phone_number: zohoOrg.phone,
            zoho_organization_id: zohoOrgId
        };
        
        return this.auth.makeApiRequest('/business/create-from-zoho', {
            method: 'POST',
            body: JSON.stringify(businessData)
        });
    }
}
```

### 4. Complete Plugin Initialization Flow

```javascript
// extension.js - Main initialization
class EBMPlugin {
    constructor() {
        this.auth = new AuthenticationManager();
        this.businessSetup = new BusinessSetupManager(this.auth);
        this.init();
    }
    
    async init() {
        // Initialize Zoho SDK
        await ZFAPPS.extension.init();
        
        // Check authentication status
        if (this.auth.isAuthenticated()) {
            try {
                // Verify token is still valid
                await this.auth.makeApiRequest('/auth/verify');
                await this.showMainInterface();
            } catch (error) {
                this.showLoginForm();
            }
        } else {
            this.showLoginForm();
        }
    }
    
    showLoginForm() {
        document.getElementById('login-form').style.display = 'block';
        document.getElementById('main-interface').style.display = 'none';
        
        document.getElementById('loginForm').onsubmit = async (e) => {
            e.preventDefault();
            try {
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                
                const user = await this.auth.login(username, password);
                await this.showMainInterface();
            } catch (error) {
                document.getElementById('login-error').textContent = error.message;
            }
        };
    }
    
    async showMainInterface() {
        // Hide login, show main interface
        document.getElementById('login-form').style.display = 'none';
        document.getElementById('main-interface').style.display = 'block';
        
        // Initialize business setup
        await this.businessSetup.initializeBusinessSetup();
        
        // Set up logout handler
        document.getElementById('logout-btn').onclick = () => {
            this.auth.logout();
        };
        
        // Initialize main plugin functionality
        await this.initializeMainFeatures();
    }
    
    async initializeMainFeatures() {
        // Set up invoice monitoring, EBM generation, etc.
        // This is where the existing EBM functionality would go
    }
}

// Initialize plugin when page loads
window.onload = () => {
    new EBMPlugin();
};
```

## Security Considerations

### 1. Token Storage
- Use `localStorage` for JWT tokens (acceptable for Zoho widget context)
- Consider token encryption for sensitive environments
- Implement automatic token refresh before expiration

### 2. CORS and CSP
- Configure backend CORS to allow Zoho domains
- Update plugin manifest with required connect-src domains
- Handle CSP restrictions in Zoho environment

### 3. Authentication State
- Implement proper token validation
- Handle network failures gracefully
- Provide clear error messages to users

## Implementation Steps

### Phase 1: Backend API Updates
1. ✅ Authentication system is already complete
2. Add CORS configuration for Zoho domains
3. Create business association endpoints
4. Add Zoho organization integration

### Phase 2: Plugin Authentication UI
1. Create login form in widget.html
2. Implement AuthenticationManager class
3. Add error handling and validation
4. Test authentication flow

### Phase 3: Business Integration
1. Implement BusinessSetupManager
2. Create Zoho → Backend business mapping
3. Handle business profile synchronization
4. Test complete setup flow

### Phase 4: Main Features Integration
1. Connect existing EBM functionality
2. Add authenticated API calls
3. Implement status monitoring
4. Add user-specific features

## Current Status Assessment

### ✅ Ready Components
- Backend JWT authentication system
- User and Business models
- FastAPI clean architecture
- Basic plugin structure

### 🔨 Needs Implementation
- Plugin authentication UI
- CORS configuration updates
- Business association logic
- Frontend JavaScript authentication manager

### 🧪 Needs Testing
- Cross-origin authentication flow
- Token management in widget context
- Business setup automation
- Error handling scenarios

## Next Steps

1. **Start with CORS**: Update backend CORS to allow Zoho domains
2. **Plugin Auth UI**: Implement basic login form and authentication manager
3. **Business Integration**: Create business association endpoints
4. **Testing**: Test authentication flow in Zoho environment
5. **Feature Integration**: Connect to existing EBM functionality

This architecture provides a solid foundation for seamless user authentication from the Zoho plugin to the backend API while maintaining security best practices.