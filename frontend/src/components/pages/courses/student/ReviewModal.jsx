import React, { useState } from "react";

export default function ReviewModal({ corso, onClose, onSubmit, error }) {
  const [descrizione, setDescrizione] = useState("");
  const [voto, setVoto] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!voto || isNaN(voto) || voto < 1 || voto > 5) return;
    onSubmit(corso, descrizione, Number(voto));
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50 backdrop-blur-sm backdrop-brightness-75">
      <div className="relative bg-white/90 p-6 rounded-lg shadow-2xl w-[22rem] max-w-full border-2 border-[#991B1B]">
        <button
          className="absolute top-2 right-2 text-gray-500 hover:text-red-700 text-xl"
          onClick={onClose}
        >
          &times;
        </button>
        <h3 className="text-lg font-bold mb-4 text-[#991B1B]">Aggiungi Recensione</h3>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block font-semibold mb-1">Descrizione:</label>
            <textarea
              className="border rounded p-2 w-full"
              value={descrizione}
              onChange={e => setDescrizione(e.target.value)}
              rows={3}
              required
            />
          </div>
          <div>
            <label className="block font-semibold mb-1">Voto (1-5):</label>
            <input
              type="number"
              min={1}
              max={5}
              className="border rounded p-2 w-full"
              value={voto}
              onChange={e => setVoto(e.target.value)}
              required
            />
          </div>
          {error && <div className="text-red-600">{error}</div>}
          <div className="flex justify-end gap-4 mt-2">
            <button
              type="button"
              className="px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
              onClick={onClose}
            >
              Annulla
            </button>
            <button
              type="submit"
              className="px-3 py-1 bg-[#991B1B] text-white rounded hover:bg-red-800 font-semibold"
            >
              Invia
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}