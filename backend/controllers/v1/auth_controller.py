from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db
from models.user import User
from auth.schemas import UserLogin, Token, UserResponse, UserCreate
from services.auth_service import AuthService, ACCESS_TOKEN_EXPIRE_MINUTES
from repositories.user_repository import UserRepository
from auth.dependencies import get_current_user

class AuthController:
    """Controller for authentication-related endpoints"""
    
    def __init__(self):
        self.router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
        self._register_routes()
    
    def _register_routes(self):
        """Register all auth routes"""
        self.router.add_api_route(
            "/login", 
            self.login, 
            methods=["POST"], 
            response_model=Token,
            summary="User Login",
            description="Authenticate user with username and password to get JWT token",
            responses={
                200: {"description": "Login successful, returns JWT token"},
                401: {"description": "Invalid credentials"},
                400: {"description": "User account is disabled"}
            }
        )
        self.router.add_api_route(
            "/register", 
            self.register, 
            methods=["POST"], 
            response_model=UserResponse,
            summary="User Registration",
            description="Register a new user account",
            responses={
                200: {"description": "User registered successfully"},
                400: {"description": "Username or email already exists"}
            }
        )
        self.router.add_api_route(
            "/me", 
            self.get_current_user_info, 
            methods=["GET"], 
            response_model=UserResponse,
            summary="Get Current User",
            description="Get information about the currently authenticated user",
            responses={
                200: {"description": "User information retrieved successfully"},
                401: {"description": "Not authenticated"}
            }
        )
        self.router.add_api_route(
            "/verify", 
            self.verify_token, 
            methods=["GET"],
            summary="Verify Token",
            description="Verify if the provided JWT token is valid",
            responses={
                200: {"description": "Token is valid"},
                401: {"description": "Token is invalid or expired"}
            }
        )
    
    async def login(self, user_credentials: UserLogin, db: Session = Depends(get_db)):
        """Login endpoint to authenticate user and return JWT token"""
        user_repository = UserRepository(db)
        user = AuthService.authenticate_user(user_repository, user_credentials.username, user_credentials.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if user.is_active is not True:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is disabled"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": user.username, "role": user.role}, 
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
            "user": UserResponse.model_validate(user)
        }

    async def register(self, user_data: UserCreate, db: Session = Depends(get_db)):
        """Register a new user"""
        user_repository = UserRepository(db)
        
        # Check if username already exists
        if user_repository.exists_by_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists (if provided)
        if user_data.email and user_repository.exists_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = AuthService.hash_password(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            role=user_data.role
        )
        
        created_user = user_repository.create(new_user)
        return UserResponse.model_validate(created_user)

    async def get_current_user_info(self, current_user: User = Depends(get_current_user)):
        """Get current authenticated user information"""
        return UserResponse.model_validate(current_user)

    async def verify_token(self, current_user: User = Depends(get_current_user)):
        """Verify if token is valid"""
        return {"valid": True, "username": current_user.username, "role": current_user.role}
