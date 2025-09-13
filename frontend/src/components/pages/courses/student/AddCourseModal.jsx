"use client";
import React from 'react';
import { useState, useEffect } from 'react';
import MobileSheet from "@/components/utils/MobileSheet";
import { AnimatePresence, motion } from 'framer-motion';

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
    const [sheetOpen, setSheetOpen] = useState(true);
    const softClose = () => {
        setSheetOpen(false);
        setTimeout(() => setShowAddModal(false), 240);
    };
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
        <MobileSheet open={sheetOpen} onClose={softClose} title="Aggiungi Corso">
            <motion.div layout>
              <AnimatePresence initial={false} mode="wait">
                {!selectedCourseId ? (
                  <motion.div key="list" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }} transition={{ duration: 0.18 }}>
                    <div className="mb-4 ">
                            <h4 className="font-semibold mb-2 text-black">Corsi disponibili:</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                {availableCourses.map(corso => (
                                    <div
                                        key={corso.id}
                                        className="border border-black rounded-lg p-4 shadow hover:bg-gray-100 cursor-pointer transition"
                                        onClick={() => handleSelectCourse(corso.id)}
                                    >
                                        <div className="font-bold text-[#991B1B]">{corso.nome}</div>
                                        <div className="text-sm text-gray-700">CFU: {corso.cfu}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                  </motion.div>
                ) : (
                  <motion.div key={showAddEdition ? 'form' : 'editions'} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }} transition={{ duration: 0.18 }} layout>
                        <div className="mb-4">
                            <div className="grid grid-cols-1 gap-2">
                                {editions.map(edition => (
                                    <div
                                        key={edition.id + "_" + edition.data}
                                        className="border border-black rounded-lg p-3 flex items-center justify-between hover:bg-gray-100 cursor-pointer transition"
                                    >
                                        <span>
                                            <div className='text-black'>{edition.data}</div>
                                            <div className="text-sm text-gray-700">
                                                Docente: {edition.docente ? edition.docente : "N/A"}
                                            </div>
                                        </span>
                                        <button
                                            className="px-2 py-1 bg-green-600 text-white rounded hover:bg-green-800"
                                            onClick={async () => { await handleEnroll(selectedCourseId, edition.id, edition.data); softClose(); }}
                                        >
                                            Iscriviti
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <AnimatePresence initial={false} mode="wait">
                        {!showAddEdition ? (
                            <motion.div key="editions-actions" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }} transition={{ duration: 0.18 }} className="flex flex-row justify-center gap-6 mt-4">
                                <button
                                    className="px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition text-sm"
                                    onClick={softClose}
                                >
                                    Chiudi
                                </button>
                                <button
                                    className="px-3 py-1 bg-[#991B1B] text-white rounded hover:bg-red-800 font-semibold transition text-sm flex items-center"
                                    onClick={() => setShowAddEdition(true)}
                                >
                                    <span className="mr-1 text-lg">+</span> Aggiungi Edizione
                                </button>
                            </motion.div>
                        ) : (
                            <motion.form key="form" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }} transition={{ duration: 0.18 }} onSubmit={handleAddEdition} className="space-y-2 mt-4">
                                <h4 className="font-semibold mb-2 text-black">Aggiungi nuova edizione</h4>
                                <label className="block font-semibold text-black">Data:</label>
                                <select
                                    required
                                    className="border rounded p-2 w-full text-black"
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
                                    placeholder="Orario"
                                    className="border rounded p-2 w-full text-black"
                                    value={newEdition.orario}
                                    onChange={e => setNewEdition({ ...newEdition, orario: e.target.value })}
                                />

                                <input
                                    type="text"
                                    required
                                    placeholder="Modalità Esame"
                                    className="border rounded p-2 w-full text-black"
                                    value={newEdition.mod_Esame}
                                    onChange={e => setNewEdition({ ...newEdition, mod_Esame: e.target.value })}
                                />

                                <label className="block font-semibold text-black">Docente:</label>
                                <select
                                  required
                                  className="border rounded p-2 w-full text-black"
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
                                    <span className="font-semibold text-black">Esonero:</span>
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
                            </motion.form>
                        )}
                        </AnimatePresence>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
                {error && (
                  <div className="text-red-600 mt-2">
                    {typeof error === "string"
                      ? error
                      : Array.isArray(error)
                        ? error.map((e, i) => <div key={i}>{e.msg || JSON.stringify(e)}</div>)
                        : error.detail && Array.isArray(error.detail)
                          ? error.detail.map((e, i) => <div key={i}>{e.msg || JSON.stringify(e)}</div>)
                          : JSON.stringify(error)}
                  </div>
                )}
                {success && <div className="text-green-600 mt-2">{success}</div>}
        </MobileSheet>
    );
}
