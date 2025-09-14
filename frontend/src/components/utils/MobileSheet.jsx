'use client'
import React, { useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

export default function MobileSheet({ open, onClose, title, children, footer }) {
  const panelRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const onKey = (e) => {
      if (e.key === 'Escape') onClose?.();
    };
    document.addEventListener('keydown', onKey);
    return () => {
      document.body.style.overflow = prev;
      document.removeEventListener('keydown', onKey);
    };
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[60]"
          role="dialog"
          aria-modal="true"
          onClick={onClose}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div className="absolute inset-0 bg-black/40" />
          <motion.div
            ref={panelRef}
            className="absolute left-0 right-0 bottom-0 bg-white rounded-t-2xl shadow-2xl border-t border-gray-200 max-h-[85vh] overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
            initial={{ y: 48 }}
            animate={{ y: 0 }}
            exit={{ y: 160 }}
            layout
            drag="y"
            dragConstraints={{ top: 0, bottom: 0 }}
            dragElastic={{ top: 0, bottom: 0.25 }}
            onDragEnd={(_, info) => {
              if (info.offset.y > 80) onClose?.();
            }}
            transition={{ type: 'spring', mass: 0.9, stiffness: 260, damping: 24 }}
          >
            <div className="h-6 flex items-center justify-center">
              <div className="mt-2 h-1.5 w-10 rounded-full bg-gray-300" />
            </div>
            <div className="px-4 pb-2 flex items-center justify-between">
              <h2 className="text-base font-semibold text-[#822433] truncate">{title}</h2>
              {/* <button
                className="text-gray-500 hover:text-red-700 text-xl leading-none px-2"
                onClick={onClose}
                aria-label="Chiudi"
              >
                ×
              </button> */}
            </div>
            <motion.div className="px-4 pt-2 pb-3 overflow-y-auto" layout>
              {children}
            </motion.div>
            {footer && (
              <motion.div className="px-4 pb-[max(1rem,env(safe-area-inset-bottom))] pt-2 border-t bg-white" layout>
                {footer}
              </motion.div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
