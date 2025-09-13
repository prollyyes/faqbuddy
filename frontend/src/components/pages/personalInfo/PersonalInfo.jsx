'use client'
import React, { useEffect, useState } from 'react'
import Button from '../../utils/Button';
import { motion } from 'framer-motion';
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
  const [dimBackground, setDimBackground] = useState(false);
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

  if (!profile) {
    return (
      <motion.div className="bg-white min-h-screen text-black p-6 flex items-center justify-center">
        <p className="italic">Caricamento profilo...</p>
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
          className="bg-white min-h-screen text-black p-6 pt-10 pb-24"
          initial={{ x: -50 }}
          animate={{ x: 0 }}
          transition={{ duration: 0 }}
        >
          <div className={dimBackground ? 'opacity-40' : 'opacity-100'}>
            <div className="max-w-md mx-auto text-center pt-12">
              {/* <h1 className="text-2xl font-bold text-[#822433] mb-6">
                Profilo {isStudente ? 'Studente' : 'Insegnante'}
              </h1> */}
              <div className="text-left space-y-4">
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
                {isStudente && (
                  <div className="w-full pt-6 relative">
                    <div className="flex justify-between items-center">
                      <p className="text-sm text-[#822433] font-semibold">Rating</p>
                      <button
                        onClick={() => {
                          setShowInfo(true);
                          setDimBackground(true);
                        }}
                        className="text-[#822433] text-xl hover:text-[#a00028] pt-2"
                        title="Info"
                      >
                        <HiOutlineInformationCircle />
                      </button>
                    </div>
                    {/* <p className="text-sm pt-2 text-black">Livello {profile.livello || '-'}</p> */}
                    <div className="w-full bg-gray-200 rounded-full h-4 mt-1">
                      <div
                        className="bg-[#822433] h-4 rounded-full"
                        style={{ width: `${profile.percentuale || 0}%` }}
                      ></div>
                    </div>
                    {/* <p className="text-sm mt-1 text-right text-gray-600">{profile.percentuale ? `${profile.percentuale}%` : '-'}</p> */}
                  </div>
                )}
              </div>
            </div>
            <div className="pt-5 flex flex-col items-end space-y-4">
              {isEdit ? (
                <div className="flex flex-row gap-4">
                  <Button className="text-2xl font-bold" onClick={handleSave}>Salva</Button>
                  <Button className="text-2xl font-bold" onClick={() => { setIsEdit(false); setEditData(profile); setPendingCV(null); }}>Annulla</Button>
                  <Button className="text-2xl font-bold" onClick={() => setShowPasswordModal(true)}>
                    Cambia password
                  </Button>
                </div>
              ) : (
                <Button
                  className="font-bold text-2xl"
                  onClick={() => setIsEdit(true)}
                >
                  Modifica Profilo
                </Button>
              )}
            </div>
          </div>

          {showInfo && (
            <div className="fixed inset-0 backdrop-brightness-75 flex items-center justify-center z-40">
              <div className="bg-white backdrop-blur-md border border-[#822433] rounded-lg shadow-lg py-2 px-3 text-sm w-72 min-h-[14rem] text-center relative flex flex-col justify-between">
                {/* X in alto a destra */}
                <button
                  className="absolute top-2 right-2 text-[#822433] hover:text-[#a00028] text-2xl font-black"
                  onClick={() => {
                    setShowInfo(false);
                    setDimBackground(false);
                  }}
                  aria-label="Chiudi"
                >
                  <IoClose />
                </button>
                <div className="flex-1 flex items-center justify-center">
                  <p className="text-black">
                    Con un rating di livello 5 o superiore sei considerato abbastanza affidabile da poter caricare materiale senza necessità di verifica dei contenuti.<br />Puoi aumentare il tuo rating tramite 'Like' ai materiali che pubblichi.
                  </p>
                </div>
              </div>
            </div>
          )}

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