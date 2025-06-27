import React from 'react';

// --- COMPONENTE STUDENTE ---
export const InfoProfiloStudente = ({ profile, editData, isEdit, handleEditChange }) => (
  <>
    {[
      { label: 'Nome', name: 'nome' },
      { label: 'Cognome', name: 'cognome' },
      { label: 'Email', name: 'email' },
      { label: 'Matricola', name: 'matricola' },
      { label: 'Corso di Laurea', name: 'corso_laurea' }
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
  </>
);