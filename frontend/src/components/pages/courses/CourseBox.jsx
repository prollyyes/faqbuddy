import React from "react";

export default function CourseBox({ corso, children }) {
  return (
    <div className="border rounded-lg p-4 shadow-md bg-white w-full md:w-1/2 lg:w-1/3 flex flex-col gap-2">
      <h3 className="text-lg font-bold mb-2 text-[#991B1B]">{corso.nome}</h3>
      <p className="text-sm text-gray-600 font-bold">CFU: {corso.cfu}</p>
      <p className="text-sm">
        Docente: {(corso.docente_nome || corso.docente_cognome)
          ? `${corso.docente_nome ?? ""} ${corso.docente_cognome ?? ""}`.trim()
          : "N/A"}
      </p>
      {corso.edition_data && <p className="text-sm">Data Edizione: {corso.edition_data}</p>}
      {corso.voto !== undefined && corso.voto !== null && (
        <span className="block text-green-700 font-bold">Voto: {corso.voto}</span>
      )}
      {children}
    </div>
  );
}