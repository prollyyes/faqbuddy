'use client'

import React, { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { IoCheckmarkSharp } from 'react-icons/io5'

// Framer Motion based CardDeck
// Props: items = array of { id, title, subtitle, content, image }
export default function CardDeck({ items = [], index: controlledIndex = 0, onIndexChange, controlledDirection = null, autoAdvanceMs = 4000 }){
  const [direction, setDirection] = useState(0) // -1 back, +1 forward
  const index = controlledIndex
  const [progress, setProgress] = useState(0) // 0..1 fill for active dot
  const intervalRef = useRef(null)
  const containerRef = useRef(null)

  const canNext = index < items.length - 1
  const canPrev = index > 0

  const handleSwipe = (offsetX, velocity) => {
    const threshold = 100
    if(offsetX < -threshold || velocity < -500){
      if(canNext){
        setDirection(1)
        onIndexChange?.(index + 1)
      }
    } else if (offsetX > threshold || velocity > 500){
      if(canPrev){
        setDirection(-1)
        onIndexChange?.(index - 1)
      }
    }
  }

  const variants = {
    enter: (dir) => ({ x: dir > 0 ? 300 : -300, opacity: 0, scale: 0.95 }),
    center: { x: 0, opacity: 1, scale: 1 },
    exit: (dir) => ({ x: dir > 0 ? -300 : 300, opacity: 0, scale: 0.95 })
  }

  // Keyboard navigation: left/right arrows
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'ArrowLeft' && canPrev) {
        setDirection(-1)
        onIndexChange?.(index - 1)
      } else if (e.key === 'ArrowRight' && canNext) {
        setDirection(1)
        onIndexChange?.(index + 1)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [index, canPrev, canNext, onIndexChange])

  // Auto-advance with progress fill on active dot
  useEffect(() => {
    // Reset progress on index change
    setProgress(0)
    if (!autoAdvanceMs || autoAdvanceMs <= 0) return
    const start = Date.now()
    const tick = () => {
      const elapsed = Date.now() - start
      const ratio = Math.min(1, elapsed / autoAdvanceMs)
      setProgress(ratio)
      if (ratio >= 1) {
        if (canNext) {
          setDirection(1)
          onIndexChange?.(index + 1)
        }
        return
      }
      intervalRef.current = requestAnimationFrame(tick)
    }
    intervalRef.current = requestAnimationFrame(tick)
    return () => {
      if (intervalRef.current) cancelAnimationFrame(intervalRef.current)
    }
  }, [index, autoAdvanceMs, onIndexChange, canNext])

  return (
    <div className="w-full">
      <div ref={containerRef} className="relative w-full h-[65vh] flex items-center justify-center">
        <AnimatePresence initial={false} custom={controlledDirection ?? direction}>
          {items.slice(index, index+1).map((item, i) => (
            <motion.div
              key={item.id ?? index}
              className="absolute w-full h-full flex items-center justify-center p-4"
              drag="x"
              dragConstraints={{ left: 0, right: 0 }}
              dragElastic={0.2}
              onDragEnd={(e, info) => handleSwipe(info.offset.x, info.velocity.x)}
              custom={controlledDirection ?? direction}
              variants={variants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ type: 'spring', stiffness: 160, damping: 18, mass: 0.9 }}
            >
              <div className="bg-white w-full max-w-2xl h-full rounded-2xl shadow-lg overflow-hidden flex flex-col">
                {item.image && (
                  <div className="w-full flex-1 h-0 bg-gray-100 flex items-center justify-center">
                    <img src={item.image} alt={item.title} className="object-contain h-full w-full" />
                  </div>
                )}
                <div className="p-6">
                  <h3 className="text-lg font-bold mb-1">{item.title}</h3>
                  {item.subtitle && <div className="text-sm text-gray-500 mb-2">{item.subtitle}</div>}
                  {item.content && <div className="text-sm text-gray-700">{item.content}</div>}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Stack shadow/peek for next two cards */}
      <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
        <div className="w-full max-w-md h-0">
          {items.slice(index+1, index+3).map((it, i) => (
            <div key={it.id || i} className={`absolute left-0 right-0 mx-auto w-full max-w-md rounded-2xl bg-white shadow-md`} style={{transform: `translateY(${12 + i*8}px) scale(${1 - 0.03*(i+1)})`, zIndex: 40 - i}} />
          ))}
        </div>
      </div>

      {/* Progress Dots placed below the card area */}
      <div className="mt-3 w-full flex items-center justify-center gap-2">
        {items.map((_, i) => {
          const isActive = i === index
          const isLastActive = isActive && i === items.length - 1
          if (isLastActive) {
            return (
              <div
                key={i}
                className="rounded-full bg-gray-700 flex items-center justify-center"
                style={{ width: '10px', height: '10px' }}
              >
                <IoCheckmarkSharp className="text-[9px] text-white" />
              </div>
            )
          }
          return (
            <div key={i} className={`relative h-2 rounded-full overflow-hidden ${isActive ? 'w-12 bg-gray-200' : 'w-2 bg-gray-300'} transition-[width,background-color] duration-200`}>
              {isActive && (
                <div className="absolute left-0 top-0 h-2 bg-gray-500" style={{ width: `${progress * 100}%` }} />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
