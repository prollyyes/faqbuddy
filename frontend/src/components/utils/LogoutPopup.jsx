'use client'
import React from 'react';
import { motion } from 'framer-motion';
import { useLogout } from './LogoutContext';
import { useRouter } from 'next/navigation';

export default function LogoutPopup() {
  const { isOpen, closeLogout } = useLogout();
  const router = useRouter();

  if (!isOpen) return null;

  const handleLogout = () => {
    try { localStorage.removeItem('token'); } catch {}
    closeLogout();
    router.push('/auth');
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50 pointer-events-none">
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="bg-white px-6 py-8 w-[280px] rounded-xl border-2 border-[#822433] text-center text-[#822433] shadow-lg pointer-events-auto"
      >
        <p className="mb-6 text-lg font-medium">Sei sicuro di voler effettuare il logout?</p>
        <div className="flex justify-center gap-4">
          <button
            onClick={closeLogout}
            className="px-4 py-2 border border-[#822433] rounded-md hover:bg-[#822433] hover:text-white transition font-semibold"
          >
            No
          </button>
          <button
            onClick={handleLogout}
            className="px-4 py-2 border border-[#822433] bg-[#822433] text-white rounded-md hover:opacity-90 transition font-semibold"
          >
            Sì
          </button>
        </div>
      </motion.div>
    </div>
  );
}

