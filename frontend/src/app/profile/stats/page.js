"use client";

import React from "react";
import Button from "@/components/utils/Button";

export default function EsamiPage() {
  return (
    <div className="min-h-screen bg-white p-6 text-[#822433]">
      <h1 className="text-2xl font-bold mb-6">Statistiche Esami</h1>

      <div className="space-y-4">
        {/* Sezione statistiche generiche */}
        <div className="bg-white rounded-lg shadow border border-[#822433] p-4">
          <h2 className="text-lg font-semibold mb-2">Esami sostenuti</h2>
          <p className="text-sm">Totale: 12</p>
          <p className="text-sm">Media: 27.3</p>
        </div>

        {/* Altre statistiche future qui */}
      </div>

      {/* Bottone per aggiungere esame */}
      <div className="fixed bottom-24 w-full px-6">
        <Button className="w-full">Aggiungi nuovo esame</Button>
      </div>
    </div>
  );
}
