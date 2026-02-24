from sqlalchemy.orm import Session
from app.models.user_model import User
from app.schemas.user_schema import UserCreate

class UserRepository:

    def __init__(self, db: Session):
        self.db = db


    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()


    def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()


    def create(self, user_data: UserCreate, hashed_password: str) -> User:
        user = User(
            name=user_data.name,
            email=user_data.email,
            hashed_password=hashed_password
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user


    def update(self, user: User, update_data: dict) -> User:
        for key, value in update_data.items():
            setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)
        return user


    def get_all(self) -> list[User]:
        return self.db.query(User).all()


    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()