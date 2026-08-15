import React from 'react';
import { useNavigate } from 'react-router-dom';
import { mockCustomers } from '../../mock/mockCustomers';
import { mockProducts } from '../../mock/mockProducts';
import './MainRecommendPage.css';

export default function MainRecommendPage() {
  const navigate = useNavigate();
  const customer = mockCustomers[0];
  const recommendedProducts = mockProducts.slice(0, 4);

  return (
    <div className="main-recommend-page" data-node-id="13:2846" data-name="메인화면 1">
      <div className="main-recommend-page__body" data-node-id="13:2847" data-name="Body">
        <div className="main-recommend-page__app" data-node-id="13:2849" data-name="App">
          <div className="main-recommend-page__screen" data-node-id="13:2850" data-name="MainScreen">
            <header className="main-recommend-page__topbar" data-node-id="13:2851">
              <div className="main-recommend-page__brand">M·Journey</div>
              <div className="main-recommend-page__checkin">◉ <span>체크인</span></div>
            </header>

            <section className="main-recommend-page__hero" data-node-id="13:2864">
              <p className="main-recommend-page__greeting" data-node-id="13:2867">안녕하세요, {customer.name} 고객님</p>
              <h1 className="main-recommend-page__title" data-node-id="13:2869">오늘의 맞춤 추천</h1>

              <div className="main-recommend-page__context-banner" data-node-id="13:2873">
                <div className="main-recommend-page__context-icon">✦</div>
                <div className="main-recommend-page__context-text">
                  <div className="context-label">오늘의 AI 컨텍스트</div>
                  <div className="context-desc">{customer.recent_interests.join(' · ')}</div>
                </div>
              </div>

              <div className="main-recommend-page__filters">
                <div className="filter selected">전체</div>
                <div className="filter">데일리</div>
                <div className="filter">비즈니스</div>
                <div className="filter">파티</div>
                <div className="filter">여행</div>
              </div>
            </section>

            <section className="main-recommend-page__ai-section" data-node-id="13:2908">
              <div className="section-header">
                <button
                  type="button"
                  className="section-label section-label--button"
                >
                  AI 상품 추천
                </button>
                <button
                  type="button"
                  className="section-link"
                  onClick={() => navigate('/all-recommend')}
                >
                  전체 보기
                </button>
              </div>

              <div className="product-grid">
                {recommendedProducts.map((product, index) => (
                  <article key={product.product_id || index} className="product-card" data-node-id="13:2917">
                    <div className="product-image">{product.brand}</div>
                    <div className="product-meta">
                      <div className="brand">{product.brand}</div>
                      <div className="name">{product.product_name}</div>
                      <div className="price">{product.price.toLocaleString()}원</div>
                      <div className="ai-desc">{product.tags[0]}</div>
                    </div>
                  </article>
                ))}
              </div>
            </section>

            <section className="main-recommend-page__popular" data-node-id="13:3030">
              <div className="popular-header">
                <div className="section-label">지금 인기</div>
                <h2 className="popular-title">최근 인기 상품</h2>
              </div>

              <div className="popular-grid">
                <div className="popular-card">
                  <div className="popular-image">사진 1</div>
                  <div className="popular-meta">
                    <div className="brand">브랜드명</div>
                    <div className="name">상품명 1</div>
                    <div className="price">가격</div>
                  </div>
                </div>
                <div className="popular-card">
                  <div className="popular-image">사진 2</div>
                  <div className="popular-meta">
                    <div className="brand">브랜드명</div>
                    <div className="name">상품명 2</div>
                    <div className="price">가격</div>
                  </div>
                </div>
                <div className="popular-card">
                  <div className="popular-image">사진 3</div>
                  <div className="popular-meta">
                    <div className="brand">브랜드명</div>
                    <div className="name">상품명 3</div>
                    <div className="price">가격</div>
                  </div>
                </div>
              </div>
            </section>

            <footer className="main-recommend-page__cta">
              <div className="cta-banner">나를 위한 룩북
                <button className="cta-button" onClick={() => navigate('/lookbook')}>룩북 보러가기</button>
              </div>
            </footer>

            <nav className="main-recommend-page__nav">
              <div className="nav-item" onClick={() => navigate('/main')} style={{cursor: 'pointer'}}>홈</div>
              <div className="nav-item" onClick={() => navigate('/lookbook')} style={{cursor: 'pointer'}}>룩북</div>
              <div className="nav-item" onClick={() => navigate('/wishlist')} style={{cursor: 'pointer'}}>찜</div>
              <div className="nav-item" onClick={() => navigate('/mypage')} style={{cursor: 'pointer'}}>MY</div>
            </nav>
          </div>
        </div>
      </div>
    </div>
  );
}
