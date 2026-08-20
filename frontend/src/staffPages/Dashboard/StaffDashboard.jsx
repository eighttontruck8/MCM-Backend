import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchStaffVisits, getAuthUser, updateStaffVisitStatus } from '../../api/client';
import ProductImage from '../../components/ProductImage/ProductImage';
import StaffShell from '../../components/StaffShell/StaffShell';
import { splitPurchasesByChannel } from '../../utils/staffDashboardData';
import { clearStaffActiveVisit, getStaffActiveVisit } from '../../utils/staffSession';
import { createMockTasteReport } from '../../utils/staffTasteReport';
import './StaffDashboard.css';

const money = (value) => `${Number(value ?? 0).toLocaleString('ko-KR')}원`;
const date = (value) => value ? new Date(value).toLocaleDateString('ko-KR') : '-';

function ProductCard({ product, badge }) {
  return (
    <article className="staff-dashboard__product-card">
      <ProductImage src={product.image_url} alt={product.name} className="staff-dashboard__product-image" />
      <div className="staff-dashboard__product-copy">
        {badge && <span className="staff-dashboard__product-badge">{badge}</span>}
        <strong>{product.name}</strong>
        <span>{product.category} · {money(product.price)}</span>
        {product.purchased_at && <small>{date(product.purchased_at)} 구매</small>}
        {product.reason && <small>{product.reason}</small>}
      </div>
    </article>
  );
}

// [Frontend-Staff-03-'직원 고객 인사이트 홈'] 수락한 고객의 AI 취향과 채널별 구매 이력을 /staff에서 통합 표시한다.
export default function StaffDashboard() {
  const navigate = useNavigate();
  const staff = getAuthUser();
  const [activeVisit, setActiveVisit] = useState(() => getStaffActiveVisit());
  const [queueCount, setQueueCount] = useState(0);
  const [isCompleting, setIsCompleting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (!staff?.store_id) return undefined;
    const timer = window.setTimeout(() => {
      fetchStaffVisits(staff.store_id)
        .then((response) => setQueueCount(response.items.length))
        .catch(() => undefined);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [staff?.store_id]);

  const profile = activeVisit?.profile;
  const guide = activeVisit?.guide;
  const report = useMemo(
    () => activeVisit?.tasteReport ?? createMockTasteReport(profile, activeVisit?.visit),
    [activeVisit, profile],
  );
  const purchases = useMemo(() => splitPurchasesByChannel(profile?.purchases), [profile?.purchases]);
  const interestProducts = profile?.recently_viewed_products ?? [];
  const recommendations = guide?.recommended_products ?? [];

  const handleComplete = async () => {
    const checkinId = activeVisit?.visit?.checkin_id;
    if (!checkinId || !window.confirm(`${profile?.masked_name ?? '고객'} 고객님의 응대를 완료하시겠습니까?`)) return;
    setIsCompleting(true);
    setErrorMessage('');
    try {
      await updateStaffVisitStatus(checkinId, 'COMPLETED');
      clearStaffActiveVisit();
      setActiveVisit(null);
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsCompleting(false);
    }
  };

  return (
    <StaffShell active="dashboard" connectionState={activeVisit ? '고객 응대 중' : '대기 가능'} queueCount={queueCount}>
      {!activeVisit ? (
        <section className="staff-dashboard__empty">
          <span className="staff-dashboard__eyebrow">TODAY'S CLIENTELING</span>
          <h1>{staff?.display_name ?? '직원'} 쇼퍼님,<br />새로운 고객을 맞이할 준비가 되었습니다.</h1>
          <p>웨이팅 리스트에서 고객의 간단한 취향 정보를 확인하고 응대를 시작해 주세요.</p>
          <button type="button" onClick={() => navigate('/staff/waiting')}>
            웨이팅 리스트 보기 {queueCount > 0 && `· ${queueCount}명`}
          </button>
        </section>
      ) : (
        <div className="staff-dashboard">
          <section className="staff-dashboard__intro">
            <div>
              <span className="staff-dashboard__eyebrow">ACTIVE CLIENT</span>
              <h1>{profile?.masked_name ?? '고객'} 고객님 인사이트</h1>
              <p>{profile?.membership ?? 'MEMBER'} · 누적 방문 {profile?.visit_count ?? 0}회 · 방문 목적 {profile?.visit_purpose ?? '-'}</p>
            </div>
            <div className="staff-dashboard__intro-actions">
              <span><i /> 현재 응대 중</span>
              <button type="button" disabled={isCompleting} onClick={handleComplete}>
                {isCompleting ? '완료 처리 중' : '응대 완료'}
              </button>
            </div>
          </section>

          {errorMessage && <p className="staff-dashboard__error" role="alert">{errorMessage}</p>}

          <section className="staff-dashboard__ai-card">
            <div className="staff-dashboard__ai-heading">
              <span className="staff-dashboard__ai-mark">AI</span>
              <div><small>AI TASTE PROFILE</small><h2>고객 취향 프로필</h2></div>
            </div>
            <p className="staff-dashboard__ai-summary">{guide?.customer_summary ?? report.summary}</p>
            <div className="staff-dashboard__metrics">
              {report.metrics.map((metric) => (
                <div key={metric.label}><span>{metric.label}</span><strong>{metric.value}</strong></div>
              ))}
            </div>
            <div className="staff-dashboard__tags">
              {report.tags.map((tag) => <span key={tag}>#{tag}</span>)}
            </div>
          </section>

          <section className="staff-dashboard__section">
            <div className="staff-dashboard__section-heading">
              <div><span>INTEREST &amp; AI PICKS</span><h2>최근 관심 상품과 추천</h2></div>
              <small>고객 동의 범위 내 정보</small>
            </div>
            <div className="staff-dashboard__product-grid">
              {[...interestProducts.map((item) => ({ ...item, badge: '최근 조회' })), ...recommendations.map((item) => ({ ...item, badge: 'AI 추천' }))]
                .slice(0, 6)
                .map((product) => <ProductCard key={`${product.badge}-${product.product_id}`} product={product} badge={product.badge} />)}
              {!interestProducts.length && !recommendations.length && <p className="staff-dashboard__empty-copy">공유된 관심 상품이 없습니다.</p>}
            </div>
          </section>

          <section className="staff-dashboard__section">
            <div className="staff-dashboard__section-heading">
              <div><span>PURCHASE HISTORY</span><h2>최근 구매 내역</h2></div>
              <small>총 {profile?.purchase_count ?? 0}건</small>
            </div>
            <div className="staff-dashboard__purchase-columns">
              <div className="staff-dashboard__purchase-column">
                <h3><span>ONLINE</span> 온라인 구매 <b>{purchases.online.length}</b></h3>
                <div className="staff-dashboard__purchase-list">
                  {purchases.online.map((product) => <ProductCard key={product.purchase_id} product={product} />)}
                  {!purchases.online.length && <p className="staff-dashboard__empty-copy">최근 온라인 구매가 없습니다.</p>}
                </div>
              </div>
              <div className="staff-dashboard__purchase-column">
                <h3><span>STORE</span> 오프라인 구매 <b>{purchases.offline.length}</b></h3>
                <div className="staff-dashboard__purchase-list">
                  {purchases.offline.map((product) => <ProductCard key={product.purchase_id} product={product} />)}
                  {!purchases.offline.length && <p className="staff-dashboard__empty-copy">최근 오프라인 구매가 없습니다.</p>}
                </div>
              </div>
            </div>
          </section>
        </div>
      )}
    </StaffShell>
  );
}
