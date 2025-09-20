'use client'

import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { FaStar } from 'react-icons/fa';
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

function SectionHeader({ title}) {
  return (
    <div className="flex items-center justify-between">
      <h2 className="text-lg font-semibold">{title}</h2>
    </div>
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

  const courseOptionLabels = useMemo(
    () => courseOptions.map((c) => (Array.isArray(c) ? c[0] : c)),
    [courseOptions]
  );

  const buildMaterialData = (item, courseName, editionLabel, index) => {
    const path = item.path_file ?? item[0];
    const tipo = item.tipo ?? item[1];
    const rating = item.rating_medio ?? item[3] ?? 'n/d';
    const verificato = item.verificato ?? item[2];
    const editionText = editionLabel || 'edizione';
    const courseText = courseName || 'corso';
    const displayName = `${tipo || 'Materiale'} · ${courseText} (${editionText})`;
    return { path, tipo, rating, verificato, displayName };
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
        return (
          <div className="space-y-2">
            {items.map((item, idx) => {
              const data = buildMaterialData(item);
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
            </ul>
          </div>
        );
      }
      if (sheetPayload.type === 'info') {
        const { data } = sheetPayload;
        return (
          <div className="space-y-3 text-sm text-[#822433]">
            <p className="text-base font-semibold">{data.titolo}</p>
            <ul className="space-y-1">
              <li>Categoria: <span className="font-medium">{data.categoria || '—'}</span></li>
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
          {includeMaterials && (
            <article className="space-y-3">
              <SectionHeader
                title="Materiali"
              />
              <MaterialsPreview
                items={materials}
                hasSearched={hasSearched}
                onShowAll={() => openSheet({ mode: 'list', type: 'materiali', items: materials, courseName: selectedCourse, editionLabel: selectedEdition === 'all' ? 'tutte le edizioni' : selectedEditionDate })}
                onShowItem={(data) => openSheet({ mode: 'item', type: 'materiale', data })}
                buildMaterialData={(item, idx) =>
                  buildMaterialData(item, selectedCourse, selectedEdition === 'all' ? 'tutte le edizioni' : selectedEditionDate, idx)
                }
                courseName={selectedCourse}
                editionLabel={selectedEdition === 'all' ? 'tutte le edizioni' : selectedEditionDate}
              />
            </article>
          )}

          {includeInfo && (
            <article className="space-y-3">
              <SectionHeader
                title="Informazioni corso"
              />
              <InfoPreview
                items={info}
                hasSearched={hasSearched}
                onShowAll={() => openSheet({ mode: 'list', type: 'info', items: info })}
                onShowItem={(data) => openSheet({ mode: 'item', type: 'info', data })}
              />
            </article>
          )}

          {includeReviews && (
            <article className="space-y-3">
              <SectionHeader
                title="Review"
              />
              <ReviewsPreview
                items={reviews}
                hasSearched={hasSearched}
                onShowAll={() => openSheet({ mode: 'list', type: 'review', items: reviews })}
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
