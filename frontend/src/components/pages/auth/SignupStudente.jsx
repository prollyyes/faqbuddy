import React from 'react';
import InputField from '@/components/utils/InputField';

export function SignupStudente({ formData, handleChange }) {
  return (
    <>
      <InputField
        name="corsoDiLaurea"
        placeholder="Corso di Laurea"
        value={formData.corsoDiLaurea || ''}
        onChange={handleChange}
      />
      <InputField
        name="numeroDiMatricola"
        placeholder="Numero di matricola"
        value={formData.numeroDiMatricola || ''}
        onChange={handleChange}
      />
    </>
  );
}