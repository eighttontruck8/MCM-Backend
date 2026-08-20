import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchProducts, fetchRecommendations } from '../../api/client';
import PageLayout from '../../components/PageLayout/PageLayout';
import ProductImage from '../../components/ProductImage/ProductImage';
import { useWishlist } from '../../utils/wishlistStorage';
import { mockProducts } from '../../mock/mockProducts';
import './AllRecommendPage.css';

const LOCAL_IMAGE_MAP = Object.fromEntries(mockProducts.map((p) => [p.product_id, p.image_url]));

// [Frontend-04-'추천 및 고객 활동 REST 연동']
export default function AllRecommendPage() {
  const navigate = useNavigate();
  const wishlist = useWishlist();
  const [products, setProducts] = useState([]);
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const timer = window.setTimeout(async () => {
      try {
        const [recommendations, catalog] = await Promise.all([
          fetchRecommendations().catch(() => ({ items: [] })),
          fetchProducts(),
        ]);
        const merged = [...recommendations.items, ...catalog.items].filter(
          (product, index, items) => items.findIndex((item) => item.product_id === product.product_id) === index,
        ).map((p) => ({ ...p, image_url: LOCAL_IMAGE_MAP[p.product_id] || p.image_url }));
        setProducts(merged);
      } catch (error) {
        setErrorMessage(error.message);
      } finally {
        setIsLoading(false);
      }
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const filteredProducts = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    if (!keyword) return products;
    return products.filter((product) => [product.name, product.category, ...product.tags].join(' ').toLowerCase().includes(keyword));
  }, [products, query]);

  const backButton = (
    <button type="button" className="all-recommend-page__back" onClick={() => navigate('/main')}>‹</button>
  );

  return (
    <PageLayout navActive="home" eyebrow={`${filteredProducts.length}개`} title="전체 추천 상품" headerRight={backButton}>
      <div className="all-recommend-page__search">
        <input type="search" placeholder="상품명 또는 태그 검색" value={query} onChange={(event) => setQuery(event.target.value)} />
      </div>
      {errorMessage && <p className="recommend-list-state" role="alert">{errorMessage}</p>}
      {isLoading ? <p className="recommend-list-state">불러오는 중...</p> : (
        <div className="all-recommend-page__list">
          {filteredProducts.map((product) => (
            <article key={product.product_id} className="product-row">
              <div className="product-row__left"><ProductImage className="product-image" src={product.image_url} alt={product.name} /></div>
              <div className="product-row__content">
                <div className="product-row__tag">{product.tags[0] ?? product.category}</div>
                <div className="product-row__brand">{product.line}</div>
                <div className="product-row__name">{product.name}</div>
                <div className="product-row__price">{product.price.toLocaleString()}원</div>
                <div className="product-row__desc">{product.category} · {product.inventory?.in_stock ? `재고 ${product.inventory.quantity}개` : '재고 없음'}</div>
              </div>
              <button type="button" disabled={wishlist.pendingProductId === product.product_id} className={`product-row__fav ${wishlist.isLiked(product.product_id) ? 'product-row__fav--active' : ''}`} onClick={() => wishlist.toggle(product)} aria-label={wishlist.isLiked(product.product_id) ? '찜 해제' : '찜하기'}>
                {wishlist.isLiked(product.product_id) ? '♥' : '♡'}
              </button>
            </article>
          ))}
          {!filteredProducts.length && <p className="recommend-list-state">조건에 맞는 추천 상품이 없습니다.</p>}
        </div>
      )}
    </PageLayout>
  );
}
