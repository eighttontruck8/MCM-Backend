import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { setShoppingMode } from '../../api/client';
import { getCheckin, saveCheckin } from '../../utils/checkinSession';
import './ShoppingOptionPage.css';

const PERSONALIZATION_QUESTIONS = [
  '고객님만을 위해 준비된 맞춤 추천을 바로 받아보세요.',
  '나보다 나를 더 잘 아는 맞춤 쇼핑을 시작해보세요.',
  '취향 설명 없이 바로 시작하는 맞춤 쇼핑을 경험해보세요.',
];

// [Frontend-14-'맞춤 서비스 동의'] 진입할 때 한 문구만 선택해 재렌더링 중에는 바뀌지 않게 한다.
export default function ShoppingOptionPage() {
  const navigate = useNavigate();
  const [question] = useState(
    () => PERSONALIZATION_QUESTIONS[Math.floor(Math.random() * PERSONALIZATION_QUESTIONS.length)],
  );
  const [submittingMode, setSubmittingMode] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSelect = async (shoppingMode) => {
    const checkin = getCheckin();
    if (!checkin?.checkin_id) {
      navigate('/check-in', { replace: true });
      return;
    }
    setSubmittingMode(shoppingMode);
    setErrorMessage('');
    try {
      const response = await setShoppingMode(checkin.checkin_id, shoppingMode);
      saveCheckin({ ...checkin, ...response });
      navigate(shoppingMode === 'STAFF_ASSISTED' ? '/visit-info' : '/lookbook');
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setSubmittingMode(null);
    }
  };

  return (
    <main className="shopping-option-page">
      <section className="shopping-option-page__card" aria-labelledby="personalization-question">
        <p className="shopping-option-page__eyebrow">PERSONAL SHOPPER</p>
        <h1 id="personalization-question" className="shopping-option-page__title">{question}</h1>
        <p className="shopping-option-page__consent-description">
          동의 시, 고객님의 온라인 활동 정보 및 이전 구매이력을 토대로 취향에 맞는 추천을 준비해드려요.
        </p>
        <button type="button" className="shopping-option-page__accept" disabled={Boolean(submittingMode)} onClick={() => handleSelect('STAFF_ASSISTED')}>
          {submittingMode === 'STAFF_ASSISTED' ? '준비 중...' : '수락하고 맞춤 서비스 받기'}
        </button>
        <button type="button" className="shopping-option-page__decline" disabled={Boolean(submittingMode)} onClick={() => handleSelect('PRIVATE')}>
          {submittingMode === 'PRIVATE' ? '처리 중...' : '기본 매장 서비스만 이용하기'}
        </button>
        {errorMessage && <p className="shopping-option-page__error" role="alert">{errorMessage}</p>}
      </section>
    </main>
  );
}
