import logging
from jose import JWTError, jwt
from app.schemas.pagination import PaginatedResponse
from app.schemas.user_schema import UserCreate, UserUpdate
from app.core.security import create_refresh_token, hash_password, verify_password, create_access_token
from app.repository.user_repo import UserRepository
from app.models.user_model import UserRole
from app.core.config import settings
from app.core.exceptions import UserAlreadyExistsException, InvalidCredentialsException, UserNotFoundException, UnauthorizedException

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
        access_token = create_access_token(user)
        refresh_token = create_refresh_token(user)
        self.repository.update(user, {"refresh_token": refresh_token})
        logger.info(f"User logged in successfully - ID: {user.id}, Email: {email}")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }


    def refresh_token(self, refresh_token: str):
        credentials_exception = InvalidCredentialsException("Invalid or expired refresh token")
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            token_type: str = payload.get("type")
            if user_id is None or token_type != "refresh":
                raise credentials_exception
        except (JWTError, ValueError, TypeError):
            raise credentials_exception
        user = self.repository.get_by_id(int(user_id))
        if not user or user.refresh_token != refresh_token:
            raise credentials_exception
        new_access_token = create_access_token(user)
        logger.info(f"Access token refreshed - UserID: {user.id}")
        return {"access_token": new_access_token, "token_type": "bearer"}


    def logout_user(self, user_id: int):
        user = self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundException("User not found")
        self.repository.update(user, {"refresh_token": None})
        logger.info(f"User logged out - ID: {user_id}")


    def get_all_users(self, page: int, limit: int):
        skip = (page - 1) * limit
        data = self.repository.get_all(skip, limit)
        total = self.repository.count_all()
        return PaginatedResponse.create(data, total, page, limit)


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
    
    
    def update_user_role(self, user_id: int):
        user = self.repository.get_by_id(user_id)
        if not user:
            logger.warning(f"Role update attempt for non-existent user: {user_id}")
            raise UserNotFoundException("User not found")
        new_role = UserRole.admin if user.role == UserRole.user else UserRole.user
        updated_user = self.repository.update(user, {"role": new_role})
        logger.info(f"User role updated - ID: {user_id}, New Role: {new_role.value}")
        return updated_user


    def delete_user(self, user_id: int):
        user = self.repository.get_by_id(user_id)
        if not user:
            logger.warning(f"Delete attempt for non-existent user: {user_id}")
            raise UserNotFoundException("User not found")
        self.repository.delete(user)
        logger.info(f"User deleted successfully - ID: {user_id}")