import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createLookbook, fetchProducts } from '../../api/client';
import PageLayout from '../../components/PageLayout/PageLayout';
import ProductImage from '../../components/ProductImage/ProductImage';
import { getCheckin } from '../../utils/checkinSession';
import { getLookbook, saveLookbook, saveSelectedLook } from '../../utils/lookbookSession';
import { mockProducts } from '../../mock/mockProducts';
import lookbookFallback from '../../mock/customerLookbookMock.json';
import './LookbookPage.css';

const LOCAL_IMAGE_MAP = Object.fromEntries(mockProducts.map((p) => [p.product_id, p.image_url]));

// [Frontend-04-'추천 및 고객 활동 REST 연동']
export default function LookbookPage() {
  const navigate = useNavigate();
  const [checkin] = useState(() => getCheckin());
  const [lookbook, setLookbook] = useState(() => {
    const cached = getLookbook(checkin?.checkin_id);
    // 캐시된 데이터가 옛날 형식(p00X.jpg 이미지)이면 무시
    if (cached?.looks?.[0]?.image_url && /p\d+\.\w+$/i.test(cached.looks[0].image_url)) return null;
    return cached;
  });
  const [isLoading, setIsLoading] = useState(!lookbook);
  const [noticeMessage, setNoticeMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const looks = Array.isArray(lookbook?.looks) ? lookbook.looks : [];

  useEffect(() => {
    if (lookbook) return undefined;
    const timer = window.setTimeout(async () => {
      try {
        if (checkin?.checkin_id) {
          try {
            const response = await createLookbook(checkin.checkin_id);
            if (Array.isArray(response?.looks) && response.looks.length > 0) {
              // 로컬 이미지 매핑 적용
              const mapped = { ...response, looks: response.looks.map((l) => ({ ...l, image_url: LOCAL_IMAGE_MAP[l.product_id] || l.image_url })) };
              saveLookbook(checkin.checkin_id, mapped);
              setLookbook(mapped);
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
          image_url: LOCAL_IMAGE_MAP[product.product_id] || product.image_url,
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
        // API 모두 실패 시 로컬 mock 룩북으로 fallback
        setLookbook(lookbookFallback);
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
    <PageLayout navActive="lookbook" eyebrow="MY LOOKBOOK" title={lookbook?.title ?? 'AI 큐레이션 룩북'}>
      {lookbook?.intro && <p className="lookbook-intro__copy">{lookbook.intro}</p>}
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
        {looks.map((look, index) => {
          // 세트 구조 (items 배열이 있는 경우)
          if (Array.isArray(look.items)) {
            return (
              <div key={look.look_name || index} className="lookbook-set">
                <div className="lookbook-set__title">{look.look_name}</div>
                <div className="lookbook-set__items">
                  {look.items.map((item) => (
                    <button type="button" key={item.product_id} className="lookbook-card lookbook-card--set-item" onClick={() => openLook(item)}>
                      <ProductImage className="lookbook-card__image" src={item.image_url} alt={item.product} />
                      <div className="lookbook-card__meta">
                        <div className="lookbook-card__title">{item.product}</div>
                        <div className="lookbook-card__subtitle">{item.category} · {item.price?.toLocaleString()}원</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            );
          }
          // 단일 아이템 구조 (API 응답 호환)
          return (
            <button type="button" key={look.product_id} className={`lookbook-card lookbook-card--${index % 3 === 0 ? 'full' : index % 3 === 1 ? 'half-left' : 'half-right'}`} onClick={() => openLook(look)}>
              <ProductImage className="lookbook-card__image" src={look.image_url} alt={look.product} />
              <div className="lookbook-card__meta">
                <div className="lookbook-card__title">{look.product}</div>
                <div className="lookbook-card__subtitle">{look.styling}</div>
              </div>
            </button>
          );
        })}
      </section>
    </PageLayout>
  );
}
