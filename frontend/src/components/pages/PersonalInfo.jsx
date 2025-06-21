'use client'
import React from 'react'
import Button from '../utils/Button';

const PersonalInfo = () => {

  return (
    <div className="bg-white min-h-screen text-black p-6">
      <div className="max-w-md mx-auto text-center">
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
              <p className="text-sm text-[#800020] font-semibold">{field.label}</p>
              <p className="text-lg">{field.value}</p>
            </div>
          ))}
        </div>
      </div>
      <div className="fixed bottom-33 left-0 w-full flex justify-center">
        <Button className="text-2xl font-bold">
          Modifica Profilo
        </Button>
      </div>
    </div>
  );
};

export default PersonalInfo