'use client';

import React, { Component, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Button from '@/components/utils/Button';
import Link from 'next/link';
import { FiArrowRight } from "react-icons/fi";


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
  const isLast = index === steps.length - 1;

  /**
   * Go to next step unless we are already on the final screen.
   */
  const handleNext = () => {
    setIndex(current => (current < steps.length - 1 ? current + 1 : current));
  };

  const handleSkip = () => {
    setIndex(steps.length-1)
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-between pt-20 py-6 px-4 bg-white gap-6">
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
    <AnimatePresence mode="wait" initial={false}>
        <motion.section
            key={index}
            drag="x"
            dragConstraints={{ left: 0, right: 0 }}
            onDragEnd={(e, info) => {
            if (info.offset.x < -50 && index < steps.length - 1) {
                handleNext();
            } else if (info.offset.x > 50 && index > 0) {
                setIndex(current => current - 1);
            }
            }}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.4 }}
            className="flex-1 flex flex-col items-center justify-center text-center space-y-4 px-2"
        >
            <motion.div
            className="w-64 h-64 rounded-2xl flex items-center justify-center overflow-hidden"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2 }}
            >
            <img
                src={steps[index].image}
                alt={`Step ${index + 1}`}
                className="object-contain w-full h-full"
            />
            </motion.div>

            <h2 className="text-2xl font-semibold text-black">{steps[index].title}</h2>
            <p className="text-sm text-black max-w-xs">{steps[index].description}</p>
        </motion.section>
    </AnimatePresence>

      {/* ---------------------------------------------------------- */}
      {/* Dots Indicator                                            */}
      {/* ---------------------------------------------------------- */}
      <div className="flex gap-2 mb-4 mt-1">
        {steps.map((_, i) => (
          <span
            key={i}
            className={`w-2.5 h-2.5 rounded-full ${i === index ? 'bg-[#822433]' : 'bg-black'}`}
          />
        ))}
      </div>

      {/* ---------------------------------------------------------- */}
      {/* Action Button                                             */}
      {/* ---------------------------------------------------------- */}
      <div className="w-full mb-2 mt-auto">
        {isLast ? (
          <Link href="/auth" className="w-full block">
            <Button className={`w-full bg-[#822433] hover:bg-red-900 text-[#822433] rounded-xl text-lg font-medium`}>
              Get Started
            </Button>
          </Link>
        ) : (
          <Button
            onClick={handleNext}
            className={`w-full py-3  bg-[#822433] hover:bg-red-900 text-[#822433] rounded-xl text-lg font-medium`}
          >
            Next
          </Button>
        )}
      </div>
    </div>
  );
}