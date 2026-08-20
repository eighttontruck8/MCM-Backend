import test from 'node:test';
import assert from 'node:assert/strict';
import { getCheckinContinuationPath } from './checkinNavigation.js';

test('새 체크인은 쇼핑 방식 선택 화면으로 이동한다', () => {
  assert.equal(getCheckinContinuationPath({ status: 'CHECKED_IN', shopping_mode: null }), '/shopping-option');
});

test('선택 또는 진행 중인 활성 체크인은 현재 단계로 이어간다', () => {
  assert.equal(
    getCheckinContinuationPath({ status: 'CHECKED_IN', shopping_mode: 'STAFF_ASSISTED' }),
    '/visit-info',
  );
  assert.equal(getCheckinContinuationPath({ status: 'SELF_SHOPPING' }), '/lookbook');
  assert.equal(getCheckinContinuationPath({ status: 'WAITING_FOR_STAFF' }), '/visit-info-complete');
  assert.equal(getCheckinContinuationPath({ status: 'ASSIGNED' }), '/staff-assignment');
  assert.equal(getCheckinContinuationPath({ status: 'SERVING' }), '/staff-assignment');
});
