import React from 'react';

// --- COMPONENTE INSEGNANTE ---
export const InfoProfiloInsegnante = ({
  profile,
  editData,
  isEdit,
  handleEditChange,
  pendingCV,
  setPendingCV
}) => (
  <>
    {[
      { label: 'Nome', name: 'nome' },
      { label: 'Cognome', name: 'cognome' },
      { label: 'Email', name: 'email' },
      { label: 'Info Mail', name: 'infoMail' },
      { label: 'Sito Web', name: 'sitoWeb' },
      { label: 'Ricevimento', name: 'ricevimento' }
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
    <div className="w-full border-b border-[#822433] pb-3">
      <p className="text-sm text-[#822433] font-extrabold">CV</p>
      {isEdit ? (
        <>
          <input
            type="file"
            accept=".pdf,.doc,.docx"
            onChange={e => {
              const file = e.target.files[0];
              if (file) setPendingCV(file);
            }}
            className="w-full border border-gray-300 px-2 py-1 rounded"
          />
          {pendingCV && (
            <p className="text-xs mt-2 text-gray-600">CV selezionato: {pendingCV.name}</p>
          )}
          {!pendingCV && editData.cv && (
            <p className="text-xs mt-2 text-gray-600">CV attuale: {editData.cv}</p>
          )}
        </>
      ) : (
        profile.cv ? (
          <a
            href={`https://drive.google.com/file/d/${profile.cv}/view`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[#822433] underline"
          >
            Visualizza CV
          </a>
        ) : (
          <p className="text-lg font-medium">-</p>
        )
      )}
    </div>
  </>
);