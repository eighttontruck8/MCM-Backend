import React from 'react';
import { useNavigate } from 'react-router-dom';
import './LookDetailPage.css';

const products = [
  { id: 1, name: '상품명 1', price: '가격', status: 'in-stock' },
  { id: 2, name: '상품명 2', price: '가격', status: 'out-of-stock' },
  { id: 3, name: '상품명 3', price: '가격', status: 'coming' },
];

export default function LookDetailPage() {
  const navigate = useNavigate();
  return (
    <div className="look-detail" data-node-id="17:6">
      <section className="look-detail__hero" data-node-id="17:7">
        <div className="hero__controls">
          <button className="btn-icon" aria-label="favorite">♡</button>
          <button className="btn-icon" aria-label="close" onClick={() => navigate('/lookbook')}>✕</button>
        </div>

        <div className="hero__image">사진 1</div>

        <div className="hero__meta">
          <h1 className="hero__title">룩 1</h1>
          <p className="hero__subtitle">룩 설명 · AI 매칭 매칭률</p>
        </div>
      </section>

      <section className="look-detail__items" data-node-id="17:8">
        <div className="items__heading">구성 아이템</div>
        <ul className="items__list">
          {products.map((p) => (
            <li key={p.id} className="item-row" data-node-id={`17:9${p.id}`}>
              <div className="item-row__left">
                <div className="item-row__name">{p.name}</div>
                <div className="item-row__price">{p.price}</div>
              </div>
              <div className="item-row__right">
                <span className={`badge badge--${p.status}`}>{p.status === 'in-stock' ? '재고 있음' : p.status === 'out-of-stock' ? '재고 없음' : '입고 예정'}</span>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
