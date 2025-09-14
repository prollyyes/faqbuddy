'use client'
import ProfileNavBarStudente from '@/components/utils/ProfileNavBarStudente';
import ProfileNavBarInsegnante from '@/components/utils/ProfileNavBarInsegnante';
import Header from '@/components/utils/Header';
import { useEffect, useState } from 'react';
import { LogoutProvider } from '@/components/utils/LogoutContext';
import LogoutPopup from '@/components/utils/LogoutPopup';

const HOST = process.env.NEXT_PUBLIC_HOST;


export default function ProfileLayout({ children }) {
  const [ruolo, setRuolo] = useState(null);
  
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;
    fetch(`${HOST}/profile/me`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => setRuolo(data.ruolo));
  }, []);

  return (
    <LogoutProvider>
      <div className="min-h-screen bg-white ">
        <Header />
        {ruolo === 'studente' && <ProfileNavBarStudente />}
        {ruolo === 'insegnante' && <ProfileNavBarInsegnante />}
        <main className="pt-4">{children}</main>
        <LogoutPopup />
      </div>
    </LogoutProvider>
  );
}
