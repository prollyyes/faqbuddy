"use client";

import React, { useEffect, useState } from "react";

export default function TileButton({
  label,
  imgRedSrc,
  imgWhiteSrc,
  onClick,
  // Sizing controls (Tailwind classes)
  heightClass = "h-36",
  paddingYClass = "py-4",
  textSizeClass = "text-sm",
  iconSizeHoverClass = "w-16 h-16",
  iconSizeIdleClass = "w-12 h-12",
  className = "",
}) {
  const [hovered, setHovered] = useState(false);
  const [active, setActive] = useState(false);
  const [isTouchDevice, setIsTouchDevice] = useState(false);

  useEffect(() => {
    const isTouch = typeof window !== 'undefined' && ('ontouchstart' in window || navigator.maxTouchPoints > 0);
    setIsTouchDevice(isTouch);
  }, []);

  const isHot = hovered || active;

  const handleClick = (e) => {
    setActive(true);
    setTimeout(() => setActive(false), 200);
    if (onClick) onClick(e);
  };

  return (
    <button
      className={`flex flex-col items-center justify-center gap-2 ${textSizeClass} ${paddingYClass} px-4 w-full ${heightClass} border-2 rounded-xl shadow-lg transition-colors duration-300 ${
        isHot ? 'bg-white text-[#822433] border-[#822433]' : 'bg-[#822433] text-white border-[#822433]'
      } ${className}`}
      onClick={handleClick}
      onMouseEnter={!isTouchDevice ? () => setHovered(true) : undefined}
      onMouseLeave={!isTouchDevice ? () => setHovered(false) : undefined}
    >
      <span className="font-semibold">{label}</span>
      <img
        src={isHot ? imgRedSrc : imgWhiteSrc}
        alt={label}
        className={`transition-all duration-300 object-contain ${isHot ? iconSizeHoverClass : iconSizeIdleClass}`}
      />
    </button>
  );
}

