// [Frontend-18-'활성 체크인 이어가기'] 재개된 체크인은 현재 상태에 맞는 다음 화면으로 이동한다.
export function getCheckinContinuationPath(checkin) {
  if (checkin?.status === 'SELF_SHOPPING') return '/lookbook';
  if (checkin?.status === 'WAITING_FOR_STAFF') return '/visit-info-complete';
  if (checkin?.status === 'ASSIGNED' || checkin?.status === 'SERVING') return '/staff-assignment';
  if (checkin?.status === 'CHECKED_IN' && checkin?.shopping_mode === 'STAFF_ASSISTED') return '/visit-info';
  return '/shopping-option';
}
