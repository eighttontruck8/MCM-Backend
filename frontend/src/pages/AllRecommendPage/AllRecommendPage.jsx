import React from 'react';
import { useNavigate } from 'react-router-dom';
import { mockProducts } from '../../mock/mockProducts';
import { useWishlist } from '../../utils/wishlistStorage';
import './AllRecommendPage.css';

export default function AllRecommendPage() {
  const navigate = useNavigate();
  const { isLiked, toggle } = useWishlist();
  const products = mockProducts;

  return (
    <div className="all-recommend-page" data-node-id="17:5" data-name="전체 추천 상품">
      <div className="all-recommend-page__body">
        <header className="all-recommend-page__top">
          <button className="all-recommend-page__back" onClick={() => navigate('/main')}>‹</button>
          <h1 className="all-recommend-page__title">전체 추천 상품</h1>
          <div className="all-recommend-page__count">{products.length}개</div>
        </header>

        <div className="all-recommend-page__search">
          <input type="text" placeholder="상품명 또는 태그 검색" />
        </div>

        <nav className="all-recommend-page__tabs">
          <button className="tab tab--active">전체</button>
          <button className="tab">데일리</button>
          <button className="tab">비즈니스</button>
          <button className="tab">파티</button>
          <button className="tab">여행</button>
        </nav>

        <main className="all-recommend-page__list">
          {products.map((product) => (
            <article key={product.product_id} className="product-row">
              <div className="product-row__left">
                <div className="product-image">{product.brand}</div>
              </div>
              <div className="product-row__content">
                <div className="product-row__tag">{product.tags[0]}</div>
                <div className="product-row__brand">{product.brand}</div>
                <div className="product-row__name">{product.product_name}</div>
                <div className="product-row__price">{product.price.toLocaleString()}원</div>
                <div className="product-row__desc">{product.category} · {product.stock_status === 'in_stock' ? '재고 있음' : '재고 없음'}</div>
              </div>
              <button
                type="button"
                className={`product-row__fav ${isLiked(product.product_id) ? 'product-row__fav--active' : ''}`}
                onClick={() => toggle(product)}
                aria-label={isLiked(product.product_id) ? '찜 해제' : '찜하기'}
              >
                {isLiked(product.product_id) ? '♥' : '♡'}
              </button>
            </article>
          ))}
        </main>

      </div>
    </div>
  );
}
