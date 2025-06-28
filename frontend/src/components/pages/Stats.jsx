"use client";

import React from "react";
import Button from "@/components/utils/Button";
import Chart from "@/components/utils/ExamsChart";
import { LuCirclePlus } from "react-icons/lu";
import ProgressRing from "@/components/utils/ProgressRing";

export default function EsamiPage() {
  return (
    <div className="min-h-screen bg-white pt-30 px-6 text-[#822433] overflow-auto">
      <h1 className="text-2xl font-bold mb-6">Statistiche Esami</h1>

      <div className="space-y-4">
        {/* Grafico voti per materia */}
        <div className="bg-white rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-2">Andamento Voti per Materia</h2>
          <div className="w-fit max-w-full overflow-x-auto">
            <Chart
              data={[
                { corso: "Analisi 1", voto: 28 },
                { corso: "Analisi 2", voto: 27 },
                { corso: "Fisica 1", voto: 26 },
                { corso: "Fisica 2", voto: 29 },
                { corso: "Algebra Lineare", voto: 30 },
                { corso: "Geometria", voto: 27 },
                { corso: "Chimica", voto: 24 },
                { corso: "Programmazione", voto: 30 },
                { corso: "Strutture Dati", voto: 28 },
                { corso: "Sistemi Operativi", voto: 26 },
                { corso: "Basi di Dati", voto: 29 },
                { corso: "Reti", voto: 27 },
                { corso: "Ingegneria del Software", voto: 30 },
                { corso: "Intelligenza Artificiale", voto: 28 },
                { corso: "Machine Learning", voto: 30 },
                { corso: "Calcolo Numerico", voto: 25 },
                { corso: "Ricerca Operativa", voto: 26 },
                { corso: "Probabilità", voto: 27 },
                { corso: "Statistica", voto: 28 },
                { corso: "Automatica", voto: 26 },
                { corso: "Controlli", voto: 29 },
                { corso: "Visione Artificiale", voto: 30 },
                { corso: "Robotica", voto: 28 },
                { corso: "Logica", voto: 27 },
                { corso: "Compilatori", voto: 29 },
                { corso: "Cloud Computing", voto: 30 },
                { corso: "Cybersecurity", voto: 27 },
                { corso: "Blockchain", voto: 25 },
                { corso: "Etica dell’IA", voto: 30 },
                { corso: "Imprenditorialità", voto: 26 }
              ]}
            />
          </div>
        </div>

        {/* Anelli di completamento */}
        <div className="flex flex-row justify-around items-stretch gap-6 bg-white rounded-lg p-4">
          <ProgressRing current={30} total={40} type='esami' className="w-3/4 md:w-auto" />
          <ProgressRing current={150} total={180} type='CFU' className="w-3/4 md:w-auto" />
        </div>

        {/* Sezione statistiche generiche unificata */}
        <div className="bg-white rounded-lg p-4 flex flex-col md:flex-row justify-between items-start gap-6">
          {/* Statistiche Esami */}
          <div className="space-y-2 w-full md:w-1/2">
            <div className="flex gap-2">
              <span className="font-bold">Esami sostenuti:</span>
              <span>30</span>
            </div>
            <div className="flex gap-2">
              <span className="font-bold">Media aritmetica:</span>
              <span>27.3</span>
            </div>
            <div className="flex gap-2">
              <span className="font-bold">Media ponderata:</span>
              <span>27.8</span>
            </div>
          </div>
        </div>

        {/* Altre statistiche future qui */}
      </div>

      {/* Bottone per aggiungere esame */}
      <div className="fixed bottom-24 left-1/2 transform -translate-x-1/2 px-6">
        <Button className="flex items-center justify-start gap-3 py-3 px-8 text-lg whitespace-nowrap w-full">
          <LuCirclePlus className="text-xl" />
          <span>Aggiungi Esame</span>
        </Button>
      </div>

      <div className="h-35" />
    </div>
  );
}
