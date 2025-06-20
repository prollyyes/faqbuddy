'use client'

import React from 'react';

const Courses = () => {
  return (
    <div className="min-h-screen bg-white p-6 text-[#800020]">
      <h1 className="text-3xl font-bold mb-4">I tuoi Corsi</h1>
      <p className="mb-6 text-gray-700">
        In questa sezione puoi consultare i corsi a cui sei iscritto, esplorare i dettagli, e accedere a materiale didattico o comunicazioni dai docenti.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {/* Esempio corso */}
        <div className="border border-[#800020] rounded-md p-4 hover:shadow-md transition">
          <h2 className="text-xl font-semibold text-[#800020]">Corso di Sistemi Operativi</h2>
          <p className="text-gray-600">Prof. Rossi · 6 CFU</p>
          <p className="mt-2 text-sm text-gray-700">Approfondimento su processi, thread, scheduling e gestione della memoria.</p>
        </div>
      </div>
    </div>
  );
};

export default Courses;