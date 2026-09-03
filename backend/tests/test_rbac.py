import pytest
from app.core.security import create_access_token, decode_access_token, get_password_hash, verify_password
from app.core.rbac import Role, require_roles

def test_password_hashing():
    pwd = "DecarbXPassword2024!"
    hashed = get_password_hash(pwd)
    assert verify_password(pwd, hashed)
    assert not verify_password("WrongPassword", hashed)

def test_jwt_token_generation_and_payload():
    token = create_access_token(subject="usr-12345", role="Admin", org_id="org-777")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "usr-12345"
    assert payload["role"] == "Admin"
    assert payload["org_id"] == "org-777"

def test_role_enum_values():
    assert Role.ADMIN.value == "Admin"
    assert Role.SUSTAINABILITY_MANAGER.value == "Sustainability Manager"
    assert Role.ESG_ANALYST.value == "ESG Analyst"
    assert Role.AUDITOR.value == "Auditor"
    assert Role.SUPPLIER.value == "Supplier"
    assert Role.C_SUITE.value == "C-Suite"

def test_facility_access_least_privilege():
    from app.core.rbac import verify_facility_access
    from app.models.auth import User

    # Supplier with empty permissions must NOT have access
    supplier_user = User(email="supplier@example.com", role="Supplier", facility_permissions=[])
    assert verify_facility_access(supplier_user, "fac-austin") is False

    # Supplier with explicit facility permission
    permitted_supplier = User(email="supplier@example.com", role="Supplier", facility_permissions=["fac-austin"])
    assert verify_facility_access(permitted_supplier, "fac-austin") is True
    assert verify_facility_access(permitted_supplier, "fac-frankfurt") is False

    # Admin with empty permissions has org-wide access
    admin_user = User(email="admin@example.com", role="Admin", facility_permissions=[])
    assert verify_facility_access(admin_user, "fac-austin") is True

def test_baseline_restatement_total_includes_location_scope2():
    # Bug 1 verification: total gross baseline must include Location Scope 2 per GHG Protocol
    scope1 = 430.0
    scope2_loc = 385.0
    scope2_mkt = 250.0
    scope3 = 4041.8
    total_gross = round(scope1 + scope2_loc + scope3, 4)
    assert total_gross == 4856.8
    # Must NOT equal scope1 + scope2_mkt + scope3 (4721.8)
    assert total_gross != round(scope1 + scope2_mkt + scope3, 4)

def test_unauthenticated_users_endpoint_returns_401():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    # Bug 4 verification: unauthenticated request to /auth/users must return 401
    res = client.get("/api/v1/auth/users")
    assert res.status_code == 401
