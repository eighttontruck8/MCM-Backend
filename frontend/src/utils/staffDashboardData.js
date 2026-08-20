// [Frontend-Staff-01-'직원 고객 구매내역 분리'] API 채널 값을 기준으로 온·오프라인 구매를 구분한다.
export function splitPurchasesByChannel(purchases = []) {
  return {
    online: purchases.filter((purchase) => purchase.channel === 'ONLINE'),
    offline: purchases.filter((purchase) => purchase.channel === 'OFFLINE'),
  };
}
