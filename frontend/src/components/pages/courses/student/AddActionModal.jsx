"use client";
import React, { useEffect, useState } from "react";
import MobileSheet from "@/components/utils/MobileSheet";

export default function AddActionModal({ onClose, onReview, canAddReview = true }) {
  const [sheetOpen, setSheetOpen] = useState(true);
  useEffect(() => { setSheetOpen(true); }, []);
  const softClose = () => { setSheetOpen(false); setTimeout(() => onClose?.(), 240); };
  const handleReviewClick = () => {
    if (!canAddReview) return;
    onReview?.();
    softClose();
  };
  return (
    <MobileSheet open={sheetOpen} onClose={softClose} title="Lascia una Recensione!">
      <div className="flex flex-col gap-3">
        <button
          className={`px-4 py-3 rounded-lg ${canAddReview ? "bg-[#991B1B] text-white" : "bg-gray-200 text-gray-500 cursor-not-allowed"}`}
          onClick={handleReviewClick}
          disabled={!canAddReview}
        >
          {canAddReview ? "Aggiungi Review" : "Recensione già inviata"}
        </button>
      </div>
    </MobileSheet>
  );
}
