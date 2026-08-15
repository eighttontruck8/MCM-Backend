import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { createOrResumeCheckin, fetchEntryTag, getAccessToken } from '../../api/client';
import { saveCheckin, saveEntryTag } from '../../utils/checkinSession';
import './NfcLoadingPage.css';

const ICON = 'https://www.figma.com/api/mcp/asset/fcba47cd-35ec-4e4f-9c58-f5bcc3379427.svg';

export default function NfcLoadingPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    let cancelled = false;

    // [Frontend-01-'QR JWT 체크인 연동'] QR 토큰은 검증 후 세션에만 보관한다.
    const connectEntry = async () => {
      const tagToken = searchParams.get('tag_token');
      if (!tagToken) {
        setErrorMessage('QR 코드에 매장 진입 정보가 없습니다. 다시 스캔해주세요.');
        return;
      }
      try {
        const entryTag = await fetchEntryTag(tagToken);
        if (cancelled) return;
        saveEntryTag(entryTag);
        if (!getAccessToken()) {
          navigate('/login?next=check-in', { replace: true });
          return;
        }
        const checkin = await createOrResumeCheckin(tagToken);
        if (cancelled) return;
        saveCheckin({ ...checkin, entry: entryTag });
        navigate('/checkin-complete', { replace: true });
      } catch (error) {
        if (!cancelled) setErrorMessage(error.message || '매장 진입 정보를 확인하지 못했습니다.');
      }
    };

    connectEntry();

    return () => {
      cancelled = true;
    };
  }, [navigate, searchParams]);
  return (
    <div className="nfc-loading" data-node-id="17:70">
      <div className="nfc-loading__inner">
        <div className="nfc-center" aria-hidden>
          <div className="nfc-rings">
            <div className="ring ring--3" />
            <div className="ring ring--2" />
            <div className="ring ring--1" />
            <div className="nfc-icon">
              <img src={ICON} alt="nfc icon" />
            </div>
          </div>
        </div>

        <div className="nfc-text">
          <div className="nfc-eyebrow">QR CHECK-IN</div>
          <h1 className="nfc-title">{errorMessage ? 'QR 확인 실패' : '매장 확인 중...'}</h1>
          <p className={`nfc-sub ${errorMessage ? 'nfc-sub--error' : ''}`}>
            {errorMessage || '안전한 매장 진입 정보를 확인하고 있습니다.'}
          </p>
          {errorMessage && (
            <button type="button" className="nfc-retry" onClick={() => navigate('/login', { replace: true })}>
              로그인 화면으로 이동
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
