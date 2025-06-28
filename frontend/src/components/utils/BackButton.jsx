'use client'

import Link from 'next/link';
import { IoReturnUpBackOutline } from 'react-icons/io5';
import { motion } from 'framer-motion';

export default function BackButton({ href = '/', onClick }) {
  return (
    <motion.div
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="left-8 top-20 z-50"
    >
      {onClick ? (
        <button
          type="button"
          onClick={onClick}
          className="text-[#822433] hover:text-white hover:bg-[#822433] active:text-white active:bg-[#822433] transition-colors rounded-full text-2xl focus:outline-none"
        >
          <IoReturnUpBackOutline />
        </button>
      ) : (
        <Link href={href}>
          <button
            type="button"
            className="text-[#822433] hover:text-white hover:bg-[#822433] active:text-white active:bg-[#822433] transition-colors rounded-full text-2xl focus:outline-none"
          >
            <IoReturnUpBackOutline />
          </button>
        </Link>
      )}
    </motion.div>
  );
}
