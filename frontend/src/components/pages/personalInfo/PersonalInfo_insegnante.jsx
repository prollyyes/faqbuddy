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
  <div className="bg-white rounded-xl border border-gray-100 p-4">
    <div className="space-y-3">
      {[
        { label: 'Nome', name: 'nome' },
        { label: 'Cognome', name: 'cognome' },
        { label: 'Email', name: 'email' },
        { label: 'Info Mail', name: 'infoMail' },
        { label: 'Sito Web', name: 'sitoWeb' },
        { label: 'Ricevimento', name: 'ricevimento' }
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
            <p className="text-[15px] font-medium mt-1 break-words">{profile[field.name] || '-'}</p>
          )}
        </div>
      ))}

      <div className="pt-1">
        <p className="text-[11px] uppercase tracking-wide text-[#822433] font-extrabold">CV</p>
        {isEdit ? (
          <>
            <input
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={e => {
                const file = e.target.files[0];
                if (file) setPendingCV(file);
              }}
              className="mt-1 w-full border border-gray-300 px-3 h-11 rounded-lg text-[15px] bg-white"
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
            <p className="text-[15px] font-medium mt-1">-</p>
          )
        )}
      </div>
    </div>
  </div>
);
