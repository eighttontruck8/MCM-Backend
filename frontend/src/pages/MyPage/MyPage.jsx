import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { clearAuth, fetchMyProfile, fetchPurchases } from '../../api/client';
import PageLayout from '../../components/PageLayout/PageLayout';
import { useWishlist } from '../../utils/wishlistStorage';
import './MyPage.css';

// [Frontend-04-'추천 및 고객 활동 REST 연동']
export default function MyPage() {
  const navigate = useNavigate();
  const wishlist = useWishlist();
  const [customer, setCustomer] = useState(null);
  const [purchases, setPurchases] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  const preferenceTags = [customer?.preferred_style, ...(customer?.preferred_colors ?? [])]
    .filter((tag) => tag && tag !== '미정');

  useEffect(() => {
    const timer = window.setTimeout(async () => {
      try {
        const [profile, history] = await Promise.all([fetchMyProfile(), fetchPurchases()]);
        setCustomer(profile);
        setPurchases(history.items);
      } catch (error) {
        setErrorMessage(error.message);
      } finally {
        setIsLoading(false);
      }
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const logout = () => {
    if (!window.confirm(`${customer?.name ?? '고객'}님, 로그아웃 하시겠습니까?`)) return;
    clearAuth();
    navigate('/login', { replace: true });
  };

  return (
    <PageLayout navActive="mypage" eyebrow="MY PAGE" title={customer?.name ?? '마이페이지'}>
      {errorMessage && <p className="my-page__state" role="alert">{errorMessage}</p>}
      {isLoading ? <p className="my-page__state">고객 정보를 불러오고 있습니다.</p> : (
        <>
          <section className="profile-hero">
            <div className="avatar">{customer?.name?.charAt(0) ?? '고'}</div>
            <div className="profile-info">
              <div className="profile-name">{customer?.name ?? '고객'}</div>
              <div className="profile-id">#{customer?.customer_id}</div>
            </div>
            <div className="profile-stats">
              <div className="stat">{purchases.length}건<br/><span>구매 이력</span></div>
              <div className="stat">{wishlist.items.length}건<br/><span>관심 상품</span></div>
              <div className="stat">{customer?.visit_count ?? 0}회<br/><span>방문 횟수</span></div>
            </div>
          </section>
          <section className="tags-section">
            <div className="section-title">AI 분석 취향 프로필</div>
            <div className="tags">
              {preferenceTags.length
                ? preferenceTags.map((tag) => <span key={tag} className="tag">{tag}</span>)
                : <p className="my-page__empty">아직 분석된 취향 정보가 없습니다.</p>}
            </div>
          </section>
          <section className="recent-section">
            <div className="section-title">최근 구매 이력</div>
            <ul className="recent-list">
              {purchases.map((purchase) => (
                <li key={purchase.purchase_id} className="recent-item">
                  <div>
                    <div className="recent-name">{purchase.name}</div>
                    <div className="recent-date">{new Date(purchase.purchased_at).toLocaleDateString('ko-KR')} · {purchase.category}</div>
                  </div>
                  <div className="recent-price">{purchase.price.toLocaleString()}원</div>
                </li>
              ))}
            </ul>
            {!purchases.length && <p className="my-page__empty">최근 구매 이력이 없습니다.</p>}
          </section>
        </>
      )}
      <section className="settings-section">
        <button type="button" className="setting">개인정보 처리방침</button>
        <button type="button" className="setting" onClick={logout}>로그아웃</button>
      </section>
    </PageLayout>
  );
}
