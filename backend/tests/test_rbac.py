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
