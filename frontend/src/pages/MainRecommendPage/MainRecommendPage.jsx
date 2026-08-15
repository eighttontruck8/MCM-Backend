import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchMyProfile, fetchRecommendations } from '../../api/client';
import { useWishlist } from '../../utils/wishlistStorage';
import './MainRecommendPage.css';

// [Frontend-04-'추천 및 고객 활동 REST 연동']
export default function MainRecommendPage() {
  const navigate = useNavigate();
  const [customer, setCustomer] = useState(null);
  const [products, setProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  const wishlist = useWishlist();

  useEffect(() => {
    const timer = window.setTimeout(async () => {
      try {
        const [profile, recommendations] = await Promise.all([fetchMyProfile(), fetchRecommendations()]);
        setCustomer(profile);
        setProducts(recommendations.items);
      } catch (error) {
        setErrorMessage(error.message);
      } finally {
        setIsLoading(false);
      }
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  return (
    <div className="main-recommend-page" data-node-id="13:2846" data-name="메인화면 1">
      <div className="main-recommend-page__body">
        <div className="main-recommend-page__app">
          <div className="main-recommend-page__screen">
            <header className="main-recommend-page__topbar">
              <div className="main-recommend-page__brand">M·Journey</div>
              <div className="main-recommend-page__checkin">◉ <span>체크인</span></div>
            </header>

            <section className="main-recommend-page__hero">
              <p className="main-recommend-page__greeting">안녕하세요, {customer?.name ?? '고객'}님</p>
              <h1 className="main-recommend-page__title">오늘의 맞춤 추천</h1>
              <div className="main-recommend-page__context-banner">
                <div className="main-recommend-page__context-icon">✦</div>
                <div className="main-recommend-page__context-text">
                  <div className="context-label">개인화 컨텍스트</div>
                  <div className="context-desc">{customer?.preferred_style ?? '고객님의 취향을 분석하고 있습니다.'}</div>
                </div>
              </div>
            </section>

            <section className="main-recommend-page__ai-section">
              <div className="section-header">
                <div className="section-label">AI 상품 추천</div>
                <button type="button" className="section-link" onClick={() => navigate('/all-recommend')}>전체 보기</button>
              </div>
              {errorMessage && <p className="recommend-state recommend-state--error" role="alert">{errorMessage}</p>}
              {isLoading ? (
                <p className="recommend-state">추천 상품을 불러오고 있습니다.</p>
              ) : products.length ? (
                <div className="product-grid">
                  {products.slice(0, 4).map((product) => (
                    <article key={product.product_id} className="product-card">
                      <div className="product-image" style={{ backgroundImage: `url(${product.image_url})` }} aria-label={product.name} />
                      <div className="product-meta">
                        <div className="brand">{product.line}</div>
                        <div className="name">{product.name}</div>
                        <div className="price">{product.price.toLocaleString()}원</div>
                        <div className="ai-desc">{product.tags[0] ?? product.category}</div>
                        <button type="button" className="recommend-favorite" disabled={wishlist.pendingProductId === product.product_id} onClick={() => wishlist.toggle(product)}>
                          {wishlist.isLiked(product.product_id) ? '♥ 찜 해제' : '♡ 찜하기'}
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                <p className="recommend-state">아직 생성된 추천이 없습니다. 룩북을 먼저 만들어보세요.</p>
              )}
            </section>

            <footer className="main-recommend-page__cta">
              <div className="cta-banner">나를 위한 룩북
                <button type="button" className="cta-button" onClick={() => navigate('/lookbook')}>룩북 보러가기</button>
              </div>
            </footer>
            <nav className="main-recommend-page__nav">
              <button type="button" className="nav-item" onClick={() => navigate('/main')}>홈</button>
              <button type="button" className="nav-item" onClick={() => navigate('/lookbook')}>룩북</button>
              <button type="button" className="nav-item" onClick={() => navigate('/wishlist')}>찜</button>
              <button type="button" className="nav-item" onClick={() => navigate('/mypage')}>MY</button>
            </nav>
          </div>
        </div>
      </div>
    </div>
  );
}
