'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import Button from '@/components/utils/Button';
import axios from 'axios';
import { useRouter } from 'next/navigation';

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
    annoDiImmatricolazione: '',
    numeroDiMatricola: '',
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
      annoDiImmatricolazione: '',
      numeroDiMatricola: '',
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
        const signupData = {
          nome: formData.nome,
          cognome: formData.cognome,
          sesso: formData.sesso,
          eta: formData.eta,
          corsoDiLaurea: formData.corsoDiLaurea,
          annoDiImmatricolazione: formData.annoDiImmatricolazione,
          numeroDiMatricola: formData.numeroDiMatricola,
          email: formData.email,
          password: formData.password,
        };
        await axios.post('http://127.0.0.1:8000/signup', signupData);
        setSuccess('Registrazione avvenuta con successo! Effettua il login.');
        setSignupStep(1);
        setMode('login');
        setFormData({
          nome: '',
          cognome: '',
          sesso: '',
          eta: '',
          corsoDiLaurea: '',
          annoDiImmatricolazione: '',
          numeroDiMatricola: '',
          email: '',
          password: '',
          confermaPassword: '',
        });
      } catch (err) {
        const msg = err.response?.data?.detail;
        if (msg === 'Email già registrata') {
          setError('Questa email è già stata registrata');
        } else {
          setError('Errore durante la registrazione');
        }
      }
    } else {
      try {
        const loginData = {
          email: formData.email,
          password: formData.password,
        };
        const response = await axios.post('http://127.0.0.1:8000/login', loginData);
        // Save user_id as token in localStorage
        const { access_token } = response.data;
        localStorage.setItem('token', access_token);
        // attende che localStorage sia "committed" prima del redirect
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
      }, 5000);
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

      {/* Content below header */}
      <main className="flex-1 flex items-center justify-center pt-36 px-6">
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
              <h2 className="text-2xl font-semibold text-center">
                {mode === 'login' ? 'Accedi al tuo account' : 'Crea un nuovo account'}
              </h2>

              <form className="space-y-4" onSubmit={handleSubmit}>
                {error && (
                  <div className="text-[#822433] text-sm text-center mb-4">
                    {error}
                  </div>
                )}
                {mode === 'signup' && signupStep === 1 && (
                  <>
                    <input
                      type="text"
                      name="nome"
                      placeholder="Nome"
                      required
                      value={formData.nome}
                      onChange={handleChange}
                      className="w-full border border-gray-300 px-4 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#822433]"
                    />
                    <input
                      type="text"
                      name="cognome"
                      placeholder="Cognome"
                      required
                      value={formData.cognome}
                      onChange={handleChange}
                      className="w-full border border-gray-300 px-4 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#822433]"
                    />
                    <input
                      type="text"
                      name="sesso"
                      placeholder="Sesso"
                      value={formData.sesso}
                      onChange={handleChange}
                      className="w-full border border-gray-300 px-4 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#822433]"
                    />
                    <input
                      type="number"
                      name="eta"
                      placeholder="Età"
                      value={formData.eta}
                      onChange={handleChange}
                      className="w-full border border-gray-300 px-4 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#822433]"
                    />
                    <input
                      type="text"
                      name="corsoDiLaurea"
                      placeholder="Corso di laurea"
                      value={formData.corsoDiLaurea}
                      onChange={handleChange}
                      className="w-full border border-gray-300 px-4 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#822433]"
                    />
                    <input
                      type="text"
                      name="annoDiImmatricolazione"
                      placeholder="Anno di immatricolazione"
                      value={formData.annoDiImmatricolazione}
                      onChange={handleChange}
                      className="w-full border border-gray-300 px-4 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#822433]"
                    />
                    <input
                      type="text"
                      name="numeroDiMatricola"
                      placeholder="Numero di matricola"
                      value={formData.numeroDiMatricola}
                      onChange={handleChange}
                      className="w-full border border-gray-300 px-4 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#822433]"
                    />
                    <Button type="button" onClick={() => setSignupStep(2)} className="w-full bg-[#822433] hover:bg-red-900 text-[#822433] rounded-xl py-3">Avanti</Button>
                  </>
                )}

                {((mode === 'signup' && signupStep === 2) || mode === 'login') && (
                  <>
                    {mode === 'signup' && (
                      <button type="button" onClick={() => setSignupStep(1)} className="text-sm text-[#822433] underline">← Indietro</button>
                    )}
                    <input
                      type="email"
                      name="email"
                      placeholder="Email"
                      value={formData.email}
                      onChange={handleChange}
                      className="w-full border border-gray-300 px-4 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#822433]"
                    />
                    <div className="relative">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        name="password"
                        placeholder="Password"
                        value={formData.password}
                        onChange={handleChange}
                        className="w-full border border-gray-300 px-4 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#822433] pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(prev => !prev)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-sm text-[#822433] focus:outline-none"
                      >
                        {showPassword ? 'Nascondi' : 'Mostra'}
                      </button>
                    </div>
                    {mode === 'signup' && (
                      <input
                        type={showPassword ? 'text' : 'password'}
                        name="confermaPassword"
                        placeholder="Conferma Password"
                        value={formData.confermaPassword}
                        onChange={handleChange}
                        className="w-full border border-gray-300 px-4 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#822433]"
                      />
                    )}
                    <Button type="submit" className="w-full bg-[#822433] hover:bg-red-900 text-[#822433] rounded-xl py-3">
                      {mode === 'login' ? 'Accedi' : 'Registrati'}
                    </Button>
                  </>
                )}
              </form>

              <p className="text-center text-sm">
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