'use client'
import React, { useEffect, useMemo, useState } from 'react'
import Button from '../../utils/Button';
import { motion, AnimatePresence } from 'framer-motion';
import { HiOutlineInformationCircle } from "react-icons/hi2";
import { IoClose } from "react-icons/io5";
import axios from 'axios';
import { InfoProfiloStudente } from './PeronalInfo_studente';
import { InfoProfiloInsegnante } from './PersonalInfo_insegnante';
import ChangePasswordModal from './ChangePasswordModal';
import SwipeWrapperStudente from '@/components/wrappers/SwipeWrapperStudente';
import SwipeWrapperInsegnante from '@/components/wrappers/SwipeWrapperInsegnante';
import SwipeWrapperHome from '@/components/wrappers/SwipeWrapperHome';


const HOST = process.env.NEXT_PUBLIC_HOST;

const PersonalInfo = () => {
  const [showInfo, setShowInfo] = useState(false);
  const [profile, setProfile] = useState(null);
  const [isEdit, setIsEdit] = useState(false);
  const [editData, setEditData] = useState({});
  const [pendingCV, setPendingCV] = useState(null);
  const [showPasswordModal, setShowPasswordModal] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;

    fetch(`${HOST}/profile/me`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => {
        setProfile(data);
        setEditData(data);
      })
      .catch(() => setProfile(null));
  }, []);

  const initials = useMemo(() => {
    const n = editData?.nome?.[0] || profile?.nome?.[0] || '';
    const c = editData?.cognome?.[0] || profile?.cognome?.[0] || '';
    return (n + c).toUpperCase();
  }, [editData?.nome, editData?.cognome, profile?.nome, profile?.cognome]);

  if (!profile) {
    return (
      <motion.div className="bg-gray-50 min-h-screen text-black p-5 flex items-center justify-center">
        <div className="w-full max-w-md animate-pulse">
          <div className="bg-white rounded-2xl shadow-sm p-4 border border-gray-100">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-full bg-gray-200" />
              <div className="flex-1">
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-2" />
                <div className="h-3 bg-gray-200 rounded w-1/3" />
              </div>
            </div>
          </div>
          <div className="mt-4 space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white rounded-xl p-4 border border-gray-100">
                <div className="h-4 bg-gray-200 rounded w-1/3 mb-2" />
                <div className="h-4 bg-gray-200 rounded w-2/3" />
              </div>
            ))}
          </div>
        </div>
      </motion.div>
    );
  }

  const isStudente = profile.ruolo === 'studente';

  // Scelgo il wrapper in base al ruolo
  const Wrapper = isStudente ? SwipeWrapperStudente : SwipeWrapperInsegnante;

  const handleEditChange = (e) => {
    const { name, value } = e.target;
    setEditData(prev => ({ ...prev, [name]: value }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      let newCVId = editData.cv;

      if (pendingCV) {
        if (profile.cv) {
          try {
            await axios.delete(`${HOST}/files/delete/${profile.cv}`, {
              headers: { Authorization: `Bearer ${token}` }
            });
          } catch {
            alert("Errore durante l'eliminazione del vecchio CV");
          }
        }
        const formData = new FormData();
        formData.append("file", pendingCV);
        formData.append("parent_folder", "FAQBuddy");
        formData.append("child_folder", "CV");
        formData.append("nome", editData.nome);
        formData.append("cognome", editData.cognome);
        try {
          const res = await axios.post(
            `${HOST}/files/upload`,
            formData,
            { headers: { "Content-Type": "multipart/form-data" } }
          );
          newCVId = res.data.file_id;
        } catch {
          alert("Errore durante l'upload del CV");
        }
      }

      await axios.put(`${HOST}/profile/me`, { ...editData, cv: newCVId }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProfile({ ...editData, cv: newCVId });
      setIsEdit(false);
      setPendingCV(null);
    } catch (err) {
      alert('Errore durante il salvataggio');
    }
  };

  return (
    <SwipeWrapperHome>
      <Wrapper>
        <motion.div
          className="bg-gray-50 min-h-screen text-black pt-20 pb-28"
          initial={{ x: -50 }}
          animate={{ x: 0 }}
          transition={{ duration: 0 }}
        >
          <div className="mx-auto max-w-md">
            {/* Header card */}
            <div className="px-5 pt-6">
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-[#822433]/10 flex items-center justify-center text-[#822433] font-bold">
                  {initials || 'P'}
                </div>
                <div className="flex-1 overflow-hidden">
                  <p className="text-base font-semibold truncate">{profile.nome} {profile.cognome}</p>
                  <p className="text-xs text-gray-500 truncate">{profile.email}</p>
                </div>
                <span className="text-[10px] px-2 py-1 rounded-full bg-[#822433]/10 text-[#822433] whitespace-nowrap">
                  {isStudente ? 'Studente' : 'Insegnante'}
                </span>
              </div>
            </div>

            {/* Content */}
            <div className="px-5 mt-5 space-y-4">
              {isStudente ? (
                <InfoProfiloStudente
                  profile={profile}
                  editData={editData}
                  isEdit={isEdit}
                  handleEditChange={handleEditChange}
                />
              ) : (
                <InfoProfiloInsegnante
                  profile={profile}
                  editData={editData}
                  isEdit={isEdit}
                  handleEditChange={handleEditChange}
                  pendingCV={pendingCV}
                  setPendingCV={setPendingCV}
                />
              )}

              {/* Rating */}
              {isStudente && (
                <div className="bg-white rounded-xl border border-gray-100 p-4">
                  <div className="flex justify-between items-center">
                    <p className="text-sm text-[#822433] font-semibold">Rating</p>
                    <button
                      onClick={() => setShowInfo(true)}
                      className="text-[#822433] text-xl hover:text-[#a00028]"
                      title="Info"
                    >
                      <HiOutlineInformationCircle />
                    </button>
                  </div>
                  <div className="mt-2 flex items-center gap-3">
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-[#822433] h-3 rounded-full"
                        style={{ width: `${profile.percentuale || 0}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-600 w-10 text-right">
                      {profile.percentuale ? `${profile.percentuale}%` : '-'}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Azioni profilo (non fixed) */}
          <div className="mx-auto max-w-md px-5 py-5">
            {isEdit ? (
              <div className="flex gap-2 items-center justify-between">
                <Button className="flex-1 h-11 text-base font-semibold" onClick={handleSave}>Salva</Button>
                <Button className="flex-1 h-11 text-base font-semibold" onClick={() => { setIsEdit(false); setEditData(profile); setPendingCV(null); }}>Annulla</Button>
                <Button className="h-11 px-3 text-sm font-semibold" onClick={() => setShowPasswordModal(true)}>
                  Cambia password
                </Button>
              </div>
            ) : (
              <Button
                className="w-full h-12 text-base font-semibold"
                onClick={() => setIsEdit(true)}
              >
                Modifica Profilo
              </Button>
            )}
          </div>

          {/* Centered Modal: Rating info */}
          <AnimatePresence>
            {showInfo && (
              <motion.div
                className="fixed inset-0 z-[60] flex items-center justify-center"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <button className="absolute inset-0 bg-black/40" onClick={() => setShowInfo(false)} aria-label="Chiudi" />
                <motion.div
                  className="relative mx-5 w-full max-w-sm bg-white rounded-2xl shadow-2xl border border-gray-200 p-4"
                  initial={{ scale: 0.95, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.95, opacity: 0 }}
                  transition={{ type: 'spring', stiffness: 260, damping: 20 }}
                >
                  <div className="flex justify-between items-start">
                    <h3 className="text-base font-semibold text-[#822433]">Come funziona il rating</h3>
                    <button className="text-2xl text-[#822433]" onClick={() => setShowInfo(false)} aria-label="Chiudi">
                      <IoClose />
                    </button>
                  </div>
                  <p className="text-sm text-gray-700 mt-2">
                    Con un rating di livello 5 o superiore sei considerato abbastanza affidabile da poter caricare materiale senza necessità di verifica dei contenuti. Puoi aumentare il tuo rating tramite "Like" ai materiali che pubblichi.
                  </p>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>

          <ChangePasswordModal
            open={showPasswordModal}
            onClose={() => setShowPasswordModal(false)}
          />
        </motion.div>
      </Wrapper>
    </SwipeWrapperHome>
  );
};

export default PersonalInfo
