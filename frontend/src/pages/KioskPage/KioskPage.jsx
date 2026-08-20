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
      <div className="kiosk-page__border">
        <div className="kiosk-page__container">
          <header className="kiosk-page__header">
            <div className="kiosk-page__brand">M·Journey</div>
            <div className="kiosk-page__divider" />
            <p className="kiosk-page__subtitle">Your Personal Shopping Experience</p>
          </header>

          <main className="kiosk-page__body">
            <p className="kiosk-page__qr-label">체크인 QR</p>
            <div className="kiosk-page__qr-frame">
              <div className="kiosk-page__qr-corner kiosk-page__qr-corner--tl" />
              <div className="kiosk-page__qr-corner kiosk-page__qr-corner--tr" />
              <div className="kiosk-page__qr-corner kiosk-page__qr-corner--bl" />
              <div className="kiosk-page__qr-corner kiosk-page__qr-corner--br" />
              <div className="kiosk-page__qr-wrapper">
                <QRCodeSVG
                  value={qrUrl}
                  size={260}
                  level="H"
                  bgColor="#ffffff"
                  fgColor="#1a1816"
                  className="kiosk-page__qr"
                />
              </div>
            </div>

            <div className="kiosk-page__info">
              <p className="kiosk-page__cta">스마트폰으로 QR을 스캔해주세요</p>
              <div className="kiosk-page__divider kiosk-page__divider--short" />
              <p className="kiosk-page__description">
                회원님의 취향과 스타일을 반영한<br />
                프리미엄 맞춤 쇼핑이 시작됩니다
              </p>
            </div>
          </main>

          <footer className="kiosk-page__footer">
            <div className="kiosk-page__footer-line" />
            <div className="kiosk-page__footer-brand">MCM HAUS × M·Journey</div>
          </footer>
        </div>
      </div>
    </div>
  );
}
