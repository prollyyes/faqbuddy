'use client'
import React from 'react'
import { MdMenuBook } from "react-icons/md";
import { PiStudentBold } from "react-icons/pi";
import { RiWechatLine } from "react-icons/ri";

const NavBar = () => {
  return (
    <nav className="fixed bottom-0 w-full flex justify-around bg-white border-t border-gray-300 py-4 z-50">
      <button className="flex flex-col items-center text-[14px] text-[#800020] hover:opacity-80" onClick={() => window.location.href = '/menu'}>
        <MdMenuBook className="text-3xl" />
      </button>
      <button className="flex flex-col items-center text-[14px] text-[#800020] hover:opacity-80" onClick={() => window.location.href = '/chatbot'}>
        <RiWechatLine className="text-3xl" />
      </button>
      <button className="flex flex-col items-center text-[14px] text-[#800020] hover:opacity-80" onClick={() => window.location.href = '/profile'}>
        <PiStudentBold className="text-3xl" />
      </button>
    </nav>
  )
}

export default NavBar
