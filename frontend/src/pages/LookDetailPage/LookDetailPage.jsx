import { useNavigate } from 'react-router-dom';
import { getSelectedLook } from '../../utils/lookbookSession';
import { useWishlist } from '../../utils/wishlistStorage';
import './LookDetailPage.css';

// [Frontend-04-'추천 및 고객 활동 REST 연동']
export default function LookDetailPage() {
  const navigate = useNavigate();
  const look = getSelectedLook();
  const wishlist = useWishlist();

  if (!look) {
    return <div className="look-detail"><p className="look-detail__state">선택한 룩이 없습니다.</p><button type="button" onClick={() => navigate('/lookbook')}>룩북으로 돌아가기</button></div>;
  }

  return (
    <div className="look-detail">
      <section className="look-detail__hero">
        <div className="hero__controls">
          <button type="button" className="btn-icon" disabled={wishlist.pendingProductId === look.product_id} aria-label="favorite" onClick={() => wishlist.toggle({ ...look, name: look.product, category: 'LOOKBOOK', tags: [] })}>
            {wishlist.isLiked(look.product_id) ? '♥' : '♡'}
          </button>
          <button type="button" className="btn-icon" aria-label="close" onClick={() => navigate('/lookbook')}>✕</button>
        </div>
        <div className="hero__image" style={{ backgroundImage: `url(${look.image_url})` }} />
        <div className="hero__meta">
          <h1 className="hero__title">{look.product}</h1>
          <p className="hero__subtitle">{look.styling}</p>
        </div>
      </section>
      <section className="look-detail__items">
        <div className="items__heading">구성 아이템</div>
        <ul className="items__list">
          <li className="item-row">
            <div className="item-row__left">
              <div className="item-row__name">{look.product}</div>
              <div className="item-row__price">{look.price.toLocaleString()}원</div>
            </div>
            <div className="item-row__right"><span className="badge badge--in-stock">재고 있음</span></div>
          </li>
        </ul>
      </section>
    </div>
  );
}
