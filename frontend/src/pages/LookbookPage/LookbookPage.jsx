import React from 'react';
import { useNavigate } from 'react-router-dom';
import './LookbookPage.css';

export default function LookbookPage() {
  const navigate = useNavigate();
  const cards = [
    { id: 1, layout: 'full', title: '룩 1', subtitle: '매장 매칭봇', label: '사진 1' },
    { id: 2, layout: 'half-left', title: '룩 2', subtitle: '매장 매칭봇', label: '사진 2' },
    { id: 3, layout: 'half-right', title: '룩 3', subtitle: '매장 매칭봇', label: '사진 3' },
    { id: 4, layout: 'tall', title: '룩 4', subtitle: '매장 매칭봇', label: '사진 1' },
    { id: 5, layout: 'tall-right', title: '룩 2', subtitle: '매장 매칭봇', label: '사진 2' },
    { id: 6, layout: 'full', title: '룩 3', subtitle: '매장 매칭봇', label: '사진 3' },
  ];

  return (
    <div className="lookbook-page" data-node-id="13:3190">
      <div className="lookbook-page__container">
        <header className="lookbook-header" data-node-id="13:3191">
          <div className="lookbook-header__brand">M-Journey</div>
          <button className="lookbook-header__checkin">체크인</button>
        </header>

        <section className="lookbook-intro" data-node-id="13:3192">
          <div className="lookbook-intro__eyebrow">MY LOOKBOOK</div>
          <h1 className="lookbook-intro__title">AI 큐레이션 룩북</h1>
        </section>

        <section className="lookbook-grid" data-node-id="13:3193">
          {cards.map((c) => (
            <article
              key={c.id}
              className={`lookbook-card lookbook-card--${c.layout}`}
              data-node-id={`13:${3200 + c.id}`}
              onClick={() => navigate('/look-detail')}
              style={{cursor: 'pointer'}}>
              <div className="lookbook-card__image">{c.label}</div>
              <div className="lookbook-card__meta">
                <div className="lookbook-card__title">{c.title}</div>
                <div className="lookbook-card__subtitle">{c.subtitle}</div>
              </div>
            </article>
          ))}
        </section>

        <nav className="lookbook-bottomnav" data-node-id="13:3199">
          <button className="nav-btn" onClick={() => navigate('/main')}>홈</button>
          <button className="nav-btn nav-btn--active" onClick={() => navigate('/lookbook')}>룩북</button>
          <button className="nav-btn" onClick={() => navigate('/wishlist')}>찜</button>
          <button className="nav-btn" onClick={() => navigate('/mypage')}>MY</button>
        </nav>
      </div>
    </div>
  );
}
