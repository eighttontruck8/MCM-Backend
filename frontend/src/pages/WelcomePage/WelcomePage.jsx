import { useNavigate } from 'react-router-dom';
import './WelcomePage.css';

/**
 * [Frontend-17-'매장 키오스크 QR 체크인'] QR 스캔 후 고객이 도착하는 랜딩 페이지.
 * 간단한 서비스 소개와 로그인 버튼을 제공한다.
 */
export default function WelcomePage() {
  const navigate = useNavigate();

  return (
    <div className="welcome-page">
      <div className="welcome-page__container welcome-page__fade-in">
        <header className="welcome-page__header">
          <div className="welcome-page__brand">M·Journey</div>
        </header>

        <main className="welcome-page__body">
          <div className="welcome-page__icon">✦</div>
          <h1 className="welcome-page__title">
            오직, 고객님만을 위한<br />맞춤 쇼핑이 시작됩니다
          </h1>
          <p className="welcome-page__description">
            온라인에서 분석한 취향 정보를 바탕으로<br />
            매장에서의 쇼핑 경험을 한층 더 특별하게 만들어드립니다.
          </p>

          <ul className="welcome-page__benefits">
            <li>AI가 분석한 스타일 기반 상품 추천</li>
            <li>전담 직원의 1:1 맞춤 코디 서비스</li>
            <li>나만의 큐레이션 룩북 제공</li>
          </ul>
        </main>

        <footer className="welcome-page__footer">
          <button
            type="button"
            className="welcome-page__login-button"
            onClick={() => navigate('/login')}
          >
            로그인하고 시작하기
          </button>
          <p className="welcome-page__consent-notice">
            시작하기를 누르면 서비스 이용약관 및<br />개인정보 수집·활용에 동의하는 것으로 간주됩니다.
          </p>
          <p className="welcome-page__footer-note">
            계정이 없으신가요? 로그인 화면에서 바로 가입하실 수 있습니다.
          </p>
        </footer>
      </div>
    </div>
  );
}
