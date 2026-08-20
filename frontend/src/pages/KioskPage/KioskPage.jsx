import { QRCodeSVG } from 'qrcode.react';
import './KioskPage.css';

/**
 * [Frontend-17-'매장 키오스크 QR 체크인'] 매장 태블릿에 항시 표시하는 QR 체크인 화면.
 * QR 코드는 배포된 프론트엔드의 /welcome 경로를 가리킨다.
 */
export default function KioskPage() {
  const baseUrl = window.location.origin;
  const qrUrl = `${baseUrl}/welcome`;

  return (
    <div className="kiosk-page">
      <div className="kiosk-page__container">
        <header className="kiosk-page__header">
          <div className="kiosk-page__brand">M·Journey</div>
        </header>

        <main className="kiosk-page__body">
          <h1 className="kiosk-page__title">체크인</h1>

          <div className="kiosk-page__qr-wrapper">
            <QRCodeSVG
              value={qrUrl}
              size={280}
              level="H"
              bgColor="#ffffff"
              fgColor="#0a0a0a"
              className="kiosk-page__qr"
            />
          </div>

          <p className="kiosk-page__description">
            QR코드를 스캔하시면 회원님의 취향을 바탕으로 한<br />
            맞춤형 쇼핑 경험을 시작하실 수 있습니다.
          </p>
        </main>

        <footer className="kiosk-page__footer">
          <div className="kiosk-page__footer-brand">MCM × M·Journey</div>
        </footer>
      </div>
    </div>
  );
}
