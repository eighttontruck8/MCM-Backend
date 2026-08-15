import './CustomerCheckInPage.css';

const toolbarIcons = ['✎', '◌', '⌂', '#', '❒', '▢', '◧', '⌁', '◫', '⟡'];

export default function CustomerCheckInPage() {
  return (
    <div className="customer-checkin-page">
      <header className="customer-checkin-topbar">
        <div className="customer-checkin-brand-box">
          <div className="customer-checkin-brand-icon" aria-hidden="true">
            ◌
          </div>
          <span className="customer-checkin-brand-name">M-Journey</span>
        </div>

        <div className="customer-checkin-top-actions">
          <div className="customer-checkin-user-pill" aria-label="현재 사용자">
            <div className="customer-checkin-user-avatar" aria-hidden="true" />
            <span className="customer-checkin-user-chevron">⌄</span>
          </div>

          <div className="customer-checkin-zoom-pill" aria-label="zoom level">
            <span>38%</span>
            <span className="customer-checkin-user-chevron">⌄</span>
          </div>

          <button type="button" className="customer-checkin-share-btn">
            Share
          </button>
        </div>
      </header>

      <main className="customer-checkin-main">
        <div className="customer-checkin-label">체크인 확인</div>

        <div className="customer-checkin-card" aria-label="check-in confirmation card">
          <div className="customer-checkin-card-header">
            <div className="customer-checkin-card-brand">M-JOURNEY</div>
            <span className="customer-checkin-card-mark">◌</span>
          </div>

          <div className="customer-checkin-card-body">
            <div className="customer-checkin-card-tag-row">
              <span className="customer-checkin-tag">체크인 완료</span>
            </div>

            <div className="customer-checkin-user-block">
              <div className="customer-checkin-avatar-circle">김</div>
              <div className="customer-checkin-user-text">
                <div className="customer-checkin-user-name">김** 고객</div>
                <div className="customer-checkin-user-sub">2026.08.14 · 신규 방문</div>
              </div>
            </div>

            <div className="customer-checkin-info-grid">
              <div className="customer-checkin-info-box">
                <span className="customer-checkin-info-label">전화번호</span>
                <span className="customer-checkin-info-value">010-12**-****</span>
              </div>

              <div className="customer-checkin-info-box">
                <span className="customer-checkin-info-label">방문일</span>
                <span className="customer-checkin-info-value">2026.08.14</span>
              </div>
            </div>

            <button type="button" className="customer-checkin-cta">
              고객 응대 시작하기
            </button>
          </div>
        </div>

        <div className="customer-checkin-editor-shell">
          <div className="customer-checkin-editor-bar">
            <span className="customer-checkin-editor-text">Sign up to comment, edit, inspect and more.</span>
            <div className="customer-checkin-editor-buttons">
              <button type="button" className="customer-checkin-secondary-btn">
                Sign up
              </button>
              <button type="button" className="customer-checkin-primary-btn">
                Continue
              </button>
            </div>
          </div>

          <div className="customer-checkin-toolbar" aria-label="editor toolbar">
            {toolbarIcons.map((icon, index) => (
              <span key={`${icon}-${index}`} className="customer-checkin-toolbar-item" aria-hidden="true">
                {icon}
              </span>
            ))}
          </div>
        </div>
      </main>

      <div className="customer-checkin-cookie-banner" aria-label="cookies banner">
        <p>
          This website uses cookies, pixel tags, and local storage for performance, personalization, and marketing purposes.
          We use our own cookies and some from third parties. Only essential cookies are turned on by default.
          <a href="#">Cookies settings</a>
        </p>

        <div className="customer-checkin-cookie-actions">
          <button type="button" className="customer-checkin-cookie-btn customer-checkin-cookie-btn--ghost">
            Do not allow cookies
          </button>
          <button type="button" className="customer-checkin-cookie-btn customer-checkin-cookie-btn--solid">
            Allow all cookies
          </button>
          <button type="button" className="customer-checkin-cookie-close" aria-label="close cookies banner">
            ×
          </button>
        </div>
      </div>
    </div>
  );
}
