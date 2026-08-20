const QUICK_STAFF_CONSENT = {
  agreed: true,
  policy_version: 'staff-profile-share-v1',
  scopes: ['PURCHASE_HISTORY', 'INTEREST_PRODUCTS', 'STYLE_PROFILE'],
};

const QUICK_VISIT_PURPOSE = { code: 'FREE_SHOPPING', note: '매장 체크인 후 직원 응대 요청' };

// [Frontend-20-'빠른 직원 응대 체크인'] 신규 체크인을 직원 대기열 상태까지 순서대로 전환한다.
export async function moveCheckinToStaffQueue(checkin, { setShoppingMode, createServiceRequest }) {
  if (checkin.status !== 'CHECKED_IN') return checkin;

  let nextCheckin = checkin;
  if (nextCheckin.shopping_mode !== 'STAFF_ASSISTED') {
    const shoppingMode = await setShoppingMode(nextCheckin.checkin_id, 'STAFF_ASSISTED');
    nextCheckin = { ...nextCheckin, ...shoppingMode };
  }
  const serviceRequest = await createServiceRequest(
    nextCheckin.checkin_id,
    QUICK_STAFF_CONSENT,
    QUICK_VISIT_PURPOSE,
  );
  return { ...nextCheckin, ...serviceRequest, visit_purpose: QUICK_VISIT_PURPOSE };
}
