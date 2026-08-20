import test from 'node:test';
import assert from 'node:assert/strict';
import { createMockTasteReport } from './staffTasteReport.js';

test('동의된 고객 프로필로 직원용 mock 취향 리포트를 만든다', () => {
  const report = createMockTasteReport({
    masked_name: '김**',
    preferred_style: '미니멀',
    preferred_colors: ['블랙', '화이트'],
    membership: 'GOLD',
    visit_count: 4,
  });

  assert.equal(report.name, '김**');
  assert.match(report.summary, /미니멀/);
  assert.deepEqual(report.tags, ['블랙', '화이트']);
  assert.equal(report.recommendations.length, 3);
});
