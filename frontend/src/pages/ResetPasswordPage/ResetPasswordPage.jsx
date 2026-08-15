import React from 'react';
import { useNavigate } from 'react-router-dom';
import './ResetPasswordPage.css';

export default function ResetPasswordPage() {
  const navigate = useNavigate();

  return (
    <div className="reset-password-page" data-node-id="13:1572" data-name="비밀번호 찾기2">
      <div className="reset-password-page__body" data-node-id="13:1573" data-name="Body">
        <div className="reset-password-page__app" data-node-id="13:1575" data-name="App">
          <header className="reset-password-page__header" data-node-id="13:1576" data-name="AuthScreen">
            <a href="#" className="reset-password-page__back-button" data-node-id="13:1578" data-name="Button">
              <span className="reset-password-page__back-icon" data-node-id="13:1579">
                ←
              </span>
            </a>
            <div className="reset-password-page__header-copy" data-node-id="13:1581" data-name="Container">
              <p className="reset-password-page__header-label" data-node-id="13:1583">
                비밀번호 찾기
              </p>
              <p className="reset-password-page__header-title" data-node-id="13:1586">
                새 비밀번호 설정
              </p>
            </div>
          </header>

          <main className="reset-password-page__content" data-node-id="13:1589" data-name="Container">
            <p className="reset-password-page__description" data-node-id="13:1591">
              새로운 비밀번호를 입력해주세요.
            </p>

            <div className="reset-password-page__field" data-node-id="13:1593" data-name="Input">
              <label htmlFor="new-password" className="reset-password-page__label" data-node-id="13:1594" data-name="Label">
                새 비밀번호
              </label>
              <input
                id="new-password"
                type="password"
                className="reset-password-page__input"
                placeholder="••••••••"
                data-node-id="13:1597"
                data-name="Password Input"
              />
            </div>

            <div className="reset-password-page__field" data-node-id="13:1599" data-name="Input">
              <label htmlFor="confirm-password" className="reset-password-page__label" data-node-id="13:1600" data-name="Label">
                비밀번호 확인
              </label>
              <input
                id="confirm-password"
                type="password"
                className="reset-password-page__input"
                placeholder="••••••••"
                data-node-id="13:1603"
                data-name="Password Input"
              />
            </div>

            <button
              type="button"
              className="reset-password-page__submit"
              data-node-id="13:1605"
              data-name="Container"
              onClick={() => navigate('/password-complete')}
            >
              비밀번호 변경
            </button>
          </main>
        </div>
      </div>
    </div>
  );
}
