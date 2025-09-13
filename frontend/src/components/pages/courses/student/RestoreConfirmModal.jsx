"use client";
import React, { useEffect, useState } from "react";
import Button from "@/components/utils/Button";
import MobileSheet from "@/components/utils/MobileSheet";

export default function RestoreConfirmModal({ open, onClose, onConfirm }) {
  const [sheetOpen, setSheetOpen] = useState(open);

  useEffect(() => {
    if (open) setSheetOpen(true);
  }, [open]);

  const softClose = () => {
    setSheetOpen(false);
    setTimeout(() => onClose?.(), 240);
  };

  if (!open && !sheetOpen) return null;
  return (
    <MobileSheet
      open={sheetOpen}
      onClose={softClose}
      title="Sei sicuro?"
      footer={
        <div className="flex gap-3">
          <button className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg" onClick={softClose}>Annulla</button>
          <Button className="flex-1 px-4 py-2" onClick={async () => { await onConfirm?.(); softClose(); }}>Continua</Button>
        </div>
      }
    >
      <p className="text-sm text-gray-700">
        Ripristinando questo corso tra gli attivi <span className="font-semibold text-[#991B1B]">tutte le recensioni e i materiali caricati andranno persi</span>.
        <br />Vuoi continuare?
      </p>
    </MobileSheet>
  );
}
