import { useNavigate } from 'react-router-dom';
import './AppBottomNav.css';

const ITEMS = [
  { key: 'home', label: '홈', path: '/main' },
  { key: 'lookbook', label: '룩북', path: '/lookbook' },
  { key: 'wishlist', label: '찜', path: '/wishlist' },
  { key: 'mypage', label: 'MY', path: '/mypage' },
];

// [Frontend-06-'공통 모바일 내비게이션'] 핵심 고객 화면의 위치와 시각 계층을 동일하게 유지한다.
export default function AppBottomNav({ active }) {
  const navigate = useNavigate();

  return (
    <nav className="app-bottom-nav" aria-label="주요 메뉴">
      {ITEMS.map((item) => (
        <button
          type="button"
          key={item.key}
          className={`app-bottom-nav__item${active === item.key ? ' app-bottom-nav__item--active' : ''}`}
          aria-current={active === item.key ? 'page' : undefined}
          onClick={() => navigate(item.path)}
        >
          {item.label}
        </button>
      ))}
    </nav>
  );
}
