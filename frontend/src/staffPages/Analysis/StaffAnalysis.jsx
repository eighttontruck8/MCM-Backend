import { useNavigate } from 'react-router-dom';
import './StaffAnalysis.css';

const styleTendency = [
  { label: '미니멀', value: 82, color: '#44d7b6' },
  { label: '프리미엄', value: 68, color: '#42b9ff' },
  { label: '모던', value: 56, color: '#7e9bff' },
  { label: '캐주얼', value: 41, color: '#ffb84d' },
];

const preferredCategories = [
  { label: '아우터', value: 88 },
  { label: '니트', value: 72 },
  { label: '팬츠', value: 52 },
  { label: '액세서리', value: 34 },
];

const purchasePatterns = [
  '세련된 실루엣 선호',
  '프리미엄 원단 우선 고려',
  '양질의 아우터 재구매 경향',
  '중성적 톤 기반 쇼핑',
  '중복 색상 조합 선호',
];

export default function StaffAnalysis() {
  const navigate = useNavigate();

  return (
    <div className="staff-analysis-page">
      <header className="staff-analysis-topbar">
        <div className="staff-analysis-brand-pill">
          <div className="staff-analysis-brand-mark">◌</div>
          <span className="staff-analysis-brand-name">M-Journey</span>
        </div>
      </header>

      <main className="staff-analysis-canvas">
        <section className="staff-analysis-floating-card">
          <div className="staff-analysis-floating-header">
            <span className="staff-analysis-floating-title">AI 취향 분석 리포트</span>
            <button
              type="button"
              className="staff-analysis-close-btn"
              aria-label="닫기"
              onClick={() => navigate('/staff')}
            >
              ×
            </button>
          </div>

          <div className="staff-analysis-panel-group">
            <div className="staff-analysis-panel section-style">
              <h2 className="staff-analysis-panel-title">스타일 경향</h2>
              <div className="staff-analysis-chart-group">
                {styleTendency.map((item) => (
                  <div key={item.label} className="staff-analysis-row">
                    <span className="staff-analysis-label">{item.label}</span>
                    <div className="staff-analysis-bar-track">
                      <div
                        className="staff-analysis-bar-fill"
                        style={{ width: `${item.value}%`, background: item.color }}
                      />
                    </div>
                    <span className="staff-analysis-value-text">{item.value}%</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="staff-analysis-panel section-category">
              <h2 className="staff-analysis-panel-title">선호 카테고리</h2>
              <div className="staff-analysis-list">
                {preferredCategories.map((item) => (
                  <div key={item.label} className="staff-analysis-category-row">
                    <span className="staff-analysis-category-label">{item.label}</span>
                    <div className="staff-analysis-category-track">
                      <div
                        className="staff-analysis-category-fill"
                        style={{ width: `${item.value}%` }}
                      />
                    </div>
                    <span className="staff-analysis-value-text">{item.value}%</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="staff-analysis-panel section-pattern">
              <h2 className="staff-analysis-panel-title">구매 패턴</h2>
              <div className="staff-analysis-patterns">
                {purchasePatterns.map((pattern) => (
                  <div key={pattern} className="staff-analysis-pattern-item">
                    <span className="staff-analysis-bullet" />
                    <span>{pattern}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="staff-analysis-box">
              <h2 className="staff-analysis-box-title">AI 종합 분석</h2>
              <p className="staff-analysis-box-text">
                이 고객은 고급 원단과 정교한 디테일을 갖춘 아우터와 니트 제품에 높은 관심을 보이며,
                미니멀하고 세련된 실루엣을 선호하는 경향이 뚜렷합니다. 최근에는 고가의 프리미엄 아이템을
                우선적으로 검토하며, 계절 초반 신상품 진열과 한정 컬렉션 제안의 반응이 좋습니다.
                고객의 취향과 결합된 맞춤형 스타일링 제안은 전환율과 재구매 확률을 높이는 데 유리합니다.
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
