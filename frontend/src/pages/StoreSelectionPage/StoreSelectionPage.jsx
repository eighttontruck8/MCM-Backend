import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createOrResumeStoreCheckin, fetchStores } from '../../api/client';
import { saveCheckin } from '../../utils/checkinSession';
import './StoreSelectionPage.css';

function distanceKm(position, store) {
  if (store.latitude == null || store.longitude == null) return null;
  const radians = (degrees) => (degrees * Math.PI) / 180;
  const earthRadiusKm = 6371;
  const latitudeDelta = radians(store.latitude - position.latitude);
  const longitudeDelta = radians(store.longitude - position.longitude);
  const a = Math.sin(latitudeDelta / 2) ** 2
    + Math.cos(radians(position.latitude)) * Math.cos(radians(store.latitude))
    * Math.sin(longitudeDelta / 2) ** 2;
  return earthRadiusKm * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// [Frontend-15-'가까운 매장 체크인'] 위치 허용 시 거리순, 미허용 시 서버 기본 순서로 매장을 표시한다.
export default function StoreSelectionPage() {
  const navigate = useNavigate();
  const [stores, setStores] = useState([]);
  const [position, setPosition] = useState(null);
  const [locationMessage, setLocationMessage] = useState(
    () => (navigator.geolocation ? '현재 위치를 확인하고 있습니다.' : '위치 기능을 사용할 수 없어 기본 순서로 안내합니다.'),
  );
  const [pendingStoreId, setPendingStoreId] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    fetchStores().then((response) => setStores(response.items)).catch((error) => setErrorMessage(error.message));
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setPosition({ latitude: coords.latitude, longitude: coords.longitude });
        setLocationMessage('현재 위치에서 가까운 순서입니다.');
      },
      () => setLocationMessage('위치 권한이 없어 기본 순서로 안내합니다.'),
      { timeout: 5000, maximumAge: 60000 },
    );
  }, []);

  const sortedStores = useMemo(() => stores
    .map((store) => ({ ...store, distance: position ? distanceKm(position, store) : null }))
    .sort((a, b) => (a.distance ?? Number.POSITIVE_INFINITY) - (b.distance ?? Number.POSITIVE_INFINITY)), [stores, position]);

  const handleCheckin = async (storeId) => {
    setPendingStoreId(storeId);
    setErrorMessage('');
    try {
      const checkin = await createOrResumeStoreCheckin(storeId);
      saveCheckin(checkin);
      navigate('/shopping-option');
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setPendingStoreId(null);
    }
  };

  return (
    <main className="store-selection-page">
      <header className="store-selection-page__header">
        <p>STORE CHECK-IN</p>
        <h1>방문하신 매장을 선택해주세요.</h1>
        <span>{locationMessage}</span>
      </header>
      <section className="store-selection-page__list" aria-label="매장 목록">
        {sortedStores.map((store) => (
          <button key={store.store_id} type="button" disabled={Boolean(pendingStoreId)} onClick={() => handleCheckin(store.store_id)}>
            <span className="store-selection-page__store-name">{store.name}</span>
            <span className="store-selection-page__address">{store.address}</span>
            <span className="store-selection-page__distance">{store.distance == null ? '매장 선택' : `${store.distance.toFixed(1)} km`}</span>
          </button>
        ))}
      </section>
      {errorMessage && <p className="store-selection-page__error" role="alert">{errorMessage}</p>}
    </main>
  );
}
