import AppBottomNav from '../../components/AppBottomNav/AppBottomNav';
import { useWishlist } from '../../utils/wishlistStorage';
import './WishlistPage.css';

// [Frontend-04-'추천 및 고객 활동 REST 연동']
export default function WishlistPage() {
  const { items, toggle, isLoading, pendingProductId, errorMessage } = useWishlist();

  return (
    <div className="wishlist-page">
      <div className="wishlist-page__container">
        <header className="wishlist-header"><div className="wishlist-header__brand">M-Journey</div></header>
        <main className="wishlist-main">
          <div className="wishlist-main__eyebrow">WISHLIST</div>
          <h1 className="wishlist-main__title">좋아요 한 상품</h1>
          <div className="wishlist-main__count">총 {items.length}개</div>
          {errorMessage && <p className="wishlist-empty-state" role="alert">{errorMessage}</p>}
          {isLoading ? <div className="wishlist-empty-state">찜 목록을 불러오고 있습니다.</div> : items.length === 0 ? (
            <div className="wishlist-empty-state">아직 좋아요 한 상품이 없어요.</div>
          ) : (
            <ul className="wishlist-list">
              {items.map((item) => (
                <li key={item.product_id} className="wishlist-item">
                  <div className="wishlist-item__left"><div className="wishlist-item__img" style={{ backgroundImage: `url(${item.image_url})` }} /></div>
                  <div className="wishlist-item__center">
                    <div className="wishlist-item__brand">{item.line}</div>
                    <div className="wishlist-item__name">{item.name}</div>
                    <div className="wishlist-item__price">{item.price.toLocaleString()}원</div>
                    <div className="wishlist-item__tags">{item.tags.map((tag) => <span key={tag} className="tag">{tag}</span>)}</div>
                  </div>
                  <div className="wishlist-item__right">
                    <button type="button" disabled={pendingProductId === item.product_id} className="fav" onClick={() => toggle(item)}>♥</button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </main>
        <AppBottomNav active="wishlist" />
      </div>
    </div>
  );
}
