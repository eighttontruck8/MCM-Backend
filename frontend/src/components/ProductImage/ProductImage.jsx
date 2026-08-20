import { useState } from 'react';
import { API_BASE_URL } from '../../api/client';
import './ProductImage.css';

function resolveImageUrl(source) {
  if (!source) return null;
  if (/^https?:\/\//i.test(source)) return source;
  return `${API_BASE_URL}${source.startsWith('/') ? source : `/${source}`}`;
}

// [Frontend-08-'상품 이미지 대체 표시'] 원본 이미지가 없어도 상품 카드 구조와 정보를 유지한다.
export default function ProductImage({ src, alt, className = '' }) {
  const [failed, setFailed] = useState(false);
  const resolvedSource = resolveImageUrl(src);

  return (
    <div className={`${className} product-visual${failed || !resolvedSource ? ' product-visual--fallback' : ''}`}>
      {resolvedSource && !failed ? (
        <img
          className="product-visual__image"
          src={resolvedSource}
          alt={alt}
          loading="lazy"
          onError={() => setFailed(true)}
        />
      ) : (
        <span className="product-visual__fallback" aria-label={`${alt} 이미지 준비 중`}>IMAGE<br />COMING SOON</span>
      )}
    </div>
  );
}
