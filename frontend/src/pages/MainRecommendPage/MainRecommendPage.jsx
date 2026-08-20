import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchMyProfile, fetchRecommendations } from '../../api/client';
import PageLayout from '../../components/PageLayout/PageLayout';
import ProductImage from '../../components/ProductImage/ProductImage';
import { useWishlist } from '../../utils/wishlistStorage';
import { mockProducts } from '../../mock/mockProducts';
import brandImage from '../../assets/brand.png';
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
        // API 실패 시 mock 데이터로 fallback
        const fallback = mockProducts.slice(0, 6).map((p) => ({
          product_id: p.product_id,
          name: p.name,
          line: p.brand,
          price: p.price,
          image_url: p.image_url,
          category: p.category,
          tags: p.tags,
        }));
        setProducts(fallback);
      } finally {
        setIsLoading(false);
      }
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const checkinButton = (
    <button type="button" className="main-recommend-page__checkin" onClick={() => navigate('/check-in/stores')}>
      ◉ <span>체크인</span>
    </button>
  );

  return (
    <PageLayout navActive="home" eyebrow={`안녕하세요, ${customer?.name ?? '고객'}님`} title="오늘의 맞춤 추천" headerRight={checkinButton}>
      <div className="main-recommend-page__brand-banner">
        <img src={brandImage} alt="MCM Brand" className="main-recommend-page__brand-image" />
      </div>

      <div className="main-recommend-page__context-banner">
        <div className="main-recommend-page__context-icon">✦</div>
        <div className="main-recommend-page__context-text">
          <div className="context-label">개인화 컨텍스트</div>
          <div className="context-desc">{customer?.preferred_style ?? '고객님의 취향을 분석하고 있습니다.'}</div>
        </div>
      </div>

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
                <ProductImage className="product-image" src={product.image_url} alt={product.name} />
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
    </PageLayout>
  );
}
