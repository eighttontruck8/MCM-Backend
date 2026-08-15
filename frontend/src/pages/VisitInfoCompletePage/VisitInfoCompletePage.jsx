import { useNavigate } from 'react-router-dom';
import { getCheckin } from '../../utils/checkinSession';
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
  const checkin = getCheckin();
  const waitMinutes = checkin?.estimated_wait_minutes ?? 3;
  const purpose = PURPOSE_LABELS[checkin?.visit_purpose?.code] ?? '방문 목적';

  return (
    <div className="visit-info-complete-page">
      <div className="visit-info-complete-page__body">
        <div className="visit-info-complete-page__app">
          <div className="visit-info-complete-page__screen">
            <p className="visit-info-complete-page__eyebrow">Staff Assistance</p>
            <div className="visit-info-complete-page__icon" aria-hidden="true">✓</div>
            <div className="visit-info-complete-page__title">
              <p>직원 응대 요청이</p>
              <p>접수되었습니다</p>
            </div>
            <p className="visit-info-complete-page__description">
              담당 직원이 요청을 확인하고 있습니다.<br />배정 결과는 이 화면에서 실시간으로 안내할 예정입니다.
            </p>
            <div className="visit-info-complete-page__status-card">
              <div><span>현재 상태</span><strong>직원 배정 대기</strong></div>
              <div><span>예상 대기 시간</span><strong>약 {waitMinutes}분</strong></div>
              <div><span>방문 목적</span><strong>{purpose}</strong></div>
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
