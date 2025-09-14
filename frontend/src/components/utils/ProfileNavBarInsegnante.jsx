'use client'
import React from 'react'
import Link from 'next/link';
import { LuUserRound, LuLogOut } from "react-icons/lu";
import { VscMortarBoard } from "react-icons/vsc";
import { motion } from 'framer-motion';
import { usePathname } from 'next/navigation';
import { useLogout } from '@/components/utils/LogoutContext';

const ProfileNavBarInsegnante = () => {
  const pathname = usePathname();
  const { openLogout } = useLogout();

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
        onClick={openLogout}
        className={`group flex flex-col items-center text-[14px] rounded-full p-2 transition-all duration-200 hover:bg-[#822433] active:bg-[#822433]`}
      >
        <LuLogOut className="text-3xl text-[#822433] group-hover:text-white active:text-white" />
      </button>
    </motion.nav>
  )
}

export default ProfileNavBarInsegnante
