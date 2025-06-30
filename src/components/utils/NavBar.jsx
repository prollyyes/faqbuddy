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
      className="fixed bottom-0 w-full flex justify-around bg-white border-t border-gray-300 py-3.5 z-50"
    >
      <Link
        href="/homepage/materials"
        className={`group flex flex-col items-center text-[14px] rounded-full p-2 transition-all duration-200 ${
          pathname === '/homepage/materials' ? 'bg-[#822433]' : 'hover:bg-[#822433] active:bg-[#822433]'
        }`}
      >
        <MdMenuBook
          className={`text-3xl ${
            pathname === '/homepage/materials' ? 'text-white' : 'text-[#822433] group-hover:text-white active:text-white'
          }`}
        />
      </Link>
      <Link
        href="/homepage/chat"
        className={`group flex flex-col items-center text-[14px] rounded-full p-2 transition-all duration-200 ${
          pathname === '/homepage/chat' ? 'bg-[#822433]' : 'hover:bg-[#822433] active:bg-[#822433]'
        }`}
      >
        <RiWechatLine
          className={`text-3xl ${
            pathname === '/homepage/chat' ? 'text-white' : 'text-[#822433] group-hover:text-white active:text-white'
          }`}
        />
      </Link>
      <Link
        href="/profile/personalInfo"
        className="group flex flex-col items-center text-[14px] text-[#822433] hover:bg-[#822433] active:bg-[#822433] rounded-full p-2 transition-all duration-200"
      >
        <PiStudentBold className="text-3xl group-hover:text-white active:text-white" />
      </Link>
    </motion.nav>
  )
}

export default NavBar
