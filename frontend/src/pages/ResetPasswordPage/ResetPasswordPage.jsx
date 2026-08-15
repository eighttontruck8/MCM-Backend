import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { confirmPasswordReset } from '../../api/client';
import './ResetPasswordPage.css';

// [Frontend-05-'비밀번호 재설정 메일 연동']
export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const resetToken = searchParams.get('token') ?? '';
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!resetToken) {
      setErrorMessage('메일의 비밀번호 재설정 링크로 접속해주세요.');
      return;
    }
    if (password.length < 12) {
      setErrorMessage('새 비밀번호는 12자 이상이어야 합니다.');
      return;
    }
    if (password !== confirmation) {
      setErrorMessage('비밀번호 확인 값이 일치하지 않습니다.');
      return;
    }
    setIsSubmitting(true);
    setErrorMessage('');
    try {
      await confirmPasswordReset(resetToken, password);
      navigate('/password-complete', { replace: true });
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="reset-password-page">
      <div className="reset-password-page__body">
        <div className="reset-password-page__app">
          <header className="reset-password-page__header">
            <button type="button" className="reset-password-page__back-button" onClick={() => navigate('/find-password')}>
              <span className="reset-password-page__back-icon">←</span>
            </button>
            <div className="reset-password-page__header-copy">
              <p className="reset-password-page__header-label">비밀번호 찾기</p>
              <p className="reset-password-page__header-title">새 비밀번호 설정</p>
            </div>
          </header>
          <main className="reset-password-page__content">
            <p className="reset-password-page__description">기존 비밀번호와 다른 12자 이상의 비밀번호를 입력해주세요.</p>
            <form onSubmit={handleSubmit}>
              <div className="reset-password-page__field">
                <label htmlFor="new-password" className="reset-password-page__label">새 비밀번호</label>
                <input id="new-password" type="password" autoComplete="new-password" required minLength={12} className="reset-password-page__input" placeholder="••••••••••••" value={password} onChange={(event) => setPassword(event.target.value)} />
              </div>
              <div className="reset-password-page__field">
                <label htmlFor="confirm-password" className="reset-password-page__label">비밀번호 확인</label>
                <input id="confirm-password" type="password" autoComplete="new-password" required minLength={12} className="reset-password-page__input" placeholder="••••••••••••" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} />
              </div>
              {!resetToken && <p className="reset-password-page__error" role="alert">유효한 재설정 링크가 없습니다.</p>}
              {errorMessage && <p className="reset-password-page__error" role="alert">{errorMessage}</p>}
              <button type="submit" disabled={isSubmitting || !resetToken} className="reset-password-page__submit reset-password-page__submit--active">
                {isSubmitting ? '변경 중...' : '비밀번호 변경'}
              </button>
            </form>
          </main>
        </div>
      </div>
    </div>
  );
}
