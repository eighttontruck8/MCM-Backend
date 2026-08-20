import { useNavigate } from 'react-router-dom';
import './PasswordCompletePage.css';

export default function PasswordCompletePage() {
  const navigate = useNavigate();

  return (
    <div className="password-complete-page" data-node-id="13:1611" data-name="비밀번호 변경완료">
      <div className="password-complete-page__body" data-node-id="13:1612" data-name="Body">
        <div className="password-complete-page__app" data-node-id="13:1614" data-name="App">
          <header className="password-complete-page__header" data-node-id="13:1615" data-name="AuthScreen">
            <a href="#" className="password-complete-page__back-button" data-node-id="13:1617" data-name="Button">
              <span className="password-complete-page__back-icon" data-node-id="13:1618">
                ←
              </span>
            </a>
            <div className="password-complete-page__header-copy" data-node-id="13:1620" data-name="Container">
              <p className="password-complete-page__header-label" data-node-id="13:1622">
                비밀번호 찾기
              </p>
              <p className="password-complete-page__header-title" data-node-id="13:1625">
                변경 완료
              </p>
            </div>
          </header>

          <main className="password-complete-page__content" data-node-id="13:1628" data-name="Container">
            <div className="password-complete-page__status" data-node-id="13:1629" data-name="Container">
              <div className="password-complete-page__status-icon-wrapper" data-node-id="13:1644" data-name="Container:margin">
                <div className="password-complete-page__status-icon" data-node-id="13:1630" data-name="Container">
                  <p className="password-complete-page__status-check" data-node-id="13:1632">
                    ✓
                  </p>
                </div>
              </div>

              <p className="password-complete-page__status-title" data-node-id="13:1635">
                비밀번호가 변경되었습니다
              </p>
              <p className="password-complete-page__status-subtitle" data-node-id="13:1638">
                새 비밀번호로 로그인해주세요.
              </p>
            </div>

            <button
              type="button"
              className="password-complete-page__button"
              data-node-id="13:1640"
              data-name="Container"
              onClick={() => navigate('/login')}
            >
              <span className="password-complete-page__button-text" data-node-id="13:1642">
                로그인으로 돌아가기
              </span>
            </button>
          </main>
        </div>
      </div>
    </div>
  );
}
