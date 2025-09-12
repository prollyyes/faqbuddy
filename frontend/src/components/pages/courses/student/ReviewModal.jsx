import React, { useState } from "react";

export default function ReviewModal({ corso, onClose, onSubmit, error }) {
  const [descrizione, setDescrizione] = useState("");
  const [voto, setVoto] = useState(0);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!voto || voto < 1 || voto > 5) return;
    onSubmit(corso, descrizione, voto);
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
            <label className="block font-semibold mb-1 text-black">Lascia una review !</label>
            <textarea
              className="border rounded p-2 w-full text-black"
              value={descrizione}
              onChange={e => setDescrizione(e.target.value)}
              rows={3}
              required
            />
          </div>
          <div>
            <label className="block font-semibold mb-2 text-black">Quanto sei soddisfatto?</label>
            <div className="flex gap-3 mb-1">
              {[1,2,3,4,5].map((num) => (
                <button
                  key={num}
                  type="button"
                  aria-label={`Voto ${num}`}
                  title={`Voto ${num}`}
                  onClick={() => setVoto(num)}
                  className={`w-8 h-8 rounded-full border-2 flex items-center justify-center transition-all duration-200
                    ${voto >= num ? 'bg-[#991B1B] border-[#991B1B]' : 'bg-white border-black'}
                    hover:border-[#991B1B] hover:bg-[#fde8e8] focus:outline-none
                  `}
                >
                  <span className={`block w-4 h-4 rounded-full ${voto >= num ? 'bg-white' : ''}`}></span>
                </button>
              ))}
            </div>
          </div>
          {error && <div className="text-red-600">{error}</div>}
          <div className="flex justify-end gap-4 mt-2">
            {/* <button
              type="button"
              className="px-3 py-1 bg-gray-200 text-gray-700 rounded border-1 border-black hover:bg-gray-300"
              onClick={onClose}
            >
              Annulla
            </button> */}
            <button
              type="submit"
              className="px-3 py-1 bg-[#991B1B] text-white rounded border-1 border-black hover:bg-red-800 font-semibold"
            >
              Invia
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}