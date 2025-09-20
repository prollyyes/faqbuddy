'use client'

import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { FaStar } from 'react-icons/fa';
import Button from '@/components/utils/Button';
import MobileSheet from '@/components/utils/MobileSheet';

const HOST = process.env.NEXT_PUBLIC_HOST;

export default function ReasearchMaterials() {
  const [laureaOptions, setLaureaOptions] = useState([]);
  const [courseOptions, setCourseOptions] = useState([]);
  const [editionOptions, setEditionOptions] = useState([]);

  const [selectedLaurea, setSelectedLaurea] = useState('');
  const [selectedCourse, setSelectedCourse] = useState('');
  const [selectedEdition, setSelectedEdition] = useState('');
  const [selectedEditionDate, setSelectedEditionDate] = useState('');

  const [includeMaterials, setIncludeMaterials] = useState(true);
  const [includeInfo, setIncludeInfo] = useState(false);
  const [includeReviews, setIncludeReviews] = useState(false);

  const [materials, setMaterials] = useState([]);
  const [info, setInfo] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);

  const [sheetOpen, setSheetOpen] = useState(false);
  const [sheetPayload, setSheetPayload] = useState(null);

  const activeFilters = useMemo(
    () => [
      includeMaterials ? 'materiali' : null,
      includeInfo ? 'info' : null,
      includeReviews ? 'review' : null,
    ].filter(Boolean),
    [includeMaterials, includeInfo, includeReviews]
  );

  const handleLaureaFocus = async () => {
    if (laureaOptions.length) return;
    try {
      const res = await axios.get(`${HOST}/getCorsoLaurea`);
      const options = res.data.nomi.map(entry => (Array.isArray(entry) ? entry[0] : entry));
      setLaureaOptions(options);
    } catch (error) {
      console.error('[GET getCorsoLaurea] error:', error);
    }
  };

  const loadCourses = async (nomeCorso) => {
    try {
      const res = await axios.post(`${HOST}/getCorso`, { nomeCorso });
      setCourseOptions(res.data.nomi);
      setEditionOptions([]);
    } catch (error) {
      console.error('[POST getCorso] error:', error);
    }
  };

  const loadEditions = async (course) => {
    try {
      const res = await axios.post(`${HOST}/getEdizione`, { nomeCorso: course });
      setEditionOptions(
        res.data.edizioni.map((e) =>
          Array.isArray(e)
            ? { id: e[2].toString(), date: e[1], label: `${e[0]} - ${e[1]}` }
            : { id: e.toString(), date: '', label: e }
        )
      );
    } catch (error) {
      console.error('[POST getEdizione] error:', error);
    }
  };

  const resetResults = () => {
    setMaterials([]);
    setInfo([]);
    setReviews([]);
    setHasSearched(false);
  };

  const handleLaureaChange = async (event) => {
    const value = event.target.value;
    setSelectedLaurea(value);
    setSelectedCourse('');
    setSelectedEdition('');
    setSelectedEditionDate('');
    setCourseOptions([]);
    setEditionOptions([]);
    resetResults();
    if (value) await loadCourses(value);
  };

  const handleCourseChange = async (event) => {
    const value = event.target.value;
    setSelectedCourse(value);
    setSelectedEdition('');
    setSelectedEditionDate('');
    setEditionOptions([]);
    resetResults();
    if (value) await loadEditions(value);
  };

  const handleEditionChange = (event) => {
    const value = event.target.value;
    if (value === 'all') {
      setSelectedEdition('all');
      setSelectedEditionDate('');
    } else if (value) {
      const [id, date] = value.split('|');
      setSelectedEdition(id);
      setSelectedEditionDate(date);
    } else {
      setSelectedEdition('');
      setSelectedEditionDate('');
    }
    resetResults();
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
              nomeCorso: selectedCourse,
            };

      const requests = [];
      if (includeMaterials) requests.push(axios.post(`${HOST}/getMaterials`, payload));
      if (includeInfo) requests.push(axios.post(`${HOST}/getInfoCorso`, payload));
      if (includeReviews) requests.push(axios.post(`${HOST}/getReview`, payload));

      const responses = await Promise.all(requests);
      responses.forEach((res) => {
        const url = res.config.url;
        if (url.includes('getMaterials')) {
          setMaterials(res.data.materiale);
        } else if (url.includes('getInfoCorso')) {
          setInfo(res.data.materiale);
        } else if (url.includes('getReview')) {
          setReviews(res.data.materiale);
        }
      });
    } catch (error) {
      console.error('[POST search endpoints] error:', error);
    }
  };

  useEffect(() => {
    if (!hasSearched || !selectedEdition) return;
    handleSearch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCourse, selectedEdition, selectedEditionDate, includeMaterials, includeInfo, includeReviews]);

  const handleOpenSheet = (payload) => {
    setSheetPayload(payload);
    setSheetOpen(true);
  };

  const handleCloseSheet = () => {
    setSheetOpen(false);
    setTimeout(() => setSheetPayload(null), 240);
  };

  const sheetTitle = useMemo(() => {
    if (!sheetPayload) return '';
    switch (sheetPayload.type) {
      case 'materiale':
        return 'Materiale';
      case 'info':
        return 'Info corso';
      case 'review':
        return 'Review';
      default:
        return '';
    }
  }, [sheetPayload]);

  const renderSheetContent = () => {
    if (!sheetPayload) return null;

    if (sheetPayload.type === 'materiale') {
      const { path, tipo, rating, verificato } = sheetPayload;
      return (
        <div className="space-y-3 text-sm text-[#822433]">
          <p className="text-base font-semibold break-all">{path}</p>
          <ul className="space-y-1">
            <li>Tipo: <span className="font-medium">{tipo}</span></li>
            <li>Rating: <span className="font-medium">{rating ?? 'n/d'}</span></li>
            <li>Verificato: <span className="font-medium">{verificato ? 'sì' : 'no'}</span></li>
          </ul>
        </div>
      );
    }

    if (sheetPayload.type === 'info') {
      const {
        titolo,
        categoria,
        docenteNome,
        docenteCognome,
        email,
        cfu,
        idoneita,
        orario,
        esonero,
        modalitaEsame,
        prerequisiti,
        frequenza,
      } = sheetPayload;
      return (
        <div className="space-y-3 text-sm text-[#822433]">
          <p className="text-base font-semibold">{titolo}</p>
          <ul className="space-y-1">
            <li>Categoria: <span className="font-medium">{categoria || '—'}</span></li>
            <li>Docente: <span className="font-medium">{`${docenteNome ?? ''} ${docenteCognome ?? ''}`.trim() || '—'}</span></li>
            <li>Email: <span className="font-medium break-all">{email || '—'}</span></li>
            <li>CFU: <span className="font-medium">{cfu ?? '—'}</span></li>
            <li>Idoneità: <span className="font-medium">{idoneita ? 'sì' : 'no'}</span></li>
            <li>Orario: <span className="font-medium">{orario || '—'}</span></li>
            <li>Esonero: <span className="font-medium">{esonero ? 'sì' : 'no'}</span></li>
            <li>Esame: <span className="font-medium">{modalitaEsame || '—'}</span></li>
            <li>Prerequisiti: <span className="font-medium">{prerequisiti || '—'}</span></li>
            <li>Frequenza obbligatoria: <span className="font-medium">{(frequenza || '').toLowerCase() === 'no' ? 'no' : 'sì'}</span></li>
          </ul>
        </div>
      );
    }

    if (sheetPayload.type === 'review') {
      const { descrizione, voto } = sheetPayload;
      return (
        <div className="space-y-3 text-sm text-[#822433]">
          <p className="text-base font-semibold leading-snug">{descrizione}</p>
          <div className="flex items-center gap-1 text-[#991B1B]">
            {[...Array(Number(voto))].map((_, idx) => (
              <FaStar key={idx} size={16} />
            ))}
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="min-h-screen bg-white text-[#822433]">
      <motion.div
        key="materials-search"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
        className="mx-auto w-full max-w-md px-4 pb-28 pt-20 space-y-8"
      >
        <header className="space-y-1">
          <h1 className="text-2xl font-semibold">Ricerca materiali</h1>
          <p className="text-sm text-[#a25966]">Completa i campi, scegli i filtri e avvia.</p>
        </header>

        <section className="space-y-4 rounded-2xl border border-[#f0d6db] bg-white px-4 py-5 shadow-sm">
          <div className="space-y-3">
            <select
              className="w-full rounded-xl border border-[#f0d6db] bg-white px-3 py-2 text-black focus:outline-none focus:ring-2 focus:ring-[#c85a71]/40"
              value={selectedLaurea}
              onFocus={handleLaureaFocus}
              onChange={handleLaureaChange}
            >
              <option value="">Corso di laurea</option>
              {laureaOptions.map((entry, idx) => {
                const nome = Array.isArray(entry) ? entry[0] : entry;
                return (
                  <option key={idx} value={nome}>
                    {nome}
                  </option>
                );
              })}
            </select>
            <select
              className="w-full rounded-xl border border-[#f0d6db] bg-white px-3 py-2 text-black focus:outline-none focus:ring-2 focus:ring-[#c85a71]/40"
              value={selectedCourse}
              onChange={handleCourseChange}
              disabled={!courseOptions.length}
            >
              <option value="">Corso</option>
              {courseOptions.map((c, idx) => {
                const nome = Array.isArray(c) ? c[0] : c;
                return (
                  <option key={idx} value={nome}>
                    {nome}
                  </option>
                );
              })}
            </select>
            <select
              className="w-full rounded-xl border border-[#f0d6db] bg-white px-3 py-2 text-black focus:outline-none focus:ring-2 focus:ring-[#c85a71]/40"
              value={
                selectedEdition === 'all'
                  ? 'all'
                  : selectedEdition && selectedEditionDate
                  ? `${selectedEdition}|${selectedEditionDate}`
                  : ''
              }
              onChange={handleEditionChange}
              disabled={!editionOptions.length}
            >
              <option value="">Edizione</option>
              <option value="all">Tutte</option>
              {editionOptions.map((ed, idx) => (
                <option key={idx} value={`${ed.id}|${ed.date}`}>
                  {ed.date}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-wrap gap-2">
            {[
              ['Materiali', includeMaterials, setIncludeMaterials],
              ['Info', includeInfo, setIncludeInfo],
              ['Review', includeReviews, setIncludeReviews],
            ].map(([label, active, setter]) => (
              <button
                key={label}
                type="button"
                onClick={() => setter(!active)}
                className={`px-3 py-2 text-xs rounded-full border transition ${
                  active ? 'bg-[#822433] text-white border-transparent' : 'border-[#f0d6db] text-[#822433]'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <div className="space-y-2 text-xs text-[#a25966]">
            {selectedCourse ? (
              <p>{selectedCourse} · {selectedEdition === 'all' ? 'tutte le edizioni' : selectedEditionDate || '—'} · {activeFilters.length ? activeFilters.join(', ') : 'nessun filtro'}</p>
            ) : (
              <p>Compila i campi per abilitare la ricerca.</p>
            )}
            <Button onClick={handleSearch} disabled={!selectedEdition} className="w-full py-3 text-sm">
              Cerca
            </Button>
          </div>
        </section>

        <section className="space-y-8">
          {includeMaterials && (
            <article className="space-y-3">
              <h2 className="text-lg font-semibold">Materiali</h2>
              {materials.length > 0 ? (
                <div className="space-y-2">
                  {materials.map((m, idx) => {
                    const path = m.path_file ?? m[0];
                    const tipo = m.tipo ?? m[1];
                    const rating = m.rating_medio ?? m[3] ?? 'n/d';
                    const verificato = m.verificato ?? m[2];
                    return (
                      <button
                        key={idx}
                        className="w-full text-left rounded-xl border border-[#f0d6db] bg-white px-4 py-3 shadow-sm hover:shadow-md transition active:scale-[0.99]"
                        onClick={() => handleOpenSheet({ type: 'materiale', path, tipo, rating, verificato })}
                      >
                        <p className="text-sm font-semibold break-all line-clamp-2">{path}</p>
                        <div className="mt-2 flex items-center justify-between text-xs text-[#a25966]">
                          <span>{tipo}</span>
                          <span>{verificato ? 'verificato ✅' : 'non verificato'}</span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              ) : hasSearched ? (
                <p className="text-sm text-[#a25966]">Nessun materiale trovato.</p>
              ) : (
                <p className="text-sm text-[#a25966]">Imposta i filtri e premi Cerca.</p>
              )}
            </article>
          )}

          {includeInfo && (
            <article className="space-y-3">
              <h2 className="text-lg font-semibold">Informazioni corso</h2>
              {info.length > 0 ? (
                <div className="space-y-2">
                  {info.map((i, idx) => {
                    const record = Array.isArray(i) ? i : Object.values(i);
                    const payload = {
                      type: 'info',
                      titolo: record[0],
                      categoria: record[1],
                      docenteNome: record[2],
                      docenteCognome: record[3],
                      email: record[4],
                      cfu: record[5],
                      idoneita: record[6],
                      orario: record[7],
                      esonero: record[8],
                      modalitaEsame: record[9],
                      prerequisiti: record[10],
                      frequenza: record[11],
                    };
                    return (
                      <button
                        key={idx}
                        className="w-full text-left rounded-xl border border-[#f0d6db] bg-white px-4 py-3 shadow-sm hover:shadow-md transition active:scale-[0.99]"
                        onClick={() => handleOpenSheet(payload)}
                      >
                        <p className="text-sm font-semibold">{payload.titolo}</p>
                        <p className="mt-2 text-xs text-[#a25966]">
                          {payload.docenteNome || payload.docenteCognome
                            ? `${payload.docenteNome ?? ''} ${payload.docenteCognome ?? ''}`
                            : 'Docente non disponibile'}
                        </p>
                      </button>
                    );
                  })}
                </div>
              ) : hasSearched ? (
                <p className="text-sm text-[#a25966]">Nessuna informazione trovata.</p>
              ) : (
                <p className="text-sm text-[#a25966]">Esegui una ricerca per vedere i dati.</p>
              )}
            </article>
          )}

          {includeReviews && (
            <article className="space-y-3">
              <h2 className="text-lg font-semibold">Review</h2>
              {reviews.length > 0 ? (
                <div className="space-y-2">
                  {reviews.map((r, idx) => {
                    const descrizione = r.descrizione ?? r[0];
                    const voto = r.voto ?? r[1];
                    return (
                      <button
                        key={idx}
                        className="w-full text-left rounded-xl border border-[#f0d6db] bg-white px-4 py-3 shadow-sm hover:shadow-md transition active:scale-[0.99]"
                        onClick={() => handleOpenSheet({ type: 'review', descrizione, voto })}
                      >
                        <p className="text-sm font-semibold line-clamp-3">{descrizione}</p>
                        <div className="mt-2 flex items-center gap-1 text-xs text-[#a25966]">
                          {[...Array(Number(voto))].map((_, idxStar) => (
                            <FaStar key={idxStar} color="#991B1B" size={14} />
                          ))}
                        </div>
                      </button>
                    );
                  })}
                </div>
              ) : hasSearched ? (
                <p className="text-sm text-[#a25966]">Nessuna review trovata.</p>
              ) : (
                <p className="text-sm text-[#a25966]">Attiva il filtro Review e cerca.</p>
              )}
            </article>
          )}
        </section>
      </motion.div>

      {sheetPayload && (
        <MobileSheet open={sheetOpen} onClose={handleCloseSheet} title={sheetTitle}>
          <div className="space-y-6">
            {renderSheetContent()}
            <div className="flex justify-end">
              <button
                onClick={handleCloseSheet}
                className="px-4 py-2 bg-[#822433] text-white rounded-lg"
              >
                Chiudi
              </button>
            </div>
          </div>
        </MobileSheet>
      )}
    </div>
  );
}
