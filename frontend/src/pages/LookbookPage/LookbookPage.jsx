import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createLookbook, fetchProducts } from '../../api/client';
import AppBottomNav from '../../components/AppBottomNav/AppBottomNav';
import ProductImage from '../../components/ProductImage/ProductImage';
import { getCheckin } from '../../utils/checkinSession';
import { getLookbook, saveLookbook, saveSelectedLook } from '../../utils/lookbookSession';
import './LookbookPage.css';

// [Frontend-04-'추천 및 고객 활동 REST 연동']
export default function LookbookPage() {
  const navigate = useNavigate();
  const [checkin] = useState(() => getCheckin());
  const [lookbook, setLookbook] = useState(() => getLookbook(checkin?.checkin_id));
  const [isLoading, setIsLoading] = useState(!lookbook);
  const [noticeMessage, setNoticeMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const looks = Array.isArray(lookbook?.looks) ? lookbook.looks : [];

  useEffect(() => {
    // [Frontend-11-'빈 룩북 복구'] 저장값이나 AI 응답에 상품이 없으면 매장 카탈로그로 페이지를 복구한다.
    if (lookbook) return undefined;
    const timer = window.setTimeout(async () => {
      try {
        if (checkin?.checkin_id) {
          try {
            const response = await createLookbook(checkin.checkin_id);
            if (Array.isArray(response?.looks) && response.looks.length > 0) {
              saveLookbook(checkin.checkin_id, response);
              setLookbook(response);
              return;
            }
            setNoticeMessage('생성된 맞춤 룩북에 상품이 없어 현재 매장의 추천 상품을 보여드립니다.');
          } catch {
            setNoticeMessage('맞춤 룩북을 불러오지 못해 현재 매장의 추천 상품을 보여드립니다.');
          }
        } else {
          setNoticeMessage('체크인하면 고객님의 취향을 반영한 맞춤 룩북을 만들 수 있습니다.');
        }

        const catalog = await fetchProducts();
        const catalogLooks = (Array.isArray(catalog?.items) ? catalog.items : []).slice(0, 6).map((product) => ({
          product_id: product.product_id,
          product: product.name,
          styling: product.tags?.slice(0, 2).join(' · ') || product.category,
          image_url: product.image_url,
          price: product.price,
          in_stock: product.inventory?.in_stock ?? false,
        }));
        if (catalogLooks.length === 0) {
          throw new Error('현재 표시할 수 있는 룩북 상품이 없습니다.');
        }
        setLookbook({
          title: '매장 추천 룩북',
          intro: '현재 매장에서 바로 만나볼 수 있는 상품입니다.',
          looks: catalogLooks,
        });
      } catch (error) {
        setErrorMessage(error.message || '룩북을 불러오지 못했습니다.');
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
        <main className="lookbook-content">
          <section className="lookbook-intro">
            <div className="lookbook-intro__eyebrow">MY LOOKBOOK</div>
            <h1 className="lookbook-intro__title">{lookbook?.title ?? 'AI 큐레이션 룩북'}</h1>
            {lookbook?.intro && <p className="lookbook-intro__copy">{lookbook.intro}</p>}
          </section>
          {isLoading && <p className="lookbook-state">재고를 확인하고 맞춤 룩북을 만들고 있습니다.</p>}
          {noticeMessage && <p className="lookbook-state lookbook-state--notice">{noticeMessage}</p>}
          {errorMessage && (
            <section className="lookbook-empty" role="status">
              <p className="lookbook-state lookbook-state--error">{errorMessage}</p>
              <button type="button" className="lookbook-empty__button" onClick={() => navigate('/main')}>홈으로 돌아가기</button>
            </section>
          )}
          {!isLoading && !errorMessage && looks.length === 0 && (
            <section className="lookbook-empty" role="status">
              <p className="lookbook-state">현재 표시할 수 있는 룩북 상품이 없습니다.</p>
              <button type="button" className="lookbook-empty__button" onClick={() => navigate('/all-recommend')}>전체 추천 상품 보기</button>
            </section>
          )}
          <section className="lookbook-grid">
            {looks.map((look, index) => (
              <button type="button" key={look.product_id} className={`lookbook-card lookbook-card--${index % 3 === 0 ? 'full' : index % 3 === 1 ? 'half-left' : 'half-right'}`} onClick={() => openLook(look)}>
                <ProductImage className="lookbook-card__image" src={look.image_url} alt={look.product} />
                <div className="lookbook-card__meta">
                  <div className="lookbook-card__title">{look.product}</div>
                  <div className="lookbook-card__subtitle">{look.styling}</div>
                </div>
              </button>
            ))}
          </section>
        </main>
        <AppBottomNav active="lookbook" />
      </div>
    </div>
  );
}
