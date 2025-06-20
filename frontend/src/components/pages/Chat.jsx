'use client'
import React from 'react'
import { IoSendSharp } from "react-icons/io5";
import Link from 'next/link';
import { motion } from 'framer-motion';

const Chat = () => {
    const [chatExpanded, setChatExpanded] = React.useState(false);
    const [message, setMessage] = React.useState('');
    return (
        <div className="bg-white text-black min-h-screen">
            <header className="w-full flex items-center justify-center text-[#822433] pt-2 fixed top-0 bg-white z-50 shadow-sm">
                <img src="/logo.png" alt="logo_img" className="w-10 h-10 object-contain mb-1" />
                <Link href="/" className="text-3xl font-bold tracking-wider">
                FAQBuddy
                </Link>
            </header>
            <motion.div
                initial={{ height: 'auto' }}
                animate={{ height: chatExpanded ? '100vh' : 'auto' }}
                transition={{ duration: 0.5, ease: 'easeInOut' }}
                className={`overflow-hidden transition-all duration-500 ease-in-out ${
                    chatExpanded ? 'fixed inset-x-0 top-0 z-40 bg-white pt-16 pb-24' : 'w-full max-w-md mx-auto mt-4 p-4 rounded-lg'
                }`}
            >
                {!chatExpanded && (
                    <motion.div
                        key="collapsed-chat"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex flex-col mt-27 items-center justify-center p-6"
                    >
                        <motion.p
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5 }}
                            className="text-lg font-semibold text-[#800020] mb-2"
                        >
                            Fai una domanda al tuo <span className="italic">FAQbuddy</span>!
                        </motion.p>
                    </motion.div>
                )}
            </motion.div>

            <motion.div
              layout
              transition={{ type: "spring", stiffness: 200, damping: 20 }}
              className={`${
                chatExpanded
                  ? "fixed bottom-16 left-0 w-full px-4 pb-4 z-40 bg-white"
                  : "w-full max-w-md mx-auto mt-2 px-4"
              }`}
            >
              <div className="flex items-center w-full gap-2">
                <input
                  type="text"
                  placeholder="Scrivi un messaggio..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  className="flex-1 border border-gray-300 rounded-full px-4 py-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-[#800020]"
                />
                <button
                  className="text-[#800020] hover:text-[#a32230] transition"
                  onClick={() => {
                    if (message.trim()) {
                      setChatExpanded(true);
                      setMessage('');
                    }
                  }}
                >
                  <IoSendSharp className="text-[1.65rem]" />
                </button>
              </div>
            </motion.div>
        </div>
    )
}

export default Chat
