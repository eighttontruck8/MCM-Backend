import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useWishlist } from '../../utils/wishlistStorage';
import './WishlistPage.css';

export default function WishlistPage(){
  const navigate = useNavigate();
  const { items, toggle } = useWishlist();

  return (
    <div className="wishlist-page" data-node-id="15:4941">
      <div className="wishlist-page__container">
        <header className="wishlist-header">
          <div className="wishlist-header__brand">M-Journey</div>
          <button className="wishlist-header__checkin">체크인</button>
        </header>

        <main className="wishlist-main">
          <div className="wishlist-main__eyebrow">WISHLIST</div>
          <h1 className="wishlist-main__title">좋아요 한 상품</h1>
          <div className="wishlist-main__count">총 {items.length}개</div>

          {items.length === 0 ? (
            <div className="wishlist-empty-state">아직 좋아요 한 상품이 없어요.</div>
          ) : (
            <ul className="wishlist-list">
              {items.map((item, index) => (
                <li key={item.product_id ?? `${item.brand}-${index}`} className="wishlist-item" data-node-id={`15:49${50 + index}`}>
                  <div className="wishlist-item__left">
                    <div className="wishlist-item__img">{item.brand}</div>
                  </div>
                  <div className="wishlist-item__center">
                    <div className="wishlist-item__brand">{item.brand}</div>
                    <div className="wishlist-item__name">{item.product_name}</div>
                    <div className="wishlist-item__price">{item.price.toLocaleString()}원</div>
                    <div className="wishlist-item__tags">
                      {(item.tags.length ? item.tags : ['AI 추천 태그']).map((t, tagIndex) => (
                        <span key={`${item.product_id}-${tagIndex}`} className="tag">{t}</span>
                      ))}
                    </div>
                  </div>
                  <div className="wishlist-item__right">
                    <button type="button" className="fav" onClick={() => toggle(item)}>❤</button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </main>

        <nav className="wishlist-bottomnav">
          <button className="nav" onClick={() => navigate('/main')}>홈</button>
          <button className="nav" onClick={() => navigate('/lookbook')}>룩북</button>
          <button className="nav nav--active" onClick={() => navigate('/wishlist')}>찜</button>
          <button className="nav" onClick={() => navigate('/mypage')}>MY</button>
        </nav>
      </div>
    </div>
  );
}
