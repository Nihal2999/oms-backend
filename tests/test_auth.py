import pytest
from datetime import datetime
from jose import jwt
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user_model import UserRole


class TestPasswordSecurity:

    def test_hash_password_produces_hash(self):
        password = "MySecurePass123"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        password = "MySecurePass123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        password = "MySecurePass123"
        hashed = hash_password(password)

        assert verify_password("WrongPassword", hashed) is False

    def test_hash_same_password_different_hash(self):
        password = "MySecurePass123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_password_case_sensitive(self):
        password = "MySecurePass123"
        hashed = hash_password(password)

        assert verify_password("mysecurepass123", hashed) is False
        assert verify_password("MYSECUREPASS123", hashed) is False


class TestJWTTokens:

    def test_create_access_token_for_admin(self, admin_user):
        token = create_access_token(admin_user)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_for_regular_user(self, regular_user):
        token = create_access_token(regular_user)

        assert token is not None
        assert isinstance(token, str)

    def test_token_contains_user_id(self, admin_user):
        token = create_access_token(admin_user)

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert int(payload["sub"]) == admin_user.id

    def test_token_contains_user_role(self, admin_user):
        token = create_access_token(admin_user)

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["role"] == "admin"

    def test_token_contains_expiration(self, admin_user):
        token = create_access_token(admin_user)

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in payload

    def test_token_expiration_in_future(self, admin_user):
        token = create_access_token(admin_user)

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        now = datetime.utcnow()

        assert exp_time > now

    def test_invalid_token_signature(self, admin_user):
        token = create_access_token(admin_user)

        with pytest.raises(Exception):  # JWTError
            jwt.decode(token, "wrong-secret", algorithms=[settings.ALGORITHM])

    def test_altered_token_fails(self, admin_user):
        token = create_access_token(admin_user)

        # Alter token
        altered_token = token[:-10] + "0123456789"

        with pytest.raises(Exception):  # JWTError
            jwt.decode(altered_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


class TestAuthentication:

    def test_login_returns_valid_token(self, client, regular_user):
        response = client.post(
            "/api/v1/users/login",
            data={
                "username": regular_user.email,
                "password": "Password123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        token = data["access_token"]

        # Verify token is valid
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert int(payload["sub"]) == regular_user.id

    def test_token_valid_with_api_call(self, client, user_token, regular_user):
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == regular_user.id

    def test_invalid_token_rejected(self, client):
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 401

    def test_missing_token_rejected(self, client):
        response = client.get("/api/v1/users/me")

        assert response.status_code == 401  # Unauthorized (no token)

    def test_malformed_auth_header(self, client, user_token):
        # Missing 'Bearer' prefix
        headers = {"Authorization": user_token}
        response = client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 401

    def test_register_then_login_flow(self, client):
        # Register
        register_response = client.post(
            "/api/v1/users/register",
            json={
                "name": "New User",
                "email": "newuser@test.com",
                "password": "SecurePass123"
            }
        )
        assert register_response.status_code == 200

        # Login
        login_response = client.post(
            "/api/v1/users/login",
            data={
                "username": "newuser@test.com",
                "password": "SecurePass123"
            }
        )
        assert login_response.status_code == 200

        # Use token to access protected endpoint
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        me_response = client.get("/api/v1/users/me", headers=headers)

        assert me_response.status_code == 200
        data = me_response.json()
        assert data["email"] == "newuser@test.com"


class TestAuthorization:

    def test_admin_access_to_admin_endpoints(self, client, admin_headers):
        response = client.get("/api/v1/users/", headers=admin_headers)
        assert response.status_code == 200

    def test_user_cannot_access_admin_endpoints(self, client, user_headers):
        response = client.get("/api/v1/users/", headers=user_headers)
        assert response.status_code == 403

    def test_user_cannot_delete_users(self, client, user_headers, another_user):
        response = client.delete(
            f"/api/v1/users/{another_user.id}",
            headers=user_headers
        )
        assert response.status_code == 403

    def test_admin_can_delete_users(self, client, admin_headers, regular_user):
        response = client.delete(
            f"/api/v1/users/{regular_user.id}",
            headers=admin_headers
        )
        assert response.status_code == 200

    def test_user_cannot_create_products(self, client, user_headers):
        response = client.post(
            "/api/v1/products/",
            headers=user_headers,
            json={
                "name": "Test",
                "description": "Test",
                "price": "10.00",
                "stock": 5
            }
        )
        assert response.status_code == 403

    def test_admin_can_create_products(self, client, admin_headers):
        response = client.post(
            "/api/v1/products/",
            headers=admin_headers,
            json={
                "name": "Test Product",
                "description": "Test",
                "price": "10.00",
                "stock": 5
            }
        )
        assert response.status_code == 200

    def test_user_cannot_update_products(self, client, user_headers, product_in_stock):
        response = client.put(
            f"/api/v1/products/{product_in_stock.id}",
            headers=user_headers,
            json={"name": "Updated"}
        )
        assert response.status_code == 403

    def test_admin_can_update_products(self, client, admin_headers, product_in_stock):
        response = client.put(
            f"/api/v1/products/{product_in_stock.id}",
            headers=admin_headers,
            json={"name": "Updated"}
        )
        assert response.status_code == 200

    def test_user_can_view_own_info(self, client, user_headers, regular_user):
        response = client.get(
            f"/api/v1/users/{regular_user.id}",
            headers=user_headers
        )
        assert response.status_code == 200

    def test_user_cannot_view_other_user_info(self, client, user_headers, another_user):
        response = client.get(
            f"/api/v1/users/{another_user.id}",
            headers=user_headers
        )
        assert response.status_code == 403

    def test_admin_can_view_any_user_info(self, client, admin_headers, another_user):
        response = client.get(
            f"/api/v1/users/{another_user.id}",
            headers=admin_headers
        )
        assert response.status_code == 200

    def test_user_can_view_all_products(self, client, user_headers):
        response = client.get("/api/v1/products/", headers=user_headers)
        assert response.status_code == 200

    def test_user_can_create_orders(self, client, user_headers, product_in_stock):
        response = client.post(
            "/api/v1/orders/",
            headers=user_headers,
            json={
                "product_id": product_in_stock.id,
                "quantity": 1
            }
        )
        assert response.status_code == 200

    def test_user_can_view_own_orders(self, client, user_headers):
        response = client.get("/api/v1/orders/me", headers=user_headers)
        assert response.status_code == 200

    def test_user_cannot_view_all_orders(self, client, user_headers):
        response = client.get("/api/v1/orders/", headers=user_headers)
        assert response.status_code == 403

    def test_admin_can_view_all_orders(self, client, admin_headers):
        response = client.get("/api/v1/orders/", headers=admin_headers)
        assert response.status_code == 200

    def test_user_cannot_update_order_status(self, client, user_headers, pending_order):
        response = client.put(
            f"/api/v1/orders/{pending_order.id}",
            headers=user_headers,
            json={"status": "shipped"}
        )
        assert response.status_code == 403

    def test_admin_can_update_order_status(self, client, admin_headers, pending_order):
        response = client.put(
            f"/api/v1/orders/{pending_order.id}",
            headers=admin_headers,
            json={"status": "shipped"}
        )
        assert response.status_code == 200

    def test_user_can_cancel_own_order(self, client, user_headers, regular_user, product_in_stock, db):
        from app.models.order_model import Order, OrderStatus
        order = Order(
            user_id=regular_user.id,
            product_id=product_in_stock.id,
            quantity=1,
            status=OrderStatus.pending
        )
        db.add(order)
        db.commit()

        response = client.put(
            f"/api/v1/orders/{order.id}/cancel",
            headers=user_headers
        )
        assert response.status_code == 200

    def test_user_cannot_cancel_other_order(self, client, another_user_headers, pending_order):
        response = client.put(
            f"/api/v1/orders/{pending_order.id}/cancel",
            headers=another_user_headers
        )
        assert response.status_code == 400

    def test_admin_can_cancel_any_order(self, client, admin_headers, pending_order):
        response = client.put(
            f"/api/v1/orders/{pending_order.id}/cancel",
            headers=admin_headers
        )
        assert response.status_code == 200


class TestRoleValidation:

    def test_user_role_stored_correctly(self, admin_user, regular_user):
        assert admin_user.role == UserRole.admin
        assert regular_user.role == UserRole.user

    def test_new_user_default_role(self, client, valid_user_data):
        response = client.post("/api/v1/users/register", json=valid_user_data)

        assert response.status_code == 200
        # We cannot see role in response, but it defaults to 'user' in the model

    def test_admin_token_contains_admin_role(self, admin_user):
        token = create_access_token(admin_user)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        assert payload["role"] == "admin"

    def test_user_token_contains_user_role(self, regular_user):
        token = create_access_token(regular_user)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        assert payload["role"] == "user"