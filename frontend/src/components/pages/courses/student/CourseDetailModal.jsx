"use client";
import React from "react";
import MobileSheet from "@/components/utils/MobileSheet";

export default function CourseDetailModal({ corso, onClose }) {
  if (!corso) return null;
  return (
    <MobileSheet open={true} onClose={onClose} title={corso.nome}>
      <div className="mb-2 text-gray-700">CFU: <span className="font-bold">{corso.cfu}</span></div>
      <div className="mb-2 text-gray-700">Edizione: <span className="font-bold">{corso.edition_data}</span></div>
      <div className="mb-2 text-gray-700">
        Docente: <span className="font-bold">{corso.docente_nome} {corso.docente_cognome}</span>
      </div>
      <div className="mb-2 text-gray-700">Modalità esame: <span className="font-bold">{corso.mod_Esame || corso.mod_esame || "N/A"}</span></div>
      <div className="mb-2 text-gray-700">Orario: <span className="font-bold">{corso.orario || "N/A"}</span></div>
      <div className="mb-2 text-gray-700">Esonero: <span className="font-bold">{corso.esonero ? "Sì" : "No"}</span></div>
      <div className="mb-2 text-gray-700">Stato: <span className="font-bold">{corso.stato}</span></div>
      {corso.voto !== undefined && corso.voto >= 18 && (
        <div className="mb-2 text-gray-700">
          Voto: <span className="font-bold text-green-700">{corso.voto}</span>
        </div>
      )}
    </MobileSheet>
  );
}
