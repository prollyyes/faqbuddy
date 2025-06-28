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
      <div className="mb-1">Edizione: <span className="font-semibold">{corso.edition_data}</span></div>
      <div className="mb-1">CFU: <span className="font-semibold">{corso.cfu}</span></div>
      <div className="mb-1">Stato: <span className="font-semibold">{corso.stato}</span></div>
      {children}
    </div>
  );
}