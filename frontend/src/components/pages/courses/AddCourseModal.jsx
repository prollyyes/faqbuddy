import React from 'react';
import { useState, useEffect } from 'react';

export default function AddCourseModal({
    availableCourses,
    selectedCourseId,
    editions,
    showAddEdition,
    newEdition,
    error,
    success,
    setShowAddModal,
    handleSelectCourse,
    handleEnroll,
    setShowAddEdition,
    handleAddEdition,
    setNewEdition,
    docenti
}) {

    const selectedCourse = availableCourses.find(c => c.id === selectedCourseId);
    const anni = [];
    for (let anno = 2015; anno <= 2025; anno++) {
        anni.push(anno);
    }
    const semestri = ["S1", "S2"];
    const opzioniData = [];
    anni.forEach(anno => {
        semestri.forEach(sem => opzioniData.push(`${sem}/${anno}`));
    });

    return (
        <div className="fixed inset-0 flex items-center justify-center z-50 backdrop-blur-sm backdrop-brightness-75 pt-25">
            <div className="relative pointer-events-auto bg-white/80 p-6 rounded-lg shadow-2xl w-[22rem] max-w-full max-h-[90vh] overflow-y-auto border-2 border-[#991B1B] backdrop-blur-md">
                <button
                    className="absolute top-2 right-2 text-gray-500 hover:text-red-700 text-xl"
                    onClick={() => setShowAddModal(false)}
                >
                    &times;
                </button>
                <h3 className="text-lg font-bold mb-4 text-[#991B1B]">Aggiungi Corso</h3>
                {!selectedCourseId ? (
                    <>
                        <div className="mb-4">
                            <h4 className="font-semibold mb-2">Corsi disponibili:</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {availableCourses.map(corso => (
                                    <div
                                        key={corso.id}
                                        className="border rounded-lg p-4 shadow hover:bg-gray-100 cursor-pointer transition"
                                        onClick={() => handleSelectCourse(corso.id)}
                                    >
                                        <div className="font-bold text-[#991B1B]">{corso.nome}</div>
                                        <div className="text-sm text-gray-700">CFU: {corso.cfu}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </>
                ) : (
                    <>
                        <div className="mb-4">
                            <div className="grid grid-cols-1 gap-2">
                                {editions.map(edition => (
                                    <div
                                        key={edition.id}
                                        className="border rounded-lg p-3 flex items-center justify-between hover:bg-gray-100 cursor-pointer transition"
                                    >
                                        <span>
                                            {edition.data} - Docente: {edition.docente_nome && edition.docente_cognome
                                                ? `${edition.docente_nome} ${edition.docente_cognome}`
                                                : "N/A"}
                                        </span>
                                        <button
                                            className="px-2 py-1 bg-green-600 text-white rounded hover:bg-green-800"
                                            onClick={() => handleEnroll(selectedCourseId, edition.id, edition.data)}
                                        >
                                            Iscriviti
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                        {!showAddEdition ? (
                            <div className="flex flex-row justify-center gap-6 mt-4">
                                <button
                                    className="px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition text-sm"
                                    onClick={() => setShowAddModal(false)}
                                >
                                    Chiudi
                                </button>
                                <button
                                    className="px-3 py-1 bg-[#991B1B] text-white rounded hover:bg-red-800 font-semibold transition text-sm flex items-center"
                                    onClick={() => setShowAddEdition(true)}
                                >
                                    <span className="mr-1 text-lg">+</span> Aggiungi Edizione
                                </button>
                            </div>
                        ) : (
                            <form onSubmit={handleAddEdition} className="space-y-2 mt-4">
                                <h4 className="font-semibold mb-2">Aggiungi nuova edizione</h4>
                                <label className="block font-semibold">Data:</label>
                                <select
                                    required
                                    className="border rounded p-2 w-full"
                                    value={newEdition.data}
                                    onChange={e => setNewEdition({ ...newEdition, data: e.target.value })}
                                >
                                    <option value="">Seleziona data</option>
                                    {opzioniData.map(opt => (
                                        <option key={opt} value={opt}>{opt}</option>
                                    ))}
                                </select>
                                <input
                                    type="text"
                                    required
                                    placeholder="Orario"
                                    className="border rounded p-2 w-full"
                                    value={newEdition.orario}
                                    onChange={e => setNewEdition({ ...newEdition, orario: e.target.value })}
                                />

                                <input
                                    type="text"
                                    required
                                    placeholder="Modalità Esame"
                                    className="border rounded p-2 w-full"
                                    value={newEdition.mod_Esame}
                                    onChange={e => setNewEdition({ ...newEdition, mod_Esame: e.target.value })}
                                />

                                <label className="block font-semibold">Docente:</label>
                                <select
                                  required
                                  className="border rounded p-2 w-full"
                                  value={newEdition.docenteId}
                                  onChange={e => setNewEdition({ ...newEdition, docenteId: e.target.value })}
                                >
                                  <option value="">Seleziona docente</option>
                                  {docenti.map(docente => (
                                    <option key={docente.id} value={docente.id}>
                                      {docente.nome} {docente.cognome}
                                    </option>
                                  ))}
                                </select>

                                <div className="flex items-center gap-2">
                                    <span className="font-semibold">Esonero:</span>
                                    <button
                                        type="button"
                                        className={`px-4 py-1 rounded-full transition font-semibold text-sm
                                            ${newEdition.esonero
                                                ? "bg-[#991B1B] text-white"
                                                : "bg-gray-200 text-gray-700"}
                                        `}
                                        onClick={() => setNewEdition({ ...newEdition, esonero: !newEdition.esonero })}
                                    >
                                        {newEdition.esonero ? "Sì" : "No"}
                                    </button>
                                </div>

                                <div className="flex flex-row justify-center gap-6 mt-4">
                                    <button
                                        className="px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition text-sm"
                                        type="button"
                                        onClick={() => setShowAddEdition(false)}
                                    >
                                        Indietro
                                    </button>
                                    <button
                                        className="px-3 py-1 bg-[#991B1B] text-white rounded hover:bg-red-800 font-semibold transition text-sm flex items-center"
                                        type="submit"
                                    >
                                        <span className="mr-1 text-lg">+</span> Aggiungi edizione e iscriviti
                                    </button>
                                </div>
                            </form>
                        )}
                    </>
                )}
                {error && (
                    <div className="text-red-600 mt-2">
                        {typeof error === "string"
                            ? error
                            : Array.isArray(error)
                                ? error.map((e, i) => <div key={i}>{e.msg || JSON.stringify(e)}</div>)
                                : JSON.stringify(error)}
                    </div>
                )}
                {success && <div className="text-green-600 mt-2">{success}</div>}
            </div>
        </div>
    );
}