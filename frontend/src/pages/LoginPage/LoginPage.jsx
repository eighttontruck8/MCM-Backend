import React from 'react';
import { useNavigate } from 'react-router-dom';
import './LoginPage.css';

export default function LoginPage() {
  const navigate = useNavigate();

  return (
    <div className="login-page" data-node-id="17:8" data-name="로그인">
      <div className="login-page__body" data-node-id="17:9" data-name="Body">
        <div className="login-page__app" data-node-id="17:10" data-name="App">
          <section className="login-page__hero" data-node-id="17:11" data-name="AuthScreen">
            <div className="login-page__hero-backdrop" data-node-id="17:12" data-name="Container">
              <div className="login-page__hero-image" data-node-id="17:13" data-name="ImgPlaceholder">
                <div className="login-page__hero-text" data-node-id="17:14" data-name="Text">
                  <p className="login-page__hero-image-label" data-node-id="17:15">
                    브랜드 이미지
                  </p>
                </div>
              </div>
              <div className="login-page__hero-gradient" data-node-id="17:16" data-name="Container" />
              <div className="login-page__hero-copy" data-node-id="17:17" data-name="Container">
                <p className="login-page__hero-subtitle" data-node-id="17:18">
                  Luxury AI Retail
                </p>
                <p className="login-page__hero-title" data-node-id="17:19">
                  M·Journey
                </p>
              </div>
            </div>
          </section>

          <div className="login-page__tabs" data-node-id="17:20" data-name="Container">
            <button type="button" className="login-page__tab login-page__tab--active" data-node-id="17:21" data-name="Button">
              로그인
            </button>
            <button
              type="button"
              className="login-page__tab login-page__tab--inactive"
              data-node-id="17:22"
              data-name="Button"
              onClick={() => navigate('/signup')}
            >
              회원가입
            </button>
          </div>

          <form
            className="login-page__form"
            data-node-id="17:23"
            data-name="Container"
            onSubmit={(event) => {
              event.preventDefault();
              navigate('/checkin-complete');
            }}
          >
            <div className="login-page__field" data-node-id="17:24" data-name="Input">
              <label htmlFor="login-id" className="login-page__label" data-node-id="17:25" data-name="Label">
                아이디
              </label>
              <input
                id="login-id"
                type="text"
                className="login-page__input"
                placeholder="아이디를 입력해주세요"
                data-node-id="17:26"
                data-name="Text Input"
              />
            </div>

            <div className="login-page__field" data-node-id="17:27" data-name="Input">
              <label htmlFor="login-password" className="login-page__label" data-node-id="17:28" data-name="Label">
                비밀번호
              </label>
              <input
                id="login-password"
                type="password"
                className="login-page__input"
                placeholder="••••••••"
                data-node-id="17:29"
                data-name="Password Input"
              />
            </div>

            <div className="login-page__meta" data-node-id="17:30" data-name="Container">
              <label className="login-page__remember" data-node-id="17:31">
                <input type="checkbox" className="login-page__checkbox" />
                <span>자동 로그인</span>
              </label>
              <button
                type="button"
                className="login-page__link"
                data-node-id="17:32"
                onClick={() => navigate('/find-password')}
              >
                비밀번호 찾기
              </button>
            </div>

            <button type="submit" className="login-page__submit" data-node-id="17:33" data-name="Container">
              로그인
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
