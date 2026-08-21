import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { createOrResumeCheckin, signupCustomer, signupStaff } from '../../api/client';
import { clearEntryTag, getEntryTag, saveCheckin } from '../../utils/checkinSession';
import brandImage from '../../assets/brand.png';
import './SignupPage.css';

export default function SignupPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isStaffSignup = searchParams.get('role') === 'staff';
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [storeId, setStoreId] = useState('S001');
  const [signupCode, setSignupCode] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const authQuery = searchParams.toString() ? `?${searchParams}` : '';

  const handleSubmit = async (event) => {
    event.preventDefault();
    setErrorMessage('');
    if (password !== passwordConfirm) {
      setErrorMessage('비밀번호가 일치하지 않습니다.');
      return;
    }
    setIsSubmitting(true);
    try {
      if (isStaffSignup) {
        await signupStaff({ name, email, password, storeId, signupCode });
        navigate('/login?role=staff&reason=signup-complete', { replace: true });
        return;
      }
      await signupCustomer({ name, phone, email, password });
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
      if (isStaffSignup && error.code === 'EMAIL_ALREADY_REGISTERED') {
        setErrorMessage('이미 고객 또는 직원으로 가입된 이메일입니다. 기존 계정으로 로그인해주세요.');
        return;
      }
      setErrorMessage(error.message || '회원가입하지 못했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="signup-page" data-node-id="13:1475" data-name="회원가입">
      <div className="signup-page__body" data-node-id="13:1476" data-name="Body">
        <div className="signup-page__app" data-node-id="13:1478" data-name="App">
          <section className="signup-page__hero" data-node-id="13:1479" data-name="AuthScreen">
            <div className="signup-page__hero-backdrop" data-node-id="13:1480" data-name="Container">
              {/* [Frontend-Auth-'로그인·회원가입 브랜드 이미지 통일'] */}
              <div className="signup-page__hero-image" data-node-id="13:1481">
                <img src={brandImage} alt="MCM Brand" className="signup-page__hero-img" />
              </div>
              <div className="signup-page__hero-gradient" data-node-id="13:1485" data-name="Container" />
              <div className="signup-page__hero-copy" data-node-id="13:1486" data-name="Container">
                <p className="signup-page__hero-subtitle" data-node-id="13:1488">
                  Luxury AI Retail
                </p>
                <p className="signup-page__hero-title" data-node-id="13:1491">
                  M·Journey
                </p>
              </div>
            </div>
          </section>

          <div className="signup-page__tabs" data-node-id="13:1494" data-name="Container">
            <button
              type="button"
              className="signup-page__tab signup-page__tab--inactive"
              data-node-id="13:1495"
              data-name="Button"
              onClick={() => navigate(`/login${authQuery}`)}
            >
              {isStaffSignup ? '직원 로그인' : '로그인'}
            </button>
            <button type="button" className="signup-page__tab signup-page__tab--active" data-node-id="13:1498" data-name="Button">
              {isStaffSignup ? '직원 회원가입' : '회원가입'}
            </button>
          </div>

          <form className="signup-page__form" data-node-id="13:1503" data-name="Container" onSubmit={handleSubmit}>
            <div className="signup-page__field" data-node-id="13:1504" data-name="Input">
              <label htmlFor="signup-name" className="signup-page__label" data-node-id="13:1505" data-name="Label">
                이름
              </label>
              <input
                id="signup-name"
                type="text"
                className="signup-page__input"
                placeholder="홍길동"
                autoComplete="name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                minLength={2}
                required
                data-node-id="13:1508"
                data-name="Text Input"
              />
            </div>

            {!isStaffSignup && (
              <div className="signup-page__field" data-node-id="13:1510" data-name="Input">
                <label htmlFor="signup-phone" className="signup-page__label" data-node-id="13:1511" data-name="Label">
                  연락처
                </label>
                <input
                  id="signup-phone"
                  type="tel"
                  className="signup-page__input"
                  placeholder="010-0000-0000"
                  autoComplete="tel"
                  value={phone}
                  onChange={(event) => setPhone(event.target.value)}
                  pattern="01[016789]-?[0-9]{3,4}-?[0-9]{4}"
                  required
                  data-node-id="13:1514"
                  data-name="Phone Input"
                />
              </div>
            )}

            {isStaffSignup && (
              <>
                {/* [Frontend-12-'직원 셀프 회원가입'] 매장과 비공개 가입 코드를 백엔드에서 검증한다. */}
                <div className="signup-page__field">
                  <label htmlFor="signup-store-id" className="signup-page__label">매장 코드</label>
                  <input
                    id="signup-store-id"
                    type="text"
                    className="signup-page__input"
                    value={storeId}
                    onChange={(event) => setStoreId(event.target.value)}
                    autoComplete="organization"
                    required
                  />
                </div>
                <div className="signup-page__field">
                  <label htmlFor="signup-staff-code" className="signup-page__label">직원 가입 코드</label>
                  <input
                    id="signup-staff-code"
                    type="password"
                    className="signup-page__input"
                    placeholder="관리자에게 받은 가입 코드"
                    value={signupCode}
                    onChange={(event) => setSignupCode(event.target.value)}
                    autoComplete="off"
                    minLength={4}
                    required
                  />
                </div>
                <p className="signup-page__notice">직원 계정은 승인된 가입 코드가 있어야 생성할 수 있습니다.</p>
              </>
            )}

            {/* [Frontend-01-'인증 이메일 식별자 통일'] 백엔드 로그인 계약과 동일하게 이메일을 사용한다. */}
            <div className="signup-page__field" data-node-id="13:1516" data-name="Input">
              <label htmlFor="signup-email" className="signup-page__label" data-node-id="13:1517" data-name="Label">
                이메일
              </label>
              <input
                id="signup-email"
                type="email"
                className="signup-page__input"
                placeholder={isStaffSignup ? 'staff@example.com' : 'customer@example.com'}
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
                data-node-id="13:1520"
                data-name="Text Input"
              />
            </div>

            <div className="signup-page__field" data-node-id="13:1522" data-name="Input">
              <label htmlFor="signup-password" className="signup-page__label" data-node-id="13:1523" data-name="Label">
                비밀번호
              </label>
              <input
                id="signup-password"
                type="password"
                className="signup-page__input"
                placeholder="4자 이상"
                autoComplete="new-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                minLength={4}
                required
                data-node-id="13:1526"
                data-name="Password Input"
              />
            </div>

            <div className="signup-page__field">
              <label htmlFor="signup-password-confirm" className="signup-page__label">
                비밀번호 확인
              </label>
              <input
                id="signup-password-confirm"
                type="password"
                className="signup-page__input"
                placeholder="비밀번호를 다시 입력해주세요"
                autoComplete="new-password"
                value={passwordConfirm}
                onChange={(event) => setPasswordConfirm(event.target.value)}
                minLength={4}
                required
              />
            </div>

            {errorMessage && <p className="signup-page__error" role="alert">{errorMessage}</p>}

            <button
              type="submit"
              className="signup-page__submit"
              data-node-id="13:1528"
              data-name="Container"
              disabled={isSubmitting}
            >
              {isSubmitting ? '가입 중...' : isStaffSignup ? '직원 가입하기' : '가입하기'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
