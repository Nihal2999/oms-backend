class TestUserAPI:

    def test_register_user_success(self, client, valid_user_data):
        response = client.post("/api/v1/users/register", json=valid_user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == valid_user_data["name"]
        assert data["email"] == valid_user_data["email"]
        assert "id" in data

    def test_register_user_invalid_email(self, client):
        response = client.post("/api/v1/users/register", json={
            "name": "Test User",
            "email": "invalid-email",
            "password": "Password123"
        })

        assert response.status_code == 422  # Validation error

    def test_register_user_password_too_short(self, client):
        response = client.post("/api/v1/users/register", json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "short"
        })

        assert response.status_code == 422

    def test_register_user_duplicate_email(self, client, regular_user, valid_user_data):
        response = client.post("/api/v1/users/register", json={
            "name": "Another User",
            "email": regular_user.email,
            "password": "Password456"
        })

        assert response.status_code == 400
        data = response.json()
        assert "Email already registered" in data["detail"]

    def test_login_user_success(self, client, regular_user):
        response = client.post(
            "/api/v1/users/login",
            data={
                "username": regular_user.email,
                "password": "Password123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_user_invalid_email(self, client):
        response = client.post(
            "/api/v1/users/login",
            data={
                "username": "nonexistent@test.com",
                "password": "AnyPassword123"
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert "Invalid credentials" in data["detail"]

    def test_login_user_invalid_password(self, client, regular_user):
        response = client.post(
            "/api/v1/users/login",
            data={
                "username": regular_user.email,
                "password": "WrongPassword"
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert "Invalid credentials" in data["detail"]

    def test_get_current_user(self, client, user_headers):
        response = client.get("/api/v1/users/me", headers=user_headers)

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["email"] == "john@example.com"

    def test_get_current_user_no_auth(self, client):
        response = client.get("/api/v1/users/me")

        assert response.status_code == 401  # Unauthorized (no token provided)

    def test_get_user_by_id_self(self, client, user_headers, regular_user):
        response = client.get(f"/api/v1/users/{regular_user.id}", headers=user_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == regular_user.id
        assert data["email"] == regular_user.email

    def test_get_user_by_id_other_user_unauthorized(self, client, user_headers, another_user):
        response = client.get(f"/api/v1/users/{another_user.id}", headers=user_headers)

        assert response.status_code == 403

    def test_get_user_by_id_admin_access(self, client, admin_headers, another_user):
        response = client.get(f"/api/v1/users/{another_user.id}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == another_user.id

    def test_get_user_not_found(self, client, user_headers):
        response = client.get("/api/v1/users/99999", headers=user_headers)

        assert response.status_code == 404

    def test_get_all_users_admin_only(self, client, admin_headers, user_headers):
        # Admin should succeed
        response = client.get("/api/v1/users/", headers=admin_headers)
        assert response.status_code == 200

        # Regular user should fail
        response = client.get("/api/v1/users/", headers=user_headers)
        assert response.status_code == 403

    def test_update_user_self(self, client, user_headers, regular_user):
        response = client.put(
            f"/api/v1/users/{regular_user.id}",
            headers=user_headers,
            json={
                "name": "Updated Name",
                "email": "updated@test.com"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["email"] == "updated@test.com"

    def test_update_user_other_unauthorized(self, client, user_headers, another_user):
        response = client.put(
            f"/api/v1/users/{another_user.id}",
            headers=user_headers,
            json={"name": "Hacked Name"}
        )

        assert response.status_code == 403

    def test_update_user_admin_can_update_any(self, client, admin_headers, another_user):
        response = client.put(
            f"/api/v1/users/{another_user.id}",
            headers=admin_headers,
            json={"name": "Admin Updated"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Admin Updated"

    def test_delete_user_admin_only(self, client, admin_headers, user_headers, regular_user):
        # Admin should succeed
        user_to_delete = regular_user
        response = client.delete(f"/api/v1/users/{user_to_delete.id}", headers=admin_headers)
        assert response.status_code == 200

        # Regular user's token is now invalid because they were deleted
        response = client.delete("/api/v1/users/99999", headers=user_headers)
        assert response.status_code == 401  # Unauthorized (user was deleted, token invalid)


class TestProductAPI:

    def test_create_product_admin_only(self, client, admin_headers, user_headers):
        product_data = {
            "name": "Test Product",
            "description": "Test",
            "price": "99.99",
            "stock": 10
        }

        # Admin should succeed
        response = client.post("/api/v1/products/", headers=admin_headers, json=product_data)
        assert response.status_code == 200

        # Regular user should fail
        response = client.post("/api/v1/products/", headers=user_headers, json=product_data)
        assert response.status_code == 403

    def test_create_product_success(self, client, admin_headers):
        product_data = {
            "name": "New Laptop",
            "description": "High-performance laptop",
            "price": "999.99",
            "stock": 5
        }

        response = client.post("/api/v1/products/", headers=admin_headers, json=product_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Laptop"
        assert data["price"] == "999.99"
        assert data["stock"] == 5

    def test_create_product_invalid_price(self, client, admin_headers):
        response = client.post("/api/v1/products/", headers=admin_headers, json={
            "name": "Test",
            "description": "Test",
            "price": "-10.00",
            "stock": 5
        })

        assert response.status_code == 422

    def test_create_product_invalid_stock(self, client, admin_headers):
        response = client.post("/api/v1/products/", headers=admin_headers, json={
            "name": "Test",
            "description": "Test",
            "price": "10.00",
            "stock": -5
        })

        assert response.status_code == 422

    def test_get_products_no_auth(self, client):
        response = client.get("/api/v1/products/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_products_with_pagination(self, client):
        response = client.get("/api/v1/products/?skip=0&limit=5")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_products_with_search(self, client, product_in_stock):
        response = client.get("/api/v1/products/?search=Laptop")

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_get_product_by_id(self, client, product_in_stock):
        response = client.get(f"/api/v1/products/{product_in_stock.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == product_in_stock.id
        assert data["name"] == product_in_stock.name

    def test_get_product_not_found(self, client):
        response = client.get("/api/v1/products/99999")

        assert response.status_code == 404

    def test_get_product_deleted_not_found(self, client, deleted_product):
        response = client.get(f"/api/v1/products/{deleted_product.id}")

        assert response.status_code == 404

    def test_update_product_admin_only(self, client, admin_headers, user_headers, product_in_stock):
        update_data = {"name": "Updated"}

        # Admin should succeed
        response = client.put(
            f"/api/v1/products/{product_in_stock.id}",
            headers=admin_headers,
            json=update_data
        )
        assert response.status_code == 200

        # Regular user should fail
        response = client.put(
            f"/api/v1/products/{product_in_stock.id}",
            headers=user_headers,
            json=update_data
        )
        assert response.status_code == 403

    def test_update_product_success(self, client, admin_headers, product_in_stock):
        response = client.put(
            f"/api/v1/products/{product_in_stock.id}",
            headers=admin_headers,
            json={
                "name": "Updated Name",
                "price": "899.99"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["price"] == "899.99"

    def test_delete_product_admin_only(self, client, admin_headers, user_headers, product_low_stock):
        # Regular user should fail
        response = client.delete(f"/api/v1/products/{product_low_stock.id}", headers=user_headers)
        assert response.status_code == 403

        # Admin should succeed
        response = client.delete(f"/api/v1/products/{product_low_stock.id}", headers=admin_headers)
        assert response.status_code == 200

    def test_delete_product_success(self, client, admin_headers, product_in_stock):
        response = client.delete(
            f"/api/v1/products/{product_in_stock.id}",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]

    def test_delete_product_not_found(self, client, admin_headers):
        response = client.delete("/api/v1/products/99999", headers=admin_headers)

        assert response.status_code == 404

    def test_restore_product_admin_only(self, client, admin_headers, user_headers, deleted_product):
        # Regular user should fail
        response = client.put(
            f"/api/v1/products/{deleted_product.id}/restore",
            headers=user_headers
        )
        assert response.status_code == 403

        # Admin should succeed
        response = client.put(
            f"/api/v1/products/{deleted_product.id}/restore",
            headers=admin_headers
        )
        assert response.status_code == 200

    def test_restore_product_success(self, client, admin_headers, deleted_product):
        response = client.put(
            f"/api/v1/products/{deleted_product.id}/restore",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == deleted_product.id

    def test_restore_product_not_deleted(self, client, admin_headers, product_in_stock):
        response = client.put(
            f"/api/v1/products/{product_in_stock.id}/restore",
            headers=admin_headers
        )

        assert response.status_code == 400
        

class TestOrderAPI:

    def test_create_order_success(self, client, user_headers, product_in_stock):
        response = client.post(
            "/api/v1/orders/",
            headers=user_headers,
            json={
                "product_id": product_in_stock.id,
                "quantity": 2
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == product_in_stock.id
        assert data["quantity"] == 2
        assert data["status"] == "pending"

    def test_create_order_requires_auth(self, client, product_in_stock):
        response = client.post(
            "/api/v1/orders/",
            json={
                "product_id": product_in_stock.id,
                "quantity": 1
            }
        )

        assert response.status_code == 401  # Unauthorized (no token provided)

    def test_create_order_product_not_found(self, client, user_headers):
        response = client.post(
            "/api/v1/orders/",
            headers=user_headers,
            json={
                "product_id": 99999,
                "quantity": 1
            }
        )

        assert response.status_code == 404

    def test_create_order_insufficient_stock(self, client, user_headers, product_low_stock):
        response = client.post(
            "/api/v1/orders/",
            headers=user_headers,
            json={
                "product_id": product_low_stock.id,
                "quantity": 10
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "Not enough stock" in data["detail"]

    def test_create_order_invalid_quantity(self, client, user_headers, product_in_stock):
        response = client.post(
            "/api/v1/orders/",
            headers=user_headers,
            json={
                "product_id": product_in_stock.id,
                "quantity": 0
            }
        )

        assert response.status_code == 422

    def test_get_my_orders(self, client, user_headers, regular_user, pending_order):
        response = client.get("/api/v1/orders/me", headers=user_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_my_orders_requires_auth(self, client):
        response = client.get("/api/v1/orders/me")

        assert response.status_code == 401  # Unauthorized (no token provided)

    def test_get_all_orders_admin_only(self, client, admin_headers, user_headers):
        # Admin should succeed
        response = client.get("/api/v1/orders/", headers=admin_headers)
        assert response.status_code == 200

        # Regular user should fail
        response = client.get("/api/v1/orders/", headers=user_headers)
        assert response.status_code == 403

    def test_get_all_orders_success(self, client, admin_headers, pending_order):
        response = client.get("/api/v1/orders/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_update_order_status_admin_only(self, client, admin_headers, user_headers, pending_order):
        update_data = {"status": "shipped"}

        # Admin should succeed
        response = client.put(
            f"/api/v1/orders/{pending_order.id}",
            headers=admin_headers,
            json=update_data
        )
        assert response.status_code == 200

        # Regular user should fail
        response = client.put(
            f"/api/v1/orders/{pending_order.id}",
            headers=user_headers,
            json=update_data
        )
        assert response.status_code == 403

    def test_update_order_status_success(self, client, admin_headers, pending_order):
        response = client.put(
            f"/api/v1/orders/{pending_order.id}",
            headers=admin_headers,
            json={"status": "shipped"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "shipped"

    def test_update_order_status_not_found(self, client, admin_headers):
        response = client.put(
            "/api/v1/orders/99999",
            headers=admin_headers,
            json={"status": "shipped"}
        )

        assert response.status_code == 404

    def test_cancel_order_by_owner(self, client, user_headers, regular_user, pending_order):
        response = client.put(
            f"/api/v1/orders/{pending_order.id}/cancel",
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "cancelled successfully" in data["message"]

    def test_cancel_order_by_admin(self, client, admin_headers, pending_order):
        response = client.put(
            f"/api/v1/orders/{pending_order.id}/cancel",
            headers=admin_headers
        )

        assert response.status_code == 200

    def test_cancel_order_unauthorized(self, client, another_user_headers, pending_order):
        response = client.put(
            f"/api/v1/orders/{pending_order.id}/cancel",
            headers=another_user_headers
        )

        assert response.status_code == 400

    def test_cancel_order_requires_auth(self, client, pending_order):
        response = client.put(f"/api/v1/orders/{pending_order.id}/cancel")

        assert response.status_code == 401  # Unauthorized (no token provided)

    def test_cancel_order_not_found(self, client, user_headers):
        response = client.put(
            "/api/v1/orders/99999/cancel",
            headers=user_headers
        )

        assert response.status_code == 404

    def test_cancel_shipped_order_fails(self, client, user_headers, shipped_order):
        response = client.put(
            f"/api/v1/orders/{shipped_order.id}/cancel",
            headers=user_headers
        )

        assert response.status_code == 400

    def test_cancel_delivered_order_fails(self, client, user_headers, delivered_order):
        response = client.put(
            f"/api/v1/orders/{delivered_order.id}/cancel",
            headers=user_headers
        )

        assert response.status_code == 400

    def test_cancel_already_cancelled_order(self, client, user_headers, cancelled_order):
        response = client.put(
            f"/api/v1/orders/{cancelled_order.id}/cancel",
            headers=user_headers
        )

        assert response.status_code == 400


class TestHealthCheck:

    def test_root_endpoint(self, client):
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Running" in data["message"]

    def test_health_check(self, client):
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"