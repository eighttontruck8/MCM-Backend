import React, { useState, useEffect } from 'react';
import { fetchLookbook, fetchProductById } from '../api/mockApi';

const CustomerLookbook = ({ customerId = "C001" }) => {
  const [lookbook, setLookbook] = useState(null);
  const [lookbookProducts, setLookbookProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadLookbookData = async () => {
      try {
        setIsLoading(true);
        
        // 1. AI가 만들어준 고객 맞춤 룩북 텍스트 데이터를 불러옵니다.
        const lookbookData = await fetchLookbook(customerId);
        setLookbook(lookbookData);

        // 2. 룩북에 제안된 상품들의 실제 이미지와 가격을 불러옵니다.
        const productPromises = lookbookData.looks.map((look) => 
          fetchProductById(look.product_id)
        );
        const products = await Promise.all(productPromises);
        setLookbookProducts(products);

      } catch (error) {
        console.error("룩북 데이터를 불러오는데 실패했습니다.", error);
      } finally {
        setIsLoading(false);
      }
    };

    loadLookbookData();
  }, [customerId]);

  if (isLoading) {
    return <div style={{ padding: '20px', textAlign: 'center' }}>고객님을 위한 맞춤 룩북을 구성 중입니다...</div>;
  }

  if (!lookbook) return <div>룩북 정보를 찾을 수 없습니다.</div>;

  return (
    <div style={{ maxWidth: '480px', margin: '0 auto', padding: '20px', backgroundColor: '#fdfdfd' }}>
      <h2 style={{ textAlign: 'center' }}>📱 {lookbook.title}</h2>
      <p style={{ fontStyle: 'italic', color: '#555', textAlign: 'center' }}>{lookbook.intro}</p>
      
      <div style={{ marginTop: '30px' }}>
        {lookbookProducts.map((product, index) => (
          <div key={product.product_id} style={{ marginBottom: '40px', paddingBottom: '20px', borderBottom: '1px solid #eee' }}>
            <img 
              src={product.image_url} 
              alt={product.product_name} 
              style={{ width: '100%', borderRadius: '12px', objectFit: 'cover' }} 
            />
            <h3 style={{ margin: '15px 0 5px', fontSize: '18px' }}>{product.product_name}</h3>
            <p style={{ fontWeight: 'bold', margin: '0 0 15px' }}>{product.price.toLocaleString()}원</p>
            
            <div style={{ backgroundColor: '#f5f5f5', padding: '15px', borderRadius: '8px' }}>
              <p style={{ margin: 0, fontSize: '14px', lineHeight: '1.5' }}>
                <strong>👗 스타일링 팁:</strong> <br />
                {lookbook.looks[index].styling}
              </p>
            </div>
          </div>
        ))}
      </div>
      
      <div style={{ padding: '20px', backgroundColor: '#111', color: '#fff', borderRadius: '8px', textAlign: 'center' }}>
        <p style={{ margin: 0, fontWeight: 'bold' }}>{lookbook.closing}</p>
      </div>
    </div>
  );
};

export default CustomerLookbook;