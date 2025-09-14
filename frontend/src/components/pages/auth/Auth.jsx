'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Button from '@/components/utils/Button';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import { SignupInsegnante } from './SignupInsegnante';
import { SignupStudente } from './SignupStudente';
import InputField from '@/components/utils/InputField';
import { IoMdEye, IoMdEyeOff } from "react-icons/io";

const HOST = process.env.NEXT_PUBLIC_HOST;

async function uploadCV(cvFile, nome, cognome) {
  const formData = new FormData();
  formData.append("file", cvFile);
  formData.append("parent_folder", "FAQBuddy");
  formData.append("child_folder", "CV");
  formData.append("nome", nome);
  formData.append("cognome", cognome);

  const response = await axios.post(
    `${HOST}/files/upload`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return response.data;
}

export default function Auth() {
  const router = useRouter();
  const [mode, setMode] = useState('login');
  const [showPassword, setShowPassword] = useState(false);
  const [signupStep, setSignupStep] = useState(1);
  const [formData, setFormData] = useState({
    nome: '',
    cognome: '',
    sesso: '',
    eta: '',
    corsoDiLaurea: '',
    numeroDiMatricola: '',
    infoMail: '',
    sitoWeb: '',
    cv: '',
    ricevimento: '',
    ruolo: 'studente',
    email: '',
    password: '',
    confermaPassword: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const toggleMode = () => {
    setMode(prev => (prev === 'login' ? 'signup' : 'login'));
    setSignupStep(1);
    setFormData({
      nome: '',
      cognome: '',
      sesso: '',
      eta: '',
      corsoDiLaurea: '',
      numeroDiMatricola: '',
      infoMail: '',
      sitoWeb: '',
      cv: '',
      ricevimento: '',
      ruolo: 'studente',
      email: '',
      password: '',
      confermaPassword: '',
    });
    setError('');
    setSuccess('');
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (mode === 'signup') {
      if (formData.password !== formData.confermaPassword) {
        setError('Le password non corrispondono');
        return;
      }
      try {
        // 1. Se insegnante, carica prima il CV
        if (formData.ruolo === 'insegnante' && formData.cv) {
          const uploadResult = await uploadCV(formData.cv, formData.nome, formData.cognome);
          formData.cv = uploadResult.file_id;
        }

        // 2. Poi invia i dati di signup
        const signupData = {
          nome: formData.nome,
          cognome: formData.cognome,
          ruolo: formData.ruolo,
          email: formData.email,
          password: formData.password,
          ...(formData.ruolo === 'studente' && {
            corsoDiLaurea: formData.corsoDiLaurea,
            numeroDiMatricola: parseInt(formData.numeroDiMatricola, 10) || undefined,
          }),
          ...(formData.ruolo === 'insegnante' && {
            infoMail: formData.infoMail,
            sitoWeb: formData.sitoWeb,
            ricevimento: formData.ricevimento,
            cv: formData.cv,
          }),
        };
        await axios.post(`${HOST}/signup`, signupData);
        setSuccess('Registrazione avvenuta con successo! Effettua il login.');
        setSignupStep(1);
        setMode('login');
        setFormData({
          nome: '',
          cognome: '',
          sesso: '',
          eta: '',
          corsoDiLaurea: '',
          numeroDiMatricola: '',
          infoMail: '',
          sitoWeb: '',
          cv: '',
          ricevimento: '',
          ruolo: 'studente',
          email: '',
          password: '',
          confermaPassword: '',
        });
      } catch (err) {
        const msg = err.response?.data?.detail;
        if (msg === 'Email già registrata') {
          setError('Questa email è già stata registrata');
        } else if (msg) {
          setError(msg);
        } else {
          setError('Errore durante la registrazione');
        }
      }
    } else {
      // LOGIN
      if (!formData.email || !formData.password) {
        setError('Inserisci sia email che password');
        return;
      }
      try {
        const loginData = {
          email: formData.email,
          password: formData.password,
        };
        const response = await axios.post(`${HOST}/login`, loginData);
        const { access_token } = response.data;
        localStorage.setItem('token', access_token);
        setTimeout(() => {
          router.push('/homepage/chat');
        }, 500);
      } catch (err) {
        const msg = err.response?.data?.detail;
        if (msg === 'Utente non valido') {
          setError('Email non registrata');
        } else if (msg === 'Password non valida') {
          setError('Password errata');
        } else {
          setError('Errore durante il login');
        }
      }
    }
  };

  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => {
        setSuccess('');
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [success]);

  return (
    <div className="min-h-screen flex flex-col bg-white text-black">

      <div className="fixed top-4 right-4 z-50 space-y-2">
        {success && (
          <div className="px-4 py-2 rounded-lg bg-green-600 text-white shadow-lg">
            {success}
          </div>
        )}
        {error && (
          <div className="px-4 py-2 rounded-lg bg-red-600 text-white shadow-lg">
            {error}
          </div>
        )}
      </div>

      <main className="flex-1 flex items-center justify-center px-6">
        <div className="w-full max-w-sm">
          <AnimatePresence mode="wait">
            <motion.div
              key={mode}
              initial={{ x: mode === 'login' ? 100 : -100, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: mode === 'login' ? -100 : 100, opacity: 0 }}
              transition={{ duration: 0.4 }}
              className="space-y-6"
            >
              <div className="text-center mb-6">
                <h1 className="text-2xl font-bold text-[#822433]">
                  {mode === 'login' ? 'Bentornato!' : ''}
                </h1>
              </div>

              <form className="space-y-4" onSubmit={handleSubmit}>
                {error && (
                  <div className="text-[#822433] text-sm text-center mb-4">
                    {error}
                  </div>
                )}
                {mode === 'signup' && signupStep === 1 && (
                  <>
                    <div className="flex items-center justify-center mb-4">
                      <span className={`mr-2 font-semibold ${formData.ruolo !== 'insegnante' ? 'text-[#822433]' : 'text-gray-400'}`}>Studente</span>
                      <button
                        type="button"
                        className={`w-14 h-7 flex items-center rounded-full p-1 duration-300 ease-in-out ${formData.ruolo === 'insegnante' ? 'bg-[#822433]' : 'bg-gray-300'}`}
                        onClick={() =>
                          setFormData(prev => ({
                            ...prev,
                            ruolo: prev.ruolo === 'insegnante' ? 'studente' : 'insegnante'
                          }))
                        }
                      >
                        <div
                          className={`bg-white w-5 h-5 rounded-full shadow-md transform duration-300 ease-in-out ${formData.ruolo === 'insegnante' ? 'translate-x-7' : ''}`}
                        />
                      </button>
                      <span className={`ml-2 font-semibold ${formData.ruolo === 'insegnante' ? 'text-[#822433]' : 'text-gray-400'}`}>Insegnante</span>
                    </div>
                    <InputField
                      name="nome"
                      placeholder="Nome"
                      required
                      value={formData.nome}
                      onChange={handleChange}
                    />
                    <InputField
                      name="cognome"
                      placeholder="Cognome"
                      required
                      value={formData.cognome}
                      onChange={handleChange}
                    />
                    {formData.ruolo === 'studente' && (
                      <SignupStudente formData={formData} handleChange={handleChange} />
                    )}
                    {formData.ruolo === 'insegnante' && (
                      <SignupInsegnante formData={formData} handleChange={handleChange} setFormData={setFormData} />
                    )}
                    <Button type="button" onClick={() => setSignupStep(2)} className="w-full bg-[#822433] hover:bg-red-900 text-[#822433] rounded-xl py-3">Avanti</Button>
                  </>
                )}

                {((mode === 'signup' && signupStep === 2) || mode === 'login') && (
                  <>
                    {mode === 'signup' && (
                      <button type="button" onClick={() => setSignupStep(1)} className="text-sm text-[#822433] underline">← Indietro</button>
                    )}
                    <InputField
                      type="email"
                      name="email"
                      placeholder="Email"
                      value={formData.email}
                      onChange={handleChange}
                    />
                    <div className="relative">
                      <InputField
                        type={showPassword ? 'text' : 'password'}
                        name="password"
                        placeholder="Password"  
                        value={formData.password}
                        onChange={handleChange}
                        style={{ paddingRight: '2.5rem' }}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(prev => !prev)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-2xl text-[#822433] focus:outline-none focus:ring-2 focus:ring-[#822433] focus:bg-[#fbeaec] rounded-full"
                        aria-label={showPassword ? "Nascondi password" : "Mostra password"}
                      >
                        {showPassword ? <IoMdEye /> : <IoMdEyeOff />}
                      </button>
                    </div>
                    {mode === 'signup' && (
                      <InputField
                        type={showPassword ? 'text' : 'password'}
                        name="confermaPassword"
                        placeholder="Conferma Password"
                        value={formData.confermaPassword}
                        onChange={handleChange}
                      />
                    )}
                    <Button 
                      type="default" 
                      className="w-full hover:bg-red-900">
                      {mode === 'login' ? 'Accedi' : 'Registrati'}
                    </Button>
                  </>
                )}
              </form>

              <p className="text-center text-sm italic">
                {mode === 'login' ? "Non hai un account?" : 'Hai già un account?'}{' '}
                <button
                  onClick={toggleMode}
                  className="text-[#822433] font-medium hover:underline ml-1"
                >
                  {mode === 'login' ? 'Registrati' : 'Accedi'}
                </button>
              </p>
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}