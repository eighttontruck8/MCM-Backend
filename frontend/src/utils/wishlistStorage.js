import { useEffect, useState } from 'react';

export const WISHLIST_STORAGE_KEY = 'mjourney_wishlist_products';
export const WISHLIST_EVENT = 'mjourney_wishlist_changed';

export function readWishlist() {
  if (typeof window === 'undefined') return [];

  try {
    const stored = window.localStorage.getItem(WISHLIST_STORAGE_KEY);
    if (!stored) return [];

    const parsed = JSON.parse(stored);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function writeWishlist(items) {
  if (typeof window === 'undefined') return [];

  const nextItems = Array.isArray(items) ? items : [];
  window.localStorage.setItem(WISHLIST_STORAGE_KEY, JSON.stringify(nextItems));
  window.dispatchEvent(new CustomEvent(WISHLIST_EVENT, { detail: nextItems }));
  return nextItems;
}

export function normalizeProduct(product) {
  if (!product || typeof product !== 'object') return null;

  return {
    product_id: product.product_id ?? product.id ?? String(Date.now()),
    brand: product.brand ?? 'M·JOURNEY',
    product_name: product.product_name ?? product.name ?? '상품',
    price: product.price ?? 0,
    tags: Array.isArray(product.tags) ? product.tags : [],
    category: product.category ?? '기타',
    stock_status: product.stock_status ?? 'in_stock',
  };
}

export function toggleWishlistItem(product) {
  const normalized = normalizeProduct(product);
  if (!normalized) return readWishlist();

  const current = readWishlist();
  const exists = current.some((item) => item.product_id === normalized.product_id);

  const nextItems = exists
    ? current.filter((item) => item.product_id !== normalized.product_id)
    : [...current, normalized];

  return writeWishlist(nextItems);
}

export function isProductLiked(productId) {
  const wishlist = readWishlist();
  return wishlist.some((item) => item.product_id === productId);
}

export function useWishlist() {
  const [items, setItems] = useState(() => readWishlist());

  useEffect(() => {
    const sync = () => setItems(readWishlist());

    window.addEventListener(WISHLIST_EVENT, sync);
    window.addEventListener('storage', sync);

    return () => {
      window.removeEventListener(WISHLIST_EVENT, sync);
      window.removeEventListener('storage', sync);
    };
  }, []);

  const toggle = (product) => {
    const nextItems = toggleWishlistItem(product);
    setItems(nextItems);
  };

  return {
    items,
    isLiked: (productId) => items.some((item) => item.product_id === productId),
    toggle,
  };
}
