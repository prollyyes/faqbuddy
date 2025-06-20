'use client'
import React from 'react'
import { MdMenuBook } from "react-icons/md";
import { PiStudentBold } from "react-icons/pi";
import { RiWechatLine } from "react-icons/ri";
import Link from 'next/link';
import { motion } from 'framer-motion';
import { usePathname } from 'next/navigation';

const NavBar = () => {
  const pathname = usePathname();

  return (
    <motion.nav
      initial={{ x: -100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="fixed bottom-0 w-full flex justify-around bg-white border-t border-gray-300 py-4 z-50"
    >
      <Link href="/menu" className="group flex flex-col items-center text-[14px] text-[#800020] hover:bg-[#800020] rounded-full p-2 transition-all duration-200">
        <MdMenuBook className="text-3xl group-hover:text-white" />
      </Link>
      <Link
        href="/chat"
        className={`group flex flex-col items-center text-[14px] rounded-full p-2 transition-all duration-200 ${
          pathname === '/chat' ? 'bg-[#800020]' : ''
        }`}
      >
        <RiWechatLine
          className={`text-3xl ${
            pathname === '/chat' ? 'text-white' : 'text-[#800020]'
          }`}
        />
      </Link>
      <Link href="/profile/personalInfo" className="group flex flex-col items-center text-[14px] text-[#800020] hover:bg-[#800020] rounded-full p-2 transition-all duration-200">
        <PiStudentBold className="text-3xl group-hover:text-white" />
      </Link>
    </motion.nav>
  )
}

export default NavBar
