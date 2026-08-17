from pathlib import Path
import re


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_SOURCE = REPOSITORY_ROOT / "frontend" / "src"


def _read(relative_path: str) -> str:
    return (FRONTEND_SOURCE / relative_path).read_text(encoding="utf-8")


def test_customer_pages_share_bottom_navigation_and_spacing() -> None:
    navigation = _read("components/AppBottomNav/AppBottomNav.css")
    main_page = _read("pages/MainRecommendPage/MainRecommendPage.jsx")
    main_style = _read("pages/MainRecommendPage/MainRecommendPage.css")
    lookbook = _read("pages/LookbookPage/LookbookPage.jsx")
    wishlist = _read("pages/WishlistPage/WishlistPage.jsx")
    my_page = _read("pages/MyPage/MyPage.jsx")

    assert "position: sticky" in navigation
    assert "bottom: 0" in navigation
    assert "margin-top: auto" in navigation
    assert 'AppBottomNav active="home"' in main_page
    assert 'AppBottomNav active="lookbook"' in lookbook
    assert 'AppBottomNav active="wishlist"' in wishlist
    assert 'AppBottomNav active="mypage"' in my_page
    assert "padding: 24px var(--page-gutter)" in main_style


def test_protected_pages_redirect_with_user_friendly_message() -> None:
    app = _read("App.jsx")
    client = _read("api/client.js")
    login = _read("pages/LoginPage/LoginPage.jsx")

    assert "function RequireAuth" in app
    assert "/login?reason=auth-required" in app
    assert "서비스 이용은 로그인이 필요합니다." in client
    assert "서비스 이용은 로그인이 필요합니다." in login


def test_lookbook_empty_state_and_logout_confirmation_are_visible() -> None:
    lookbook = _read("pages/LookbookPage/LookbookPage.jsx")
    my_page = _read("pages/MyPage/MyPage.jsx")

    assert "lookbook-empty" in lookbook
    assert "홈으로 돌아가기" in lookbook
    assert "님, 로그아웃 하시겠습니까?" in my_page
    assert "최근 구매 이력이 없습니다." in my_page


def test_catalog_fallback_and_product_image_placeholder_are_connected() -> None:
    all_recommend = _read("pages/AllRecommendPage/AllRecommendPage.jsx")
    lookbook = _read("pages/LookbookPage/LookbookPage.jsx")
    lookbook_session = _read("utils/lookbookSession.js")
    product_image = _read("components/ProductImage/ProductImage.jsx")

    assert "fetchProducts" in all_recommend
    assert 'AppBottomNav active="home"' in all_recommend
    assert "fetchProducts" in lookbook
    assert "매장 추천 룩북" in lookbook
    assert "Array.isArray(stored.data.looks)" in lookbook_session
    assert "IMAGE<br />COMING SOON" in product_image


def test_home_checkin_button_uses_server_side_demo_entry() -> None:
    main_page = _read("pages/MainRecommendPage/MainRecommendPage.jsx")
    client = _read("api/client.js")

    assert "createOrResumeDemoCheckin" in main_page
    assert "onClick={handleCheckin}" in main_page
    assert "saveCheckin(checkin)" in main_page
    assert "'/api/v1/check-ins/demo'" in client


def test_css_does_not_define_fonts_smaller_than_eleven_pixels() -> None:
    undersized = re.compile(r"font-size\s*:\s*(?:[0-9](?:\.\d+)?|10(?:\.\d+)?)px")
    for stylesheet in FRONTEND_SOURCE.rglob("*.css"):
        assert not undersized.search(stylesheet.read_text(encoding="utf-8")), stylesheet
