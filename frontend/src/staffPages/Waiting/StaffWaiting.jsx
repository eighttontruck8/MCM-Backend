import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  readStaffVisitState,
  STAFF_CHECKIN_EVENT,
  STAFF_CHECKIN_STORAGE_KEY,
  STAFF_VISIT_STATE_EVENT,
  STAFF_VISIT_STATE_KEY,
  markStaffVisitServing,
} from '../../utils/staffCheckinSignal';
import './StaffWaiting.css';

const toolbarIcons = ['✎', '◌', '⌂', '#', '❒', '▢', '◧', '⌁', '◫', '⟡'];

const defaultCustomer = {
  name: '김** 고객',
  totalVisits: 28,
  phone: '010-****-3374',
  visitDate: '2026년 8월 13일',
};

export default function StaffWaiting() {
  const navigate = useNavigate();
  const [showAlert, setShowAlert] = useState(false);
  const [visitState, setVisitState] = useState(() => readStaffVisitState());

  const customer = visitState.customer ?? defaultCustomer;
  const customerName = customer.name ?? defaultCustomer.name;
  const customerVisits = customer.visit_count ?? customer.totalVisits ?? defaultCustomer.totalVisits;
  const customerPhone = customer.phone ?? defaultCustomer.phone;
  const customerVisitDate = customer.visitDate ?? new Date(visitState.updatedAt ?? Date.now()).toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
  const wishlist = visitState.wishlist ?? [];
  const recentlyViewed = visitState.recentlyViewed ?? [];
  const purchaseHistory = visitState.purchaseHistory ?? [];

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const syncStateFromStorage = () => {
      const nextState = readStaffVisitState();
      setVisitState(nextState);
      setShowAlert(nextState.status !== 'waiting');
    };

    syncStateFromStorage();

    const handleStorageChange = (event) => {
      if (
        event.key === STAFF_CHECKIN_STORAGE_KEY ||
        event.key === STAFF_VISIT_STATE_KEY ||
        event.type === 'storage'
      ) {
        syncStateFromStorage();
      }
    };

    const handleCustomEvent = () => {
      syncStateFromStorage();
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener(STAFF_CHECKIN_EVENT, handleCustomEvent);
    window.addEventListener(STAFF_VISIT_STATE_EVENT, handleCustomEvent);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener(STAFF_CHECKIN_EVENT, handleCustomEvent);
      window.removeEventListener(STAFF_VISIT_STATE_EVENT, handleCustomEvent);
    };
  }, []);

  return (
    <div className={`staff-waiting-page ${showAlert ? 'staff-waiting-page--checked-in' : ''}`}>
      <header className="waiting-topbar">
        <div className="waiting-brand-box">
          <div className="waiting-brand-icon" aria-hidden="true">
            ⌂
          </div>
          <span className="waiting-brand-name">M-Journey</span>
        </div>
      </header>

      <main className="waiting-stage">
        <div className="waiting-stage-label">{showAlert ? '체크인한 고객이 있습니다.' : '대기중'}</div>

        <div className="waiting-board" aria-label="waiting board">
          <div className="waiting-board-header">
            <div className="waiting-board-flag">M JOURNEY</div>
            <span className="waiting-board-time">00:00</span>
          </div>

          <div className="waiting-board-body">
            {showAlert ? (
              <div className="waiting-alert-card" aria-live="polite">
                <div className="waiting-alert-header">
                  <h2 className="waiting-alert-title">체크인 완료 고객</h2>
                  <span className="waiting-alert-badge">완료</span>
                </div>

                <div className="waiting-alert-body">
                  <div className="waiting-customer-row">
                    <div className="waiting-avatar">{customerName.charAt(0) || '김'}</div>
                    <div className="waiting-customer-info">
                      <p className="waiting-customer-name">{customerName}</p>
                      <p className="waiting-customer-sub">총 {customerVisits}회 방문</p>
                    </div>
                  </div>

                  <div className="waiting-detail-grid">
                    <div className="waiting-detail-box">
                      <span className="waiting-detail-label">연락처</span>
                      <div className="waiting-detail-value">{customerPhone}</div>
                    </div>

                    <div className="waiting-detail-box">
                      <span className="waiting-detail-label">방문 일시</span>
                      <div className="waiting-detail-value">{customerVisitDate}</div>
                    </div>
                  </div>

                  <div className="waiting-transfer-block">
                    <div className="waiting-transfer-section">
                      <span className="waiting-transfer-label">최근 구매 이력</span>
                      <div className="waiting-transfer-list">
                        {purchaseHistory.slice(0, 2).map((item) => (
                          <span key={item.id ?? item.product} className="waiting-transfer-pill">
                            {item.product}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="waiting-transfer-section">
                      <span className="waiting-transfer-label">관심 상품</span>
                      <div className="waiting-transfer-list">
                        {wishlist.slice(0, 3).map((item) => (
                          <span key={item} className="waiting-transfer-pill">
                            {item}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="waiting-transfer-section">
                      <span className="waiting-transfer-label">최근 본 상품</span>
                      <div className="waiting-transfer-list">
                        {recentlyViewed.slice(0, 2).map((item) => (
                          <span key={item.product_id} className="waiting-transfer-pill">
                            {item.name}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <button
                    type="button"
                    className="waiting-cta"
                    onClick={() => {
                      const nextState = markStaffVisitServing({
                        customer,
                        wishlist,
                        recentlyViewed,
                        purchaseHistory,
                      });
                      setVisitState(nextState);
                      setShowAlert(nextState.status !== 'waiting');
                      navigate('/staff');
                    }}
                  >
                    고객 응대 시작하기
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="waiting-status-pill">◌</div>

                <div className="waiting-empty-message">
                  <div className="waiting-message-row">
                    <span className="waiting-message-dot" aria-hidden="true" />
                    <span className="waiting-message-text">현재 체크인된 고객이 없습니다.</span>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

      </main>
    </div>
  );
}
