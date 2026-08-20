const ACTIVE_VISIT_KEY = 'mjourney_staff_active_visit';

// [Frontend-03-'직원 대기열 및 실시간 배정 연동']
export function saveStaffActiveVisit(visit) {
  window.sessionStorage.setItem(ACTIVE_VISIT_KEY, JSON.stringify(visit));
}

export function getStaffActiveVisit() {
  const rawVisit = window.sessionStorage.getItem(ACTIVE_VISIT_KEY);
  if (!rawVisit) return null;
  try {
    return JSON.parse(rawVisit);
  } catch {
    window.sessionStorage.removeItem(ACTIVE_VISIT_KEY);
    return null;
  }
}

export function clearStaffActiveVisit() {
  window.sessionStorage.removeItem(ACTIVE_VISIT_KEY);
}
