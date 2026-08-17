import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { createOrResumeCheckin, login } from '../../api/client';
import { clearEntryTag, getEntryTag, saveCheckin } from '../../utils/checkinSession';
import './LoginPage.css';

export default function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setErrorMessage('');
    setIsSubmitting(true);
    try {
      const tokens = await login(email, password, remember);
      if (tokens.user.role === 'STAFF') {
        clearEntryTag();
        navigate('/staff/waiting', { replace: true });
        return;
      }

      const entryTag = getEntryTag();
      if (searchParams.get('next') === 'check-in' && entryTag?.tag_token) {
        const checkin = await createOrResumeCheckin(entryTag.tag_token);
        saveCheckin({ ...checkin, entry: entryTag });
        clearEntryTag();
        navigate('/checkin-complete', { replace: true });
        return;
      }
      navigate('/main', { replace: true });
    } catch (error) {
      setErrorMessage(error.message || '로그인하지 못했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="login-page" data-node-id="17:8" data-name="로그인">
      <div className="login-page__body" data-node-id="17:9" data-name="Body">
        <div className="login-page__app" data-node-id="17:10" data-name="App">
          <section className="login-page__hero" data-node-id="17:11" data-name="AuthScreen">
            <div className="login-page__hero-backdrop" data-node-id="17:12" data-name="Container">
              <div className="login-page__hero-image" data-node-id="17:13" data-name="ImgPlaceholder">
                <div className="login-page__hero-text" data-node-id="17:14" data-name="Text">
                  <p className="login-page__hero-image-label" data-node-id="17:15">
                    브랜드 이미지
                  </p>
                </div>
              </div>
              <div className="login-page__hero-gradient" data-node-id="17:16" data-name="Container" />
              <div className="login-page__hero-copy" data-node-id="17:17" data-name="Container">
                <p className="login-page__hero-subtitle" data-node-id="17:18">
                  Luxury AI Retail
                </p>
                <p className="login-page__hero-title" data-node-id="17:19">
                  M·Journey
                </p>
              </div>
            </div>
          </section>

          <div className="login-page__tabs" data-node-id="17:20" data-name="Container">
            <button type="button" className="login-page__tab login-page__tab--active" data-node-id="17:21" data-name="Button">
              로그인
            </button>
            <button
              type="button"
              className="login-page__tab login-page__tab--inactive"
              data-node-id="17:22"
              data-name="Button"
              onClick={() => navigate(`/signup${searchParams.toString() ? `?${searchParams}` : ''}`)}
            >
              회원가입
            </button>
          </div>

          <form
            className="login-page__form"
            data-node-id="17:23"
            data-name="Container"
            onSubmit={handleSubmit}
          >
            <div className="login-page__field" data-node-id="17:24" data-name="Input">
              <label htmlFor="login-email" className="login-page__label" data-node-id="17:25" data-name="Label">
                이메일
              </label>
              <input
                id="login-email"
                type="email"
                className="login-page__input"
                placeholder="customer@example.com"
                data-node-id="17:26"
                data-name="Text Input"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </div>

            <div className="login-page__field" data-node-id="17:27" data-name="Input">
              <label htmlFor="login-password" className="login-page__label" data-node-id="17:28" data-name="Label">
                비밀번호
              </label>
              <input
                id="login-password"
                type="password"
                className="login-page__input"
                placeholder="••••••••"
                data-node-id="17:29"
                data-name="Password Input"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </div>

            <div className="login-page__meta" data-node-id="17:30" data-name="Container">
              <label className="login-page__remember" data-node-id="17:31">
                <input type="checkbox" className="login-page__checkbox" checked={remember} onChange={(event) => setRemember(event.target.checked)} />
                <span>자동 로그인</span>
              </label>
              <button
                type="button"
                className="login-page__link"
                data-node-id="17:32"
                onClick={() => navigate('/find-password')}
              >
                비밀번호 찾기
              </button>
            </div>

            {errorMessage && <p className="login-page__error" role="alert">{errorMessage}</p>}

            <button type="submit" className="login-page__submit" data-node-id="17:33" data-name="Container" disabled={isSubmitting}>
              {isSubmitting ? '로그인 중...' : '로그인'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
