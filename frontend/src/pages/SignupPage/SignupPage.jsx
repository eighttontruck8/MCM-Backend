import { useNavigate } from 'react-router-dom';
import './SignupPage.css';

export default function SignupPage() {
  const navigate = useNavigate();

  return (
    <div className="signup-page" data-node-id="13:1475" data-name="회원가입">
      <div className="signup-page__body" data-node-id="13:1476" data-name="Body">
        <div className="signup-page__app" data-node-id="13:1478" data-name="App">
          <section className="signup-page__hero" data-node-id="13:1479" data-name="AuthScreen">
            <div className="signup-page__hero-backdrop" data-node-id="13:1480" data-name="Container">
              <div className="signup-page__hero-image" data-node-id="13:1481" data-name="ImgPlaceholder">
                <div className="signup-page__hero-text" data-node-id="13:1482" data-name="Text">
                  <p className="signup-page__hero-image-label" data-node-id="13:1483">
                    브랜드 이미지
                  </p>
                </div>
              </div>
              <div className="signup-page__hero-gradient" data-node-id="13:1485" data-name="Container" />
              <div className="signup-page__hero-copy" data-node-id="13:1486" data-name="Container">
                <p className="signup-page__hero-subtitle" data-node-id="13:1488">
                  Luxury AI Retail
                </p>
                <p className="signup-page__hero-title" data-node-id="13:1491">
                  M·Journey
                </p>
              </div>
            </div>
          </section>

          <div className="signup-page__tabs" data-node-id="13:1494" data-name="Container">
            <button
              type="button"
              className="signup-page__tab signup-page__tab--inactive"
              data-node-id="13:1495"
              data-name="Button"
              onClick={() => navigate('/login')}
            >
              로그인
            </button>
            <button type="button" className="signup-page__tab signup-page__tab--active" data-node-id="13:1498" data-name="Button">
              회원가입
            </button>
          </div>

          <form className="signup-page__form" data-node-id="13:1503" data-name="Container">
            <div className="signup-page__field" data-node-id="13:1504" data-name="Input">
              <label htmlFor="signup-name" className="signup-page__label" data-node-id="13:1505" data-name="Label">
                이름
              </label>
              <input
                id="signup-name"
                type="text"
                className="signup-page__input"
                placeholder="홍길동"
                data-node-id="13:1508"
                data-name="Text Input"
              />
            </div>

            <div className="signup-page__field" data-node-id="13:1510" data-name="Input">
              <label htmlFor="signup-phone" className="signup-page__label" data-node-id="13:1511" data-name="Label">
                연락처
              </label>
              <input
                id="signup-phone"
                type="tel"
                className="signup-page__input"
                placeholder="010-0000-0000"
                data-node-id="13:1514"
                data-name="Phone Input"
              />
            </div>

            {/* [Frontend-01-'인증 이메일 식별자 통일'] 백엔드 로그인 계약과 동일하게 이메일을 사용한다. */}
            <div className="signup-page__field" data-node-id="13:1516" data-name="Input">
              <label htmlFor="signup-email" className="signup-page__label" data-node-id="13:1517" data-name="Label">
                이메일
              </label>
              <input
                id="signup-email"
                type="email"
                className="signup-page__input"
                placeholder="customer@example.com"
                autoComplete="email"
                required
                data-node-id="13:1520"
                data-name="Text Input"
              />
            </div>

            <div className="signup-page__field" data-node-id="13:1522" data-name="Input">
              <label htmlFor="signup-password" className="signup-page__label" data-node-id="13:1523" data-name="Label">
                비밀번호
              </label>
              <input
                id="signup-password"
                type="password"
                className="signup-page__input"
                placeholder="••••••••"
                data-node-id="13:1526"
                data-name="Password Input"
              />
            </div>

            <button
              type="submit"
              className="signup-page__submit"
              data-node-id="13:1528"
              data-name="Container"
              onClick={(event) => {
                event.preventDefault();
                navigate('/login');
              }}
            >
              가입하기
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
