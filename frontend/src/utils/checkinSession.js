const ENTRY_TAG_KEY = 'mjourney_entry_tag';
const CHECKIN_KEY = 'mjourney_checkin';

export function saveEntryTag(entryTag) {
  window.sessionStorage.setItem(ENTRY_TAG_KEY, JSON.stringify(entryTag));
}

export function getEntryTag() {
  const rawEntryTag = window.sessionStorage.getItem(ENTRY_TAG_KEY);
  if (!rawEntryTag) return null;
  try {
    return JSON.parse(rawEntryTag);
  } catch {
    window.sessionStorage.removeItem(ENTRY_TAG_KEY);
    return null;
  }
}

export function clearEntryTag() {
  window.sessionStorage.removeItem(ENTRY_TAG_KEY);
}

export function saveCheckin(checkin) {
  window.sessionStorage.setItem(CHECKIN_KEY, JSON.stringify(checkin));
}

export function getCheckin() {
  const rawCheckin = window.sessionStorage.getItem(CHECKIN_KEY);
  if (!rawCheckin) return null;
  try {
    return JSON.parse(rawCheckin);
  } catch {
    window.sessionStorage.removeItem(CHECKIN_KEY);
    return null;
  }
}
