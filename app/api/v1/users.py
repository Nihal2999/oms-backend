from fastapi import APIRouter, Depends
from app.services.user_service import UserService
from app.schemas.user_schema import UserCreate, UserResponse, UserUpdate
from app.models.user_model import User
from app.db.database import get_db
from app.repository.user_repo import UserRepository
from app.core.security import get_current_user, get_admin_user
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service(db = Depends(get_db)):
    return UserService(UserRepository(db))


@router.get("/", response_model=list[UserResponse])
def get_users(
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_admin_user)
):
    return service.get_all_users()


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


@router.post("/register", response_model=UserResponse)
def register_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service),
):
    return service.register_user(user)


@router.post("/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service),
):
    return service.login_user(form_data.username, form_data.password)