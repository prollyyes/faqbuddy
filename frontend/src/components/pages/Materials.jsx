"use client";

import React, { useState, useEffect } from "react";
import Button from "@/components/utils/Button";
import BackButton from "@/components/utils/BackButton";
import { AnimatePresence, motion } from "framer-motion";
import { useRouter } from "next/navigation";
import SwipeWrapperHome from "../wrappers/SwipeWrapperHome";

export default function MaterialsPage() {
  const router = useRouter();
  const [hovered, setHovered] = useState(null);
  const [active, setActive] = useState(null);
  const [isTouchDevice, setIsTouchDevice] = useState(false);

  useEffect(() => {
    const isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    setIsTouchDevice(isTouch);
  }, []);

  const renderContent = () => {
    const content = (
      <motion.div
        key="default"
        initial={{ opacity: 0, x: -50 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 50 }}
        transition={{ duration: 0.3 }}
        className="w-full flex flex-col items-center space-y-6"
      >
        <div className="flex justify-center">
          <button
            className={`flex flex-col items-center justify-center gap-4 text-xl py-10 px-8 w-full h-56 max-w-md border-2 rounded-xl shadow-lg transition-colors duration-300 ${
              hovered === 'help' || active === 'help'
                ? 'bg-white text-[#822433] border-[#822433]'
                : 'bg-[#822433] text-white border-[#822433]'
            }`}
            onClick={() => {
              setActive("help");
              setTimeout(() => {
                setActive(null);
              }, 200);
              router.push("/homepage/materials/upload");
              }}
            onMouseEnter={!isTouchDevice ? () => setHovered('help') : undefined}
            onMouseLeave={!isTouchDevice ? () => setHovered(null) : undefined}
          >
            <span>Aiuta il tuo Buddy</span>
            <img
              src={(hovered === 'help' || active === 'help') ? "/images/Help.png" : "/images/HelpW.png"}
              alt="Aiuta il tuo Buddy"
              className="w-24 h-24 transition-all duration-300"
            />
          </button>
        </div>
        <div className="flex justify-center">
          <button
            className={`flex flex-col items-center justify-center gap-4 text-xl py-10 px-8 w-full h-56 max-w-md border-2 rounded-xl shadow-lg transition-colors duration-300 ${
              hovered === 'search' || active === 'search'
                ? 'bg-white text-[#822433] border-[#822433]'
                : 'bg-[#822433] text-white border-[#822433]'
            }`}
            onClick={() => {
              setActive("search");
              setTimeout(() => {
                setActive(null);
              }, 200);
              router.push("/homepage/materials/research");
            }}
            onMouseEnter={!isTouchDevice ? () => setHovered('search') : undefined}
            onMouseLeave={!isTouchDevice ? () => setHovered(null) : undefined}
          >
            <span>Ricerca Materiali</span>
            <img
              src={(hovered === 'search' || active === 'search') ? "/images/Search.png" : "/images/SearchW.png"}
              alt="Ricerca Materiali"
              className="w-24 h-24 transition-all duration-300"
            />
          </button>
        </div>
      </motion.div>
    );

    return <AnimatePresence mode="wait">{content}</AnimatePresence>;
  };

  return (
    <SwipeWrapperHome>
      <div className="h-screen flex flex-col justify-center items-center bg-white px-6 text-[#822433] space-y-8">
        {renderContent()}
      </div>
    </SwipeWrapperHome>
  );
}
