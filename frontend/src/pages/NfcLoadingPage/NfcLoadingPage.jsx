import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './NfcLoadingPage.css';

const ICON = 'https://www.figma.com/api/mcp/asset/fcba47cd-35ec-4e4f-9c58-f5bcc3379427.svg';

export default function NfcLoadingPage() {
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setTimeout(() => {
      navigate('/login');
    }, 2500);

    return () => clearTimeout(timer);
  }, [navigate]);
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
          <div className="nfc-eyebrow">NFC CHECK-IN</div>
          <h1 className="nfc-title">태그 인식 중...</h1>
          <p className="nfc-sub">NFC 태그에 기기를 가까이 대주세요</p>
        </div>
      </div>
    </div>
  );
}
