import React from 'react';
import InputField from '@/components/utils/InputField';
import { useRef } from 'react';

export function SignupInsegnante({ formData, handleChange, setFormData }) {
  const fileInputRef = useRef();

  return (
    <>
      <InputField
        name="infoMail"
        placeholder="Info Mail"
        value={formData.infoMail || ''}
        onChange={handleChange}
      />
      <InputField
        name="sitoWeb"
        placeholder="Sito Web"
        value={formData.sitoWeb || ''}
        onChange={handleChange}
      />
      
      {/* Upload file CV custom */}
      <div className="mb-2">
        <button
          type="button"
          className="w-full border border-gray-300 px-4 py-2 rounded-xl bg-white text-left hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#822433] transition"
          onClick={() => fileInputRef.current.click()}
        >
          {formData.cv ? formData.cv.name : <span className="text-gray-400 italic">Carica il tuo CV (PDF, DOC, DOCX)</span>}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          name="cv"
          accept=".pdf,.doc,.docx"
          onChange={e => setFormData(prev => ({
            ...prev,
            cv: e.target.files[0]
          }))}
          className="hidden"
        />
      </div>
      <InputField
        name="ricevimento"
        placeholder="Ricevimento"
        value={formData.ricevimento || ''}
        onChange={handleChange}
      />
    </>
  );
}