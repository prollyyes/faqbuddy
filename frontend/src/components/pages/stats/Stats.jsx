"use client";

import React, { useEffect, useState } from "react";
import Chart from "@/components/pages/stats/ExamsChart";


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
    // { corso: "", voto: null },
    // { corso: "", voto: null },
    // { corso: "", voto: null },
    // { corso: "", voto: null },
    // { corso: "", voto: null }
  ];

  return (
    <div className="min-h-screen bg-white pt-30 px-6 text-[#822433] overflow-auto">
      {/* <h1 className="text-2xl font-bold mb-6">Statistiche Esami</h1> */}

      <div className="space-y-4">
        {/* Grafico voti per materia */}
        
        <div className="bg-white rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-2">Andamento Voti</h2>
          <div className="w-full">
            <Chart data={chartData} />
          </div>
        </div>

        <div className="bg-white rounded-lg p-4 flex flex-col md:flex-row justify-between items-stretch gap-6">
          
          {/* Colonna destra: Anello CFU piccolo */}
          {/* <div className="flex justify-center items-center w-full md:w-1/2">
            <ProgressRing
              current={stats.cfu_completati}
              total={stats.cfu_totali}
              type="CFU"
              className="w-16 h-16"
            />
          </div> */}
          
                    {/* Colonna sinistra: Tabella esami compatta */}
          <div className="bg-white rounded-lg p-2 w-full max-w-md">
            <h2 className="text-base font-semibold mb-2">Esami sostenuti</h2>
            <div className="overflow-x-auto">
              <table className="w-full border border-gray-300 rounded text-sm">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="px-2 py-2 text-left">Esame</th>
                    <th className="px-2 py-2 text-left">Voto</th>
                    <th className="px-2 py-2 text-left">CFU</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.esami.map((nome, i) => (
                    <tr key={i} className="border-t">
                      <td className="px-2 py-1">{nome}</td>
                      <td className="px-2 py-1">{stats.voti[i]}</td>
                      <td className="px-2 py-1">{stats.cfu[i]}</td>
                      </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          
        </div>
      </div>
      <div className="h-35" />
    </div>
  );
}