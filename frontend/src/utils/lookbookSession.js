const LOOKBOOK_KEY = 'mjourney_lookbook';
const SELECTED_LOOK_KEY = 'mjourney_selected_look';

// [Frontend-04-'추천 및 고객 활동 REST 연동']
function readJson(key) {
  const raw = window.sessionStorage.getItem(key);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    window.sessionStorage.removeItem(key);
    return null;
  }
}

export function saveLookbook(checkinId, lookbook) {
  window.sessionStorage.setItem(LOOKBOOK_KEY, JSON.stringify({ checkin_id: checkinId, data: lookbook }));
}

export function getLookbook(checkinId) {
  try {
    const stored = readJson(LOOKBOOK_KEY);
    if (!stored || typeof stored !== 'object') return null;
    if (stored.checkin_id !== checkinId) {
      window.sessionStorage.removeItem(LOOKBOOK_KEY);
      return null;
    }
    if (!stored.data || !Array.isArray(stored.data?.looks) || stored.data.looks.length === 0) {
      window.sessionStorage.removeItem(LOOKBOOK_KEY);
      return null;
    }
    return stored.data;
  } catch {
    window.sessionStorage.removeItem(LOOKBOOK_KEY);
    return null;
  }
}

export function saveSelectedLook(look) {
  window.sessionStorage.setItem(SELECTED_LOOK_KEY, JSON.stringify(look));
}

export function getSelectedLook() {
  return readJson(SELECTED_LOOK_KEY);
}
