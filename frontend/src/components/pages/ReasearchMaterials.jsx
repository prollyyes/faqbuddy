'use client'

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Button from "../utils/Button";
import axios from "axios";

export default function ReasearchMaterials() {
  const [laureaOptions, setLaureaOptions] = useState([]);
  const [courseOptions, setCourseOptions] = useState([]);
  const [selectedLaurea, setSelectedLaurea] = useState('');
  const [editionOptions, setEditionOptions] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState('');
  const [selectedEdition, setSelectedEdition] = useState('');
  const [selectedEditionDate, setSelectedEditionDate] = useState('');
  const [materials, setMaterials] = useState([]);
  const [info, setInfo] = useState([]);
  const [reviews, setReviews] = useState([]); 
  const [hasSearched, setHasSearched] = useState(false);
  const [includeMaterials, setIncludeMaterials] = useState(true);
  const [includeInfo, setIncludeInfo] = useState(false);
  const [includeReviews, setIncludeReviews] = useState(false);

  const handleLaureaFocus = async () => {
    if (laureaOptions.length === 0) {
      try {
        const response = await axios.get('http://127.0.0.1:8000/getCorsoLaurea');
        const nomi = response.data.nomi.map((entry) =>
          Array.isArray(entry) ? entry[0] : entry
        );
        setLaureaOptions(nomi);
      } catch (error) {
        console.error('[GET getCorsoLaurea] error:', error);
      }
    }
  };

  const getEdizioni = async (corso) => {
    try {
      const response = await axios.post('http://127.0.0.1:8000/getEdizione', { nomeCorso: corso });
      setEditionOptions(
        response.data.edizioni.map((e) =>
          Array.isArray(e)
            ? { id: e[2].toString(), date: e[1], label: `${e[0]} - ${e[1]}` }
            : { id: e.toString(), date: '', label: e }
        )
      );
    } catch (error) {
      console.error('[POST getEdizione] error:', error);
    }
  };

  const getCorsi = async (nomeCorso) => {
    try {
      const response = await axios.post('http://127.0.0.1:8000/getCorso', { nomeCorso });
      setCourseOptions(response.data.nomi);
      setSelectedCourse('');
      setEditionOptions([]);
      setSelectedEdition('');
      setSelectedEditionDate('');
    } catch (error) {
      console.error('[POST getCorso] error:', error);
    }
  };

  const handleLaureaChange = async (e) => {
    const laurea = e.target.value;
    setSelectedLaurea(laurea);
    setSelectedCourse('');
    setEditionOptions([]);
    setSelectedEdition('');
    setSelectedEditionDate('');
    setMaterials([]);
    setInfo([]);
    setReviews([]);   
    setHasSearched(false);
    if (!laurea) return;
    await getCorsi(laurea);
  };

  const handleCourseChange = async (e) => {
    const corso = e.target.value;
    setSelectedCourse(corso);
    setEditionOptions([]);
    setSelectedEdition('');
    setSelectedEditionDate('');
    setMaterials([]);
    setInfo([]);
    setReviews([]); 
    setHasSearched(false);
    if (!corso) return;
    await getEdizioni(corso);
  };

  const handleSearch = async () => {
    if (!selectedEdition) return;
    if (!includeMaterials && !includeInfo && !includeReviews) return;
    setHasSearched(true);
    setMaterials([]);
    setInfo([]);
    setReviews([]);
    try {
      const payload =
        selectedEdition === 'all'
          ? { edizioneCorso: 'all', nomeCorso: selectedCourse }
          : {
              edizioneCorso: selectedEdition,
              dataEdizione: selectedEditionDate,
              nomeCorso: selectedCourse
            };

      const requests = [];
      if (includeMaterials) {
        requests.push(axios.post('http://127.0.0.1:8000/getMaterials', payload));
      }
      if (includeInfo) {
        requests.push(axios.post('http://127.0.0.1:8000/getInfoCorso', payload));
      }
      if (includeReviews) {
        requests.push(axios.post('http://127.0.0.1:8000/getReview', payload));
      }

      const responses = await Promise.all(requests);
      let collectedMaterials = [], collectedInfo = [], collectedReviews = [];
      responses.forEach((res) => {
        const url = res.config.url;
        if (url.includes('getMaterials')) {
          collectedMaterials = res.data.materiale;
        } else if (url.includes('getInfoCorso')) {
          collectedInfo = res.data.materiale;
        } else if (url.includes('getReview')) {
          collectedReviews = res.data.materiale;
        }
      });
      setMaterials(collectedMaterials);
      setInfo(collectedInfo);
      setReviews(collectedReviews);
    } catch (error) {
      console.error('[POST getMaterials/getInfoCorso/getReview] error:', error);
    }
  };

  // useEffect per eseguire automaticamente la ricerca se i parametri cambiano dopo la prima chiamata
  useEffect(() => {
    if (hasSearched && selectedEdition) {
      handleSearch();
    }
  }, [selectedCourse, selectedEdition, selectedEditionDate, includeMaterials, includeInfo, includeReviews]);

  return (
    <div className="min-h-screen flex flex-col justify-center items-center bg-white px-6 text-[#822433] space-y-8 pt-10 pb-15">
      <motion.div
        key="research"
        initial={{ opacity: 0, x: -50 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 50 }}
        transition={{ duration: 0.3 }}
        className="w-full max-w-xl px-6 pb-36 text-[#822433] space-y-6 flex flex-col justify-center items-center pt-24"
      >
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
            value={selectedEdition === "all" ? "all" : (selectedEdition && selectedEditionDate ? `${selectedEdition}|${selectedEditionDate}` : '')}
            onChange={(e) => {
              const selVal = e.target.value;
              if (selVal === "all") {
                setSelectedEdition("all");
                setSelectedEditionDate('');
              } else {
                const [id, date] = selVal.split('|');
                setSelectedEdition(id);
                setSelectedEditionDate(date);
              }
            }}
            disabled={!editionOptions.length}
          >
            <option value="">Seleziona un'Edizione</option>
            <option value="all">Tutte le edizioni</option>
            {editionOptions.map((ed, idx) => (
              <option key={idx} value={`${ed.id}|${ed.date}`}>{ed.date}</option>
            ))}
          </select>
        </div>
        {/* Filtri di Ricerca */}
        <div className="space-y-2 w-full max-w-md">
          <label className="block font-semibold">Filtri di Ricerca</label>
          <div className="flex gap-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                className="mr-2"
                checked={includeMaterials}
                onChange={() => setIncludeMaterials(!includeMaterials)}
              />
              Materiali
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                className="mr-2"
                checked={includeInfo}
                onChange={() => setIncludeInfo(!includeInfo)}
              />
              Informazioni
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                className="mr-2"
                checked={includeReviews}
                onChange={() => setIncludeReviews(!includeReviews)}
              />
              Review
            </label>
          </div>
        </div>
        {/* Bottone Cerca */}
        <div className="flex justify-center items-center gap-4 w-full max-w-md">
          <div className="pb-[0.3px]">
            <Button className="px-6 py-2 text-sm" onClick={handleSearch} disabled={!selectedEdition}>Cerca</Button>
          </div>
        </div>
        {/* Sezione Materiali */}
        {includeMaterials && materials.length > 0 && (
          <div className="w-full max-w-md mt-6 space-y-3">
            <h3 className="font-semibold text-lg border-b pb-1">Materiali trovati</h3>
            {materials.map((m, idx) => {
              const path = m.path_file ?? m[0];
              const tipo = m.tipo ?? m[1];
              const rating = m.rating_medio ?? m[3] ?? 'n/d';
              const verificato = m.verificato ?? m[2];
              return (
                <div key={idx} className="border rounded-md p-3 text-sm space-y-1 bg-gray-50">
                  <div><strong>File:</strong> {path}</div>
                  <div><strong>Tipo:</strong> {tipo}</div>
                  <div><strong>Rating:</strong> {rating}</div>
                  <div><strong>Verificato:</strong> {verificato ? "✅" : "❌"}</div>
                </div>
              );
            })}
          </div>
        )}
        {includeMaterials && materials.length === 0 && hasSearched && (
          <div className="w-full max-w-md mt-6 text-sm text-center text-gray-600">
            Nessun materiale disponibile per questa edizione.
          </div>
        )}
        {/* Sezione Informazioni */}
        {includeInfo && info.length > 0 && (
          <div className="w-full max-w-md mt-6 space-y-3">
            <h3 className="font-semibold text-lg border-b pb-1">Informazioni corso</h3>
            {info.map((i, idx) => {
              const record = Array.isArray(i) ? i : Object.values(i);
              return (
                <div key={idx} className="border rounded-md p-3 text-sm space-y-1 bg-gray-50">
                  <div className="text-xl font-bold"><strong></strong> {record[0]}</div>
                  <div className="font-bold"><strong></strong> {record[1]}</div>
                  <div><strong>Insegnante:</strong> {record[2]+" "+record[3]}</div>
                  <div><strong>Mail:</strong> {record[4] ? record[4] : "Non disponibile"}</div>
                  <div><strong>CFU:</strong> {record[5]}</div>
                  <div><strong>Idoneità:</strong> {record[6] ? "✅" : "❌"}</div>
                  <div><strong>Orario:</strong> {record[7] ? record[7]:"Non disponibile"}</div>
                  <div><strong>Esonero:</strong> {record[8] ? "✅" : "❌"}</div>
                  <div><strong>Modalità d'esame:</strong> {record[9]}</div>
                  <div><strong>Prerequisiti:</strong> {record[10] ? record[10]:"Non disponibile"}</div>
                  <div><strong>Frequenza obbligatoria:</strong> {(record[11]|| "").toLowerCase() ==="no" ? "❌": "✅"}</div>
                </div>
              );
            })}
          </div>
        )}
        {includeInfo && info.length === 0 && hasSearched && (
          <div className="w-full max-w-md mt-6 text-sm text-center text-gray-600">
            Nessuna informazione disponibile per questa edizione.
          </div>
        )}
        {/* Sezione Review */}
        {includeReviews && reviews.length > 0 && (
          <div className="w-full max-w-md mt-6 space-y-3">
            <h3 className="font-semibold text-lg border-b pb-1">Review</h3>
            {reviews.map((r, idx) => {
              // Presupponiamo che ogni record sia un array [descrizione, voto]
              const descrizione = r.descrizione ?? r[0];
              const voto = r.voto ?? r[1];
              return (
                <div key={idx} className="border rounded-md p-3 text-sm space-y-1 bg-gray-50">
                  <div><strong>Commento:</strong> {descrizione}</div>
                  <div><strong>Voto:</strong> {voto}</div>
                </div>
              );
            })}
          </div>
        )}
        {includeReviews && reviews.length === 0 && hasSearched && (
          <div className="w-full max-w-md mt-6 text-sm text-center text-gray-600">
            Nessuna review disponibile per questa edizione.
          </div>
        )}
      </motion.div>
    </div>
  );
}