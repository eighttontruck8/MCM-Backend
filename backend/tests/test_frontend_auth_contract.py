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


def test_staff_login_and_signup_flow_is_connected() -> None:
    signup = (
        REPOSITORY_ROOT / "frontend" / "src" / "pages" / "SignupPage" / "SignupPage.jsx"
    ).read_text(encoding="utf-8")
    login = (
        REPOSITORY_ROOT / "frontend" / "src" / "pages" / "LoginPage" / "LoginPage.jsx"
    ).read_text(encoding="utf-8")
    client = (REPOSITORY_ROOT / "frontend" / "src" / "api" / "client.js").read_text(
        encoding="utf-8"
    )

    assert "직원용 로그인" in login
    assert "searchParams.get('role') === 'staff'" in login
    assert "직원 계정으로 로그인해주세요." in login
    assert "signupStaff({ name, email, password, storeId, signupCode })" in signup
    assert "navigate('/login?role=staff&reason=signup-complete', { replace: true })" in signup
    assert "이미 고객 또는 직원으로 가입된 이메일입니다." in signup
    assert "error.code === 'EMAIL_ALREADY_REGISTERED'" in signup
    assert "reason=already-registered" not in signup
    assert "직원 계정이 생성되었습니다. 로그인해주세요." in login
    assert "setNoticeMessage('')" in login
    assert "'/api/v1/auth/staff/signup'" in client
    assert "signup_code: signupCode" in client
    assert "minLength={4}" in signup
    app = (REPOSITORY_ROOT / "frontend" / "src" / "App.jsx").read_text(encoding="utf-8")
    assert 'RequireAuth role="STAFF"' in app
    assert "user?.role !== role" in app
