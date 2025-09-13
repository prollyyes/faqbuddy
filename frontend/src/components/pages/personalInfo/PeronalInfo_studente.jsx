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
    <div className="bg-white rounded-xl border border-gray-100 p-4">
      <div className="space-y-3">
        {[
          { label: 'Nome', name: 'nome' },
          { label: 'Cognome', name: 'cognome' },
          { label: 'Email', name: 'email' },
          { label: 'Matricola', name: 'matricola' }
        ].map((field, idx) => (
          <div key={idx} className="pb-3 border-b last:border-b-0">
            <p className="text-[11px] uppercase tracking-wide text-[#822433] font-extrabold">{field.label}</p>
            {isEdit ? (
              <input
                type="text"
                name={field.name}
                value={editData[field.name] || ''}
                onChange={handleEditChange}
                className="mt-1 w-full border border-gray-300 px-3 h-11 rounded-lg text-[15px]"
              />
            ) : (
              <p className="text-[15px] font-medium mt-1">{profile[field.name] || '-'}</p>
            )}
          </div>
        ))}

        {/* Corso di Laurea */}
        <div className="pt-3">
          <p className="text-[11px] uppercase tracking-wide text-[#822433] font-extrabold">Corso di Laurea</p>
          {isEdit ? (
            <select
              required
              name="corso_laurea"
              value={editData.corso_laurea || ""}
              onChange={handleEditChange}
              className="mt-1 w-full border border-gray-300 px-3 h-11 rounded-lg text-[15px] focus:outline-none focus:ring-2 focus:ring-[#822433]"
            >
              <option value="" disabled hidden>Seleziona corso di laurea</option>
              {corsi.map(corso => (
                <option key={corso.id} value={corso.id}>
                  {corso.nome}
                </option>
              ))}
            </select>
          ) : (
            <p className="text-[15px] font-medium mt-1">
              {profile.corso_laurea_nome || profile.corso_laurea || '-'}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
