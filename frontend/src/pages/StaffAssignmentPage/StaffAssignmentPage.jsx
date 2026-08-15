import React from 'react';
import { useNavigate } from 'react-router-dom';
import './StaffAssignmentPage.css';

export default function StaffAssignmentPage() {
  const navigate = useNavigate();

  const handleNavigateToMain = () => {
    navigate('/main');
  };
  return (
    <div className="staff-assignment-page" data-node-id="13:1786" data-name="담당 직원 배정">
      <div className="staff-assignment-page__body" data-node-id="13:1787" data-name="Body">
        <div className="staff-assignment-page__app" data-node-id="13:1789" data-name="App">
          <div className="staff-assignment-page__screen" data-node-id="13:1790" data-name="StaffAssignedScreen">
            <div className="staff-assignment-page__background" data-node-id="13:1791" data-name="Container" />

            <div className="staff-assignment-page__avatar" data-node-id="13:1792" data-name="Container">
              <div className="staff-assignment-page__avatar-text" data-node-id="13:1793" data-name="Text">
                <p data-node-id="13:1794">직</p>
              </div>
              <div className="staff-assignment-page__status-dot" data-node-id="13:1796" data-name="Container" />
            </div>

            <div className="staff-assignment-page__heading" data-node-id="13:1797" data-name="Container">
              <p className="staff-assignment-page__subtitle" data-node-id="13:1799">
                담당 직원 배정 완료
              </p>
              <p className="staff-assignment-page__name" data-node-id="13:1802">
                담당 직원명
              </p>
              <p className="staff-assignment-page__role" data-node-id="13:1805">
                직책 · 경력
              </p>
            </div>

            <div className="staff-assignment-page__info-card" data-node-id="13:1809" data-name="Container">
              <p className="staff-assignment-page__info-title" data-node-id="13:1811">
                전달된 정보
              </p>

              <div className="staff-assignment-page__info-row" data-node-id="13:1813">
                <span className="staff-assignment-page__info-bullet" data-node-id="13:1815">
                  ◈
                </span>
                <span className="staff-assignment-page__info-text" data-node-id="13:1818">
                  구매 이력 N건 · 관심 상품 N건
                </span>
              </div>

              <div className="staff-assignment-page__info-row" data-node-id="13:1820">
                <span className="staff-assignment-page__info-bullet" data-node-id="13:1822">
                  ◈
                </span>
                <span className="staff-assignment-page__info-text" data-node-id="13:1825">
                  AI 취향 분석 리포트
                </span>
              </div>

              <div className="staff-assignment-page__info-row" data-node-id="13:1827">
                <span className="staff-assignment-page__info-bullet" data-node-id="13:1829">
                  ◈
                </span>
                <span className="staff-assignment-page__info-text" data-node-id="13:1832">
                  AI 추천 상품 목록
                </span>
              </div>

              <div className="staff-assignment-page__visit-note" data-node-id="13:1842">
                <span className="staff-assignment-page__visit-dot" data-node-id="13:1835" />
                <span className="staff-assignment-page__visit-text" data-node-id="13:1837">
                  잠시 후 담당 직원이 방문할 예정입니다
                </span>
              </div>
            </div>

            <a href="#" className="staff-assignment-page__button" data-node-id="13:1844" data-name="Button" onClick={(e) => { e.preventDefault(); handleNavigateToMain(); }}>
              <span className="staff-assignment-page__button-text" data-node-id="13:1845">
                메인화면으로
              </span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
