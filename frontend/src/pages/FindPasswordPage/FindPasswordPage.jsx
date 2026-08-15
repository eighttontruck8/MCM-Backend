import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { requestPasswordReset } from '../../api/client';
import './FindPasswordPage.css';

// [Frontend-05-'비밀번호 재설정 메일 연동']
export default function FindPasswordPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    setIsSubmitting(true);
    setErrorMessage('');
    try {
      const response = await requestPasswordReset(email);
      if (response.reset_token) {
        navigate(`/reset-password?token=${encodeURIComponent(response.reset_token)}`);
        return;
      }
      setMessage(response.message);
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="find-password-page">
      <div className="find-password-page__body">
        <div className="find-password-page__app">
          <header className="find-password-page__header">
            <button type="button" className="find-password-page__back-button" onClick={() => navigate('/login')}>
              <span className="find-password-page__back-icon">←</span>
            </button>
            <div className="find-password-page__header-copy">
              <p className="find-password-page__header-label">비밀번호 찾기</p>
              <p className="find-password-page__header-title">이메일 입력</p>
            </div>
          </header>
          <main className="find-password-page__content">
            <p className="find-password-page__description">가입한 이메일로 15분 동안 유효한 재설정 링크를 보내드립니다.</p>
            <form onSubmit={handleSubmit}>
              <div className="find-password-page__field">
                <label htmlFor="find-password-email" className="find-password-page__label">이메일</label>
                <input id="find-password-email" type="email" autoComplete="email" required className="find-password-page__input" placeholder="customer@example.com" value={email} onChange={(event) => setEmail(event.target.value)} />
              </div>
              {message && <p className="find-password-page__message">{message}<br />메일함과 스팸함을 확인해주세요.</p>}
              {errorMessage && <p className="find-password-page__error" role="alert">{errorMessage}</p>}
              <button type="submit" disabled={isSubmitting || Boolean(message)} className="find-password-page__submit">
                {isSubmitting ? '전송 중...' : message ? '안내 메일 전송 완료' : '재설정 메일 받기'}
              </button>
            </form>
          </main>
        </div>
      </div>
    </div>
  );
}
