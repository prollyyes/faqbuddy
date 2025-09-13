'use client'
import React, { useState } from "react";
import axios from "axios";

const HOST = process.env.NEXT_PUBLIC_HOST;

export function EditionsModal({ corso, onClose, onUpdateStato }) {
    const [editStates, setEditStates] = useState({});
    const [editMode, setEditMode] = useState({});
    const [loadingId, setLoadingId] = useState(null);
    const [error, setError] = useState("");
    const [successId, setSuccessId] = useState(null);
    const [edizioni, setEdizioni] = useState(corso.edizioni);

    // Opzioni per la data (S1/anno, S2/anno)
    const anni = [];
    for (let anno = 2015; anno <= 2025; anno++) {
        anni.push(anno);
    }
    const semestri = ["S1", "S2"];
    const opzioniData = [];
    anni.forEach(anno => {
        semestri.forEach(sem => opzioniData.push(`${sem}/${anno}`));
    });

    // Prepara i valori iniziali per la modifica
    const startEdit = (ed) => {
        setEditMode({ ...editMode, [ed.edition_id]: true });
        setEditStates({
            ...editStates,
            [ed.edition_id]: {
                stato: ed.stato,
                mod_Esame: ed.mod_esame,
                orario: ed.orario,
                esonero: ed.esonero,
                data: ed.edition_data
            }
        });
        setSuccessId(null);
    };

    const handleFieldChange = (edition_id, field, value) => {
        setEditStates({
            ...editStates,
            [edition_id]: {
                ...editStates[edition_id],
                [field]: value
            }
        });
        setSuccessId(null);
    };

    const handleUpdate = async (edition_id) => {
        setLoadingId(edition_id);
        setError("");
        try {
            const token = localStorage.getItem("token");
            const payload = editStates[edition_id];
            await axios.patch(
                `${HOST}/teacher/editions/${edition_id}`,
                payload,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        "Content-Type": "application/json"
                    }
                }
            );
            setSuccessId(edition_id);
            setEditMode({ ...editMode, [edition_id]: false });

            // Aggiorna la copia locale delle edizioni
            setEdizioni(prev =>
                prev.map(ed =>
                    ed.edition_id === edition_id
                        ? { ...ed, ...payload }
                        : ed
                )
            );

            // AGGIUNGI QUESTO: aggiorna il corso padre (se la funzione esiste)
            if (onUpdateStato) onUpdateStato();

            onClose();

        } catch (e) {
            setError("Errore aggiornamento edizione");
        }
        setLoadingId(null);
    };

    return (
        <div className="fixed inset-0 flex items-center justify-center z-50 backdrop-blur-sm backdrop-brightness-75">
            <div className="relative pointer-events-auto bg-white/90 p-6 rounded-lg shadow-2xl w-[22rem] max-w-full max-h-[90vh] overflow-y-auto border-2 border-[#991B1B]">
                <button
                    className="absolute top-2 right-2 text-gray-500 hover:text-red-700 text-xl"
                    onClick={onClose}
                >
                    &times;
                </button>
                <h3 className="text-lg font-bold mb-4 text-[#991B1B]">{corso.nome}</h3>
                <div className="mb-2 text-gray-700">CFU: <span className="font-bold">{corso.cfu}</span></div>
                <h4 className="font-semibold mb-2 text-black">Edizioni:</h4>
                <div className="space-y-2">
                    {edizioni.length === 0 && (
                        <div className="text-gray-500">Nessuna edizione trovata.</div>
                    )}
                    {edizioni.map((ed) => (
                        <div key={ed.edition_id} className="border border-black rounded-lg p-3">
                            <div className="font-semibold text-[#991B1B]">{ed.data || ed.edition_data}</div>
                            {editMode[ed.edition_id] ? (
                                <>
                                    <div className="text-sm mb-1 text-black">
                                        Modalità esame:{" "}
                                        <input
                                            className="border rounded p-1 w-full"
                                            value={editStates[ed.edition_id]?.mod_Esame || ""}
                                            onChange={e => handleFieldChange(ed.edition_id, "mod_Esame", e.target.value)}
                                            disabled={loadingId === ed.edition_id}
                                        />
                                    </div>
                                    <div className="text-sm mb-1 text-black">
                                        Orario:{" "}
                                        <input
                                            className="border rounded p-1 w-full"
                                            value={editStates[ed.edition_id]?.orario || ""}
                                            onChange={e => handleFieldChange(ed.edition_id, "orario", e.target.value)}
                                            disabled={loadingId === ed.edition_id}
                                        />
                                    </div>
                                    <div className="text-sm mb-1 flex items-center gap-2 text-black">
                                        Esonero:{" "}
                                        <button
                                            type="button"
                                            className={`px-2 py-1 rounded ${editStates[ed.edition_id]?.esonero ? "bg-[#991B1B] text-white" : "bg-gray-200 text-gray-700"}`}
                                            onClick={() => handleFieldChange(ed.edition_id, "esonero", !editStates[ed.edition_id]?.esonero)}
                                            disabled={loadingId === ed.edition_id}
                                        >
                                            {editStates[ed.edition_id]?.esonero ? "Sì" : "No"}
                                        </button>
                                    </div>
                                    <div className="text-sm mb-1 text-black">
                                        <label className="block font-semibold">Data:</label>
                                        <select
                                            required
                                            className="border rounded p-2 w-full"
                                            value={editStates[ed.edition_id]?.data || ""}
                                            onChange={e => handleFieldChange(ed.edition_id, "data", e.target.value)}
                                            disabled={loadingId === ed.edition_id}
                                        >
                                            <option value="">Seleziona data</option>
                                            {opzioniData.map(opt => (
                                                <option key={opt} value={opt}>{opt}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="text-sm mb-2 text-black">
                                        Stato:{" "}
                                        <select
                                            className="border rounded p-1"
                                            value={editStates[ed.edition_id]?.stato || ed.stato}
                                            onChange={e => handleFieldChange(ed.edition_id, "stato", e.target.value)}
                                            disabled={loadingId === ed.edition_id}
                                        >
                                            <option value="attivo">Attivo</option>
                                            <option value="archiviato">Archiviato</option>
                                            <option value="annullato">Annullato</option>
                                        </select>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <button
                                            className="w-8 h-8 flex items-center justify-center bg-[#991B1B] text-white rounded-full hover:bg-red-800 text-xl shadow"
                                            style={{ marginTop: "-0.2rem" }}
                                            disabled={loadingId === ed.edition_id}
                                            onClick={() => handleUpdate(ed.edition_id)}
                                            title="Salva modifiche"
                                        >
                                            ✓
                                        </button>
                                        {successId === ed.edition_id && (
                                            <span className="text-green-600 text-sm ml-1">Modificato!</span>
                                        )}
                                    </div>
                                </>
                            ) : (
                                <>
                                    <div className="text-sm text-black">Modalità esame: <span className="font-bold">{ed.mod_Esame || ed.mod_esame || "N/A"}</span></div>
                                    <div className="text-sm text-black">Orario: <span className="font-bold">{ed.orario || "N/A"}</span></div>
                                    <div className="text-sm text-black">Esonero: <span className="font-bold">{ed.esonero ? "Sì" : "No"}</span></div>
                                    <div className="text-sm text-black">Data: <span className="font-bold">{ed.data || ed.edition_data}</span></div>
                                    <div className="text-sm mb-2 text-black">Stato: <span className="font-bold">{ed.stato}</span></div>
                                    <button
                                        className="px-2 py-1 rounded text-[#991B1B] border border-[#991B1B] hover:bg-[#991B1B] hover:text-white text-sm transition"
                                        onClick={() => startEdit(ed)}
                                    >
                                        Modifica
                                    </button>
                                </>
                            )}
                        </div>
                    ))}
                </div>
                {error && <div className="text-red-600 mt-2">{error}</div>}
            </div>
        </div>
    );
}
