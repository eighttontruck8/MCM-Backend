import React from 'react';
import { useNavigate } from 'react-router-dom';
import './ShoppingOptionPage.css';

export default function ShoppingOptionPage() {
  const navigate = useNavigate();

  const handleShoppingOptionSelect = () => {
    navigate('/visit-info');
  };
  return (
    <div className="shopping-option-page" data-node-id="7:1128" data-name="고객 입력1">
      <div className="shopping-option-page__body" data-node-id="7:1129" data-name="Body">
        <div className="shopping-option-page__app" data-node-id="7:1131" data-name="App">
          <div className="shopping-option-page__screen" data-node-id="7:1132" data-name="PreferenceScreen">
            <section className="shopping-option-page__intro" data-node-id="7:1133" data-name="Container">
              <p className="shopping-option-page__eyebrow" data-node-id="7:1135">
                쇼핑 방식 선택
              </p>
              <div className="shopping-option-page__title" data-node-id="7:1137">
                <p>오늘 어떻게</p>
                <p>도와드릴까요?</p>
              </div>
              <div className="shopping-option-page__description" data-node-id="7:1140">
                <p>원하시는 쇼핑 방식을 선택해주세요.</p>
                <p>언제든지 변경 가능합니다.</p>
              </div>
            </section>

            <div className="shopping-option-page__options" data-node-id="7:1145" data-name="Container">
              <a href="#" className="shopping-option-page__option shopping-option-page__option--primary" data-node-id="7:1146" data-name="Button" onClick={(e) => { e.preventDefault(); handleShoppingOptionSelect(); }}>
                <div className="shopping-option-page__option-header">
                  <p className="shopping-option-page__option-label" data-node-id="7:1149">
                    Option A
                  </p>
                </div>
                <div className="shopping-option-page__option-title" data-node-id="7:1151">
                  프라이빗 쇼핑
                </div>
                <div className="shopping-option-page__option-copy" data-node-id="7:1154">
                  <p>직원 응대 없이 자유롭게 둘러보며</p>
                  <p>AI 추천 서비스를 이용합니다.</p>
                </div>
                <span className="shopping-option-page__option-icon" data-node-id="7:1158">
                  ›
                </span>
              </a>

              <a href="#" className="shopping-option-page__option shopping-option-page__option--secondary" data-node-id="7:1162" data-name="Button" onClick={(e) => { e.preventDefault(); handleShoppingOptionSelect(); }}>
                <div className="shopping-option-page__option-header">
                  <p className="shopping-option-page__option-label shopping-option-page__option-label--secondary" data-node-id="7:1164">
                    Option B
                  </p>
                </div>
                <div className="shopping-option-page__option-title shopping-option-page__option-title--secondary" data-node-id="7:1166">
                  직원 응대 요청
                </div>
                <div className="shopping-option-page__option-copy shopping-option-page__option-copy--secondary" data-node-id="7:1169">
                  <p>전담 직원이 구매 이력 기반</p>
                  <p>맞춤형 응대를 제공합니다.</p>
                </div>
                <span className="shopping-option-page__option-icon shopping-option-page__option-icon--secondary" data-node-id="7:1173">
                  ›
                </span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
