import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createLookbook } from '../../api/client';
import { getCheckin } from '../../utils/checkinSession';
import { getLookbook, saveLookbook, saveSelectedLook } from '../../utils/lookbookSession';
import './LookbookPage.css';

// [Frontend-04-'추천 및 고객 활동 REST 연동']
export default function LookbookPage() {
  const navigate = useNavigate();
  const [checkin] = useState(() => getCheckin());
  const [lookbook, setLookbook] = useState(() => getLookbook(checkin?.checkin_id));
  const [isLoading, setIsLoading] = useState(Boolean(!lookbook && checkin?.checkin_id));
  const [errorMessage, setErrorMessage] = useState(() => (!lookbook && !checkin?.checkin_id ? '활성 체크인 후 맞춤 룩북을 생성할 수 있습니다.' : ''));

  useEffect(() => {
    if (lookbook || !checkin?.checkin_id) return undefined;
    const timer = window.setTimeout(async () => {
      try {
        const response = await createLookbook(checkin.checkin_id);
        saveLookbook(checkin.checkin_id, response);
        setLookbook(response);
      } catch (error) {
        setErrorMessage(error.message);
      } finally {
        setIsLoading(false);
      }
    }, 0);
    return () => window.clearTimeout(timer);
  }, [checkin?.checkin_id, lookbook]);

  const openLook = (look) => {
    saveSelectedLook(look);
    navigate('/look-detail');
  };

  return (
    <div className="lookbook-page">
      <div className="lookbook-page__container">
        <header className="lookbook-header">
          <div className="lookbook-header__brand">M-Journey</div>
          <button type="button" className="lookbook-header__checkin">체크인</button>
        </header>
        <section className="lookbook-intro">
          <div className="lookbook-intro__eyebrow">MY LOOKBOOK</div>
          <h1 className="lookbook-intro__title">{lookbook?.title ?? 'AI 큐레이션 룩북'}</h1>
          {lookbook?.intro && <p className="lookbook-intro__copy">{lookbook.intro}</p>}
        </section>
        {isLoading && <p className="lookbook-state">재고를 확인하고 맞춤 룩북을 만들고 있습니다.</p>}
        {errorMessage && <p className="lookbook-state lookbook-state--error" role="alert">{errorMessage}</p>}
        <section className="lookbook-grid">
          {(lookbook?.looks ?? []).map((look, index) => (
            <button type="button" key={look.product_id} className={`lookbook-card lookbook-card--${index % 3 === 0 ? 'full' : index % 3 === 1 ? 'half-left' : 'half-right'}`} onClick={() => openLook(look)}>
              <div className="lookbook-card__image" style={{ backgroundImage: `url(${look.image_url})` }} />
              <div className="lookbook-card__meta">
                <div className="lookbook-card__title">{look.product}</div>
                <div className="lookbook-card__subtitle">{look.styling}</div>
              </div>
            </button>
          ))}
        </section>
        <nav className="lookbook-bottomnav">
          <button type="button" className="nav-btn" onClick={() => navigate('/main')}>홈</button>
          <button type="button" className="nav-btn nav-btn--active">룩북</button>
          <button type="button" className="nav-btn" onClick={() => navigate('/wishlist')}>찜</button>
          <button type="button" className="nav-btn" onClick={() => navigate('/mypage')}>MY</button>
        </nav>
      </div>
    </div>
  );
}
