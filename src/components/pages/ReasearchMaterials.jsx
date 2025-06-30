'use client'

import React from "react";
import { motion } from "framer-motion";
import BackButton from "../utils/BackButton";
import Button from "../utils/Button";

export default function UploadMaterials() {
  return (
    <div className="h-screen flex flex-col justify-center items-center bg-white px-6 text-[#822433] space-y-8">
        <motion.div
            key="research"
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 50 }}
            transition={{ duration: 0.3 }}
            className="w-full max-w-xl px-6 pb-36 text-[#822433] space-y-6 flex flex-col justify-center items-center pt-24"
          >
            {/* Intestazione */}
            <h2 className="text-2xl font-bold pt-4 self-start">Ricerca Materiali</h2>

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
        </div>
  );
}
