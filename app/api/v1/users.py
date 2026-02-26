from fastapi import APIRouter, Depends, Query, BackgroundTasks
from app.services.user_service import UserService
from app.schemas.user_schema import UserCreate, UserResponse, UserUpdate, TokenResponse, RefreshRequest
from app.models.user_model import User
from app.db.database import get_db
from app.repository.user_repo import UserRepository
from app.core.security import get_current_user, get_admin_user
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.pagination import PaginatedResponse
from app.core.background_tasks import log_user_registered

router = APIRouter(prefix="/users", tags=["Users"])

def get_user_service(db = Depends(get_db)):
    return UserService(UserRepository(db))


@router.post("/register", response_model=UserResponse)
def register_user(
    user: UserCreate,
    background_tasks: BackgroundTasks,
    service: UserService = Depends(get_user_service),
):
    result = service.register_user(user)
    background_tasks.add_task(log_user_registered, result.id, result.email)
    return result


@router.post("/login", response_model=TokenResponse)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service),
):
    return service.login_user(form_data.username, form_data.password)


@router.post("/refresh")
def refresh_token(
    request: RefreshRequest,
    service: UserService = Depends(get_user_service),
):
    return service.refresh_token(request.refresh_token)


@router.post("/logout")
def logout_user(
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    service.logout_user(current_user.id)
    return {"message": "Logged out successfully"}


@router.get("/", response_model=PaginatedResponse[UserResponse])
def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_admin_user)
):
    return service.get_all_users(page, limit)


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    return service.get_user_by_id(user_id, current_user)


@router.put("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_admin_user),  # only admin can change roles
):
    return service.update_user_role(user_id)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    return service.update_user(user_id, user, current_user)


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_admin_user),
):
    service.delete_user(user_id)
    return {"message": "User deleted successfully"}