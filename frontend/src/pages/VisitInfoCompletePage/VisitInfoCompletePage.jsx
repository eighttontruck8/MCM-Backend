import React from 'react';
import { buildCustomerVisitPayload, triggerStaffCheckin } from '../../utils/staffCheckinSignal';
import './VisitInfoCompletePage.css';

export default function VisitInfoCompletePage() {
  const handleNavigateToStaffAssignment = () => {
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
    });

    triggerStaffCheckin(customerPayload);
  };
  return (
    <div className="visit-info-complete-page" data-node-id="13:1705" data-name="고객 입력3">
      <div className="visit-info-complete-page__body" data-node-id="13:1706" data-name="Body">
        <div className="visit-info-complete-page__app" data-node-id="13:1708" data-name="App">
          <div className="visit-info-complete-page__screen" data-node-id="13:1709" data-name="ConsentScreen">
            <div className="visit-info-complete-page__header" data-node-id="13:1710" data-name="Container">
              <p className="visit-info-complete-page__eyebrow" data-node-id="13:1712">
                맞춤 응대 준비
              </p>
              <div className="visit-info-complete-page__title" data-node-id="13:1714" data-name="Heading 2">
                <p>개인화 서비스</p>
                <p>동의 및 방문 정보</p>
              </div>
            </div>

            <div className="visit-info-complete-page__consent-card" data-node-id="13:1718" data-name="Container">
              <p className="visit-info-complete-page__section-label" data-node-id="13:1720">
                필수 동의
              </p>
              <p className="visit-info-complete-page__consent-text" data-node-id="13:1723">
                담당 직원에게 아래 정보를 공유하는 데 동의합니다.
              </p>

              <div className="visit-info-complete-page__consent-list" data-node-id="13:1725" data-name="Container">
                <div className="visit-info-complete-page__consent-item" data-node-id="13:1726">
                  <span className="visit-info-complete-page__consent-bullet" data-node-id="13:1728">
                    ◈
                  </span>
                  <span className="visit-info-complete-page__consent-item-text" data-node-id="13:1731">
                    구매 이력 및 관심 상품
                  </span>
                </div>
                <div className="visit-info-complete-page__consent-item" data-node-id="13:1733">
                  <span className="visit-info-complete-page__consent-bullet" data-node-id="13:1735">
                    ◈
                  </span>
                  <span className="visit-info-complete-page__consent-item-text" data-node-id="13:1738">
                    사이즈 · 취향 프로필
                  </span>
                </div>
                <div className="visit-info-complete-page__consent-item" data-node-id="13:1740">
                  <span className="visit-info-complete-page__consent-bullet" data-node-id="13:1742">
                    ◈
                  </span>
                  <span className="visit-info-complete-page__consent-item-text" data-node-id="13:1745">
                    AI 분석 스타일 리포트
                  </span>
                </div>
              </div>

              <div className="visit-info-complete-page__consent-confirm" data-node-id="13:1747" data-name="Button">
                <span className="visit-info-complete-page__consent-checkbox" data-node-id="13:1748">
                  ✓
                </span>
                <span className="visit-info-complete-page__consent-confirm-text" data-node-id="13:1753">
                  위 정보 공유에 동의합니다
                </span>
              </div>
            </div>

            <div className="visit-info-complete-page__purpose-block" data-node-id="13:1758" data-name="Container">
              <p className="visit-info-complete-page__section-label visit-info-complete-page__section-label--purpose" data-node-id="13:1760">
                <span className="visit-info-complete-page__section-label-text">방문 목적 </span>
                <span className="visit-info-complete-page__section-label-highlight">선택</span>
              </p>

              <div className="visit-info-complete-page__purpose-grid" data-node-id="13:1778" data-name="Container:margin">
                <button type="button" className="visit-info-complete-page__purpose-chip" data-node-id="13:1763">
                  선물 구매
                </button>
                <button type="button" className="visit-info-complete-page__purpose-chip" data-node-id="13:1766">
                  시즌 코디 업데이트
                </button>
                <button type="button" className="visit-info-complete-page__purpose-chip" data-node-id="13:1769">
                  특별 행사 준비
                </button>
                <button type="button" className="visit-info-complete-page__purpose-chip" data-node-id="13:1772">
                  자유 쇼핑
                </button>
              </div>

              <div className="visit-info-complete-page__input-row" data-node-id="13:1779" data-name="Container:margin">
                <div className="visit-info-complete-page__text-input" data-node-id="13:1776" data-name="Text Input">
                  <p className="visit-info-complete-page__placeholder" data-node-id="13:1777">
                    직접 입력...
                  </p>
                </div>
              </div>
            </div>

            <button type="button" className="visit-info-complete-page__button" data-node-id="13:1780" data-name="PrimaryBtn" onClick={handleNavigateToStaffAssignment}>
              직원 배정 요청
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
