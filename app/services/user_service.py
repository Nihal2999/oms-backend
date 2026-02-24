from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password, create_access_token
from app.repository.user import UserRepository
from app.core.exceptions import (
    UserAlreadyExistsException,
    InvalidCredentialsException,
    UserNotFoundException,
    UnauthorizedException,
)


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def get_all_users(self):
        return self.repository.get_all()

    def get_user_by_id(self, user_id: int, current_user):
        user = self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundException("User not found")

        if current_user.role != "admin" and current_user.id != user_id:
            raise UnauthorizedException("Not authorized")

        return user

    def register_user(self, user_data: UserCreate):
        existing = self.repository.get_by_email(user_data.email)
        if existing:
            raise UserAlreadyExistsException("Email already registered")

        hashed_pwd = hash_password(user_data.password)
        return self.repository.create(user_data, hashed_pwd)

    def login_user(self, email: str, password: str):
        user = self.repository.get_by_email(email)

        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException("Invalid credentials")

        token = create_access_token(
            data={"sub": str(user.id), "role": user.role}
        )

        return {"access_token": token, "token_type": "bearer"}

    def update_user(self, user_id: int, update_data: UserUpdate, current_user):
        user = self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundException("User not found")

        if current_user.role != "admin" and current_user.id != user_id:
            raise UnauthorizedException("Not authorized")

        return self.repository.update(user, update_data.model_dump(exclude_unset=True))

    def delete_user(self, user_id: int):
        user = self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundException("User not found")

        self.repository.delete(user)