import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  STAFF_CHECKIN_EVENT,
  STAFF_VISIT_STATE_EVENT,
  readStaffVisitState,
} from '../../utils/staffCheckinSignal';
import './StaffDashboard.css';

const customerList = [
  {
    id: 'C001',
    name: '김서윤',
    age: 29,
    gender: '여성',
    totalVisits: 4,
    status: '응대중',
    styleProfile: '모노톤 미니멀 럭셔리',
    preferredColors: ['블랙', '화이트', '베이지'],
    preferredFit: '오버사이즈',
    recentInterest: ['가을 아우터', '캐시미어 니트'],
    lastVisit: '2026.08.14',
    note: '정장형 실루엣을 선호하고, 고급스러운 소재를 중요하게 생각합니다.',
  },
  {
    id: 'C002',
    name: '이준호',
    age: 34,
    gender: '남성',
    totalVisits: 2,
    status: '방금 퇴실',
    styleProfile: '클래식 인터내셔널',
    preferredColors: ['네이비', '그레이', '아이보리'],
    preferredFit: '슬림핏',
    recentInterest: ['울 코트', '드레스 셔츠'],
    lastVisit: '2026.08.13',
    note: '트렌디한 세미포멀 룩을 선호하며, 손질이 정교한 원단을 중요하게 봅니다.',
  },
  {
    id: 'C003',
    name: '박하린',
    age: 27,
    gender: '여성',
    totalVisits: 6,
    status: '응대중',
    styleProfile: '소프트 로맨틱',
    preferredColors: ['카키', '베이지', '크림'],
    preferredFit: 'A라인',
    recentInterest: ['플레어 코트', '니트 세트'],
    lastVisit: '2026.08.12',
    note: '부드러운 소재감과 여성스러운 실루엣을 우선시합니다.',
  },
  {
    id: 'C004',
    name: '최민수',
    age: 41,
    gender: '남성',
    totalVisits: 1,
    status: '방금 퇴실',
    styleProfile: '모던 컨템포러리',
    preferredColors: ['다크 그레이', '블랙', '브라운'],
    preferredFit: '레귤러핏',
    recentInterest: ['울 자켓', '니트 가디건'],
    lastVisit: '2026.08.11',
    note: '실용성과 고급스러움을 함께 추구하는 편입니다.',
  },
];

export default function StaffDashboard() {
  const navigate = useNavigate();
  const [selectedCustomerId, setSelectedCustomerId] = useState('C001');
  const [activeTab, setActiveTab] = useState('AI 분석');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [liveCustomer, setLiveCustomer] = useState(() => readStaffVisitState().customer);

  useEffect(() => {
    const syncLiveCustomer = () => {
      const nextState = readStaffVisitState();
      setLiveCustomer(nextState.customer);

      if (nextState.customer?.customer_id) {
        setSelectedCustomerId(nextState.customer.customer_id);
      }
    };

    syncLiveCustomer();

    const handleStorageSync = () => syncLiveCustomer();

    window.addEventListener('storage', handleStorageSync);
    window.addEventListener(STAFF_CHECKIN_EVENT, handleStorageSync);
    window.addEventListener(STAFF_VISIT_STATE_EVENT, handleStorageSync);

    return () => {
      window.removeEventListener('storage', handleStorageSync);
      window.removeEventListener(STAFF_CHECKIN_EVENT, handleStorageSync);
      window.removeEventListener(STAFF_VISIT_STATE_EVENT, handleStorageSync);
    };
  }, []);

  const selectedCustomer = useMemo(() => {
    if (liveCustomer && typeof liveCustomer === 'object') {
      return {
        ...customerList[0],
        id: liveCustomer.customer_id ?? 'C001',
        name: liveCustomer.name ?? '김**',
        age: liveCustomer.age ?? 34,
        gender: liveCustomer.gender ?? '여성',
        totalVisits: liveCustomer.visit_count ?? 4,
        status: '응대중',
        styleProfile: liveCustomer.style_tags?.join(', ') ?? '미니멀 럭셔리',
        preferredColors: liveCustomer.preferred_colors ?? ['블랙', '화이트', '베이지'],
        preferredFit: liveCustomer.preferred_fit ?? '오버사이즈',
        recentInterest: liveCustomer.recent_interests ?? ['가을 아우터'],
        lastVisit: liveCustomer.visitDate ?? '2026.08.14',
        note: '체크인 시점에 전달된 고객 응대 정보를 반영한 프로필입니다.',
      };
    }

    return customerList.find((customer) => customer.id === selectedCustomerId) ?? customerList[0];
  }, [liveCustomer, selectedCustomerId]);

  const getStatusStyle = (status) => ({
    background: status === '응대중' ? 'rgba(118, 171, 133, 0.12)' : 'rgba(255, 255, 255, 0.04)',
    color: status === '응대중' ? '#8ad8a8' : '#d8c6a3',
    border: status === '응대중' ? '1px solid rgba(119, 211, 153, 0.38)' : '1px solid rgba(255,255,255,0.08)',
  });

  return (
    <div className="staff-dashboard-page">
      <div className={`staff-dashboard-shell ${isSidebarOpen ? 'staff-dashboard-shell--open' : ''}`}>
        <aside className="staff-dashboard-sidebar">
          <div className="staff-dashboard-sidebar-header">
            <h2 className="staff-dashboard-heading">고객 목록</h2>
            <span className="staff-dashboard-filter-pill">실시간</span>
          </div>

          <div className="staff-dashboard-list">
            {customerList.map((customer) => {
              const isSelected = customer.id === selectedCustomer.id;

              return (
                <button
                  key={customer.id}
                  type="button"
                  onClick={() => setSelectedCustomerId(customer.id)}
                  className={`staff-dashboard-customer-card ${
                    isSelected ? 'staff-dashboard-customer-card--selected' : ''
                  }`}
                >
                  <div className="staff-dashboard-avatar">{customer.name.charAt(0)}</div>

                  <div className="staff-dashboard-customer-meta">
                    <div className="staff-dashboard-row">
                      <p className="staff-dashboard-customer-name">{customer.name}</p>
                      <span
                        className={`staff-dashboard-status-badge ${
                          customer.status === '응대중'
                            ? 'staff-dashboard-status-badge--active'
                            : 'staff-dashboard-status-badge--left'
                        }`}
                      >
                        {customer.status}
                      </span>
                    </div>

                    <p className="staff-dashboard-customer-id">{customer.id}</p>

                    <div className="staff-dashboard-info-row">
                      <span>{customer.age}세</span>
                      <span className="staff-dashboard-dot" />
                      <span>{customer.gender}</span>
                    </div>

                    <div className="staff-dashboard-info-row">
                      <span>총 {customer.totalVisits}회 방문</span>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </aside>

        <main className="staff-dashboard-main">
          <header className="staff-dashboard-top-header">
            <div className="staff-dashboard-title-wrap">
              <button
                type="button"
                className="staff-dashboard-toggle-button"
                onClick={() => setIsSidebarOpen((prev) => !prev)}
                aria-label={isSidebarOpen ? '고객 목록 닫기' : '고객 목록 열기'}
              >
                {isSidebarOpen ? '목록 닫기' : '고객 목록'}
              </button>
              <span className="staff-dashboard-customer-badge">{selectedCustomer.id}</span>
              <h1 className="staff-dashboard-top-title">고객 프로필</h1>
            </div>
          </header>

          <section className="staff-dashboard-summary-card">
            <div className="staff-dashboard-profile-card">
              <div className="staff-dashboard-profile-header">
                <div className="staff-dashboard-large-avatar">{selectedCustomer.name.charAt(0)}</div>

                <div className="staff-dashboard-profile-text">
                  <p className="staff-dashboard-profile-name">{selectedCustomer.name}</p>

                  <div className="staff-dashboard-profile-info">
                    <span className="staff-dashboard-info-pill">{selectedCustomer.age}세</span>
                    <span className="staff-dashboard-info-pill">{selectedCustomer.gender}</span>
                    <span className="staff-dashboard-info-pill">총 {selectedCustomer.totalVisits}회 방문</span>
                    <span className="staff-dashboard-info-pill">최근 방문 {selectedCustomer.lastVisit}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="staff-dashboard-note-card">
              <p className="staff-dashboard-note-label">메모</p>
              <p className="staff-dashboard-note-text">{selectedCustomer.note}</p>
            </div>
          </section>

          <section className="staff-dashboard-detail-grid">
            <div className="staff-dashboard-detail-card">
              <p className="staff-dashboard-detail-label">스타일 프로필</p>
              <div className="staff-dashboard-detail-value">{selectedCustomer.styleProfile}</div>
            </div>

            <div className="staff-dashboard-detail-card">
              <p className="staff-dashboard-detail-label">선호 색상</p>
              <div className="staff-dashboard-tag-group">
                {selectedCustomer.preferredColors.map((color) => (
                  <span key={color} className="staff-dashboard-tag">{color}</span>
                ))}
              </div>
            </div>

            <div className="staff-dashboard-detail-card">
              <p className="staff-dashboard-detail-label">선호 핏</p>
              <div className="staff-dashboard-detail-value">{selectedCustomer.preferredFit}</div>
            </div>

            <div className="staff-dashboard-detail-card">
              <p className="staff-dashboard-detail-label">최근 관심 제품</p>
              <div className="staff-dashboard-tag-group">
                {selectedCustomer.recentInterest.map((item) => (
                  <span key={item} className="staff-dashboard-tag">{item}</span>
                ))}
              </div>
            </div>
          </section>

          <footer className="staff-dashboard-footer">
            <button
              type="button"
              onClick={() => {
                setActiveTab('AI 분석');
                navigate('/staff/analysis');
              }}
              className={`staff-dashboard-action-button ${
                activeTab === 'AI 분석' ? 'staff-dashboard-action-button--active' : ''
              }`}
            >
              AI 분석
            </button>

            <button
              type="button"
              onClick={() => {
                setActiveTab('AI 추천');
                navigate('/staff/recommend');
              }}
              className={`staff-dashboard-action-button ${
                activeTab === 'AI 추천' ? 'staff-dashboard-action-button--active' : ''
              }`}
            >
              AI 추천
            </button>
          </footer>
        </main>
      </div>
    </div>
  );
}
