import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  claimStaffVisit,
  fetchStaffCustomer,
  fetchStaffVisits,
  getAuthUser,
  openRealtime,
  updateStaffVisitStatus,
} from '../../api/client';
import { saveStaffActiveVisit } from '../../utils/staffSession';
import { createMockTasteReport } from '../../utils/staffTasteReport';
import './StaffWaiting.css';

// [Frontend-03-'직원 대기열 및 실시간 배정 연동']
export default function StaffWaiting() {
  const navigate = useNavigate();
  const staffUser = getAuthUser();
  const storeId = staffUser?.store_id;
  const [visits, setVisits] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [claimingId, setClaimingId] = useState(null);
  const [connectionState, setConnectionState] = useState('연결 중');
  const [errorMessage, setErrorMessage] = useState('');

  const syncQueue = useCallback(async () => {
    if (!storeId) return;
    try {
      const response = await fetchStaffVisits(storeId);
      setVisits(response.items);
      setErrorMessage('');
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsLoading(false);
    }
  }, [storeId]);

  useEffect(() => {
    if (staffUser?.role !== 'STAFF' || !storeId) {
      navigate('/login', { replace: true });
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
      socket.onopen = () => setConnectionState('실시간 연결됨');
      socket.onmessage = (message) => {
        const payload = JSON.parse(message.data);
        if (payload.event === 'PING') {
          socket.send(JSON.stringify({ event: 'PING' }));
          return;
        }
        if (['VISIT_WAITING', 'STAFF_ASSIGNED', 'VISIT_COMPLETED'].includes(payload.event)) syncQueue();
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
      const profile = await fetchStaffCustomer(visit.customer_id);
      const serving = await updateStaffVisitStatus(visit.checkin_id, 'SERVING');
      const tasteReport = createMockTasteReport(profile, visit);
      saveStaffActiveVisit({ visit, profile, tasteReport, assignment: { ...assignment, ...serving } });
      navigate('/staff/recommend');
    } catch (error) {
      setErrorMessage(error.message);
      await syncQueue();
    } finally {
      setClaimingId(null);
    }
  };

  return (
    <div className={`staff-waiting-page ${visits.length ? 'staff-waiting-page--checked-in' : ''}`}>
      <header className="waiting-topbar">
        <div className="waiting-brand-box">
          <div className="waiting-brand-icon" aria-hidden="true">⌂</div>
          <span className="waiting-brand-name">M-Journey</span>
        </div>
        <span className="waiting-connection">{connectionState}</span>
      </header>

      <main className="waiting-stage">
        <div className="waiting-stage-label">대기 고객 {visits.length}명</div>
        {errorMessage && <p className="waiting-error" role="alert">{errorMessage}</p>}
        <div className="waiting-board" aria-label="직원 응대 대기열">
          <div className="waiting-board-body">
            {isLoading ? (
              <div className="waiting-empty-message">대기열을 불러오고 있습니다.</div>
            ) : visits.length ? (
              <div className="waiting-queue-list">
                {visits.map((visit) => (
                  <article className="waiting-queue-row" key={visit.checkin_id}>
                    <p><strong>{visit.masked_name}</strong> 고객님</p>
                    <button type="button" disabled={Boolean(claimingId)} className="waiting-cta" onClick={() => handleClaim(visit)}>
                      {claimingId === visit.checkin_id ? '처리 중...' : '응대'}
                    </button>
                  </article>
                ))}
              </div>
            ) : (
              <div className="waiting-empty-message">현재 직원 응대를 기다리는 고객이 없습니다.</div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
