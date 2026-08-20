import test from 'node:test';
import assert from 'node:assert/strict';
import { moveCheckinToStaffQueue } from './staffCheckinFlow.js';

test('신규 매장 체크인을 직원 대기열 상태로 전환한다', async () => {
  const calls = [];
  const result = await moveCheckinToStaffQueue(
    { checkin_id: 'checkin-1', status: 'CHECKED_IN', shopping_mode: null },
    {
      setShoppingMode: async (checkinId, mode) => {
        calls.push(['mode', checkinId, mode]);
        return { shopping_mode: mode, status: 'CHECKED_IN' };
      },
      createServiceRequest: async (checkinId, consent, purpose) => {
        calls.push(['request', checkinId, consent.agreed, purpose.code]);
        return { status: 'WAITING_FOR_STAFF', estimated_wait_minutes: 1 };
      },
    },
  );

  assert.deepEqual(calls, [
    ['mode', 'checkin-1', 'STAFF_ASSISTED'],
    ['request', 'checkin-1', true, 'FREE_SHOPPING'],
  ]);
  assert.equal(result.status, 'WAITING_FOR_STAFF');
  assert.equal(result.estimated_wait_minutes, 1);
});

test('이미 대기 중인 체크인은 중복 요청하지 않는다', async () => {
  const checkin = { checkin_id: 'checkin-1', status: 'WAITING_FOR_STAFF' };
  assert.equal(await moveCheckinToStaffQueue(checkin, {}), checkin);
});
