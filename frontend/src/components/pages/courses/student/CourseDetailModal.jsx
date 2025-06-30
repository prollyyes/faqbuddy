import React from "react";

export default function CourseDetailModal({ corso, onClose }) {
  if (!corso) return null;
  return (
    <div className="fixed inset-0 flex items-center justify-center z-50 backdrop-blur-sm backdrop-brightness-75">
      <div className="relative bg-white/90 p-6 rounded-lg shadow-2xl w-[22rem] max-w-full max-h-[90vh] overflow-y-auto border-2 border-[#991B1B]">
        <button
          className="absolute top-2 right-2 text-gray-500 hover:text-red-700 text-xl"
          onClick={onClose}
        >
          &times;
        </button>
        <h3 className="text-lg font-bold mb-4 text-[#991B1B]">{corso.nome}</h3>
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
      </div>
    </div>
  );
}