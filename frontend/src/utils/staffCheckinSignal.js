import { mockCustomers } from '../mock/mockCustomers';
import { mockProducts } from '../mock/mockProducts';

export const STAFF_CHECKIN_STORAGE_KEY = 'mjourney_staff_waiting_checkin';
export const STAFF_VISIT_STATE_KEY = 'mjourney_staff_visit_state';
export const STAFF_CHECKIN_EVENT = 'mjourney_staff_waiting_checkin_changed';
export const STAFF_VISIT_STATE_EVENT = 'mjourney_staff_visit_state_changed';

export const DEFAULT_STAFF_VISIT_STATE = {
  status: 'waiting',
  customer: null,
  wishlist: [],
  recentlyViewed: [],
  purchaseHistory: [],
  updatedAt: null,
};

const VALID_STATUSES = new Set(['waiting', 'checked-in', 'serving']);

export function buildCustomerVisitPayload(customerOverrides = {}) {
  const baseCustomer = mockCustomers[0] ?? {
    customer_id: 'C001',
    name: '김**',
    age: 34,
    gender: '여성',
    visit_count: 28,
    total_purchase: 12500000,
    style_tags: ['미니멀 럭셔리'],
    preferred_colors: ['블랙'],
    preferred_fit: '오버사이즈 실루엣',
    recent_interests: ['가을 아우터'],
  };

  const resolvedCustomer = {
    ...baseCustomer,
    phone: '010-****-3374',
    visitDate: '2026년 8월 14일',
    ...customerOverrides,
  };

  const wishlist = [
    ...((resolvedCustomer.style_tags || []).slice(0, 2)),
    ...((resolvedCustomer.recent_interests || []).slice(0, 2)),
  ];

  const recentlyViewed = mockProducts.slice(0, 3).map((product) => ({
    product_id: product.product_id,
    name: product.product_name,
    brand: product.brand,
    price: product.price,
    category: product.category,
  }));

  const purchaseHistory = [
    { id: 'ORD-1042', product: '프리미엄 캐시미어 니트', amount: '₩850,000', date: '2026.08.11' },
    { id: 'ORD-1038', product: '시그니처 트렌치 코트', amount: '₩1,250,000', date: '2026.08.04' },
    { id: 'ORD-1029', product: '미니멀 울 슬랙스', amount: '₩450,000', date: '2026.07.19' },
  ];

  return {
    customer: resolvedCustomer,
    wishlist,
    recentlyViewed,
    purchaseHistory,
    transferredAt: new Date().toISOString(),
  };
}

export function normalizeStaffVisitState(value) {
  if (!value || typeof value !== 'object') {
    return { ...DEFAULT_STAFF_VISIT_STATE };
  }

  const status = VALID_STATUSES.has(value.status) ? value.status : 'waiting';

  return {
    status,
    customer: value.customer && typeof value.customer === 'object' ? value.customer : null,
    wishlist: Array.isArray(value.wishlist) ? value.wishlist : [],
    recentlyViewed: Array.isArray(value.recentlyViewed) ? value.recentlyViewed : [],
    purchaseHistory: Array.isArray(value.purchaseHistory) ? value.purchaseHistory : [],
    updatedAt: typeof value.updatedAt === 'string' ? value.updatedAt : null,
  };
}

export function readStaffCheckinFlag() {
  if (typeof window === 'undefined') return false;

  const storedState = window.localStorage.getItem(STAFF_VISIT_STATE_KEY);
  if (storedState) {
    try {
      const parsed = JSON.parse(storedState);
      return normalizeStaffVisitState(parsed).status !== 'waiting';
    } catch {
      return false;
    }
  }

  const legacyValue = window.localStorage.getItem(STAFF_CHECKIN_STORAGE_KEY);
  return legacyValue === 'true';
}

export function readStaffVisitState() {
  if (typeof window === 'undefined') {
    return { ...DEFAULT_STAFF_VISIT_STATE };
  }

  const storedState = window.localStorage.getItem(STAFF_VISIT_STATE_KEY);
  if (storedState) {
    try {
      return normalizeStaffVisitState(JSON.parse(storedState));
    } catch {
      const legacyValue = window.localStorage.getItem(STAFF_CHECKIN_STORAGE_KEY);
      if (legacyValue === 'true') {
        return {
          ...DEFAULT_STAFF_VISIT_STATE,
          status: 'checked-in',
          updatedAt: new Date().toISOString(),
        };
      }
    }
  }

  const legacyValue = window.localStorage.getItem(STAFF_CHECKIN_STORAGE_KEY);
  if (legacyValue === 'true') {
    return {
      ...DEFAULT_STAFF_VISIT_STATE,
      status: 'checked-in',
      updatedAt: new Date().toISOString(),
    };
  }

  return { ...DEFAULT_STAFF_VISIT_STATE };
}

export function saveStaffVisitState(partialState) {
  if (typeof window === 'undefined') return { ...DEFAULT_STAFF_VISIT_STATE };

  const currentState = readStaffVisitState();
  const nextState = normalizeStaffVisitState({
    ...currentState,
    ...partialState,
    customer: partialState?.customer ?? currentState.customer,
    wishlist: partialState?.wishlist ?? currentState.wishlist,
    recentlyViewed: partialState?.recentlyViewed ?? currentState.recentlyViewed,
    purchaseHistory: partialState?.purchaseHistory ?? currentState.purchaseHistory,
    updatedAt: new Date().toISOString(),
  });

  window.localStorage.setItem(STAFF_VISIT_STATE_KEY, JSON.stringify(nextState));
  window.localStorage.setItem(STAFF_CHECKIN_STORAGE_KEY, nextState.status !== 'waiting' ? 'true' : 'false');

  window.dispatchEvent(
    new CustomEvent(STAFF_VISIT_STATE_EVENT, {
      detail: nextState,
    })
  );

  window.dispatchEvent(
    new CustomEvent(STAFF_CHECKIN_EVENT, {
      detail: { value: nextState.status !== 'waiting' },
    })
  );

  return nextState;
}

export function triggerStaffCheckin(customerPayload = buildCustomerVisitPayload()) {
  if (typeof window === 'undefined') return { ...DEFAULT_STAFF_VISIT_STATE };

  return saveStaffVisitState({
    status: 'checked-in',
    ...customerPayload,
  });
}

export function markStaffVisitServing(customerPayload = null) {
  if (typeof window === 'undefined') return { ...DEFAULT_STAFF_VISIT_STATE };

  const current = readStaffVisitState();
  const payload = customerPayload ?? {
    customer: current.customer,
    wishlist: current.wishlist,
    recentlyViewed: current.recentlyViewed,
    purchaseHistory: current.purchaseHistory,
  };

  return saveStaffVisitState({
    status: 'serving',
    ...payload,
  });
}
