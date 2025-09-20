'use client'

import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { FaStar } from 'react-icons/fa';
import { IoMdDownload } from "react-icons/io";
import { BsEyeglasses } from "react-icons/bs";
import Button from '@/components/utils/Button';
import MobileSheet from '@/components/utils/MobileSheet';
import { ReviewsPreview, MaterialsPreview, InfoPreview } from './Preview';

const HOST = process.env.NEXT_PUBLIC_HOST;

function SelectField({ value, onChange, onFocus, disabled, placeholder, options }) {
  return (
    <select
      className="w-full rounded-xl border border-[#f0d6db] bg-white px-3 py-2 text-black focus:outline-none focus:ring-2 focus:ring-[#c85a71]/40"
      value={value}
      onChange={onChange}
      onFocus={onFocus}
      disabled={disabled}
    >
      <option value="">{placeholder}</option>
      {options.map((option, idx) => (
        <option key={idx} value={option}>
          {option}
        </option>
      ))}
    </select>
  );
}

function FilterChips({ includeMaterials, includeInfo, includeReviews, onToggleMaterials, onToggleInfo, onToggleReviews }) {
  return (
    <div className="flex flex-wrap gap-2 justify-center">
      {[
        ['Materiali', includeMaterials, onToggleMaterials],
        ['Info', includeInfo, onToggleInfo],
        ['Review', includeReviews, onToggleReviews],
      ].map(([label, active, handler]) => (
        <button
          key={label}
          type="button"
          onClick={handler}
          className={`px-3 py-2 text-xs rounded-full border transition ${active ? 'bg-[#822433] text-white border-transparent' : 'border-[#f0d6db] text-[#822433]'}`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

function FilterPanel({
  laureaOptions,
  courseOptions,
  editionOptions,
  selectedLaurea,
  selectedCourse,
  selectedEdition,
  selectedEditionDate,
  onLaureaFocus,
  onLaureaChange,
  onCourseChange,
  onEditionChange,
  includeMaterials,
  includeInfo,
  includeReviews,
  onToggleMaterials,
  onToggleInfo,
  onToggleReviews,
  summary,
  canSearch,
  onSearch,
}) {
  return (
    <section className="space-y-4 rounded-2xl border border-[#f0d6db] bg-white px-4 py-5 shadow-sm">
      <div className="space-y-3">
        <SelectField
          value={selectedLaurea}
          onChange={onLaureaChange}
          onFocus={onLaureaFocus}
          disabled={false}
          placeholder="Corso di laurea"
          options={laureaOptions}
        />
        <SelectField
          value={selectedCourse}
          onChange={onCourseChange}
          placeholder="Corso"
          options={courseOptions}
          disabled={!courseOptions.length}
        />
        <select
          className="w-full rounded-xl border border-[#f0d6db] bg-white px-3 py-2 text-black focus:outline-none focus:ring-2 focus:ring-[#c85a71]/40"
          value={
            selectedEdition === 'all'
              ? 'all'
              : selectedEdition && selectedEditionDate
              ? `${selectedEdition}|${selectedEditionDate}`
              : ''
          }
          onChange={onEditionChange}
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

      <FilterChips
        includeMaterials={includeMaterials}
        includeInfo={includeInfo}
        includeReviews={includeReviews}
        onToggleMaterials={onToggleMaterials}
        onToggleInfo={onToggleInfo}
        onToggleReviews={onToggleReviews}
      />

      <div className="space-y-2 text-xs text-[#a25966]">
        {/* <p>{summary}</p> */}
        <Button onClick={onSearch} disabled={!canSearch} className="w-full py-3 text-sm">
          Cerca
        </Button>
      </div>
    </section>
  );
}

export default function ReasearchMaterials() {
  const [laureaOptions, setLaureaOptions] = useState([]);
  const [courseOptions, setCourseOptions] = useState([]);
  const [editionOptions, setEditionOptions] = useState([]);

  const [selectedLaurea, setSelectedLaurea] = useState('');
  const [selectedCourse, setSelectedCourse] = useState('');
  const [selectedEdition, setSelectedEdition] = useState('');
  const [selectedEditionDate, setSelectedEditionDate] = useState('');

  const [includeMaterials, setIncludeMaterials] = useState(true);
  const [includeInfo, setIncludeInfo] = useState(true);
  const [includeReviews, setIncludeReviews] = useState(true);

  const [materials, setMaterials] = useState([]);
  const [info, setInfo] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);

  const [sheetOpen, setSheetOpen] = useState(false);
  const [sheetPayload, setSheetPayload] = useState(null);
  const [sectionFilter, setSectionFilter] = useState('materials');

  const activeFilters = useMemo(
    () => [
      includeMaterials ? 'materiali' : null,
      includeInfo ? 'info' : null,
      includeReviews ? 'review' : null,
    ].filter(Boolean),
    [includeMaterials, includeInfo, includeReviews]
  );

  const courseOptionLabels = useMemo(
    () => courseOptions.map((c) => (Array.isArray(c) ? c[0] : c)),
    [courseOptions]
  );

  const fallbackCourseName = selectedCourse || null;
  const fallbackEditionLabel = selectedEdition === 'all' ? null : selectedEditionDate;

  const buildMaterialData = (item, fallbackCourse, fallbackEdition, index) => {
    const path = item.path_file ?? item[0];
    const tipo = item.tipo ?? item[1];
    const rating = item.rating_medio ?? item[3] ?? 'n/d';
    const verificato = item.verificato ?? item[2];
    const editionFromItem = item.edition_data ?? item[4];
    const courseFromItem = item.nome ?? item.course_name ?? item[5];
    const editionText = editionFromItem || fallbackEdition || 'edizione';
    const courseText = courseFromItem || fallbackCourse || 'corso';
    const displayName = `${tipo || 'Materiale'} · ${courseText} (${editionText})`;
    return { path, tipo, rating, verificato, edition: editionText, course: courseText, displayName, index };
  };

  const handleLaureaFocus = async () => {
    if (laureaOptions.length) return;
    try {
      const res = await axios.get(`${HOST}/getCorsoLaurea`);
      const options = res.data.nomi.map((entry) => (Array.isArray(entry) ? entry[0] : entry));
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

  const openSheet = (payload) => {
    setSheetPayload(payload);
    setSheetOpen(true);
  };

  useEffect(() => {
    if (sectionFilter === 'materials' && !includeMaterials) setSectionFilter('all');
    if (sectionFilter === 'info' && !includeInfo) setSectionFilter('all');
    if (sectionFilter === 'review' && !includeReviews) setSectionFilter('all');
  }, [includeMaterials, includeInfo, includeReviews, sectionFilter]);

  const closeSheet = () => {
    setSheetOpen(false);
    setTimeout(() => setSheetPayload(null), 240);
  };

  const sheetTitle = useMemo(() => {
    if (!sheetPayload) return '';
    if (sheetPayload.mode === 'list') {
      switch (sheetPayload.type) {
        case 'materiali':
          return 'Tutti i materiali';
        case 'info':
          return 'Tutte le info corso';
        case 'review':
          return 'Tutte le review';
        default:
          return '';
      }
    }
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

    if (sheetPayload.mode === 'list') {
      const { type, items } = sheetPayload;
      if (type === 'materiali') {
        const fallbackCourse = sheetPayload.fallbackCourse ?? fallbackCourseName;
        const fallbackEdition = sheetPayload.fallbackEdition ?? fallbackEditionLabel;
        return (
          <div className="space-y-2">
            {items.map((item, idx) => {
              const data = buildMaterialData(item, fallbackCourse, fallbackEdition, idx);
              return (
                <button
                  key={idx}
                  className="w-full text-left rounded-lg border border-[#f0d6db] bg-white px-3 py-3 text-sm text-[#822433]"
                  onClick={() => openSheet({ mode: 'item', type: 'materiale', data })}
                >
                  <p className="font-semibold break-all line-clamp-2">{data.displayName}</p>
                  <div className="mt-1 flex items-center justify-between text-xs text-[#a25966]">
                    <span>{data.tipo}</span>
                    <span>Rating {data.rating}</span>
                  </div>
                </button>
              );
            })}
          </div>
        );
      }
      if (type === 'info') {
        return (
          <div className="space-y-2 text-sm text-[#822433]">
            {items.map((record, idx) => {
              const data = Array.isArray(record) ? record : Object.values(record);
              const payload = {
                mode: 'item',
                type: 'info',
                data: {
                  titolo: data[0],
                  categoria: data[1],
                  docenteNome: data[2],
                  docenteCognome: data[3],
                  email: data[4],
                  cfu: data[5],
                  idoneita: data[6],
                  orario: data[7],
                  esonero: data[8],
                  modalitaEsame: data[9],
                  prerequisiti: data[10],
                  frequenza: data[11],
                },
              };
              return (
                <button
                  key={idx}
                  className="w-full text-left rounded-lg border border-[#f0d6db] bg-white px-3 py-3"
                  onClick={() => openSheet(payload)}
                >
                  <p className="font-semibold">{data[0]}</p>
                  <p className="text-xs text-[#a25966]">{data[2] || data[3] ? `${data[2] ?? ''} ${data[3] ?? ''}`.trim() : 'Docente non disponibile'}</p>
                </button>
              );
            })}
          </div>
        );
      }
      if (type === 'review') {
        return (
          <div className="space-y-2 text-sm text-[#822433]">
            {items.map((r, idx) => {
              const descrizione = r.descrizione ?? r[0];
              const voto = r.voto ?? r[1];
              return (
                <button
                  key={idx}
                  className="w-full text-left rounded-lg border border-[#f0d6db] bg-white px-3 py-3"
                  onClick={() => openSheet({ mode: 'item', type: 'review', data: { descrizione, voto } })}
                >
                  <p className="font-semibold line-clamp-3">{descrizione}</p>
                  <div className="mt-1 flex gap-1 text-[#991B1B]">
                    {[...Array(Number(voto))].map((_, starIdx) => (
                      <FaStar key={starIdx} size={14} />
                    ))}
                  </div>
                </button>
              );
            })}
          </div>
        );
      }
    }

    // Quando apro la Modale mobile per un singolo elemento, faccio un check del tipo e creo la modale di conseguenza
    if (sheetPayload.mode === 'item') {
      if (sheetPayload.type === 'materiale') {
        const { data } = sheetPayload;
        return (
          <div className="space-y-3 text-sm text-[#822433]">
            <p className="text-base font-semibold break-all">{data.displayName}</p>
            <ul className="space-y-1">
              <li>Tipo: <span className="font-medium">{data.tipo}</span></li>
              <li>Rating: <span className="font-medium">{data.rating ?? 'n/d'}</span></li>
              <li>Verificato: <span className="font-medium">{data.verificato ? 'sì' : 'no'}</span></li>
              <li>Corso: <span className="font-medium">{data.course}</span></li>
              <li>Edizione: <span className="font-medium">{data.edition}</span></li>
            </ul>
            
            {/* Download materiale */}
            {/* Lo posso anche scaricare dopo la visualizzazione */}
            {/* <a
              href={`https://drive.google.com/uc?export=download&id=${data.path}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center w-11 h-11 rounded-full bg-[#822433] text-white text-2xl mt-2 shadow hover:bg-[#a25966] transition"
              download
              title="Scarica materiale"
            >
              <IoMdDownload />
            </a> */}
              {/* Visualizzazione rapida */}
            <a
              href={`https://drive.google.com/file/d/${data.path}/view`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center w-11 h-11 rounded-full bg-[#822433] text-white text-2xl shadow hover:bg-[#822433] transition"
              title="Visualizza materiale"
            >
              <IoMdDownload />
            </a>
          </div>
        );
      }
      if (sheetPayload.type === 'info') {
        const { data } = sheetPayload;
        return (
          <div className="space-y-3 text-sm text-[#822433]">
            <p className="text-base font-semibold">
              {data.nomeCorso} <span className="text-xs text-[#a25966]">({data.edizione})</span>
            </p>
            <ul className="space-y-1">
              <li>Docente: <span className="font-medium">{`${data.docenteNome ?? ''} ${data.docenteCognome ?? ''}`.trim() || '—'}</span></li>
              <li>Email: <span className="font-medium break-all">{data.email || '—'}</span></li>
              <li>CFU: <span className="font-medium">{data.cfu ?? '—'}</span></li>
              <li>Idoneità: <span className="font-medium">{data.idoneita ? 'sì' : 'no'}</span></li>
              <li>Orario: <span className="font-medium">{data.orario || '—'}</span></li>
              <li>Esonero: <span className="font-medium">{data.esonero ? 'sì' : 'no'}</span></li>
              <li>Esame: <span className="font-medium">{data.modalitaEsame || '—'}</span></li>
              <li>Prerequisiti: <span className="font-medium">{data.prerequisiti || '—'}</span></li>
              <li>Frequenza obbligatoria: <span className="font-medium">{(data.frequenza || '').toLowerCase() === 'no' ? 'no' : 'sì'}</span></li>
            </ul>
          </div>
        );
      }
      if (sheetPayload.type === 'review') {
        const { data } = sheetPayload;
        return (
          <div className="space-y-3 text-sm text-[#822433]">
            <p className="text-base font-semibold leading-snug">{data.descrizione}</p>
            <div className="flex items-center gap-1 text-[#991B1B]">
              {[...Array(Number(data.voto))].map((_, idx) => (
                <FaStar key={idx} size={16} />
              ))}
            </div>
          </div>
        );
      }
    }

    return null;
  };

  return (
    <div className="min-h-screen bg-white text-[#822433] pt-24 pb-32">
      <motion.div
        key="materials-search"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
        className="mx-auto w-full max-w-md px-4 space-y-8"
      >
        <header className="space-y-1 justify-center text-center">
          <h1 className="text-2xl font-semibold">Ricerca materiali</h1>
          {/* <p className="text-sm text-[#a25966]">Compila i campi, scegli i filtri e premi Cerca.</p> */}
        </header>

        <FilterPanel
          laureaOptions={laureaOptions}
          courseOptions={courseOptionLabels}
          editionOptions={editionOptions}
          selectedLaurea={selectedLaurea}
          selectedCourse={selectedCourse}
          selectedEdition={selectedEdition}
          selectedEditionDate={selectedEditionDate}
          onLaureaFocus={handleLaureaFocus}
          onLaureaChange={handleLaureaChange}
          onCourseChange={handleCourseChange}
          onEditionChange={handleEditionChange}
          includeMaterials={includeMaterials}
          includeInfo={includeInfo}
          includeReviews={includeReviews}
          onToggleMaterials={() => setIncludeMaterials((prev) => !prev)}
          onToggleInfo={() => setIncludeInfo((prev) => !prev)}
          onToggleReviews={() => setIncludeReviews((prev) => !prev)}
          summary={
            selectedCourse
              ? `${selectedCourse} · ${selectedEdition === 'all' ? 'tutte le edizioni' : selectedEditionDate || '—'} · ${
                  activeFilters.length ? activeFilters.join(', ') : 'nessun filtro'
                }`
              : 'Compila i campi per abilitare la ricerca.'
          }
          canSearch={Boolean(selectedEdition)}
          onSearch={handleSearch}
        />

        <section className="space-y-8">
          <div className="mt-2 flex justify-center">
            <div className="inline-flex bg-gray-100 rounded-full p-1 text-sm">
              <button
                className={`px-3 py-1 rounded-full ${sectionFilter === 'materials' ? 'bg-white shadow text-[#822433]' : 'text-gray-500'} ${!includeMaterials ? 'opacity-40' : ''}`}
                onClick={() => setSectionFilter('materials')}
                disabled={!includeMaterials}
              >
                Materiali {materials.length ? `(${materials.length})` : ''}
              </button>
              <button
                className={`px-3 py-1 rounded-full ${sectionFilter === 'info' ? 'bg-white shadow text-[#822433]' : 'text-gray-500'} ${!includeInfo ? 'opacity-40' : ''}`}
                onClick={() => setSectionFilter('info')}
                disabled={!includeInfo}
              >
                Info {info.length ? `(${info.length})` : ''}
              </button>
              <button
                className={`px-3 py-1 rounded-full ${sectionFilter === 'review' ? 'bg-white shadow text-[#822433]' : 'text-gray-500'} ${!includeReviews ? 'opacity-40' : ''}`}
                onClick={() => setSectionFilter('review')}
                disabled={!includeReviews}
              >
                Review {reviews.length ? `(${reviews.length})` : ''}
              </button>
            </div>
          </div>

          {includeMaterials && sectionFilter === 'materials' && (
            <article className="space-y-3">
              <MaterialsPreview
                items={materials}
                hasSearched={hasSearched}
                onShowItem={(data) => openSheet({ mode: 'item', type: 'materiale', data })}
                buildMaterialData={(item, idx) => buildMaterialData(item, fallbackCourseName, fallbackEditionLabel, idx)}
              />
            </article>
          )}

          {includeInfo && sectionFilter === 'info' && (
            <article className="space-y-3">
              <InfoPreview
                items={info}
                hasSearched={hasSearched}
                onShowItem={(data) => openSheet({ mode: 'item', type: 'info', data })}
              />
            </article>
          )}

          {includeReviews && sectionFilter === 'review' && (
            <article className="space-y-3">
              <ReviewsPreview
                items={reviews}
                hasSearched={hasSearched}
                onShowItem={(data) => openSheet({ mode: 'item', type: 'review', data })}
              />
            </article>
          )}
        </section>
      </motion.div>

      {sheetPayload && (
        <MobileSheet open={sheetOpen} onClose={closeSheet} title={sheetTitle}>
          <div className="space-y-6">
            {renderSheetContent()}
            <div className="flex justify-end">
              <button
                onClick={closeSheet}
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
