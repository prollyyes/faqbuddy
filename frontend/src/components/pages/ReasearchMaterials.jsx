'use client'

import React, {useState} from "react";
import { motion } from "framer-motion";
import BackButton from "../utils/BackButton";
import Button from "../utils/Button";
import axios from "axios";

export default function UploadMaterials() {
  const [laureaOptions, setLaureaOptions] = useState([]);
  const [courseOptions, setCourseOptions] = useState([]);
  const [selectedLaurea, setSelectedLaurea] = useState('');
  const [editionOptions, setEditionOptions] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState('');
  const [selectedEdition, setSelectedEdition] = useState('');
  const [materials, setMaterials] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);

  const handleLaureaFocus = async () => {
    if (laureaOptions.length === 0) {
      try {
        const response = await axios.get('http://127.0.0.1:8000/getCorsoLaurea');
        const nomi = response.data.nomi.map((entry) =>
          Array.isArray(entry) ? entry[0] : entry
        );
        console.log('[GET getCorsoLaurea] response.data:', nomi);
        setLaureaOptions(nomi);
      } catch (error) {
        console.error('[GET getCorsoLaurea] error:', error);
      }
    }
  };

  // helper per chiamare la POST getEdizione e aggiornare editionOptions
  const getEdizioni = async (corso) => {
    console.log('[POST getEdizione] payload:', { nomeCorso: corso });
    try {
      const response = await axios.post(
        'http://127.0.0.1:8000/getEdizione',
        { nomeCorso: corso }
      );
      console.log('[POST getEdizione] response.data:', response.data);
      // ogni record è [nome, data, id] → trasformiamo in oggetti con id e label
      setEditionOptions(
        response.data.edizioni.map((e) =>
          Array.isArray(e)
            ? { id: e[2], label: `${e[0]} - ${e[1]}` }
            : { id: e, label: e }
        )
      );
    } catch (error) {
      console.error('[POST getEdizione] error:', error);
    }
  };

  // helper per chiamare la POST getCorso e aggiornare courseOptions
  const getCorsi = async (nomeCorso) => {
    try {
      const response = await axios.post(
        'http://127.0.0.1:8000/getCorso',
        { nomeCorso }
      );
      console.log('[POST getCorso] response.data:', response.data);
      setCourseOptions(response.data.nomi);
      setSelectedCourse('');
      setEditionOptions([]);
      setSelectedEdition('');
    } catch (error) {
      console.error('[POST getCorso] error:', error);
    }
  };

  const handleLaureaChange = async (e) => {
    const laurea = e.target.value;
    setSelectedLaurea(laurea);
    // reset cascading selections
    setSelectedCourse('');
    setEditionOptions([]);
    setSelectedEdition('');
    if (!laurea) return;          // user picked the placeholder
    await getCorsi(laurea);
  };

  const handleCourseChange = async (e) => {
    const corso = e.target.value;
    setSelectedCourse(corso);
    setEditionOptions([]);
    setSelectedEdition('');
    if (!corso) return;
    await getEdizioni(corso);
  };

  const handleSearch = async () => {
    if (!selectedEdition) return;
    setHasSearched(true);
    setMaterials([]);      // reset precedente
    try {
      const response = await axios.post(
        'http://127.0.0.1:8000/getMaterials',
        { edizioneCorso: selectedEdition }
      );
      console.log('[POST getMaterials] response.data:', response.data);
      setMaterials(response.data.materiale);
    } catch (error) {
      console.error('[POST getMaterials] error:', error);
    }
  };

  return (
    <div className="h-screen flex flex-col justify-center items-center bg-white px-6 text-[#822433] space-y-8">
        <motion.div
            key="research"
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 50 }}
            transition={{ duration: 0.3 }}
            className="w-full max-w-xl px-6 pb-36 text-[#822433] space-y-6 flex flex-col justify-center items-center pt-24"
          >
            {/* Intestazione */}
            <h2 className="text-2xl font-bold pt-4 self-start">Ricerca Materiali</h2>

            {/* Select per Corso di Laurea */}
            <div className="space-y-2 w-full max-w-md">
              <label className="block font-semibold">Corso di Laurea</label>
              <select
                className="w-full border border-[#822433] rounded-md px-4 py-2 focus:outline-none text-black"
                value={selectedLaurea}
                onFocus={handleLaureaFocus}
                onChange={handleLaureaChange}
              >
                <option value="">Seleziona un Corso di Laurea</option>
                {laureaOptions.map((entry, idx) => {
                  const nome = Array.isArray(entry) ? entry[0] : entry;
                  return <option key={idx} value={nome}>{nome}</option>;
                })}
              </select>
            </div>

            {/* Select per Corso */}
            <div className="space-y-2 w-full max-w-md">
              <label className="block font-semibold">Corso</label>
              <select
                className="w-full border border-[#822433] rounded-md px-4 py-2 focus:outline-none text-black"
                value={selectedCourse}
                onChange={handleCourseChange}
                disabled={!courseOptions.length}
              >
                <option value="">Seleziona un Corso</option>
                {courseOptions.map((c, idx) => {
                  const nome = Array.isArray(c) ? c[0] : c;
                  return <option key={idx} value={nome}>{nome}</option>;
                })}
              </select>
            </div>

            {/* Select per Edizione */}
            <div className="space-y-2 w-full max-w-md">
              <label className="block font-semibold">Edizione</label>
              <select
                className="w-full border border-[#822433] rounded-md px-4 py-2 focus:outline-none text-black"
                value={selectedEdition}
                onChange={(e) => setSelectedEdition(e.target.value)}
                disabled={!editionOptions.length}
              >
                <option value="">Seleziona un'Edizione</option>
                {editionOptions.map((ed, idx) => (
                  <option key={idx} value={ed.id}>{ed.label}</option>
                ))}
              </select>
            </div>

            {/* Input per Anno + Bottone Cerca */}
            <div className="flex justify-center items-center gap-4 w-full max-w-md">
              <div className="pb-[0.3px]">
                <Button className="px-6 py-2 text-sm" onClick={handleSearch} disabled={!selectedEdition}>Cerca</Button>
              </div>
            </div>

            {hasSearched && materials.length === 0 && (
              <div className="w-full max-w-md mt-6 text-sm text-center text-gray-600">
                Nessun materiale disponibile per questa edizione.
              </div>
            )}

            {materials.length > 0 && (
              <div className="w-full max-w-md mt-6 space-y-3">
                <h3 className="font-semibold">Materiali trovati</h3>
                <ul className="list-disc list-inside text-sm">
                  {materials.map((m, idx) => {
                    const path   = m.path_file ?? m[0];
                    const tipo   = m.tipo      ?? m[1];
                    const verificato = m.verificato ?? m[2];
                    const rating = m.rating_medio ?? m[3] ?? 'n/d';
                    return (
                      <li key={idx}>
                        {path} — {tipo} — rating {rating}
                        {verificato ? ' ✅' : ''}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
          </motion.div>
        </div>
  );
}
