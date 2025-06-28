import React, { useEffect, useState } from 'react';
import InputField from '@/components/utils/InputField';

export function SignupStudente({ formData, handleChange }) {
  const [corsi, setCorsi] = useState([]);

  useEffect(() => {
    fetch('http://localhost:8000/corsi-di-laurea')
      .then(res => res.json())
      .then(data => setCorsi(data));
  }, []);

  return (
    <>
      <select
        required
        className="border rounded p-2 w-full mb-2"
        name="corsoDiLaurea"
        value={formData.corsoDiLaurea || ""}
        onChange={handleChange}
      >
        <option value="">Seleziona corso di laurea</option>
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