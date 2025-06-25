'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function UnauthorizedPage() {
  const router = useRouter();

  useEffect(() => {
    const timer = setTimeout(() => {
      router.push('/auth');
      return;
    }, 4000); // 4 secondi di attesa prima del redirect

    return () => clearTimeout(timer);
  }, [router]);

  return (
    <div className="flex items-center justify-center h-screen bg-white text-center px-6">
      <div>
        <h1 className="text-3xl font-bold text-[#822433] mb-4">Accesso negato</h1>
        <p className="text-lg text-gray-700">
          Devi essere autenticato per accedere a questa pagina.
        </p>
        <p className="mt-4 text-sm text-gray-500">
          Verrai reindirizzato alla pagina di login...
        </p>
      </div>
    </div>
  );
}