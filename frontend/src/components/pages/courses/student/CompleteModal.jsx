import React, { useState } from "react";

export default function CompleteModal({
    courseToComplete,
    completeVoto,
    setCompleteVoto,
    error,
    setShowCompleteModal,
    handleCompleteCourse
}) {
    const [localError, setLocalError] = useState("");

    const handleClick = () => {
        if (!completeVoto || isNaN(completeVoto) || completeVoto < 18 || completeVoto > 31) {
            setLocalError("Inserisci un voto valido tra 18 e 31");
            return;
        }
        setLocalError("");
        handleCompleteCourse();
    };

    return (
        <div className="fixed inset-0 flex items-center justify-center z-50 backdrop-blur-sm backdrop-brightness-75">
            <div className="bg-white/80 p-6 rounded-lg shadow-lg w-96 border-2 border-[#991B1B] backdrop-blur-md">
                <h3 className="text-lg font-bold mb-2 text-[#991B1B]">
                    Completa il corso: {courseToComplete?.nome}
                </h3>
                <p className="mb-2 text-sm">
                    Docente: {(courseToComplete?.docente_nome || courseToComplete?.docente_cognome)
                        ? `${courseToComplete?.docente_nome ?? ""} ${courseToComplete?.docente_cognome ?? ""}`.trim()
                        : "N/A"}
                </p>
                <label className="block mb-2">Voto:</label>
                <input
                    type="number"
                    min={18}
                    max={31}
                    value={completeVoto}
                    onChange={e => setCompleteVoto(e.target.value)}
                    className="border rounded p-2 w-full mb-4"
                />
                {(localError || error) && <div className="text-red-600 mb-2">{localError || error}</div>}
                <div className="flex flex-row justify-center gap-6 mt-4">
                    <button
                        className="px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition text-sm"
                        onClick={() => setShowCompleteModal(false)}
                    >
                        Annulla
                    </button>
                    <button
                        className="px-3 py-1 bg-[#991B1B] text-white rounded hover:bg-red-800 font-semibold transition text-sm flex items-center"
                        onClick={handleClick}
                    >
                        <span className="mr-1 text-lg">✓</span> Completa
                    </button>
                </div>
            </div>
        </div>
    );
}