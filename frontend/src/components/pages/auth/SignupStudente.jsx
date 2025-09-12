import React, { useEffect, useState } from 'react';
import InputField from '@/components/utils/InputField';

const HOST = process.env.NEXT_PUBLIC_HOST;

export function SignupStudente({ formData, handleChange }) {
  const [corsi, setCorsi] = useState([]);

  useEffect(() => {
    fetch(`${HOST}/corsi-di-laurea`)
      .then(res => res.json())
      .then(data => setCorsi(data));
  }, []);

  return (
    <>
      <select
        required
        name="corsoDiLaurea"
        value={formData.corsoDiLaurea || ""}
        onChange={handleChange}
        className={`w-full border border-gray-300 px-4 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#822433] mb-2 ${!formData.corsoDiLaurea ? 'text-gray-500' : 'text-gray-900'}`}
      >
        <option value="" disabled hidden>Seleziona corso di laurea</option>
        {corsi.map(corso => (
          <option key={corso.id} value={corso.id}>
            {corso.nome}
          </option>
        ))}
      </select>
      <InputField
        name="numeroDiMatricola"
        placeholder="Numero di matricola"
        value={formData.numeroDiMatricola || ''}
        onChange={handleChange}
      />
    </>
  );
}
