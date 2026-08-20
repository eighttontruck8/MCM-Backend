import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchCheckin, openRealtime } from '../../api/client';
import { getCheckin, saveCheckin } from '../../utils/checkinSession';
import './VisitInfoCompletePage.css';

const PURPOSE_LABELS = {
  GIFT: '선물 구매',
  SEASON_UPDATE: '시즌 코디 업데이트',
  SPECIAL_EVENT: '특별 행사 준비',
  BUSINESS_TRIP: '출장 준비',
  FREE_SHOPPING: '자유 쇼핑',
  OTHER: '기타',
};

// [Frontend-02-'쇼핑 방식 및 직원 응대 요청 연동']
export default function VisitInfoCompletePage() {
  const navigate = useNavigate();
  const [checkin] = useState(() => getCheckin());
  const checkinId = checkin?.checkin_id;
  const waitMinutes = checkin?.estimated_wait_minutes ?? 1;
  const purpose = PURPOSE_LABELS[checkin?.visit_purpose?.code] ?? '방문 목적';
  const [connectionState, setConnectionState] = useState('연결 중');

  const applyCheckinState = useCallback((nextCheckin) => {
    const assignedStaff = nextCheckin.assigned_staff ?? nextCheckin.staff;
    saveCheckin({ ...checkin, ...nextCheckin, assigned_staff: assignedStaff });
    if (assignedStaff || ['ASSIGNED', 'SERVING'].includes(nextCheckin.status)) {
      navigate('/staff-assignment', { replace: true });
    }
  }, [checkin, navigate]);

  useEffect(() => {
    if (!checkinId) {
      navigate('/check-in', { replace: true });
      return undefined;
    }

    let socket;
    let reconnectTimer;
    let disposed = false;
    const syncCheckin = async () => {
      try {
        applyCheckinState(await fetchCheckin(checkinId));
      } catch {
        setConnectionState('상태 확인 실패');
      }
    };
    const connect = () => {
      if (disposed) return;
      try {
        socket = openRealtime('/api/v1/ws/customers/me');
      } catch {
        setConnectionState('실시간 연결 실패');
        return;
      }
      socket.onopen = () => setConnectionState('배정 알림 연결됨');
      socket.onmessage = (message) => {
        const payload = JSON.parse(message.data);
        if (payload.event === 'PING') {
          socket.send(JSON.stringify({ event: 'PING' }));
        } else if (payload.event === 'STAFF_ASSIGNED' && payload.data.checkin_id === checkinId) {
          applyCheckinState(payload.data);
        } else if (payload.event === 'VISIT_COMPLETED' && payload.data.checkin_id === checkinId) {
          saveCheckin({ ...checkin, ...payload.data });
        }
      };
      socket.onclose = () => {
        if (disposed) return;
        setConnectionState('재연결 중');
        reconnectTimer = window.setTimeout(async () => {
          await syncCheckin();
          connect();
        }, 2000);
      };
      socket.onerror = () => socket.close();
    };
    syncCheckin().finally(connect);
    return () => {
      disposed = true;
      window.clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [applyCheckinState, checkin, checkinId, navigate]);

  return (
    <div className="visit-info-complete-page">
      <div className="visit-info-complete-page__body">
        <div className="visit-info-complete-page__app">
          <div className="visit-info-complete-page__screen">
            <p className="visit-info-complete-page__eyebrow">Staff Assistance</p>
            <div className="visit-info-complete-page__icon" aria-hidden="true">✓</div>
            <div className="visit-info-complete-page__title">
              <p>웨이팅을 기다리고 있습니다...</p>
            </div>
            <p className="visit-info-complete-page__description">
              담당 직원이 요청을 확인하고 있습니다.<br />응대가 시작되면 자동으로 안내해 드립니다.
            </p>
            <div className="visit-info-complete-page__status-card">
              <div><span>현재 상태</span><strong>웨이팅 중</strong></div>
              <div><span>대기시간</span><strong>약 {waitMinutes}분</strong></div>
              <div><span>방문 목적</span><strong>{purpose}</strong></div>
              <div><span>알림 상태</span><strong>{connectionState}</strong></div>
            </div>
            <button type="button" className="visit-info-complete-page__button" onClick={() => navigate('/main')}>
              쇼핑 둘러보기
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
