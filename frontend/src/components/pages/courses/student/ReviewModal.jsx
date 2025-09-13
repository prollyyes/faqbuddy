"use client";
import React, { useState } from "react";
import { FaStar } from "react-icons/fa";
import MobileSheet from "@/components/utils/MobileSheet";

export default function ReviewModal({ corso, onClose, onSubmit, error }) {
  const [sheetOpen, setSheetOpen] = useState(true);
  const softClose = () => {
    setSheetOpen(false);
    setTimeout(() => onClose?.(), 240);
  };
  const [descrizione, setDescrizione] = useState("");
  const [voto, setVoto] = useState(0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!voto || voto < 1 || voto > 5) return;
    await onSubmit(corso, descrizione, voto);
    softClose();
  };

  return (
    <MobileSheet open={sheetOpen} onClose={softClose} title="Aggiungi Recensione" footer={
      <button type="submit" form="review-form" className="w-full bg-[#991B1B] text-white rounded-lg py-3 font-semibold">Invia</button>
    }>
        <form id="review-form" onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block font-semibold mb-1 text-black">Lascia una review !</label>
            <textarea
              className="border rounded p-3 w-full text-black"
              value={descrizione}
              onChange={e => setDescrizione(e.target.value)}
              rows={3}
              required
            />
          </div>
          <div>
            <label className="block font-semibold mb-2 text-black">Quanto sei soddisfatto?</label>
            <div className="flex gap-2 mb-1">
              {[1,2,3,4,5].map((num) => (
                <button
                  key={num}
                  type="button"
                  aria-label={`Voto ${num}`}
                  title={`Voto ${num}`}
                  onClick={() => setVoto(num)}
                  className="focus:outline-none"
                >
                  <FaStar
                    size={32}
                    color={voto >= num ? "#991B1B" : "#e5e7eb"}
                    className={`transition-colors duration-200 ${voto >= num ? "" : "hover:scale-110"}`}
                  />
                </button>
              ))}
            </div>
          </div>
          {error && <div className="text-red-600">{error}</div>}
        </form>
    </MobileSheet>
  );
}
