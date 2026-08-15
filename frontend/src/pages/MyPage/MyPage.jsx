import React from 'react';
import { useNavigate } from 'react-router-dom';
import { mockCustomers } from '../../mock/mockCustomers';
import { mockProducts } from '../../mock/mockProducts';
import './MyPage.css';

export default function MyPage(){
  const navigate = useNavigate();
  const customer = mockCustomers[0];
  const recent = mockProducts.slice(0, 3).map((product, index) => ({
    id: index + 1,
    name: product.product_name,
    date: `${customer.last_visit_days_ago}일 전 구매`,
    price: `${product.price.toLocaleString()}원`,
  }));

  return (
    <div className="my-page" data-node-id="13:3399">
      <div className="my-page__container">
        <header className="my-header">
          <div className="brand">M-Journey</div>
          <button className="checkin">체크인</button>
        </header>

        <section className="profile-hero">
          <div className="avatar">{customer.name.charAt(0)}</div>
          <div className="profile-info">
            <div className="profile-name">{customer.name}</div>
            <div className="profile-id">#{customer.customer_id}</div>
          </div>

          <div className="profile-stats">
            <div className="stat">{customer.visit_count}건<br/><span>구매 이력</span></div>
            <div className="stat">{customer.recent_interests.length}건<br/><span>관심 상품</span></div>
            <div className="stat">{customer.visit_count}회<br/><span>방문 횟수</span></div>
          </div>
        </section>

        <section className="tags-section">
          <div className="section-title">AI 분석 취향 프로필</div>
          <div className="tags">
            {customer.style_tags.map((tag) => (
              <button key={tag} className="tag">{tag}</button>
            ))}
          </div>
        </section>

        <section className="recent-section">
          <div className="section-title">최근 구매 이력</div>
          <ul className="recent-list">
            {recent.map(r => (
              <li key={r.id} className="recent-item">
                <div>
                  <div className="recent-name">{r.name}</div>
                  <div className="recent-date">{r.date}</div>
                </div>
                <div className="recent-price">{r.price}</div>
              </li>
            ))}
          </ul>
        </section>

        <section className="settings-section">
          <button className="setting">개인정보 처리방침</button>
          <button className="setting">로그아웃</button>
        </section>

        <nav className="bottom-nav">
          <button className="nav" onClick={() => navigate('/main')}>홈</button>
          <button className="nav" onClick={() => navigate('/lookbook')}>룩북</button>
          <button className="nav" onClick={() => navigate('/wishlist')}>찜</button>
          <button className="nav nav--active" onClick={() => navigate('/mypage')}>MY</button>
        </nav>
      </div>
    </div>
  );
}
