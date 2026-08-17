from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_signup_and_login_screens_use_email_identity() -> None:
    signup = (
        REPOSITORY_ROOT / "frontend" / "src" / "pages" / "SignupPage" / "SignupPage.jsx"
    ).read_text(encoding="utf-8")
    login = (
        REPOSITORY_ROOT / "frontend" / "src" / "pages" / "LoginPage" / "LoginPage.jsx"
    ).read_text(encoding="utf-8")

    assert "아이디" not in signup
    assert 'htmlFor="signup-email"' in signup
    assert 'id="signup-email"' in signup
    assert 'type="email"' in signup
    assert 'autoComplete="email"' in signup
    assert 'htmlFor="login-email"' in login
    assert 'id="login-email"' in login
