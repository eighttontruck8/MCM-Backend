import { useSyncExternalStore } from 'react';

/**
 * bfcache(Back-Forward Cache)에서 복원될 때 React 트리를 리마운트시키는 훅.
 * 반환값(reviveKey)을 Routes의 key prop에 전달하면 bfcache 복원 시
 * 컴포넌트가 다시 마운트되어 useEffect가 재실행된다.
 */
let reviveCount = 0;
const listeners = new Set();

function subscribe(callback) {
  listeners.add(callback);
  return () => listeners.delete(callback);
}

function getSnapshot() {
  return reviveCount;
}

if (typeof window !== 'undefined') {
  window.addEventListener('pageshow', (event) => {
    if (event.persisted) {
      reviveCount += 1;
      listeners.forEach((listener) => listener());
    }
  });
}

export function usePageRevive() {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}
