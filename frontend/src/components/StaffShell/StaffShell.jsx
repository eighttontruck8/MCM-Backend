import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAuthUser, logout } from '../../api/client';
import { clearStaffActiveVisit } from '../../utils/staffSession';
import './StaffShell.css';

const NAV_ITEMS = [
  { id: 'waiting', label: '웨이팅 리스트', icon: '☷', path: '/staff/waiting' },
  { id: 'profile', label: '마이페이지', icon: '○' },
  { id: 'settings', label: '설정', icon: '⚙' },
  { id: 'logout', label: '로그아웃', icon: '↗' },
];

// [Frontend-Staff-02-'직원 공통 화이트 골드 셸'] 직원 이름, 상태와 핵심 기능을 모든 주요 화면에서 동일하게 제공한다.
export default function StaffShell({ children, active = 'dashboard', connectionState = '근무 중', queueCount = 0 }) {
  const navigate = useNavigate();
  const staff = getAuthUser();
  const [openPanel, setOpenPanel] = useState(null);
  const [realtimeNotice, setRealtimeNotice] = useState(true);

  const handleNav = async (item) => {
    if (item.path) {
      navigate(item.path);
      return;
    }
    if (item.id === 'logout') {
      if (!window.confirm(`${staff?.display_name ?? '직원'} 쇼퍼님, 로그아웃하시겠습니까?`)) return;
      clearStaffActiveVisit();
      await logout().catch(() => undefined);
      navigate('/login?role=staff', { replace: true });
      return;
    }
    setOpenPanel((current) => current === item.id ? null : item.id);
  };

  return (
    <div className={`staff-shell staff-shell--${active}`}>
      <header className="staff-shell__header">
        <button type="button" className="staff-shell__brand" onClick={() => navigate('/staff')}>
          <span className="staff-shell__brand-mark">M</span>
          <span><strong>M·Journey</strong><small>Clienteling</small></span>
        </button>

        <div className="staff-shell__account">
          <div className="staff-shell__identity">
            <div className="staff-shell__identity-copy">
              <strong>{staff?.display_name ?? '직원'} 쇼퍼님</strong>
              <span>{staff?.store_id ?? 'STORE'} · {connectionState}</span>
            </div>
            <span className="staff-shell__presence" aria-label="근무 중" />
          </div>

          <nav className="staff-shell__nav" aria-label="직원 메뉴">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.id}
                type="button"
                className={`staff-shell__nav-button ${active === item.id ? 'staff-shell__nav-button--active' : ''}`}
                aria-label={item.label}
                title={item.label}
                onClick={() => handleNav(item)}
              >
                <span aria-hidden="true">{item.icon}</span>
                {item.id === 'waiting' && queueCount > 0 && <b>{queueCount}</b>}
              </button>
            ))}
          </nav>

          {openPanel === 'profile' && (
            <section className="staff-shell__popover" aria-label="직원 마이페이지">
              <p className="staff-shell__popover-eyebrow">MY PROFILE</p>
              <strong>{staff?.display_name ?? '직원'} 쇼퍼</strong>
              <span>사번 {staff?.id ?? '-'}</span>
              <span>소속 매장 {staff?.store_id ?? '-'}</span>
              <span className="staff-shell__popover-status">● 현재 근무 중</span>
            </section>
          )}

          {openPanel === 'settings' && (
            <section className="staff-shell__popover" aria-label="직원 설정">
              <p className="staff-shell__popover-eyebrow">SETTINGS</p>
              <label className="staff-shell__setting-row">
                <span>실시간 대기 알림</span>
                <input type="checkbox" checked={realtimeNotice} onChange={(event) => setRealtimeNotice(event.target.checked)} />
              </label>
              <p className="staff-shell__setting-help">고객 정보는 활성 응대와 동의가 확인된 경우에만 표시됩니다.</p>
            </section>
          )}
        </div>
      </header>
      <main className="staff-shell__content">{children}</main>
    </div>
  );
}
