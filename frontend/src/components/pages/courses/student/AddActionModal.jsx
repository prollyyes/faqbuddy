import React from "react";

export default function AddActionModal({ onClose, onReview, onMaterial }) {
  return (
    <div className="fixed inset-0 flex items-center justify-center z-50 backdrop-blur-sm backdrop-brightness-75">
      <div className="relative bg-white/90 p-6 rounded-lg shadow-2xl w-[20rem] max-w-full border-2 border-[#991B1B] flex flex-col items-center">
        <button
          className="absolute top-2 right-2 text-gray-500 hover:text-red-700 text-xl"
          onClick={onClose}
        >
          &times;
        </button>
        <h3 className="text-lg font-bold mb-6 text-[#991B1B]">Cosa vuoi aggiungere?</h3>
        <button
          className="mb-4 px-4 py-2 bg-[#991B1B] text-white rounded hover:bg-red-800 w-full"
          onClick={onReview}
        >
          Aggiungi Review
        </button>
        <button
          className="px-4 py-2 bg-white text-black rounded w-full"
          onClick={onMaterial}
        >
          Aggiungi Materiale
        </button>
      </div>
    </div>
  );
}