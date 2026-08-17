from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_signup_and_login_screens_use_email_identity() -> None:
    signup = (
        REPOSITORY_ROOT / "frontend" / "src" / "pages" / "SignupPage" / "SignupPage.jsx"
    ).read_text(encoding="utf-8")
    login = (
        REPOSITORY_ROOT / "frontend" / "src" / "pages" / "LoginPage" / "LoginPage.jsx"
    ).read_text(encoding="utf-8")
    client = (REPOSITORY_ROOT / "frontend" / "src" / "api" / "client.js").read_text(
        encoding="utf-8"
    )
    signup_css = (
        REPOSITORY_ROOT / "frontend" / "src" / "pages" / "SignupPage" / "SignupPage.css"
    ).read_text(encoding="utf-8")

    assert "아이디" not in signup
    assert 'htmlFor="signup-email"' in signup
    assert 'id="signup-email"' in signup
    assert 'type="email"' in signup
    assert 'autoComplete="email"' in signup
    assert 'htmlFor="login-email"' in login
    assert 'id="login-email"' in login
    assert "signupCustomer({ name, phone, email, password })" in client
    assert "'/api/v1/auth/signup'" in client
    assert "await signupCustomer({ name, phone, email, password })" in signup
    assert "createOrResumeCheckin(entryTag.tag_token)" in signup
    assert "margin: 0 auto" in signup_css
    assert "max-width: 100%" in signup_css
    assert ".signup-page__input {\n  width: 100%" in signup_css
    assert ".signup-page__submit {\n  width: 100%" in signup_css
