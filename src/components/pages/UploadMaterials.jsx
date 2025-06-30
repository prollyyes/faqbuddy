'use client' 

import React from "react";
import { motion } from "framer-motion";
import Button from "../utils/Button";

export default function UploadMaterials() {
  return (
    <div className="h-screen flex flex-col justify-center items-center bg-white px-6 text-[#822433] space-y-8">
      <motion.div
          key="upload"
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 50 }}
          transition={{ duration: 0.3 }}
          className="w-full max-w-xl px-6 pb-35 text-[#822433] space-y-6 flex flex-col justify-start pt-16"
        >

          {/* Intestazione */}
          <h2 className="text-2xl font-bold pt-4">Carica materiale</h2>

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
      </div>
  );
}
