'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';

function parseJwt(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

export default function ProtectedLayout({ children }) {
  const router = useRouter();
  const pathname = usePathname();
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    const token = window.localStorage.getItem('token');
    if (!token) {
      console.log('No token → redirect');
      router.replace('/unauthorized');
      return;       
    }

    const payload = parseJwt(token);
    if (!payload || payload.exp * 1000 < Date.now()) {
      console.log('Token scaduto o non valido → redirect');
      window.localStorage.removeItem('token');
      router.replace('/unauthorized');
      return;     
    }

    console.log('Token valido → autorizzo children');
    setAuthorized(true);
  }, [pathname]);

  // token presente e valido: renderizzo finalmente i figli
  return <>{children}</>;
}