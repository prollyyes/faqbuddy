'use client'

import Link from 'next/link';
import { IoReturnUpBackOutline } from 'react-icons/io5';
import Button from './Button';
import { motion } from 'framer-motion';

export default function BackButton({ href = '/', onClick }) {
  return (
    <motion.div
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="left-4 top-20 z-50"
    >
      {onClick ? (
        <Button onClick={onClick}>
          <IoReturnUpBackOutline className="text-xl" />
        </Button>
      ) : (
        <Link href={href}>
          <Button>
            <IoReturnUpBackOutline className="text-xl" />
          </Button>
        </Link>
      )}
    </motion.div>
  );
}
