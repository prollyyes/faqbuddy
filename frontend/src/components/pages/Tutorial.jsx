'use client';

import React, { Component, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Button from '@/components/utils/Button';
import Link from 'next/link';
import { FiArrowRight } from "react-icons/fi";
import CardDeck from '@/components/utils/CardDeck';


/* ------------------------------------------------------------------
 * Static content
 * ------------------------------------------------------------------ */


const steps = [
  {
    title: 'Benvenuto in FAQBuddy',
    description: `Chiedi a un Buddy tutto ciò che ti serve sull'università.`,
    image: '/tutorial_img/step1.1-removebg-preview.png'
  },
  {
    title: 'Cerca qualsiasi cosa',
    description: 'Scopri la ricerca con i superpoteri grazie alla nostra AI specializzata',
    image: '/tutorial_img/step2.png'
  },
  {
    title: 'Materiale Verificato',
    description: 'Accesso ad un database di appunti, testi di esame e dispense verificati',
    image: '/tutorial_img/step3.png'
  },
  {
    title: 'Entra a far parte della community di FAQBuddy',
    description: '',
    image: '/tutorial_img/step4.png'
  }
];

/* ------------------------------------------------------------------
 * Component
 * ------------------------------------------------------------------ */

export default function Tutorial() {
  const [index, setIndex] = useState(0);
  const [deckDirection, setDeckDirection] = useState(null);
  const isLast = index === steps.length - 1;

  /**
   * Go to next step unless we are already on the final screen.
   */
  const handleNext = () => {
    setDeckDirection(1);
    setIndex(current => (current < steps.length - 1 ? current + 1 : current));
    setTimeout(() => setDeckDirection(null), 320);
  };

  const handleSkip = () => {
    setDeckDirection(1);
    setIndex(steps.length-1)
    setTimeout(() => setDeckDirection(null), 320);
  }

  return (
  <div className="min-h-screen flex flex-col items-center justify-between pt-12 pb-24 px-4 bg-white gap-6 relative">
      {/* Non mi piace questo bottone piazzato cosi */}
      {/* <div className="absolute top-25 right-8">
        <button 
          onClick={handleSkip} 
          className="text-xl text-[#822433] hover:underline"
        >
          Skip
        </button>
      </div> */}
      {/* ---------------------------------------------------------- */}
      {/* Animated Step Content                                     */}
      {/* ---------------------------------------------------------- */}
  <div className="w-full flex-1 flex flex-col items-center justify-center">
      <div className="w-full max-w-2xl">
      <CardDeck
        items={steps.map((s, idx)=>({ id: idx, title: s.title, subtitle: s.description, content: '', image: s.image }))}
        index={index}
        controlledDirection={deckDirection}
        onIndexChange={(newIndex) => {
          const dir = newIndex - index;
          setDeckDirection(dir);
          setIndex(newIndex);
          setTimeout(() => setDeckDirection(null), 320);
        }}
      />
      </div>
  </div>

      {/* ---------------------------------------------------------- */}
      {/* Dots Indicator                                            */}
      {/* ---------------------------------------------------------- */}
      {/* no dots; keep UI focused on cards */}

      {/* ---------------------------------------------------------- */}
      {/* Action Button                                             */}
      {/* ---------------------------------------------------------- */}
      <AnimatePresence>
        {isLast && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            transition={{ duration: 0.25 }}
            className="w-full max-w-2xl px-4 md:px-0 fixed bottom-8 left-1/2 -translate-x-1/2"
          >
            <Link href="/auth" className="w-full block">
              <Button size="lg" className={`w-full rounded-xl text-xl`}>
                Get Started
              </Button>
            </Link>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}