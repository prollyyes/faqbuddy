"use client";
import React, { useEffect, useState } from "react";
import MobileSheet from "@/components/utils/MobileSheet";

export default function CompleteModal({
    courseToComplete,
    completeVoto,
    setCompleteVoto,
    error,
    setShowCompleteModal,
    handleCompleteCourse
}) {
    const [localError, setLocalError] = useState("");
    const [sheetOpen, setSheetOpen] = useState(true);
    useEffect(() => { setSheetOpen(true); }, []);
    const softClose = () => { setSheetOpen(false); setTimeout(() => setShowCompleteModal(false), 240); };

    const handleClick = async () => {
        if (!completeVoto || isNaN(completeVoto) || completeVoto < 18 || completeVoto > 31) {
            setLocalError("Inserisci un voto valido tra 18 e 31");
            return;
        }
        setLocalError("");
        await handleCompleteCourse();
        softClose();
    };

    return (
        <MobileSheet
            open={sheetOpen}
            onClose={softClose}
            title={`Completa: ${courseToComplete?.nome || ''}`}
            footer={
                <div className="flex gap-3">
                    <button
                        className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg"
                        onClick={softClose}
                        type="button"
                    >
                        Annulla
                    </button>
                    <button
                        className="flex-1 px-4 py-2 bg-[#991B1B] text-white rounded-lg"
                        onClick={handleClick}
                        type="button"
                    >
                        Completa
                    </button>
                </div>
            }
        >
            <p className="mb-2 text-sm text-black">
                Docente: {(courseToComplete?.docente_nome || courseToComplete?.docente_cognome)
                    ? `${courseToComplete?.docente_nome ?? ""} ${courseToComplete?.docente_cognome ?? ""}`.trim()
                    : "N/A"}
            </p>
            <label className="block mb-2 text-black">Voto:</label>
            <input
                type="number"
                min={18}
                max={31}
                value={completeVoto}
                onChange={e => setCompleteVoto(e.target.value)}
                className="border text-black rounded p-3 w-full mb-2"
            />
            {(localError || error) && <div className="text-red-600 mb-1">{localError || error}</div>}
        </MobileSheet>
    );
}
