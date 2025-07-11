'use client'
import React, { useState } from 'react'
import Link from 'next/link';
import { LuUserRound, LuLogOut } from "react-icons/lu";
import { VscMortarBoard } from "react-icons/vsc";
import { motion } from 'framer-motion';
import { usePathname, useRouter } from 'next/navigation';

const ProfileNavBarInsegnante = () => {
  const pathname = usePathname();
  const router = useRouter();
  const [showLogoutPopup, setShowLogoutPopup] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/auth');
  };

  return (
    <motion.nav
      initial={{ x: 100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="fixed bottom-0 w-full flex justify-around bg-white border-t border-gray-300 py-3.5 z-50"
    >
      <Link
        href="/profile/personalInfo"
        className={`group flex flex-col items-center text-[14px] rounded-full p-2 transition-all duration-200 ${
          pathname === '/profile/personalInfo' ? 'bg-[#822433]' : 'hover:bg-[#822433] active:bg-[#822433]'
        }`}
      >
        <LuUserRound
          className={`text-3xl ${
            pathname === '/profile/personalInfo' ? 'text-white' : 'text-[#822433] group-hover:text-white active:text-white'
          }`}
        />
      </Link>
      <Link
        href="/profile/courses"
        className={`group flex flex-col items-center text-[14px] rounded-full p-2 transition-all duration-200 ${
          pathname === '/profile/courses' ? 'bg-[#822433]' : 'hover:bg-[#822433] active:bg-[#822433]'
        }`}
      >
        <VscMortarBoard
          className={`text-3xl ${
            pathname === '/profile/courses' ? 'text-white' : 'text-[#822433] group-hover:text-white active:text-white'
          }`}
        />
      </Link>
      <button
        onClick={() => setShowLogoutPopup(true)}
        className={`group flex flex-col items-center text-[14px] rounded-full p-2 transition-all duration-200 hover:bg-[#822433] active:bg-[#822433]`}
      >
        <LuLogOut className="text-3xl text-[#822433] group-hover:text-white active:text-white" />
      </button>
      {showLogoutPopup && (
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
                onClick={() => setShowLogoutPopup(false)}
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
      )}
    </motion.nav>
  )
}

export default ProfileNavBarInsegnante