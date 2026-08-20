import { useNavigate } from 'react-router-dom';
import { getStaffActiveVisit } from '../../utils/staffSession';
import { createMockTasteReport } from '../../utils/staffTasteReport';
import './StaffRecommendation.css';

// [Frontend-19-'직원용 mock 취향 리포트'] 응대 시작과 동시에 생성된 고객별 리포트를 표시한다.
export default function StaffRecommendation() {
  const navigate = useNavigate();
  const activeVisit = getStaffActiveVisit();
  const report = activeVisit?.tasteReport ?? createMockTasteReport(activeVisit?.profile, activeVisit?.visit);

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
          <p className="staff-recommend-sidebar-label">고객 취향 리포트</p>
          <section className="staff-recommend-profile-card">
            <div className="staff-recommend-profile-top">
              <span className="staff-recommend-profile-badge">MOCK REPORT</span>
              <span className="staff-recommend-profile-mini">{report.initial}</span>
            </div>
            <div className="staff-recommend-profile-name-row">
              <h2 className="staff-recommend-profile-name">{report.name} 고객님</h2>
              <span className="staff-recommend-profile-date">방금 생성됨</span>
            </div>
            <div className="staff-recommend-profile-tags">
              {report.tags.map((tag) => (
                <span key={tag} className="staff-recommend-profile-tag">{tag}</span>
              ))}
            </div>
          </section>

          <section className="staff-recommend-meta-card">
            <div className="staff-recommend-meta-grid">
              {report.metrics.map((item) => (
                <div key={item.label} className="staff-recommend-meta-item">
                  <span className="staff-recommend-meta-label">{item.label}</span>
                  <span className="staff-recommend-meta-value">{item.value}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="staff-recommend-action-card">
            <div className="staff-recommend-action-row">
              <span className="staff-recommend-action-title">리포트 유형</span>
              <span className="staff-recommend-action-badge">Mock</span>
            </div>
            <div className="staff-recommend-action-row">
              <span className="staff-recommend-action-title">추천 상태</span>
              <span className="staff-recommend-action-badge">Ready</span>
            </div>
          </section>
        </aside>

        <section className="staff-recommend-panel">
          <div className="staff-recommend-panel-shell">
            <div className="staff-recommend-panel-header">
              <span>취향 분석 및 추천 아이템</span>
              <button type="button" className="staff-recommend-panel-close" aria-label="닫기" onClick={() => navigate('/staff/waiting')}>
                ×
              </button>
            </div>
            <p className="staff-recommend-summary">{report.summary}</p>
            <div className="staff-recommend-suggestion-list">
              {report.recommendations.map((item) => (
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
        </section>
      </main>
    </div>
  );
}
