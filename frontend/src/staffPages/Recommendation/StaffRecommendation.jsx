import { useNavigate } from 'react-router-dom';
import './StaffRecommendation.css';

const profileSummary = {
  name: '김 고객',
  status: '고객 추천',
  tags: ['N', 'M', 'L', 'S'],
  metrics: [
    { label: '최근 방문', value: '2025.01.02' },
    { label: '선호', value: 'Minimal' },
    { label: '예산', value: '₩ 200~300K' },
    { label: '맞춤형', value: 'Premium' },
  ],
};

const aiSuggestions = [
  {
    index: 1,
    title: '오버사이즈 울 코트',
    subtitle: '고급형 아우터',
    meta: '브랜드 · Premium',
    tone: '블랙',
    score: '92%',
  },
  {
    index: 2,
    title: '캐시미어 니트',
    subtitle: '포멀 캐주얼',
    meta: '브랜드 · Warm knit',
    tone: '베이지',
    score: '87%',
  },
  {
    index: 3,
    title: '프리미엄 슬랙스',
    subtitle: '세련된 실루엣',
    meta: '브랜드 · 하이엔드',
    tone: '차콜',
    score: '84%',
  },
  {
    index: 4,
    title: '가죽 토트백',
    subtitle: '포인트 액세서리',
    meta: '브랜드 · Luxury',
    tone: '브라운',
    score: '79%',
  },
  {
    index: 5,
    title: '클래식 셔츠',
    subtitle: '미니멀 보완',
    meta: '브랜드 · 정장형',
    tone: '아이보리',
    score: '74%',
  },
];

export default function StaffRecommendation() {
  const navigate = useNavigate();

  return (
    <div className="staff-recommend-page">
      <header className="staff-recommend-topbar">
        <div className="staff-recommend-brand">
          <span className="staff-recommend-brand-mark" aria-hidden="true" />
          <span className="staff-recommend-brand-text">M-Journey</span>
        </div>
      </header>

      <main className="staff-recommend-workspace">
        <aside className="staff-recommend-sidebar">
          <p className="staff-recommend-sidebar-label">메인화면</p>

          <section className="staff-recommend-profile-card">
            <div className="staff-recommend-profile-top">
              <span className="staff-recommend-profile-badge">AI 신뢰도</span>
              <span className="staff-recommend-profile-mini">김</span>
            </div>

            <div className="staff-recommend-profile-name-row">
              <h2 className="staff-recommend-profile-name">김 고객</h2>
              <span className="staff-recommend-profile-date">01:10</span>
            </div>

            <div className="staff-recommend-profile-tags">
              {profileSummary.tags.map((tag) => (
                <span key={tag} className="staff-recommend-profile-tag">{tag}</span>
              ))}
            </div>
          </section>

          <section className="staff-recommend-meta-card">
            <div className="staff-recommend-meta-grid">
              {profileSummary.metrics.map((item) => (
                <div key={item.label} className="staff-recommend-meta-item">
                  <span className="staff-recommend-meta-label">{item.label}</span>
                  <span className="staff-recommend-meta-value">{item.value}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="staff-recommend-action-card">
            <div className="staff-recommend-action-row">
              <span className="staff-recommend-action-title">위험 분석</span>
              <span className="staff-recommend-action-badge">Low</span>
            </div>

            <div className="staff-recommend-action-row">
              <span className="staff-recommend-action-title">AI 추천 상태</span>
              <span className="staff-recommend-action-badge">Ready</span>
            </div>
          </section>
        </aside>

        <section className="staff-recommend-panel">
          <div className="staff-recommend-panel-shell">
            <div className="staff-recommend-panel-header">
              <span>AI 상호추천</span>
              <button
                type="button"
                className="staff-recommend-panel-close"
                aria-label="닫기"
                onClick={() => navigate('/staff')}
              >
                ×
              </button>
            </div>

            <div className="staff-recommend-suggestion-list">
              {aiSuggestions.map((item) => (
                <div key={item.index} className="staff-recommend-suggestion-item">
                  <span className="staff-recommend-item-number">{item.index}</span>

                  <div className="staff-recommend-item-card">
                    <div className="staff-recommend-item-label">
                      <span className="staff-recommend-item-thumb" aria-hidden="true" />
                      <div>
                        <p className="staff-recommend-item-title">{item.title}</p>
                        <p className="staff-recommend-item-sub">{item.subtitle}</p>
                      </div>
                    </div>

                    <div className="staff-recommend-item-mini">
                      <span>{item.tone}</span>
                      <strong>{item.score}</strong>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="staff-recommend-alternatives">
            <div className="staff-recommend-alternative-header">
              <span className="staff-recommend-alternative-title">대체상품</span>
              <span className="staff-recommend-alternative-sub">유사한 스타일 대안</span>
            </div>

            <div className="staff-recommend-alternative-list">
              <article className="staff-recommend-alt-card">
                <div className="staff-recommend-alt-thumb alt-1" aria-hidden="true" />
                <div className="staff-recommend-alt-info">
                  <strong>캐시미어 니트</strong>
                  <span>Warm knit · Premium</span>
                </div>
                <div className="staff-recommend-alt-score">92%</div>
              </article>

              <article className="staff-recommend-alt-card">
                <div className="staff-recommend-alt-thumb alt-2" aria-hidden="true" />
                <div className="staff-recommend-alt-info">
                  <strong>오버사이즈 울 코트</strong>
                  <span>Luxury outerwear · Black</span>
                </div>
                <div className="staff-recommend-alt-score">89%</div>
              </article>

              <article className="staff-recommend-alt-card">
                <div className="staff-recommend-alt-thumb alt-3" aria-hidden="true" />
                <div className="staff-recommend-alt-info">
                  <strong>클래식 셔츠</strong>
                  <span>Minimal · Ivory</span>
                </div>
                <div className="staff-recommend-alt-score">85%</div>
              </article>
            </div>
          </div>
        </section>
      </main>

      <div className="staff-recommend-help" aria-label="help">?</div>
    </div>
  );
}
