"use client";

import React, { useState } from "react";
import Button from "@/components/utils/Button";
import { IoReturnUpBackOutline } from "react-icons/io5";
import { AnimatePresence, motion } from "framer-motion";

export default function MaterialsPage() {
  const [view, setView] = useState("default"); // default, research, upload

  const renderContent = () => {
    let content;

    switch (view) {
      case "research":
        content = (
          <motion.div
            key="research"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
            className="w-full max-w-xl px-6 pb-36 text-[#822433] space-y-6 flex flex-col justify-center items-center pt-24"
          >
            {/* Bottone per tornare indietro */}
            <div className="absolute top-16 left-4">
              <Button onClick={() => setView("default")}>
                <IoReturnUpBackOutline className="text-xl" />
              </Button>
            </div>

            {/* Intestazione */}
            <h2 className="text-2xl font-bold pt-12 self-start">Ricerca Materiali</h2>

            {/* Select per Corso di Laurea */}
            <div className="space-y-2 w-full max-w-md">
              <label className="block font-semibold">Corso di Laurea</label>
              <select className="w-full border border-[#822433] rounded-md px-4 py-2 focus:outline-none text-black">
                <option>Ingegneria Informatica</option>
                <option>Economia</option>
                <option>Psicologia</option>
              </select>
            </div>

            {/* Select per Corso */}
            <div className="space-y-2 w-full max-w-md">
              <label className="block font-semibold">Corso</label>
              <select className="w-full border border-[#822433] rounded-md px-4 py-2 focus:outline-none text-black">
                <option>Algoritmi</option>
                <option>Microeconomia</option>
                <option>Psicologia Generale</option>
              </select>
            </div>

            {/* Input per Anno + Bottone Cerca */}
            <div className="flex items-end gap-4 w-full max-w-md">
              <div className="flex-1 space-y-2">
                <label className="block font-semibold">Anno</label>
                <input
                  type="text"
                  maxLength={4}
                  className="w-full border border-[#822433] rounded-md px-4 py-2 focus:outline-none text-black placeholder-black"
                  placeholder="Es. 2024"
                />
              </div>
              <div className="pb-[0.3px]">
                <Button className="px-6 py-2 text-sm">Cerca</Button>
              </div>
            </div>
          </motion.div>
        );
        break;

      case "upload":
        content = (
          <motion.div
            key="upload"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
            className="w-full max-w-xl px-6 pb-35 text-[#822433] space-y-6 flex flex-col justify-start"
          >
            {/* Bottone per tornare indietro */}
            <div className="absolute top-16 left-4">
              <Button onClick={() => setView("default")}>
                <IoReturnUpBackOutline className="text-xl" />
              </Button>
            </div>

            {/* Intestazione */}
            <h2 className="text-2xl font-bold pt-12">Carica materiale</h2>

            {/* Input per Corso di Laurea */}
            <div className="space-y-2">
              <label className="block font-semibold">Corso di Laurea</label>
              <input
                type="text"
                className="w-full border border-[#822433] rounded-md px-4 py-2 focus:outline-none"
                placeholder="Inserisci il corso di laurea"
              />
            </div>

            {/* Input per Nome Corso */}
            <div className="space-y-2">
              <label className="block font-semibold">Nome Corso</label>
              <input
                type="text"
                className="w-full border border-[#822433] rounded-md px-4 py-2 focus:outline-none"
                placeholder="Inserisci il nome del corso"
              />
            </div>

            {/* Bottoni */}
            <div className="flex justify-between pt-4">
              <Button className="px-4 py-2 text-sm">Valutazione</Button>
              <Button className="px-4 py-2 text-sm">Appunti</Button>
              <Button className="px-4 py-2 text-sm">Info</Button>
            </div>
          </motion.div>
        );
        break;

      default:
        content = (
          <motion.div
            key="default"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
            className="w-full flex flex-col items-center space-y-6"
          >
            <div className="flex justify-center">
              <Button
                className="text-xl py-4 px-6 w-full max-w-md"
                onClick={() => setView("upload")}
              >
                Aiuta il tuo Buddy
              </Button>
            </div>
            <div className="flex justify-center w-full max-w-md mx-auto">
              <Button
                className="text-xl py-3 px-6 w-full"
                onClick={() => setView("research")}
              >
                Ricerca Materiali
              </Button>
            </div>
          </motion.div>
        );
        break;
    }

    return <AnimatePresence mode="wait">{content}</AnimatePresence>;
  };

  return (
    <div className="h-screen flex flex-col justify-center items-center bg-white px-6 text-[#822433] space-y-8">
      {renderContent()}
    </div>
  );
}
