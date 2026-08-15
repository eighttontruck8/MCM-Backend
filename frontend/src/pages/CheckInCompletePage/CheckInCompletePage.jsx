import React from 'react';
import { useNavigate } from 'react-router-dom';
import { mockCustomers } from '../../mock/mockCustomers';
import './CheckInCompletePage.css';

const imgIcon = 'https://www.figma.com/api/mcp/asset/b5442dca-6d58-44e0-9fdd-e23966453d03.svg';

export default function CheckInCompletePage() {
  const navigate = useNavigate();
  const customer = mockCustomers[0];

  const handleNext = () => {
    navigate('/shopping-option');
  };
  return (
    <div className="checkin-complete-page" data-node-id="13:1646" data-name="체크인 완료">
      <div className="checkin-complete-page__body" data-node-id="13:1647" data-name="Body">
        <div className="checkin-complete-page__app" data-node-id="13:1649" data-name="App">
          <div className="checkin-complete-page__screen" data-node-id="13:1650" data-name="CheckInScreen">
            <div className="checkin-complete-page__background" data-node-id="13:1651" data-name="Container" />

            <div className="checkin-complete-page__icon-ring" data-node-id="13:1652" data-name="Container">
              <div className="checkin-complete-page__icon-ring-inner" data-node-id="13:1655" data-name="Container">
                <div className="checkin-complete-page__icon" data-node-id="13:1656" data-name="Icon">
                  <img alt="Check-in icon" src={imgIcon} />
                </div>
              </div>
              <div className="checkin-complete-page__outer-ring" data-node-id="13:1653" data-name="Container" />
              <div className="checkin-complete-page__inner-ring" data-node-id="13:1654" data-name="Container" />
            </div>

            <div className="checkin-complete-page__heading" data-node-id="13:1664" data-name="Container">
              <p className="checkin-complete-page__subtitle" data-node-id="13:1666">
                NFC Check-In Complete
              </p>
              <p className="checkin-complete-page__title" data-node-id="13:1669">
                체크인 완료
              </p>
              <p className="checkin-complete-page__meta" data-node-id="13:1672">
                매장명 · 방문 시간
              </p>
            </div>

            <div className="checkin-complete-page__report" data-node-id="13:1676" data-name="Container">
              <p className="checkin-complete-page__report-title" data-node-id="13:1678">
                AI 분석 리포트 준비 완료
              </p>
              <div className="checkin-complete-page__report-list" data-node-id="13:1680" data-name="Container">
                <div className="checkin-complete-page__report-item" data-node-id="13:1681" data-name="Container">
                  <p className="checkin-complete-page__report-bullet" data-node-id="13:1683">
                    ◈
                  </p>
                  <p className="checkin-complete-page__report-text" data-node-id="13:1686">
                    구매 이력 {customer.visit_count}건 · 관심 상품 {customer.recent_interests.length}건 분석
                  </p>
                </div>
                <div className="checkin-complete-page__report-item" data-node-id="13:1689" data-name="Container">
                  <p className="checkin-complete-page__report-bullet" data-node-id="13:1691">
                    ◈
                  </p>
                  <p className="checkin-complete-page__report-text" data-node-id="13:1694">
                    {customer.preferred_colors.join(' · ')} · {customer.preferred_fit}
                  </p>
                </div>
              </div>
            </div>

            <a href="#" className="checkin-complete-page__action-button" data-node-id="13:1699" data-name="Button" onClick={(e) => { e.preventDefault(); handleNext(); }}>
              <span className="checkin-complete-page__action-text" data-node-id="13:1700">
                AI 추천 받기
              </span>
            </a>

            <p className="checkin-complete-page__footer" data-node-id="13:1703">
              안녕하세요, {customer.name} 고객님
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
