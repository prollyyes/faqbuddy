import React, { useEffect, useState } from "react";
import { IoClose } from "react-icons/io5";

export default function SimulExamModal({ open, onClose, esami, onAdd }) {
  const [selected, setSelected] = useState("");
  const [voto, setVoto] = useState("");

  // Imposta esame di default quando la modale si apre o cambia la lista esami
  useEffect(() => {
    if (open && esami.length > 0) {
      setSelected(esami[0].nome);
    }
  }, [open, esami]);

  if (!open) return null;

  const cfu = esami.find(e => e.nome === selected)?.cfu || "";

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50 backdrop-blur-sm backdrop-brightness-75">
      <div className="relative bg-white/90 p-6 rounded-lg shadow-2xl w-[22rem] max-w-full border-2 border-[#991B1B]">
        <button
          className="absolute top-2 right-2 text-gray-500 hover:text-red-700 text-xl"
          onClick={onClose}
          aria-label="Chiudi"
        >
          <IoClose />
        </button>
        <h2 className="text-lg font-bold mb-4 text-[#991B1B]">Simula esame</h2>
        <form
          onSubmit={e => {
            e.preventDefault();
            if (!selected || !voto) return;
            onAdd({ nome: selected, voto: Number(voto), cfu });
            setVoto("");
            onClose();
          }}
          className="flex flex-col gap-3"
        >
          <label className="text-sm font-semibold text-black">Esame</label>
          <select
            className="border rounded px-2 py-1 text-black"
            value={selected}
            onChange={e => setSelected(e.target.value)}
          >
            {esami.map(e => (
              <option key={e.nome} value={e.nome}>{e.nome} ({e.cfu} CFU)</option>
            ))}
          </select>
          <label className="text-sm font-semibold mt-2 text-black">Voto</label>
          <input
            type="number"
            min={18}
            max={30}
            required
            className="border rounded px-2 py-1 text-black"
            value={voto}
            onChange={e => setVoto(e.target.value)}
            placeholder="Voto"
          />
          <button
            type="submit"
            className="bg-[#991B1B] text-white rounded px-3 py-1 mt-3 hover:bg-red-800"
          >
            Aggiungi
          </button>
        </form>
      </div>
    </div>
  );
}