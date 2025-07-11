import React from "react";

export default function CourseBox({ corso, children, onClick }) {
  return (
    <div
      className="rounded-lg shadow-lg bg-white p-4 w-72 cursor-pointer hover:shadow-2xl transition"
      onClick={onClick}
      tabIndex={0}
      role="button"
      style={{ position: "relative" }}
    >
      <div className="font-bold text-lg mb-2 text-[#991B1B]">{corso.nome}</div>
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