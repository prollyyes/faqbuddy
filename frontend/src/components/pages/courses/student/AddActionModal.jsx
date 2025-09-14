"use client";
import React, { useEffect, useState } from "react";
import MobileSheet from "@/components/utils/MobileSheet";

export default function AddActionModal({ onClose, onReview, onMaterial }) {
  const [sheetOpen, setSheetOpen] = useState(true);
  useEffect(() => { setSheetOpen(true); }, []);
  const softClose = () => { setSheetOpen(false); setTimeout(() => onClose?.(), 240); };
  return (
    <MobileSheet open={sheetOpen} onClose={softClose} title="Cosa vuoi aggiungere?">
      <div className="flex flex-col gap-3">
        <button className="px-4 py-3 bg-[#991B1B] text-white rounded-lg" onClick={() => { onReview?.(); softClose(); }}>Aggiungi Review</button>
        <button className="px-4 py-3 bg-gray-100 text-black rounded-lg" onClick={() => { onMaterial?.(); softClose(); }}>Aggiungi Materiale</button>
      </div>
    </MobileSheet>
  );
}
