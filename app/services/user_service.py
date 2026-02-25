import logging
from app.schemas.user_schema import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password, create_access_token
from app.repository.user_repo import UserRepository
from app.models.user_model import UserRole
from app.core.exceptions import (
    UserAlreadyExistsException,
    InvalidCredentialsException,
    UserNotFoundException,
    UnauthorizedException,
)

logger = logging.getLogger(__name__)

class UserService:

    def __init__(self, repository: UserRepository):
        self.repository = repository
        
        
    def register_user(self, user_data: UserCreate):
        existing = self.repository.get_by_email(user_data.email)
        
        if existing:
            logger.warning(f"Registration attempt with existing email: {user_data.email}")
            raise UserAlreadyExistsException("Email already registered")

        hashed_pwd = hash_password(user_data.password)
        user = self.repository.create(user_data, hashed_pwd)
        logger.info(f"User registered successfully - ID: {user.id}, Email: {user_data.email}")
        return user


    def login_user(self, email: str, password: str):
        user = self.repository.get_by_email(email)

        if not user or not verify_password(password, user.hashed_password):
            logger.warning(f"Failed login attempt for email: {email}")
            raise InvalidCredentialsException("Invalid credentials")

        token = create_access_token(user)
        logger.info(f"User logged in successfully - ID: {user.id}, Email: {email}")
        return {"access_token": token, "token_type": "bearer"}


    def get_all_users(self):
        return self.repository.get_all()


    def get_user_by_id(self, user_id: int, current_user):
        user = self.repository.get_by_id(user_id)
        if not user:
            logger.warning(f"Get user attempt for non-existent user: {user_id}")
            raise UserNotFoundException("User not found")

        if current_user.role != UserRole.admin and current_user.id != user_id:
            logger.warning(f"Unauthorized user access attempt: user {current_user.id} tried to access user {user_id}")
            raise UnauthorizedException("Not authorized")

        logger.info(f"User {user_id} retrieved by user {current_user.id}")
        return user


    def update_user(self, user_id: int, update_data: UserUpdate, current_user):
        user = self.repository.get_by_id(user_id)
        if not user:
            logger.warning(f"Update attempt for non-existent user: {user_id}")
            raise UserNotFoundException("User not found")

        if current_user.role != UserRole.admin and current_user.id != user_id:
            logger.warning(f"Unauthorized user update attempt: user {current_user.id} tried to update user {user_id}")
            raise UnauthorizedException("Not authorized")

        updated_user = self.repository.update(user, update_data.model_dump(exclude_unset=True))
        logger.info(f"User {user_id} updated by user {current_user.id}")
        return updated_user


    def delete_user(self, user_id: int):
        user = self.repository.get_by_id(user_id)
        if not user:
            logger.warning(f"Delete attempt for non-existent user: {user_id}")
            raise UserNotFoundException("User not found")

        self.repository.delete(user)
        logger.info(f"User deleted successfully - ID: {user_id}")