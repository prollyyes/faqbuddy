import React from 'react';
import InputField from '@/components/utils/InputField';

export function SignupInsegnante({ formData, handleChange, setFormData }) {
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
      {/* Upload file CV */}
      <input
        type="file"
        name="cv"
        accept=".pdf,.doc,.docx"
        onChange={e => setFormData(prev => ({
          ...prev,
          cv: e.target.files[0]
        }))}
        className="w-full border border-gray-300 px-4 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#822433]"
      />
      <InputField
        name="ricevimento"
        placeholder="Ricevimento"
        value={formData.ricevimento || ''}
        onChange={handleChange}
      />
    </>
  );
}