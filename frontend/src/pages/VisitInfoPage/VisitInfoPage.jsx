import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createServiceRequest } from '../../api/client';
import { getCheckin, saveCheckin } from '../../utils/checkinSession';
import './VisitInfoPage.css';

const PURPOSE_OPTIONS = [
  { code: 'GIFT', label: '선물 구매' },
  { code: 'SEASON_UPDATE', label: '시즌 코디 업데이트' },
  { code: 'SPECIAL_EVENT', label: '특별 행사 준비' },
  { code: 'FREE_SHOPPING', label: '자유 쇼핑' },
];

const CONSENT = {
  agreed: true,
  policy_version: 'staff-profile-share-v1',
  scopes: ['PURCHASE_HISTORY', 'STYLE_PROFILE'],
};

// [Frontend-02-'쇼핑 방식 및 직원 응대 요청 연동']
export default function VisitInfoPage() {
  const navigate = useNavigate();
  const [isAgreed, setIsAgreed] = useState(false);
  const [selectedPurpose, setSelectedPurpose] = useState('FREE_SHOPPING');
  const [note, setNote] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async () => {
    if (!isAgreed) {
      setErrorMessage('직원에게 정보를 공유하려면 필수 동의가 필요합니다.');
      return;
    }

    const checkin = getCheckin();
    if (!checkin?.checkin_id) {
      navigate('/check-in', { replace: true });
      return;
    }
    if (checkin.shopping_mode !== 'STAFF_ASSISTED') {
      navigate('/shopping-option', { replace: true });
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');
    const visitPurpose = { code: selectedPurpose, note: note.trim() || null };
    try {
      const response = await createServiceRequest(checkin.checkin_id, CONSENT, visitPurpose);
      saveCheckin({ ...checkin, ...response, visit_purpose: visitPurpose });
      navigate('/visit-info-complete');
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="visit-info-page" data-node-id="7:1178" data-name="고객 입력2">
      <div className="visit-info-page__body">
        <div className="visit-info-page__app">
          <div className="visit-info-page__screen">
            <div className="visit-info-page__header">
              <p className="visit-info-page__eyebrow">맞춤 응대 준비</p>
              <div className="visit-info-page__title">
                <p>개인화 서비스</p>
                <p>동의 및 방문 정보</p>
              </div>
            </div>

            <div className="visit-info-page__consent-panel">
              <p className="visit-info-page__section-label">필수 동의</p>
              <p className="visit-info-page__consent-copy">담당 직원에게 아래 정보를 공유하는 데 동의합니다.</p>
              <div className="visit-info-page__consent-list">
                {['구매 이력 및 관심 상품', '사이즈 · 취향 프로필'].map((label) => (
                  <div className="visit-info-page__consent-item" key={label}>
                    <span className="visit-info-page__consent-bullet">◈</span>
                    <span className="visit-info-page__consent-text">{label}</span>
                  </div>
                ))}
              </div>
              <label className={`visit-info-page__agreement ${isAgreed ? 'visit-info-page__agreement--checked' : ''}`}>
                <input
                  type="checkbox"
                  className="visit-info-page__checkbox-input"
                  checked={isAgreed}
                  onChange={(event) => setIsAgreed(event.target.checked)}
                />
                <span className={`visit-info-page__checkbox ${isAgreed ? 'visit-info-page__checkbox--checked' : ''}`} aria-hidden="true">
                  {isAgreed ? '✓' : ''}
                </span>
                <span className="visit-info-page__agreement-text">위 정보 공유에 동의합니다</span>
              </label>
            </div>

            <div className="visit-info-page__purpose-section">
              <p className="visit-info-page__section-label visit-info-page__section-label--purpose">
                <span className="visit-info-page__section-label-text">방문 목적 </span>
                <span className="visit-info-page__section-label-highlight">선택</span>
              </p>
              <div className="visit-info-page__purpose-grid">
                {PURPOSE_OPTIONS.map((purpose) => (
                  <button
                    key={purpose.code}
                    type="button"
                    disabled={isSubmitting}
                    className={`visit-info-page__pill ${selectedPurpose === purpose.code ? 'visit-info-page__pill--selected' : ''}`}
                    onClick={() => setSelectedPurpose(purpose.code)}
                  >
                    {purpose.label}
                  </button>
                ))}
              </div>
              <div className="visit-info-page__input-group">
                <textarea
                  className="visit-info-page__text-input"
                  value={note}
                  maxLength={500}
                  rows={2}
                  placeholder="직원에게 전할 내용을 입력해주세요."
                  onChange={(event) => setNote(event.target.value)}
                />
              </div>
            </div>

            {errorMessage && <p className="visit-info-page__error" role="alert">{errorMessage}</p>}
            <button
              type="button"
              disabled={isSubmitting}
              className={`visit-info-page__submit ${isAgreed ? 'visit-info-page__submit--active' : ''}`}
              onClick={handleSubmit}
            >
              {isSubmitting ? '요청 중...' : '직원 배정 요청'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
