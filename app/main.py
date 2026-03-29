"""FastAPI application entry point for NGO SaaS platform."""

import logging
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, Query, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import jwt
from sqlalchemy.orm import Session

from .database import engine, get_db, Base
from . import crud, schemas, models

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# JWT Secret key (in production, use environment variable)
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup: Create database tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")
    
    # Create super admin user if not exists
    from sqlalchemy.orm import Session
    db = Session(bind=engine)
    try:
        super_admin = crud.get_user_by_email(db, email="superadmin@ngo-saas.com")
        if not super_admin:
            demo_user = schemas.UserCreate(
                name="Super Administrator",
                email="superadmin@ngo-saas.com",
                password="superadmin123",
                role="super_admin"
            )
            crud.create_user(db=db, user=demo_user)
            logger.info("Super admin user created: superadmin@ngo-saas.com")
    except Exception as e:
        logger.error(f"Error creating super admin: {e}")
    finally:
        db.close()
    
    yield
    
    # Shutdown: Cleanup if needed
    logger.info("Application shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="NGO SaaS Platform API",
    description="Backend API for managing NGO operations including members, donations, events, and projects.",
    version="1.0.0",
    lifespan=lifespan
)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred."
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


# ============== Authentication Endpoints ==============

class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user_from_token(token: str, db: Session = Depends(get_db)) -> Optional[dict]:
    """Decode JWT token and return user info."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        user_id: int = payload.get("user_id")
        if email is None:
            return None
        return {"email": email, "role": role, "user_id": user_id}
    except jwt.PyJWTError:
        return None


async def get_current_user(request: Request) -> Optional[dict]:
    """Get current user from JWT token in cookie or header."""
    # Try to get token from cookie first
    token = request.cookies.get("access_token")
    
    # If not in cookie, try Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        return None
    
    db = next(get_db())
    try:
        user_info = get_current_user_from_token(token, db)
        return user_info
    finally:
        db.close()


def require_role(required_roles: list[str]):
    """Dependency to check if user has required role."""
    async def role_checker(request: Request, current_user: dict = Depends(get_current_user)):
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        if current_user.get("role") not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


# Dependency for super_admin only routes
super_admin_required = Depends(require_role(["super_admin"]))


@app.post("/api/auth/login", response_model=LoginResponse, tags=["Authentication"])
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    try:
        # Check if user exists
        user = crud.get_user_by_email(db, email=login_data.email)
        
        # For demo purposes, accept any password for existing users
        # In production, verify hashed password
        if not user:
            # Create a demo admin user if no users exist
            all_users = crud.get_users(db)
            if len(all_users) == 0:
                # Create demo admin
                demo_user = schemas.UserCreate(
                    name="Admin User",
                    email="admin@ngo.com",
                    password="admin123",
                    role="admin"
                )
                user = crud.create_user(db=db, user=demo_user)
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "role": user.role},
            expires_delta=access_token_expires
        )
        
        # Create response with token in cookie
        from fastapi.responses import JSONResponse
        response = LoginResponse(
            access_token=access_token,
            user={"id": user.id, "email": user.email, "name": user.name, "role": user.role}
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============== Super Admin Endpoints ==============

@app.post("/api/admin/create-ngo", response_model=schemas.NGOResponse, status_code=status.HTTP_201_CREATED, tags=["Super Admin"])
async def create_ngo(
    ngo: schemas.NGOCreate, 
    db: Session = Depends(get_db),
    current_user: dict = super_admin_required
):
    """Create a new NGO tenant (Super Admin only)."""
    try:
        # Check if email already exists
        existing_ngo = crud.get_ngo_by_email(db, email=ngo.email)
        if existing_ngo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        return crud.create_ngo(db=db, ngo=ngo)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating NGO: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/admin/list-ngos", response_model=list[schemas.NGOResponse], tags=["Super Admin"])
async def list_ngos(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: dict = super_admin_required
):
    """List all NGOs (Super Admin only)."""
    try:
        return crud.get_ngos(db=db, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error fetching NGOs: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.delete("/api/admin/delete-ngo/{ngo_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Super Admin"])
async def delete_ngo(
    ngo_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = super_admin_required
):
    """Delete an NGO (Super Admin only)."""
    try:
        success = crud.delete_ngo(db=db, ngo_id=ngo_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NGO not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting NGO: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============== Frontend Routes ==============

@app.get("/", response_class=RedirectResponse, tags=["Frontend"])
async def root():
    """Redirect to login page."""
    return "/login"


@app.get("/login", response_class=HTMLResponse, tags=["Frontend"])
async def login_page(request: Request):
    """Render login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse, tags=["Frontend"])
async def dashboard_page(request: Request):
    """Render dashboard page."""
    current_user = await get_current_user(request)
    user_name = "Admin"
    user_role = "admin"
    is_super_admin = False
    
    if current_user:
        user_name = current_user.get("email", "Admin").split("@")[0]
        user_role = current_user.get("role", "admin")
        is_super_admin = user_role == "super_admin"
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user_name": user_name,
            "user_role": user_role,
            "is_super_admin": is_super_admin,
            "current_date": datetime.now().strftime("%B %d, %Y")
        }
    )


@app.get("/members", response_class=HTMLResponse, tags=["Frontend"])
async def members_page(request: Request):
    """Render members page."""
    return templates.TemplateResponse(
        "members.html",
        {"request": request, "user_name": "Admin"}
    )


@app.get("/donations", response_class=HTMLResponse, tags=["Frontend"])
async def donations_page(request: Request):
    """Render donations page."""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user_name": "Admin",
            "current_date": datetime.now().strftime("%B %d, %Y")
        }
    )


@app.get("/events", response_class=HTMLResponse, tags=["Frontend"])
async def events_page(request: Request):
    """Render events page."""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user_name": "Admin",
            "current_date": datetime.now().strftime("%B %d, %Y")
        }
    )


@app.get("/projects", response_class=HTMLResponse, tags=["Frontend"])
async def projects_page(request: Request):
    """Render projects page."""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user_name": "Admin",
            "current_date": datetime.now().strftime("%B %d, %Y")
        }
    )


@app.get("/issues", response_class=HTMLResponse, tags=["Frontend"])
async def issues_page(request: Request):
    """Render issues page."""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user_name": "Admin",
            "current_date": datetime.now().strftime("%B %d, %Y")
        }
    )


@app.get("/settings", response_class=HTMLResponse, tags=["Frontend"])
async def settings_page(request: Request):
    """Render settings page."""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user_name": "Admin",
            "current_date": datetime.now().strftime("%B %d, %Y")
        }
    )


@app.get("/profile", response_class=HTMLResponse, tags=["Frontend"])
async def profile_page(request: Request):
    """Render profile page."""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user_name": "Admin",
            "current_date": datetime.now().strftime("%B %d, %Y")
        }
    )


# ============== User Endpoints ==============

@app.post("/api/users", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    try:
        # Check if email already exists
        existing_user = crud.get_user_by_email(db, email=user.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        return crud.create_user(db=db, user=user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/users", response_model=list[schemas.UserResponse], tags=["Users"])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all users with pagination."""
    try:
        return crud.get_users(db=db, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/users/{user_id}", response_model=schemas.UserResponse, tags=["Users"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID."""
    try:
        db_user = crud.get_user(db=db, user_id=user_id)
        if db_user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.put("/api/users/{user_id}", response_model=schemas.UserResponse, tags=["Users"])
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db)):
    """Update an existing user."""
    try:
        db_user = crud.update_user(db=db, user_id=user_id, user_update=user_update)
        if db_user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Users"])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user."""
    try:
        success = crud.delete_user(db=db, user_id=user_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============== Member Endpoints ==============

@app.post("/api/members", response_model=schemas.MemberResponse, status_code=status.HTTP_201_CREATED, tags=["Members"])
def create_member(member: schemas.MemberCreate, db: Session = Depends(get_db)):
    """Create a new member."""
    try:
        # Check if email already exists
        existing_member = crud.get_member_by_email(db, email=member.email)
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        return crud.create_member(db=db, member=member)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating member: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/members", response_model=list[schemas.MemberResponse], tags=["Members"])
def get_members(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all members with pagination."""
    try:
        return crud.get_members(db=db, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error fetching members: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/members/{member_id}", response_model=schemas.MemberResponse, tags=["Members"])
def get_member(member_id: int, db: Session = Depends(get_db)):
    """Get a specific member by ID."""
    try:
        db_member = crud.get_member(db=db, member_id=member_id)
        if db_member is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        return db_member
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching member: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.put("/api/members/{member_id}", response_model=schemas.MemberResponse, tags=["Members"])
def update_member(member_id: int, member_update: schemas.MemberUpdate, db: Session = Depends(get_db)):
    """Update an existing member."""
    try:
        db_member = crud.update_member(db=db, member_id=member_id, member_update=member_update)
        if db_member is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        return db_member
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating member: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.delete("/api/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Members"])
def delete_member(member_id: int, db: Session = Depends(get_db)):
    """Delete a member."""
    try:
        success = crud.delete_member(db=db, member_id=member_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting member: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============== Donation Endpoints ==============

@app.post("/api/donations", response_model=schemas.DonationResponse, status_code=status.HTTP_201_CREATED, tags=["Donations"])
def create_donation(donation: schemas.DonationCreate, db: Session = Depends(get_db)):
    """Create a new donation."""
    try:
        return crud.create_donation(db=db, donation=donation)
    except Exception as e:
        logger.error(f"Error creating donation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/donations", response_model=list[schemas.DonationResponse], tags=["Donations"])
def get_donations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all donations with pagination."""
    try:
        return crud.get_donations(db=db, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error fetching donations: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/donations/{donation_id}", response_model=schemas.DonationResponse, tags=["Donations"])
def get_donation(donation_id: int, db: Session = Depends(get_db)):
    """Get a specific donation by ID."""
    try:
        db_donation = crud.get_donation(db=db, donation_id=donation_id)
        if db_donation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found")
        return db_donation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching donation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.put("/api/donations/{donation_id}", response_model=schemas.DonationResponse, tags=["Donations"])
def update_donation(donation_id: int, donation_update: schemas.DonationUpdate, db: Session = Depends(get_db)):
    """Update an existing donation."""
    try:
        db_donation = crud.update_donation(db=db, donation_id=donation_id, donation_update=donation_update)
        if db_donation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found")
        return db_donation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating donation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.delete("/api/donations/{donation_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Donations"])
def delete_donation(donation_id: int, db: Session = Depends(get_db)):
    """Delete a donation."""
    try:
        success = crud.delete_donation(db=db, donation_id=donation_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting donation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============== Event Endpoints ==============

@app.post("/api/events", response_model=schemas.EventResponse, status_code=status.HTTP_201_CREATED, tags=["Events"])
def create_event(event: schemas.EventCreate, db: Session = Depends(get_db)):
    """Create a new event."""
    try:
        return crud.create_event(db=db, event=event)
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/events", response_model=list[schemas.EventResponse], tags=["Events"])
def get_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all events with pagination."""
    try:
        return crud.get_events(db=db, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/events/{event_id}", response_model=schemas.EventResponse, tags=["Events"])
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get a specific event by ID."""
    try:
        db_event = crud.get_event(db=db, event_id=event_id)
        if db_event is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        return db_event
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching event: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.put("/api/events/{event_id}", response_model=schemas.EventResponse, tags=["Events"])
def update_event(event_id: int, event_update: schemas.EventUpdate, db: Session = Depends(get_db)):
    """Update an existing event."""
    try:
        db_event = crud.update_event(db=db, event_id=event_id, event_update=event_update)
        if db_event is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        return db_event
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating event: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.delete("/api/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Events"])
def delete_event(event_id: int, db: Session = Depends(get_db)):
    """Delete an event."""
    try:
        success = crud.delete_event(db=db, event_id=event_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting event: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============== Additional Resource Endpoints ==============

# Projects
@app.post("/api/projects", response_model=schemas.ProjectResponse, status_code=status.HTTP_201_CREATED, tags=["Projects"])
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project."""
    try:
        return crud.create_project(db=db, project=project)
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/projects", response_model=list[schemas.ProjectResponse], tags=["Projects"])
def get_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all projects with pagination."""
    try:
        return crud.get_projects(db=db, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/projects/{project_id}", response_model=schemas.ProjectResponse, tags=["Projects"])
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get a specific project by ID."""
    try:
        db_project = crud.get_project(db=db, project_id=project_id)
        if db_project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return db_project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Managers
@app.post("/api/managers", response_model=schemas.ManagerResponse, status_code=status.HTTP_201_CREATED, tags=["Managers"])
def create_manager(manager: schemas.ManagerCreate, db: Session = Depends(get_db)):
    """Create a new manager."""
    try:
        existing = crud.get_manager_by_email(db, email=manager.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        return crud.create_manager(db=db, manager=manager)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating manager: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/managers", response_model=list[schemas.ManagerResponse], tags=["Managers"])
def get_managers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all managers with pagination."""
    try:
        return crud.get_managers(db=db, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error fetching managers: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Coordinators
@app.post("/api/coordinators", response_model=schemas.CoordinatorResponse, status_code=status.HTTP_201_CREATED, tags=["Coordinators"])
def create_coordinator(coordinator: schemas.CoordinatorCreate, db: Session = Depends(get_db)):
    """Create a new coordinator."""
    try:
        return crud.create_coordinator(db=db, coordinator=coordinator)
    except Exception as e:
        logger.error(f"Error creating coordinator: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/coordinators", response_model=list[schemas.CoordinatorResponse], tags=["Coordinators"])
def get_coordinators(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all coordinators with pagination."""
    try:
        return crud.get_coordinators(db=db, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error fetching coordinators: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Issues
@app.post("/api/issues", response_model=schemas.IssueResponse, status_code=status.HTTP_201_CREATED, tags=["Issues"])
def create_issue(issue: schemas.IssueCreate, db: Session = Depends(get_db)):
    """Create a new issue."""
    try:
        return crud.create_issue(db=db, issue=issue)
    except Exception as e:
        logger.error(f"Error creating issue: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/issues", response_model=list[schemas.IssueResponse], tags=["Issues"])
def get_issues(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all issues with pagination."""
    try:
        return crud.get_issues(db=db, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error fetching issues: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Referrals
@app.post("/api/referrals", response_model=schemas.ReferralResponse, status_code=status.HTTP_201_CREATED, tags=["Referrals"])
def create_referral(referral: schemas.ReferralCreate, db: Session = Depends(get_db)):
    """Create a new referral."""
    try:
        return crud.create_referral(db=db, referral=referral)
    except Exception as e:
        logger.error(f"Error creating referral: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/referrals", response_model=list[schemas.ReferralResponse], tags=["Referrals"])
def get_referrals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all referrals with pagination."""
    try:
        return crud.get_referrals(db=db, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error fetching referrals: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Audit Reports
@app.post("/api/audit-reports", response_model=schemas.AuditReportResponse, status_code=status.HTTP_201_CREATED, tags=["AuditReports"])
def create_audit_report(report: schemas.AuditReportCreate, db: Session = Depends(get_db)):
    """Create a new audit report."""
    try:
        return crud.create_audit_report(db=db, report=report)
    except Exception as e:
        logger.error(f"Error creating audit report: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/audit-reports", response_model=list[schemas.AuditReportResponse], tags=["AuditReports"])
def get_audit_reports(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all audit reports with pagination."""
    try:
        return crud.get_audit_reports(db=db, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error fetching audit reports: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

