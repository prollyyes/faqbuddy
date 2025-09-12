import React, { useEffect, useState } from 'react';

const HOST = process.env.NEXT_PUBLIC_HOST;

export const InfoProfiloStudente = ({ profile, editData, isEdit, handleEditChange }) => {
  const [corsi, setCorsi] = useState([]);

  useEffect(() => {
    if (isEdit) {
      fetch(`${HOST}/corsi-di-laurea`)
        .then(res => res.json())
        .then(data => setCorsi(data));
    }
  }, [isEdit]);

  return (
    <>
      {[
        { label: 'Nome', name: 'nome' },
        { label: 'Cognome', name: 'cognome' },
        { label: 'Email', name: 'email' },
        { label: 'Matricola', name: 'matricola' }
      ].map((field, idx) => (
        <div key={idx} className="w-full border-b border-[#822433] pb-3">
          <p className="text-sm text-[#822433] font-extrabold">{field.label}</p>
          {isEdit ? (
            <input
              type="text"
              name={field.name}
              value={editData[field.name] || ''}
              onChange={handleEditChange}
              className="w-full border border-gray-300 px-2 py-1 rounded"
            />
          ) : (
            <p className="text-lg font-medium">{profile[field.name] || '-'}</p>
          )}
        </div>
      ))}
      {/* Corso di Laurea */}
      <div className="w-full border-b border-[#822433] pb-3">
        <p className="text-sm text-[#822433] font-extrabold">Corso di Laurea</p>
        {isEdit ? (
          <select
            required
            name="corso_laurea"
            value={editData.corso_laurea || ""}
            onChange={handleEditChange}
            className="w-full border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#822433] mb-2"
          >
            <option value="" disabled hidden>Seleziona corso di laurea</option>
            {corsi.map(corso => (
              <option key={corso.id} value={corso.id}>
                {corso.nome}
              </option>
            ))}
          </select>
        ) : (
          <p className="text-lg font-medium">
            {profile.corso_laurea_nome || profile.corso_laurea || '-'}
          </p>
        )}
      </div>
    </>
  );
};