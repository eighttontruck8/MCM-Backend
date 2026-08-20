import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  claimStaffVisit,
  fetchStaffCustomer,
  fetchStaffGuide,
  fetchStaffVisits,
  getAuthUser,
  openRealtime,
  updateStaffVisitStatus,
} from '../../api/client';
import StaffShell from '../../components/StaffShell/StaffShell';
import { saveStaffActiveVisit } from '../../utils/staffSession';
import { createMockTasteReport } from '../../utils/staffTasteReport';
import './StaffWaiting.css';

const PURPOSE_LABELS = {
  GIFT: '선물 구매',
  SEASON_UPDATE: '시즌 아이템 탐색',
  SPECIAL_EVENT: '특별한 일정',
  BUSINESS_TRIP: '출장 준비',
  FREE_SHOPPING: '자유 쇼핑',
  OTHER: '기타 상담',
};

const waitTime = (value) => {
  if (!value) return '방금 도착';
  const minutes = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 60000));
  return minutes < 1 ? '방금 도착' : `${minutes}분 대기`;
};

// [Frontend-Staff-04-'취향 미리보기 대기열'] 대기 카드 상단부터 고객별 질문과 최소 취향 정보만 표시한다.
export default function StaffWaiting() {
  const navigate = useNavigate();
  const staffUser = getAuthUser();
  const storeId = staffUser?.store_id;
  const [visits, setVisits] = useState([]);
  const [profiles, setProfiles] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [claimingId, setClaimingId] = useState(null);
  const [connectionState, setConnectionState] = useState('연결 중');
  const [errorMessage, setErrorMessage] = useState('');

  const syncQueue = useCallback(async () => {
    if (!storeId) return;
    try {
      const response = await fetchStaffVisits(storeId);
      setVisits(response.items);
      const profileEntries = await Promise.all(response.items.map(async (visit) => {
        try {
          return [visit.customer_id, await fetchStaffCustomer(visit.customer_id)];
        } catch {
          return [visit.customer_id, null];
        }
      }));
      setProfiles(Object.fromEntries(profileEntries));
      setErrorMessage('');
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsLoading(false);
    }
  }, [storeId]);

  useEffect(() => {
    if (staffUser?.role !== 'STAFF' || !storeId) {
      navigate('/login?role=staff', { replace: true });
      return undefined;
    }

    let socket;
    let reconnectTimer;
    let disposed = false;
    const connect = () => {
      if (disposed) return;
      try {
        socket = openRealtime(`/api/v1/ws/staff/stores/${encodeURIComponent(storeId)}`);
      } catch (error) {
        setConnectionState('연결 실패');
        setErrorMessage(error.message);
        return;
      }
      socket.onopen = () => setConnectionState('실시간 연결');
      socket.onmessage = (message) => {
        const payload = JSON.parse(message.data);
        if (payload.event === 'PING') {
          socket.send(JSON.stringify({ event: 'PING' }));
          return;
        }
        if (['VISIT_WAITING', 'STAFF_ASSIGNED', 'VISIT_COMPLETED', 'VISIT_CANCELLED'].includes(payload.event)) syncQueue();
      };
      socket.onclose = () => {
        if (disposed) return;
        setConnectionState('재연결 중');
        reconnectTimer = window.setTimeout(async () => {
          await syncQueue();
          connect();
        }, 2000);
      };
      socket.onerror = () => socket.close();
    };

    reconnectTimer = window.setTimeout(() => syncQueue().finally(connect), 0);
    return () => {
      disposed = true;
      window.clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [navigate, staffUser?.role, storeId, syncQueue]);

  const handleClaim = async (visit) => {
    setClaimingId(visit.checkin_id);
    setErrorMessage('');
    try {
      const assignment = await claimStaffVisit(visit.checkin_id);
      const profile = profiles[visit.customer_id] ?? await fetchStaffCustomer(visit.customer_id);
      let guide = null;
      try {
        guide = await fetchStaffGuide(visit.checkin_id);
      } catch {
        // AI 장애가 직원 배정 흐름을 막지 않도록 mock 취향 리포트로 계속 진행한다.
      }
      const serving = await updateStaffVisitStatus(visit.checkin_id, 'SERVING');
      const tasteReport = createMockTasteReport(profile, visit);
      saveStaffActiveVisit({ visit, profile, guide, tasteReport, assignment: { ...assignment, ...serving } });
      navigate('/staff');
    } catch (error) {
      setErrorMessage(error.message);
      await syncQueue();
    } finally {
      setClaimingId(null);
    }
  };

  return (
    <StaffShell active="waiting" connectionState={connectionState} queueCount={visits.length}>
      <section className="staff-waiting__heading">
        <div>
          <span>CLIENT WAITING LIST</span>
          <h1>웨이팅 리스트</h1>
          <p>도착 순서대로 고객의 공유된 취향을 확인하고 응대를 시작하세요.</p>
        </div>
        <strong>{visits.length}<small>WAITING</small></strong>
      </section>

      {errorMessage && <p className="staff-waiting__error" role="alert">{errorMessage}</p>}

      <section className="staff-waiting__board" aria-label="직원 응대 대기열">
        {isLoading ? (
          <p className="staff-waiting__empty">대기열을 불러오고 있습니다.</p>
        ) : visits.length ? (
          <div className="staff-waiting__list">
            {visits.map((visit, index) => {
              const profile = profiles[visit.customer_id];
              const colors = profile?.preferred_colors ?? [];
              return (
                <article className="staff-waiting__card" key={visit.checkin_id}>
                  <div className="staff-waiting__order">{String(index + 1).padStart(2, '0')}</div>
                  <div className="staff-waiting__avatar">{visit.masked_name.charAt(0)}</div>
                  <div className="staff-waiting__customer">
                    <div className="staff-waiting__customer-meta">
                      <span>{visit.membership}</span><span>{waitTime(visit.waiting_since)}</span>
                    </div>
                    <h2>{visit.masked_name}님의 응대를 담당하시겠습니까?</h2>
                    <p>{profile?.preferred_style ?? '공유된 취향 정보를 확인 중입니다.'}</p>
                    <div className="staff-waiting__tags">
                      <span>{PURPOSE_LABELS[visit.visit_purpose] ?? visit.visit_purpose}</span>
                      {colors.slice(0, 3).map((color) => <span key={color}>#{color}</span>)}
                    </div>
                  </div>
                  <button type="button" disabled={Boolean(claimingId)} onClick={() => handleClaim(visit)}>
                    {claimingId === visit.checkin_id ? '수락 중' : '응대 수락'}
                  </button>
                </article>
              );
            })}
          </div>
        ) : (
          <div className="staff-waiting__empty">
            <span>✓</span>
            <strong>현재 대기 중인 고객이 없습니다.</strong>
            <p>새 고객이 체크인하면 이 박스의 위쪽부터 표시됩니다.</p>
          </div>
        )}
      </section>
    </StaffShell>
  );
}
