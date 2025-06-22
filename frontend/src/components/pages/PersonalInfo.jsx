'use client'
import React from 'react'
import Button from '../utils/Button';
import { motion } from 'framer-motion';
import { HiOutlineInformationCircle } from "react-icons/hi2";

const PersonalInfo = () => {
  const [showInfo, setShowInfo] = React.useState(false);
  const [dimBackground, setDimBackground] = React.useState(false);

  return (
    <motion.div
      className="bg-white min-h-screen text-black p-6"
      initial={{ x: -50 }}
      animate={{ x: 0 }}
      transition={{ duration: 0 }}
    >
      <div className={dimBackground ? 'opacity-40' : 'opacity-100'}>
        <div className="max-w-md mx-auto text-center pt-12">
          <h1 className="text-2xl font-bold text-[#800020] mb-6">Profilo Studente</h1>
          <div className="text-left space-y-4">
            {[
              { label: 'Nome', value: 'Mario Rossi' },
              { label: 'Email', value: 'mario.rossi@example.com' },
              { label: 'Matricola', value: '1234567' },
              { label: 'Corso di Laurea', value: 'Ingegneria Informatica' }
            ].map((field, index) => (
              <div
                key={index}
                className="w-full border-b border-[#800020] pb-3"
              >
                <p className="text-sm text-[#800020] font-extrabold">{field.label}</p>
                <p className="text-lg font-medium">{field.value}</p>
              </div>
            ))}
            <div className="w-full pt-6 relative">
              <div className="flex justify-between items-center">
                <p className="text-sm text-[#800020] font-semibold">Rating</p>
                <button
                  onClick={() => {
                    setShowInfo(true);
                    setDimBackground(true);
                  }}
                  className="text-[#800020] text-xl hover:text-[#a00028] pt-2"
                  title="Info"
                >
                  <HiOutlineInformationCircle />
                </button>
              </div>
              <p className="text-sm pt-2 text-black">Livello 7</p>
              <div className="w-full bg-gray-200 rounded-full h-4 mt-1">
                <div className="bg-[#800020] h-4 rounded-full" style={{ width: '70%' }}></div>
              </div>
              <p className="text-sm mt-1 text-right text-gray-600">70%</p>
            </div>
          </div>
        </div>
        <div className="pt-12 flex justify-center">
          <Button className="text-2xl font-bold">
            Modifica Profilo
          </Button>
        </div>
      </div>

      {showInfo && (
        <div className="fixed inset-0 backdrop-brightness-75 flex items-center justify-center z-40">
          <div className="bg-white backdrop-blur-md border border-[#800020] rounded-lg shadow-lg p-4 text-sm w-64 h-60 text-center relative">
            <p className="text-black">
              Con un rating di livello 5 o superiore sei considerato abbastanza affidabile da poter caricare materiale senza necessità di verifica dei contenuti.<br /><br />Puoi aumentare il tuo rating tramite 'Like' ai materiali che pubblichi.
            </p>
            <button
              onClick={() => {
                setShowInfo(false);
                setDimBackground(false);
              }}
              className="mt-6 text-[#800020] font-semibold hover:underline text-center w-full"
            >
              Chiudi
            </button>
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default PersonalInfo