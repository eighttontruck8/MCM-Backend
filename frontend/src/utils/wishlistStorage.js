import { useCallback, useEffect, useState } from 'react';
import { addWishlistItem, fetchWishlist, removeWishlistItem } from '../api/client';

// [Frontend-04-'추천 및 고객 활동 REST 연동']
export function useWishlist() {
  const [items, setItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [pendingProductId, setPendingProductId] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const refresh = useCallback(async () => {
    try {
      const response = await fetchWishlist();
      setItems(response.items);
      setErrorMessage('');
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(refresh, 0);
    return () => window.clearTimeout(timer);
  }, [refresh]);

  const isLiked = (productId) => items.some((item) => item.product_id === productId);
  const toggle = async (product) => {
    const productId = product?.product_id;
    if (!productId || pendingProductId) return;
    setPendingProductId(productId);
    setErrorMessage('');
    try {
      if (isLiked(productId)) {
        await removeWishlistItem(productId);
        setItems((current) => current.filter((item) => item.product_id !== productId));
      } else {
        const added = await addWishlistItem(productId);
        setItems((current) => [added, ...current.filter((item) => item.product_id !== productId)]);
      }
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setPendingProductId(null);
    }
  };

  return { items, isLiked, toggle, isLoading, pendingProductId, errorMessage, refresh };
}
