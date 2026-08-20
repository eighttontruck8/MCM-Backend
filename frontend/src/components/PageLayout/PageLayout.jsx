import AppBottomNav from '../AppBottomNav/AppBottomNav';
import './PageLayout.css';

/**
 * [Frontend-16-'공통 페이지 레이아웃'] 모든 고객 화면에 일관된 컨테이너, 헤더, 제목 스타일을 제공한다.
 */
export default function PageLayout({ navActive, eyebrow, title, headerRight, children }) {
  return (
    <div className="page-layout">
      <div className="page-layout__container">
        <header className="page-layout__header">
          <div className="page-layout__brand">M·Journey</div>
          {headerRight && <div className="page-layout__header-right">{headerRight}</div>}
        </header>
        {(eyebrow || title) && (
          <section className="page-layout__title-section">
            {eyebrow && <div className="page-layout__eyebrow">{eyebrow}</div>}
            {title && <h1 className="page-layout__title">{title}</h1>}
          </section>
        )}
        <main className="page-layout__content">
          {children}
        </main>
        {navActive && <AppBottomNav active={navActive} />}
      </div>
    </div>
  );
}
