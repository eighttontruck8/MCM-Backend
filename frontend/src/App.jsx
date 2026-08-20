import { BrowserRouter, Navigate, Routes, Route } from 'react-router-dom';
import { getAccessToken, getAuthUser } from './api/client';
import { usePageRevive } from './utils/usePageRevive';

// ==========================================
// 기존 고객용 화면 컴포넌트 불러오기 (유지)
// ==========================================
// 1. 로그인 & 회원가입 (Auth)
import LoginPage from './pages/LoginPage/LoginPage';
import SignupPage from './pages/SignupPage/SignupPage';
import FindPasswordPage from './pages/FindPasswordPage/FindPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage/ResetPasswordPage';
import PasswordCompletePage from './pages/PasswordCompletePage/PasswordCompletePage';

// 2. 체크인 & 오프라인 연동 흐름
import NfcLoadingPage from './pages/NfcLoadingPage/NfcLoadingPage';
import CheckInCompletePage from './pages/CheckInCompletePage/CheckInCompletePage';
import ShoppingOptionPage from './pages/ShoppingOptionPage/ShoppingOptionPage';
import VisitInfoPage from './pages/VisitInfoPage/VisitInfoPage';
import VisitInfoCompletePage from './pages/VisitInfoCompletePage/VisitInfoCompletePage';
import StaffAssignmentPage from './pages/StaffAssignmentPage/StaffAssignmentPage';
import StoreSelectionPage from './pages/StoreSelectionPage/StoreSelectionPage';

// 3. 메인 서비스 (홈, 룩북, 찜, 마이페이지)
import MainRecommendPage from './pages/MainRecommendPage/MainRecommendPage';
import AllRecommendPage from './pages/AllRecommendPage/AllRecommendPage';
import LookbookPage from './pages/LookbookPage/LookbookPage';
import LookDetailPage from './pages/LookDetailPage/LookDetailPage';
import WishlistPage from './pages/WishlistPage/WishlistPage';
import MyPage from './pages/MyPage/MyPage';

// 0. 매장 키오스크 & QR 랜딩
import KioskPage from './pages/KioskPage/KioskPage';
import WelcomePage from './pages/WelcomePage/WelcomePage';

// ==========================================
// [새로 추가된 부분] 직원용 화면 컴포넌트 불러오기
// ==========================================
import StaffDashboard from './staffPages/Dashboard/StaffDashboard';
import StaffRecommendation from './staffPages/Recommendation/StaffRecommendation';
import StaffWaiting from './staffPages/Waiting/StaffWaiting';
import StaffAnalysis from './staffPages/Analysis/StaffAnalysis';

// [Frontend-07-'보호 화면 인증 가드'] 기술적인 Bearer 오류 대신 로그인 화면과 사용자 문구를 제공한다.
function RequireAuth({ children, role = null }) {
  if (!getAccessToken()) {
    const roleQuery = role === 'STAFF' ? '&role=staff' : '';
    return <Navigate to={`/login?reason=auth-required${roleQuery}`} replace />;
  }
  const user = getAuthUser();
  if (role && user?.role !== role) {
    return <Navigate to={user?.role === 'STAFF' ? '/staff' : '/main'} replace />;
  }
  return children;
}

// ==========================================
// 전체 앱 라우팅 
// ==========================================
function App() {
  const reviveKey = usePageRevive();

  return (
    <BrowserRouter>
      <Routes key={reviveKey}>
        {/* 0. 매장 키오스크 & QR 랜딩 */}
        <Route path="/kiosk" element={<KioskPage />} />
        <Route path="/welcome" element={<WelcomePage />} />

        {/* 1. 로그인 & 회원가입 */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/find-password" element={<FindPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/password-complete" element={<PasswordCompletePage />} />

        {/* 2. 체크인 & 오프라인 연동 흐름 */}
        <Route path="/check-in" element={<NfcLoadingPage />} />
        <Route path="/check-in/stores" element={<RequireAuth><StoreSelectionPage /></RequireAuth>} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/checkin-complete" element={<RequireAuth><CheckInCompletePage /></RequireAuth>} />
        <Route path="/shopping-option" element={<RequireAuth><ShoppingOptionPage /></RequireAuth>} />
        <Route path="/visit-info" element={<RequireAuth><VisitInfoPage /></RequireAuth>} />
        <Route path="/visit-info-complete" element={<RequireAuth><VisitInfoCompletePage /></RequireAuth>} />
        <Route path="/staff-assignment" element={<RequireAuth><StaffAssignmentPage /></RequireAuth>} />

        {/* 3. 메인 서비스 */}
        <Route path="/main" element={<RequireAuth><MainRecommendPage /></RequireAuth>} />
        <Route path="/all-recommend" element={<RequireAuth><AllRecommendPage /></RequireAuth>} />
        <Route path="/lookbook" element={<RequireAuth><LookbookPage /></RequireAuth>} />
        <Route path="/look-detail" element={<RequireAuth><LookDetailPage /></RequireAuth>} />
        <Route path="/wishlist-empty" element={<Navigate to="/wishlist" replace />} />
        <Route path="/wishlist" element={<RequireAuth><WishlistPage /></RequireAuth>} />
        <Route path="/mypage" element={<RequireAuth><MyPage /></RequireAuth>} />

        {/* ========================================== */}
        {/* 4. 직원용 서비스 */}
        {/* ========================================== */}
        <Route path="/staff" element={<RequireAuth role="STAFF"><StaffDashboard /></RequireAuth>} />
        <Route path="/staff/dashboard" element={<Navigate to="/staff" replace />} />
        <Route path="/staff/recommend" element={<RequireAuth role="STAFF"><StaffRecommendation /></RequireAuth>} />
        <Route path="/staff/waiting" element={<RequireAuth role="STAFF"><StaffWaiting /></RequireAuth>} />
        <Route path="/staff/analysis" element={<RequireAuth role="STAFF"><StaffAnalysis /></RequireAuth>} />

        {/* 기존 경로 호환성 유지 */}
        <Route path="/waiting" element={<RequireAuth role="STAFF"><StaffWaiting /></RequireAuth>} />
        <Route path="/staffpage" element={<Navigate to="/staff" replace />} />
        <Route path="/staff-page" element={<Navigate to="/staff" replace />} />

        {/* 5. 404 에러 처리 */}
        <Route path="*" element={<div style={{ padding: '20px', textAlign: 'center' }}>요청하신 페이지를 찾을 수 없습니다.</div>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
