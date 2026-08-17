import './WishlistEmptyPage.css';

export default function WishlistEmptyPage() {
  return (
    <div className="wishlist-empty" data-node-id="13:3333">
      <div className="wishlist-empty__container">
        <header className="wishlist-empty__header">
          <div className="brand">M-Journey</div>
          <button className="checkin">체크인</button>
        </header>

        <main className="wishlist-empty__main">
          <div className="wishlist-empty__eyebrow">WISHLIST</div>
          <h1 className="wishlist-empty__title">좋아요 한 상품</h1>

          <div className="wishlist-empty__illustration">♡</div>

          <p className="wishlist-empty__text">아직 좋아요 한 상품이 없어요</p>
          <p className="wishlist-empty__sub">상품 카드의 ♡ 버튼을 눌러 관심 상품을 저장해보세요</p>
        </main>

        <nav className="wishlist-empty__bottomnav">
          <button className="nav">홈</button>
          <button className="nav">룩북</button>
          <button className="nav nav--active">찜</button>
          <button className="nav">MY</button>
        </nav>
      </div>
    </div>
  );
}
