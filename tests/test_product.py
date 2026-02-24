from app.models.user import User
from app.models.user import UserRole
from app.api.v1.users import get_admin_user


def test_create_product(client, db):

    # Create fake admin user
    admin_user = User(
        name="Admin",
        email="admin@test.com",
        hashed_password="fakehashed",
        role=UserRole.admin
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    # Override admin dependency
    def override_get_admin_user():
        return admin_user

    client.app.dependency_overrides[get_admin_user] = override_get_admin_user

    # Call endpoint
    response = client.post(
        "/api/v1/products/",
        json={
            "name": "Laptop",
            "description": "Gaming laptop",
            "price": 1200,
            "stock": 10
        }
    )

    assert response.status_code == 200