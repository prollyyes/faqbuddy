'use client'
import React, { useEffect, useState } from "react";
import MobileSheet from "@/components/utils/MobileSheet";

export default function SimulExamModal({ open, onClose, esami, onAdd }) {
  const [selected, setSelected] = useState("");
  const [voto, setVoto] = useState("");

  useEffect(() => {
    if (open && esami.length > 0) {
      setSelected(esami[0].nome);
    }
  }, [open, esami]);

  const cfu = esami.find(e => e.nome === selected)?.cfu || "";

  return (
    <MobileSheet
      open={open}
      onClose={onClose}
      title="Simula esame"
      footer={
        <button
          type="submit"
          form="simul-exam-form"
          className="w-full bg-[#991B1B] text-white rounded-lg py-2 font-semibold active:opacity-90"
        >
          Aggiungi
        </button>
      }
    >
      <form
        id="simul-exam-form"
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
          className="border rounded px-3 py-2 text-black"
          value={selected}
          onChange={e => setSelected(e.target.value)}
        >
          {esami.map(e => (
            <option key={e.nome} value={e.nome}>{e.nome} ({e.cfu} CFU)</option>
          ))}
        </select>
        <label className="text-sm font-semibold mt-1 text-black">Voto</label>
        <input
          type="number"
          min={18}
          max={30}
          required
          className="border rounded px-3 py-2 text-black"
          value={voto}
          onChange={e => setVoto(e.target.value)}
          placeholder="Voto"
        />
      </form>
    </MobileSheet>
  );
}
