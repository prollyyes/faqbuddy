import React from "react";
import { IoClose } from "react-icons/io5";

export default function CourseBox({ corso, children, onClick, onUnenroll, onComplete }) {
  return (
    <div
      className="rounded-lg shadow-lg bg-white p-4 w-72 cursor-pointer hover:shadow-2xl transition relative"
      onClick={onClick}
      tabIndex={0}
      role="button"
    >
      {/* é molto comodo usare le prop cosi quando vado a creare l'elemento CourseBox mi basta passare la prop onUnenroll per far si che il bottone appare */}
      {/* Bottone disiscrizione in alto a destra */}
      {onUnenroll && (
        <button
          className="absolute top-2 right-2 z-10"
          style={{
            background: "none",
            border: "none",
            boxShadow: "none",
            padding: 0,
            lineHeight: 1,
          }}
          onClick={e => { e.stopPropagation(); onUnenroll(); }}
          title="Disiscriviti dal corso"
          aria-label="Disiscriviti dal corso"
        >
          <IoClose size={28} color="#991B1B" />
        </button>
      )}
      {/* Bottone completa corso in basso a destra */}
      {onComplete && (
        <button
          className="absolute bottom-2 right-2 z-10 w-8 h-8 flex items-center justify-center bg-[#991B1B] text-white rounded-full hover:bg-red-800 text-xl shadow"
          style={{
            padding: 0,
            lineHeight: 1,
          }}
          onClick={e => { e.stopPropagation(); onComplete(); }}
          title="Completa corso"
          aria-label="Completa corso"
        >
          ✓
        </button>
      )}
      <div className="font-bold text-lg mb-2 text-[#991B1B] pr-10 break-words whitespace-normal leading-snug">{corso.nome}</div>
      <div className="mb-1 text-black">Edizione: <span className="font-semibold">{corso.edition_data}</span></div>
      <div className="mb-1 text-black" >CFU: <span className="font-semibold">{corso.cfu}</span></div>
      <div className="mb-1 text-black">Stato: <span className="font-semibold">{corso.stato}</span></div>
      {corso.voto && (
        <div className="mb-1 text-black">Voto: <span className="font-semibold text-green-600">{corso.voto}</span></div>
      )}
      {children}
    </div>
  );
}
