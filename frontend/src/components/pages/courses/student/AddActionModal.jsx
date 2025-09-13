"use client";
import React from "react";
import MobileSheet from "@/components/utils/MobileSheet";

export default function AddActionModal({ onClose, onReview, onMaterial }) {
  return (
    <MobileSheet open={true} onClose={onClose} title="Cosa vuoi aggiungere?">
      <div className="flex flex-col gap-3">
        <button className="px-4 py-3 bg-[#991B1B] text-white rounded-lg" onClick={onReview}>Aggiungi Review</button>
        <button className="px-4 py-3 bg-gray-100 text-black rounded-lg" onClick={onMaterial}>Aggiungi Materiale</button>
      </div>
    </MobileSheet>
  );
}
