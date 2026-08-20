import test from 'node:test';
import assert from 'node:assert/strict';
import { splitPurchasesByChannel } from './staffDashboardData.js';

test('직원용 구매 내역을 온·오프라인으로 나눈다', () => {
  const result = splitPurchasesByChannel([
    { purchase_id: '1', channel: 'ONLINE' },
    { purchase_id: '2', channel: 'OFFLINE' },
    { purchase_id: '3', channel: 'ONLINE' },
  ]);

  assert.deepEqual(result.online.map((item) => item.purchase_id), ['1', '3']);
  assert.deepEqual(result.offline.map((item) => item.purchase_id), ['2']);
});
