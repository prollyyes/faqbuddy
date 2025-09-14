'use client'
import React, { createContext, useContext, useMemo, useState } from 'react';

const LogoutContext = createContext(null);

export function LogoutProvider({ children }) {
  const [isOpen, setIsOpen] = useState(false);
  const value = useMemo(() => ({
    isOpen,
    openLogout: () => setIsOpen(true),
    closeLogout: () => setIsOpen(false),
  }), [isOpen]);
  return (
    <LogoutContext.Provider value={value}>{children}</LogoutContext.Provider>
  );
}

export function useLogout() {
  const ctx = useContext(LogoutContext);
  if (!ctx) throw new Error('useLogout must be used within LogoutProvider');
  return ctx;
}

