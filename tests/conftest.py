import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from decimal import Decimal
from app.main import app
from app.db.database import Base, get_db
from app.models.user_model import User, UserRole
from app.models.product_model import Product
from app.models.order_model import Order, OrderStatus
from app.core.security import hash_password, create_access_token


@pytest.fixture(scope="session")
def database():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable foreign key constraints in SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine


@pytest.fixture(scope="session")
def db_session_local(database):
    return sessionmaker(autocommit=False, autoflush=False, bind=database)


@pytest.fixture
def db(db_session_local):
    session = db_session_local()
    yield session

    # Clean up all data after the test
    # Delete in reverse order of relationships to avoid FK constraints
    session.query(Order).delete()
    session.query(Product).delete()
    session.query(User).delete()
    session.commit()
    session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db) -> User:
    user = User(
        name="Admin User",
        email="admin@example.com",
        hashed_password=hash_password("AdminPass123"),
        role=UserRole.admin,
        phone="+1234567890"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def regular_user(db) -> User:
    user = User(
        name="John Doe",
        email="john@example.com",
        hashed_password=hash_password("Password123"),
        role=UserRole.user,
        phone="+0987654321"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def another_user(db) -> User:
    user = User(
        name="Jane Smith",
        email="jane@example.com",
        hashed_password=hash_password("Password456"),
        role=UserRole.user,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def product_in_stock(db) -> Product:
    product = Product(
        name="Laptop",
        description="High-performance laptop",
        price=Decimal("999.99"),
        stock=10,
        is_deleted=False
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@pytest.fixture
def product_low_stock(db) -> Product:
    product = Product(
        name="Mouse",
        description="Wireless mouse",
        price=Decimal("29.99"),
        stock=2,
        is_deleted=False
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@pytest.fixture
def product_out_of_stock(db) -> Product:
    product = Product(
        name="Keyboard",
        description="Mechanical keyboard",
        price=Decimal("129.99"),
        stock=0,
        is_deleted=False
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@pytest.fixture
def deleted_product(db) -> Product:
    product = Product(
        name="Deleted Product",
        description="This product is deleted",
        price=Decimal("50.00"),
        stock=5,
        is_deleted=True
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@pytest.fixture
def pending_order(db, regular_user, product_in_stock) -> Order:
    order = Order(
        user_id=regular_user.id,
        product_id=product_in_stock.id,
        quantity=2,
        status=OrderStatus.pending
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@pytest.fixture
def shipped_order(db, regular_user, product_in_stock) -> Order:
    order = Order(
        user_id=regular_user.id,
        product_id=product_in_stock.id,
        quantity=1,
        status=OrderStatus.shipped
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@pytest.fixture
def delivered_order(db, regular_user, product_in_stock) -> Order:
    order = Order(
        user_id=regular_user.id,
        product_id=product_in_stock.id,
        quantity=3,
        status=OrderStatus.delivered
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@pytest.fixture
def cancelled_order(db, regular_user, product_in_stock) -> Order:
    order = Order(
        user_id=regular_user.id,
        product_id=product_in_stock.id,
        quantity=2,
        status=OrderStatus.cancelled
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@pytest.fixture
def admin_token(admin_user) -> str:
    return create_access_token(admin_user)


@pytest.fixture
def user_token(regular_user) -> str:
    return create_access_token(regular_user)


@pytest.fixture
def another_user_token(another_user) -> str:
    return create_access_token(another_user)


@pytest.fixture
def admin_headers(admin_token) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def user_headers(user_token) -> dict:
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def another_user_headers(another_user_token) -> dict:
    return {"Authorization": f"Bearer {another_user_token}"}


@pytest.fixture
def valid_user_data() -> dict:
    return {
        "name": "New User",
        "email": "newuser@example.com",
        "password": "SecurePass123"
    }


@pytest.fixture
def valid_product_data() -> dict:
    return {
        "name": "Test Product",
        "description": "Test Description",
        "price": "49.99",
        "stock": 20
    }


@pytest.fixture
def valid_order_data() -> dict:
    return {
        "product_id": 1,
        "quantity": 2
    }


@pytest.fixture
def user_repo(db):
    from app.repository.user_repo import UserRepository
    return UserRepository(db)


@pytest.fixture
def product_repo(db):
    from app.repository.product_repo import ProductRepository
    return ProductRepository(db)


@pytest.fixture
def order_repo(db):
    from app.repository.order_repo import OrderRepository
    return OrderRepository(db)