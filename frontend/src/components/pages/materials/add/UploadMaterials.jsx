'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import Button from '@/components/utils/Button';
import TileButton from '@/components/utils/TileButton';
import MobileSheet from '@/components/utils/MobileSheet';

const typeDescriptions = {
  tesi: 'Condividi la tua tesi e aiuta chi sta preparando la propria discussione.',
  slide: 'Carica le slide aggiornate per supportare gli altri durante il corso.',
  esercizi: 'Pubblica esercizi e soluzioni per rendere lo studio più efficace.',
  libro: 'Suggerisci libri o dispense che hai trovato indispensabili.',
  appunti: 'Condividi i tuoi appunti per accelerare il ripasso della community.',
  default: 'Completa i dettagli e carica materiale utile per il tuo corso.'
};

const HOST = process.env.NEXT_PUBLIC_HOST;

export default function UploadMaterials() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadType, setUploadType] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [profile, setProfile] = useState(null); // { nome, cognome, email, matricola, corso_laurea }
  const [courses, setCourses] = useState([]); // merged current + completed
  const [selectedCourseEdition, setSelectedCourseEdition] = useState(null); // { nome, edition_data }
  const [thesisTitle, setThesisTitle] = useState('');
  const fileInputRef = useRef(null);
  const closeTimeoutRef = useRef(null);

  const typeLabel = uploadType
    ? uploadType.charAt(0).toUpperCase() + uploadType.slice(1)
    : 'Seleziona un tipo';
  const typeDescription = uploadType ? (typeDescriptions[uploadType] || typeDescriptions.default) : typeDescriptions.default;
  const teacherName = selectedCourseEdition
    ? [selectedCourseEdition.docente_nome, selectedCourseEdition.docente_cognome].filter(Boolean).join(' ')
    : '';

  // Non servono più dropdown per laurea/corso: recuperiamo info da /profile
  useEffect(() => {
    // opzionale: pre-caricare profilo per abilitare subito i bottoni
    const preloadProfile = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;
        const res = await fetch(`${HOST}/profile/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const u = await res.json();
          setProfile(u);
        }
      } catch (e) {
        console.error('Preload profile error:', e);
      }
    };
    preloadProfile();
  }, []);

  useEffect(() => {
    return () => {
      if (closeTimeoutRef.current) {
        clearTimeout(closeTimeoutRef.current);
        closeTimeoutRef.current = null;
      }
    };
  }, []);

  const fetchProfile = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      alert('Utente non autenticato.');
      return null;
    }
    const res = await fetch(`${HOST}/profile/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      alert('Errore nel recupero del profilo.');
      return null;
    }
    const u = await res.json();
    setProfile(u);
    return u;
  };

  const fetchCoursesForUser = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      alert('Utente non autenticato.');
      return [];
    }
    const headers = { Authorization: `Bearer ${token}` };
    const [curRes, compRes] = await Promise.all([
      fetch(`${HOST}/profile/courses/current`, { headers }),
      fetch(`${HOST}/profile/courses/completed`, { headers }),
    ]);
    if (!curRes.ok || !compRes.ok) {
      alert('Errore nel recupero dei corsi.');
      return [];
    }
    const cur = await curRes.json();
    const comp = await compRes.json();
    // Unisci e deduplica per (edition_id, edition_data)
    const map = new Map();
    [...cur, ...comp].forEach((c) => {
      const key = `${c.edition_id}__${c.edition_data}`;
      if (!map.has(key)) map.set(key, c);
    });
    const list = Array.from(map.values());
    setCourses(list);
    return list;
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
    } else {
      // User canceled file selection, reset upload type
      setUploadType('');
    }
  };

  const handleUploadTypeClick = (type) => {
    setUploadType(type);
    setSelectedFile(null);
    setSelectedCourseEdition(null);
    setThesisTitle('');
    // On click, fetch needed data and open modal
    (async () => {
      const u = profile || (await fetchProfile());
      if (!u) return;
      if (type !== 'tesi') {
        await fetchCoursesForUser();
      }
      if (closeTimeoutRef.current) {
        clearTimeout(closeTimeoutRef.current);
        closeTimeoutRef.current = null;
      }
      setIsModalOpen(true);
      setSheetOpen(true);
    })();
  };

  const resetModalState = () => {
    setSelectedFile(null);
    setUploadType('');
    setSelectedCourseEdition(null);
    setThesisTitle('');
  };

  const handleCloseModal = (force = false) => {
    if (isUploading && !force) return;
    setSheetOpen(false);
    if (closeTimeoutRef.current) {
      clearTimeout(closeTimeoutRef.current);
      closeTimeoutRef.current = null;
    }
    closeTimeoutRef.current = setTimeout(() => {
      setIsModalOpen(false);
      resetModalState();
      closeTimeoutRef.current = null;
    }, 240);
  };

  const handleUpload = async () => {
    if (!uploadType) {
      alert('Seleziona un tipo di materiale.');
      return;
    }
    if (!selectedFile) {
      alert('Seleziona un file da caricare.');
      return;
    }

    // Ensure profile loaded
    const u = profile || (await fetchProfile());
    if (!u) return;

    setIsUploading(true);

    try {
      if (uploadType === 'tesi') {
        if (!thesisTitle.trim()) {
          alert('Inserisci il Titolo della tesi.');
          setIsUploading(false);
          return;
        }
        const fd = new FormData();
        fd.append('matricola', String(u.matricola || ''));
        fd.append('title', thesisTitle.trim());
        fd.append('file', selectedFile);
        const res = await fetch(`${HOST}/addTesi`, { method: 'POST', body: fd });
        if (res.ok) {
          alert('Tesi caricata con successo!');
        } else {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || 'Errore durante il caricamento della tesi');
        }
      } else {
        if (!selectedCourseEdition) {
          alert('Seleziona un corso ed edizione.');
          setIsUploading(false);
          return;
        }
        const fd = new FormData();
        fd.append('email', String(u.email || ''));
        fd.append('nomeCorso', String(selectedCourseEdition.nome));
        fd.append('semestre', String(selectedCourseEdition.edition_data));
        fd.append('tipo', String(uploadType));
        fd.append('file', selectedFile);
        const res = await fetch(`${HOST}/addMaterialeDidattico`, {
          method: 'POST',
          body: fd,
        });
        if (res.ok) {
          alert('Materiale caricato con successo!');
        } else {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || 'Errore durante il caricamento del materiale');
        }
      }

      // Reset UI
      handleCloseModal(true);
    } catch (error) {
      console.error('Upload error:', error);
      alert(error.message || 'Errore durante il caricamento del file');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="h-screen flex flex-col justify-center items-center bg-white px-6 text-[#822433] space-y-8">
      <motion.div
        key="upload"
        initial={{ opacity: 0, x: -50 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 50 }}
        transition={{ duration: 0.3 }}
        className="w-full max-w-xl px-6 pb-35 text-[#822433] space-y-6 flex flex-col justify-start pt-16"
      >
        {/* Intestazione */}
        <h2 className="text-2xl font-bold pt-4">Carica materiale</h2>

        {/* Niente dropdown: si usa il profilo e i corsi dell'utente */}

        {isModalOpen && (
          <MobileSheet
            open={sheetOpen}
            onClose={handleCloseModal}
            title="Dettagli materiale"
            hideTopBorder
          >
            <div className="space-y-6 text-[#822433]">
              <div
                className={`rounded-2xl p-5 transition-colors ${uploadType
                  ? 'bg-gradient-to-r from-[#fde4e8] via-[#f9d5dc] to-[#f6c7d0] text-[#681422]'
                  : 'bg-gray-100 border border-dashed border-[#d9d9d9] text-[#822433]/70'}`}
              >
                {/* <p className="text-xs uppercase tracking-[0.2em] font-semibold">Tipo materiale</p> */}
                <p className="text-2xl font-bold mt-1">{typeLabel}</p>
                <p className="text-sm mt-2 leading-relaxed max-w-xl">{typeDescription}</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {profile?.corso_laurea && (
                  <div className="rounded-xl border border-[#f0d6db] bg-white/80 px-4 py-3 shadow-sm">
                    <p className="text-[11px] uppercase tracking-wide text-[#b6485b]">Corso di laurea</p>
                    <p className="text-sm font-semibold mt-1">{profile.corso_laurea}</p>
                  </div>
                )}
                {selectedCourseEdition && (
                  <div className="rounded-xl border border-[#f0d6db] bg-white/80 px-4 py-3 shadow-sm">
                    <p className="text-[11px] uppercase tracking-wide text-[#b6485b]">Corso</p>
                    <p className="text-sm font-semibold mt-1">{selectedCourseEdition.nome}</p>
                    <p className="text-xs text-[#a35d6b]">Edizione {selectedCourseEdition.edition_data}</p>
                  </div>
                )}
                {teacherName && (
                  <div className="rounded-xl border border-[#f0d6db] bg-white/80 px-4 py-3 shadow-sm">
                    <p className="text-[11px] uppercase tracking-wide text-[#b6485b]">Docente</p>
                    <p className="text-sm font-semibold mt-1">{teacherName}</p>
                  </div>
                )}
                {selectedFile && (
                  <div className="rounded-xl border border-[#f0d6db] bg-white/80 px-4 py-3 shadow-sm">
                    <p className="text-[11px] uppercase tracking-wide text-[#b6485b]">File selezionato</p>
                    <p className="text-sm font-semibold mt-1 break-all">{selectedFile.name}</p>
                  </div>
                )}
                {uploadType && uploadType !== 'tesi' && !selectedCourseEdition && (
                  <div className="rounded-xl border border-dashed border-[#f0d6db] bg-white/60 px-4 py-3 text-sm text-[#a25966]">
                    Scegli un corso dall'elenco per collegare il materiale all'edizione corretta.
                  </div>
                )}
              </div>

              <div className="rounded-2xl border border-[#f0d6db] bg-white px-4 py-4 shadow-sm space-y-3">
                {uploadType === 'tesi' ? (
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-[#681422]">Titolo della tesi</label>
                    <input
                      type="text"
                      className="w-full border border-[#f0d6db] rounded-xl px-3 py-2 text-black focus:outline-none focus:ring-2 focus:ring-[#c85a71]/60 transition"
                      value={thesisTitle}
                      onChange={(e) => setThesisTitle(e.target.value)}
                      placeholder={'Es. "Analisi dei sistemi distribuiti"'}
                    />
                  </div>
                ) : (
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-[#681422]">Associa un corso</label>
                    <select
                      className="w-full border border-[#f0d6db] rounded-xl px-3 py-2 text-black focus:outline-none focus:ring-2 focus:ring-[#c85a71]/60 transition cursor-pointer"
                      value={selectedCourseEdition ? `${selectedCourseEdition.edition_id}__${selectedCourseEdition.edition_data}` : ''}
                      onChange={(e) => {
                        const key = e.target.value;
                        const found = courses.find(c => `${c.edition_id}__${c.edition_data}` === key);
                        if (found) setSelectedCourseEdition(found);
                      }}
                      disabled={courses.length === 0}
                    >
                      <option value="">Scegli un corso</option>
                      {courses.map((c) => (
                        <option key={`${c.edition_id}__${c.edition_data}`} value={`${c.edition_id}__${c.edition_data}`}>
                          {c.nome} — {c.edition_data}
                          {c.docente_nome || c.docente_cognome ? ` — ${c.docente_nome || ''} ${c.docente_cognome || ''}` : ''}
                        </option>
                      ))}
                    </select>
                    {courses.length === 0 && (
                      <p className="text-xs text-[#a25966]">Non risultano corsi associati. Completa prima un corso o aggiorna il profilo.</p>
                    )}
                  </div>
                )}
              </div>

              <div className="rounded-2xl border-2 border-dashed border-[#f0d6db] bg-white px-4 py-5 text-center shadow-sm">
                <p className="text-sm font-semibold text-[#681422]">Carica il tuo file</p>
                <p className="text-xs text-[#a25966] mt-1">Supportiamo PDF, documenti Office, immagini e presentazioni.</p>
                <input
                  ref={fileInputRef}
                  id="modalFileInput"
                  type="file"
                  onChange={handleFileChange}
                  accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.ppt,.pptx"
                  className="hidden"
                />
                <div className="mt-3 flex justify-center">
                  <Button
                    onClick={() => fileInputRef.current?.click()}
                    variant="outline"
                    size="md"
                    className="min-w-[160px]"
                  >
                    Scegli file
                  </Button>
                </div>
                {selectedFile ? (
                  <p className="text-xs text-[#681422] mt-3">Pronto a caricare: <span className="font-semibold break-all">{selectedFile.name}</span></p>
                ) : (
                  <p className="text-xs text-[#a25966] mt-3">Nessun file selezionato</p>
                )}
              </div>

              <div className="flex flex-col gap-2 sm:flex-row sm:justify-end sm:items-center">
                <button
                  onClick={handleCloseModal}
                  className="w-full sm:w-auto px-4 py-2 bg-white text-[#681422] rounded-lg shadow-sm hover:bg-[#fbe9ec] transition disabled:opacity-60"
                  disabled={isUploading}
                  type="button"
                >
                  Annulla
                </button>
                <button
                  onClick={handleUpload}
                  disabled={isUploading || !selectedFile || (uploadType !== 'tesi' && !selectedCourseEdition) || (uploadType === 'tesi' && !thesisTitle.trim())}
                  className="w-full sm:w-auto px-4 py-2 bg-[#991B1B] text-white rounded-lg shadow-md hover:bg-[#7e1414] transition disabled:opacity-60 disabled:shadow-none"
                  type="button"
                >
                  {isUploading ? 'Caricamento...' : 'Carica materiale'}
                </button>
              </div>
            </div>
          </MobileSheet>
        )}

        {/* Bottoni per tipo di materiale */}
        <div className="grid grid-cols-2 gap-4 pt-4">
          <TileButton
            label="Tesi"
            imgRedSrc="/images/logo_tesi_red.png"
            imgWhiteSrc="/images/logo_tesi_white.png"
            onClick={() => handleUploadTypeClick('tesi')}
            heightClass="h-24"
            paddingYClass="py-3"
            textSizeClass="text-sm"
            iconSizeHoverClass="w-16 h-16"
            iconSizeIdleClass="w-10 h-10"
          />
          <TileButton
            label="Slide"
            imgRedSrc="/images/logo_slide_red.png"
            imgWhiteSrc="/images/logo_slide_white.png"
            onClick={() => handleUploadTypeClick('slide')}
            heightClass="h-24"
            paddingYClass="py-3"
            textSizeClass="text-sm"
            iconSizeHoverClass="w-18 h-14"
            iconSizeIdleClass="w-10 h-10"
          />
          <TileButton
            label="Esercizi"
            imgRedSrc="/images/logo_esercizi_red.png"
            imgWhiteSrc="/images/logo_esercizi_white.png"
            onClick={() => handleUploadTypeClick('esercizi')}
            heightClass="h-24"
            paddingYClass="py-3"
            textSizeClass="text-sm"
            iconSizeHoverClass="w-14 h-14"
            iconSizeIdleClass="w-10 h-10"
          />
          <TileButton
            label="Libro"
            imgRedSrc="/images/logo_libro_red.png"
            imgWhiteSrc="/images/logo_libro_white.png"
            onClick={() => handleUploadTypeClick('libro')}
            heightClass="h-24"
            paddingYClass="py-3"
            textSizeClass="text-sm"
            iconSizeHoverClass="w-16 h-16"
            iconSizeIdleClass="w-10 h-10"
          />
          <TileButton
            label="Appunti"
            imgRedSrc="/images/logo_appunti_red.png"
            imgWhiteSrc="/images/logo_appunti_white.png"
            onClick={() => handleUploadTypeClick('appunti')}
            heightClass="h-24"
            paddingYClass="py-3"
            textSizeClass="text-sm"
            iconSizeHoverClass="w-14 h-14"
            iconSizeIdleClass="w-10 h-10"
          />
        </div>
      </motion.div>
    </div>
  );
}
