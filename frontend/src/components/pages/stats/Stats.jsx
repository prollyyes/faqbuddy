"use client";

import React, { useEffect, useState } from "react";
import Button from "@/components/utils/Button";
import Chart from "@/components/pages/stats/ExamsChart";
import { LuCirclePlus } from "react-icons/lu";
import ProgressRing from "@/components/utils/ProgressRing";

export default function EsamiPage() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    fetch("http://localhost:8000/profile/stats", {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => setStats(data));
  }, []);

  if (!stats) return <div className="p-8 text-center">Caricamento statistiche...</div>;

  // Prepara dati per il grafico
  let chartData = stats.esami.map((corso, i) => ({
    corso,
    voto: stats.voti[i]
  }));
  chartData = [
    ...chartData,
    { corso: "", voto: null },
    { corso: "", voto: null },
    { corso: "", voto: null },
    { corso: "", voto: null },
    { corso: "", voto: null },
    { corso: "", voto: null },
    { corso: "", voto: null },
    { corso: "", voto: null },
    { corso: "", voto: null },
    { corso: "", voto: null },
    { corso: "", voto: null },
    { corso: "", voto: null },
    { corso: "", voto: null },
    { corso: "", voto: null }
  ];

  return (
    <div className="min-h-screen bg-white pt-30 px-6 text-[#822433] overflow-auto">
      <h1 className="text-2xl font-bold mb-6">Statistiche Esami</h1>

      <div className="space-y-4">
        {/* Grafico voti per materia */}
        
        <div className="bg-white rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-2">Andamento Voti per Materia</h2>
          <div className="w-full">
            <Chart data={chartData} />
          </div>
        </div>

        {/* Anelli di completamento */}
        <div className="flex flex-row justify-around items-stretch gap-6 bg-white rounded-lg p-4">
          <ProgressRing current={stats.voti.length} total={40} type='esami' className="w-3/4 md:w-auto" />
          <ProgressRing current={stats.cfu_completati} total={stats.cfu_totali} type='CFU' className="w-3/4 md:w-auto" />
        </div>

        {/* Sezione statistiche generiche */}
        <div className="bg-white rounded-lg p-4 flex flex-col md:flex-row justify-between items-start gap-6">
          <div className="space-y-2 w-full md:w-1/2">
            <div className="flex gap-2">
              <span className="font-bold">Esami sostenuti:</span>
              <span>{stats.voti.length}</span>
            </div>
            <div className="flex gap-2">
              <span className="font-bold">Media aritmetica:</span>
              <span>{stats.media_aritmetica}</span>
            </div>
            <div className="flex gap-2">
              <span className="font-bold">Media ponderata:</span>
              <span>{stats.media_ponderata}</span>
            </div>
          </div>
        </div>
      </div>
      <div className="h-35" />
    </div>
  );
}