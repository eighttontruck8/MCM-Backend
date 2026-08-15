import React from 'react';
import { useNavigate } from 'react-router-dom';
import './FindPasswordPage.css';

export default function FindPasswordPage() {
  const navigate = useNavigate();

  return (
    <div className="find-password-page" data-node-id="13:1540" data-name="비밀번호 찾기1">
      <div className="find-password-page__body" data-node-id="13:1541" data-name="Body">
        <div className="find-password-page__app" data-node-id="13:1543" data-name="App">
          <header className="find-password-page__header" data-node-id="13:1544" data-name="AuthScreen">
            <button
              type="button"
              className="find-password-page__back-button"
              data-node-id="13:1546"
              data-name="Button"
              onClick={() => navigate('/')}
            >
              <span className="find-password-page__back-icon" data-node-id="13:1547">
                ←
              </span>
            </button>
            <div className="find-password-page__header-copy" data-node-id="13:1549" data-name="Container">
              <p className="find-password-page__header-label" data-node-id="13:1551">
                비밀번호 찾기
              </p>
              <p className="find-password-page__header-title" data-node-id="13:1554">
                아이디 입력
              </p>
            </div>
          </header>

          <main className="find-password-page__content" data-node-id="13:1557" data-name="Container">
            <p className="find-password-page__description" data-node-id="13:1559">
              비밀번호를 찾고자 하는 아이디를 입력해주세요.
            </p>

            <div className="find-password-page__field" data-node-id="13:1561" data-name="Input">
              <label htmlFor="find-password-id" className="find-password-page__label" data-node-id="13:1562" data-name="Label">
                아이디
              </label>
              <input
                id="find-password-id"
                type="text"
                className="find-password-page__input"
                placeholder="아이디를 입력해주세요"
                data-node-id="13:1565"
                data-name="Text Input"
              />
            </div>

            <button
              type="button"
              className="find-password-page__submit"
              data-node-id="13:1567"
              data-name="Container"
              onClick={() => navigate('/reset-password')}
            >
              다음
            </button>
          </main>
        </div>
      </div>
    </div>
  );
}
