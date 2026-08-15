import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { buildCustomerVisitPayload, triggerStaffCheckin } from '../../utils/staffCheckinSignal';
import './VisitInfoPage.css';

export default function VisitInfoPage() {
  const navigate = useNavigate();
  const [isAgreed, setIsAgreed] = useState(false);
  const [selectedPurpose, setSelectedPurpose] = useState('');

  const purposeOptions = ['선물 구매', '시즌 코디 업데이트', '특별 행사 준비', '자유 쇼핑'];

  const handleAgreementToggle = () => {
    setIsAgreed((prev) => !prev);
  };

  const handleSubmit = () => {
    if (!isAgreed) {
      setIsAgreed(true);
      return;
    }

    const customerPayload = buildCustomerVisitPayload({
      customer_id: 'C001',
      name: '김**',
      age: 34,
      gender: '여성',
      visit_count: 28,
      total_purchase: 12500000,
      style_tags: ['미니멀 럭셔리', '모노톤 선호'],
      preferred_colors: ['블랙', '화이트', '베이지'],
      preferred_fit: '오버사이즈 실루엣',
      recent_interests: ['가을 아우터', '캐시미어 니트'],
      phone: '010-****-3374',
      visitDate: '2026년 8월 14일',
      visitPurpose: selectedPurpose || '자유 쇼핑',
    });

    triggerStaffCheckin(customerPayload);
    navigate('/main');
  };

  return (
    <div className="visit-info-page" data-node-id="7:1178" data-name="고객 입력2">
      <div className="visit-info-page__body" data-node-id="7:1179" data-name="Body">
        <div className="visit-info-page__app" data-node-id="7:1181" data-name="App">
          <div className="visit-info-page__screen" data-node-id="7:1182" data-name="ConsentScreen">
            <div className="visit-info-page__header" data-node-id="7:1183" data-name="Container">
              <p className="visit-info-page__eyebrow" data-node-id="7:1185">
                맞춤 응대 준비
              </p>
              <div className="visit-info-page__title" data-node-id="7:1187" data-name="Heading 2">
                <p>개인화 서비스</p>
                <p>동의 및 방문 정보</p>
              </div>
            </div>

            <div className="visit-info-page__consent-panel" data-node-id="7:1191" data-name="Container">
              <p className="visit-info-page__section-label" data-node-id="7:1193">
                필수 동의
              </p>
              <p className="visit-info-page__consent-copy" data-node-id="7:1196">
                담당 직원에게 아래 정보를 공유하는 데 동의합니다.
              </p>

              <div className="visit-info-page__consent-list" data-node-id="7:1198" data-name="Container">
                <div className="visit-info-page__consent-item" data-node-id="7:1199">
                  <span className="visit-info-page__consent-bullet" data-node-id="7:1201">
                    ◈
                  </span>
                  <span className="visit-info-page__consent-text" data-node-id="7:1204">
                    구매 이력 및 관심 상품
                  </span>
                </div>
                <div className="visit-info-page__consent-item" data-node-id="7:1206">
                  <span className="visit-info-page__consent-bullet" data-node-id="7:1207">
                    ◈
                  </span>
                  <span className="visit-info-page__consent-text" data-node-id="7:1211">
                    사이즈 · 취향 프로필
                  </span>
                </div>
                <div className="visit-info-page__consent-item" data-node-id="7:1213">
                  <span className="visit-info-page__consent-bullet" data-node-id="7:1214">
                    ◈
                  </span>
                  <span className="visit-info-page__consent-text" data-node-id="7:1218">
                    AI 분석 스타일 리포트
                  </span>
                </div>
              </div>

              <label
                className={`visit-info-page__agreement ${isAgreed ? 'visit-info-page__agreement--checked' : ''}`}
                data-node-id="7:1227"
                data-name="Button:margin"
                onClick={handleAgreementToggle}
              >
                <span
                  className={`visit-info-page__checkbox ${isAgreed ? 'visit-info-page__checkbox--checked' : ''}`}
                  data-node-id="7:1221"
                  data-name="Container"
                >
                  {isAgreed ? '✓' : ''}
                </span>
                <span className="visit-info-page__agreement-text" data-node-id="7:1223">
                  위 정보 공유에 동의합니다
                </span>
              </label>
            </div>

            <div className="visit-info-page__purpose-section" data-node-id="7:1228" data-name="Container">
              <p className="visit-info-page__section-label visit-info-page__section-label--purpose" data-node-id="7:1230">
                <span className="visit-info-page__section-label-text">방문 목적 </span>
                <span className="visit-info-page__section-label-highlight">선택</span>
              </p>

              <div className="visit-info-page__purpose-grid" data-node-id="7:1248" data-name="Container:margin">
                {purposeOptions.map((purpose) => (
                  <button
                    key={purpose}
                    type="button"
                    className={`visit-info-page__pill ${selectedPurpose === purpose ? 'visit-info-page__pill--selected' : ''}`}
                    data-node-id="7:1233"
                    onClick={() => setSelectedPurpose(purpose)}
                  >
                    {purpose}
                  </button>
                ))}
              </div>

              <div className="visit-info-page__input-group" data-node-id="7:1249" data-name="Container:margin">
                <div className="visit-info-page__text-input" data-node-id="7:1246" data-name="Text Input">
                  <p className="visit-info-page__input-placeholder" data-node-id="7:1247">
                    직접 입력...
                  </p>
                </div>
              </div>
            </div>

            <button
              type="button"
              className={`visit-info-page__submit ${isAgreed ? 'visit-info-page__submit--active' : ''}`}
              data-node-id="7:1250"
              data-name="PrimaryBtn"
              onClick={handleSubmit}
            >
              직원 배정 요청
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
