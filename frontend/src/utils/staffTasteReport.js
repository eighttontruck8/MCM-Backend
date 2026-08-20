const MOCK_RECOMMENDATIONS = [
  { index: 1, title: 'Stark 비세토스 백팩', subtitle: '데일리와 비즈니스 룩에 모두 어울리는 시그니처 아이템', tone: '코냑', score: '94%' },
  { index: 2, title: 'Aren 숄더백', subtitle: '간결한 실루엣으로 포인트를 주는 미니멀 백', tone: '블랙', score: '89%' },
  { index: 3, title: 'Lauretos 크로스바디', subtitle: '가볍고 실용적인 주말 스타일링 아이템', tone: '크림', score: '85%' },
];

// [Frontend-19-'직원용 mock 취향 리포트'] 동의된 고객 프로필을 바탕으로 시연용 리포트를 즉시 구성한다.
export function createMockTasteReport(profile = {}, visit = {}) {
  const name = profile.masked_name ?? visit.masked_name ?? '고객';
  const preferredStyle = profile.preferred_style ?? '미니멀 비즈니스 캐주얼';
  const preferredColors = profile.preferred_colors?.length ? profile.preferred_colors : ['블랙', '코냑', '크림'];

  return {
    name,
    initial: name.charAt(0),
    tags: preferredColors.slice(0, 4),
    summary: `${name} 고객님은 ${preferredStyle} 스타일을 선호하며, 실용적인 수납과 차분한 컬러 조합을 중요하게 생각합니다.`,
    metrics: [
      { label: '선호 스타일', value: preferredStyle },
      { label: '선호 컬러', value: preferredColors.slice(0, 2).join(' · ') },
      { label: '멤버십', value: profile.membership ?? visit.membership ?? 'MEMBER' },
      { label: '방문 횟수', value: `${profile.visit_count ?? 1}회` },
    ],
    recommendations: MOCK_RECOMMENDATIONS,
  };
}
