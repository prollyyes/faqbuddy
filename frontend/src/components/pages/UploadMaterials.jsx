'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import Button from '@/components/utils/Button';

const HOST = process.env.NEXT_PUBLIC_HOST;

export default function UploadMaterials() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadType, setUploadType] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [profile, setProfile] = useState(null); // { nome, cognome, email, matricola, corso_laurea }
  const [courses, setCourses] = useState([]); // merged current + completed
  const [selectedCourseEdition, setSelectedCourseEdition] = useState(null); // { nome, edition_data }
  const [thesisTitle, setThesisTitle] = useState('');
  const fileInputRef = useRef(null);

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
      setIsModalOpen(true);
    })();
  };

  const handleCancel = () => {
    setSelectedFile(null);
    setUploadType('');
    setIsModalOpen(false);
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
      setSelectedFile(null);
      setUploadType('');
      setIsModalOpen(false);
      setSelectedCourseEdition(null);
      setThesisTitle('');
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

        {/* Modal per completare i dati */}
        {isModalOpen && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-white/0"
            onClick={handleCancel}
          >
            <motion.div
              initial={{ opacity: 0, y: 16, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.22, ease: 'easeOut' }}
              className="bg-white w-full max-w-xl rounded-lg shadow-lg p-6 text-[#822433] border border-[#f0d6db]"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-bold mb-2">Dettagli materiale</h3>
              <p className="text-sm mb-4">
                <strong>Tipo:</strong> {uploadType}
                {profile?.corso_laurea && (
                  <> — <strong>CDL:</strong> {profile.corso_laurea}</>
                )}
              </p>

              <div className="space-y-3">
                {uploadType === 'tesi' ? (
                  <div>
                    <label className="block text-sm font-semibold">Titolo</label>
                    <input
                      type="text"
                      className="w-full border border-[#822433] rounded-md px-3 py-2 text-black focus:outline-none focus:ring-2 focus:ring-[#c85a71] transition"
                      value={thesisTitle}
                      onChange={(e) => setThesisTitle(e.target.value)}
                      placeholder="Titolo della tesi"
                    />
                  </div>
                ) : (
                  <div>
                    <label className="block text-sm font-semibold">Seleziona corso ed edizione</label>
                    <select
                      className="w-full border border-[#822433] rounded-md px-3 py-2 text-black focus:outline-none focus:ring-2 focus:ring-[#c85a71] transition cursor-pointer"
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
                      <p className="text-sm mt-2 text-[#822433]">Nessun corso disponibile</p>
                    )}
                  </div>
                )}

                <div>
                  <label className="block text-sm font-semibold">Seleziona file</label>
                  <input
                    ref={fileInputRef}
                    id="modalFileInput"
                    type="file"
                    onChange={handleFileChange}
                    accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.ppt,.pptx"
                    className="hidden"
                  />
                  <Button
                    onClick={() => fileInputRef.current?.click()}
                    variant="default"
                    size="md"
                  >
                    Seleziona file
                  </Button>
                  {selectedFile && (
                    <p className="text-xs mt-2 text-[#822433]">File selezionato: <span className="font-semibold">{selectedFile.name}</span></p>
                  )}
                </div>
              </div>

              <div className="mt-5 flex justify-end gap-2">
                <button
                  onClick={handleCancel}
                  className="px-4 py-2 text-sm border border-[#822433] text-[#822433] rounded hover:bg-[#f7e8ec] transition"
                  disabled={isUploading}
                >
                  Annulla
                </button>
                <Button
                  onClick={handleUpload}
                  disabled={isUploading || !selectedFile || (uploadType !== 'tesi' && !selectedCourseEdition) || (uploadType === 'tesi' && !thesisTitle.trim())}
                  variant="default"
                  size="md"
                >
                  {isUploading ? 'Caricamento...' : 'Carica'}
                </Button>
              </div>
            </motion.div>
          </div>
        )}

        {/* Bottoni per tipo di materiale */}
        <div className="grid grid-cols-2 gap-4 pt-4">
          <Button onClick={() => handleUploadTypeClick('tesi')} variant="default" size="md">Tesi</Button>
          <Button onClick={() => handleUploadTypeClick('slide')} variant="default" size="md">Slide</Button>
          <Button onClick={() => handleUploadTypeClick('esercizi')} variant="default" size="md">Esercizi</Button>
          <Button onClick={() => handleUploadTypeClick('libro')} variant="default" size="md">Libro</Button>
          <Button onClick={() => handleUploadTypeClick('appunti')} variant="default" size="md">Appunti</Button>
        </div>
      </motion.div>
    </div>
  );
}
