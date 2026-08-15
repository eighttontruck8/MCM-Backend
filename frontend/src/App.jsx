import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

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

// 3. 메인 서비스 (홈, 룩북, 찜, 마이페이지)
import MainRecommendPage from './pages/MainRecommendPage/MainRecommendPage';
import AllRecommendPage from './pages/AllRecommendPage/AllRecommendPage';
import LookbookPage from './pages/LookbookPage/LookbookPage';
import LookDetailPage from './pages/LookDetailPage/LookDetailPage';
import WishlistEmptyPage from './pages/WishlistEmptyPage/WishlistEmptyPage';
import WishlistPage from './pages/WishlistPage/WishlistPage';
import MyPage from './pages/MyPage/MyPage';

// ==========================================
// [새로 추가된 부분] 직원용 화면 컴포넌트 불러오기
// ==========================================
import StaffDashboard from './staffPages/Dashboard/StaffDashboard';
import StaffRecommendation from './staffPages/Recommendation/StaffRecommendation';
import StaffWaiting from './staffPages/Waiting/StaffWaiting';
import StaffAnalysis from './staffPages/Analysis/StaffAnalysis';

// ==========================================
// 전체 앱 라우팅 
// ==========================================
function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 1. 로그인 & 회원가입 */}
        <Route path="/" element={<NfcLoadingPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/find-password" element={<FindPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/password-complete" element={<PasswordCompletePage />} />

        {/* 2. 체크인 & 오프라인 연동 흐름 */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/checkin-complete" element={<CheckInCompletePage />} />
        <Route path="/shopping-option" element={<ShoppingOptionPage />} />
        <Route path="/visit-info" element={<VisitInfoPage />} />
        <Route path="/visit-info-complete" element={<VisitInfoCompletePage />} />
        <Route path="/staff-assignment" element={<StaffAssignmentPage />} />

        {/* 3. 메인 서비스 */}
        <Route path="/main" element={<MainRecommendPage />} />
        <Route path="/all-recommend" element={<AllRecommendPage />} />
        <Route path="/lookbook" element={<LookbookPage />} />
        <Route path="/look-detail" element={<LookDetailPage />} />
        <Route path="/wishlist-empty" element={<WishlistEmptyPage />} />
        <Route path="/wishlist" element={<WishlistPage />} />
        <Route path="/mypage" element={<MyPage />} />

        {/* ========================================== */}
        {/* 4. 직원용 서비스 */}
        {/* ========================================== */}
        <Route path="/staff" element={<StaffDashboard />} />
        <Route path="/staff/dashboard" element={<StaffDashboard />} />
        <Route path="/staff/recommend" element={<StaffRecommendation />} />
        <Route path="/staff/waiting" element={<StaffWaiting />} />
        <Route path="/staff/analysis" element={<StaffAnalysis />} />

        {/* 기존 경로 호환성 유지 */}
        <Route path="/waiting" element={<StaffWaiting />} />
        <Route path="/staffpage" element={<StaffWaiting />} />
        <Route path="/staff-page" element={<StaffWaiting />} />

        {/* 5. 404 에러 처리 */}
        <Route path="*" element={<div style={{ padding: '20px', textAlign: 'center' }}>요청하신 페이지를 찾을 수 없습니다.</div>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;