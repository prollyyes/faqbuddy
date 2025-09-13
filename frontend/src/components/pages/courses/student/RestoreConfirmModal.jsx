"use client";
import React from "react";
import Button from "@/components/utils/Button";
import MobileSheet from "@/components/utils/MobileSheet";

export default function RestoreConfirmModal({ open, onClose, onConfirm }) {
  if (!open) return null;
  return (
    <MobileSheet
      open={open}
      onClose={onClose}
      title="Sei sicuro?"
      footer={
        <div className="flex gap-3">
          <button className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg" onClick={onClose}>Annulla</button>
          <Button className="flex-1 px-4 py-2" onClick={onConfirm}>Continua</Button>
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
