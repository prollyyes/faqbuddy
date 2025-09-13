'use client'
import React, { useEffect, useState } from "react";
import Chart from "@/components/pages/stats/ExamsChart";
import SimulExamModal from "./SimulExamModal";
import { simulatiStore } from "@/components/store/store";
import { useSnapshot } from "valtio";
import SwipeWrapperStudente from "@/components/wrappers/SwipeWrapperStudente";

const HOST = process.env.NEXT_PUBLIC_HOST;

export default function EsamiPage() {
  const [stats, setStats] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [esamiSimulabili, setEsamiSimulabili] = useState([]);
  const simulatiSnap = useSnapshot(simulatiStore);

  useEffect(() => {
    const token = localStorage.getItem("token");
    fetch(`${HOST}/profile/stats`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => setStats(data));
  }, []);

  // Carica i corsi non completati per la simulazione
  useEffect(() => {
    if (!showForm) return;
    const token = localStorage.getItem("token");
    fetch(`${HOST}/courses/not-completed`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => setEsamiSimulabili(data));
  }, [showForm]);

  if (!stats) return <div className="p-8 text-center italic">Caricamento statistiche...</div>;

  // Unisci esami reali e simulati
  const allEsami = [
    ...stats.esami.map((nome, i) => ({
      nome,
      voto: stats.voti[i],
      cfu: stats.cfu[i],
      simulato: false
    })),
    ...simulatiSnap.simulati.map(e => ({ ...e, simulato: true }))
  ];

  const MIN_COLONNE = 6;
  const allEsamiGrafico = allEsami.length < MIN_COLONNE
    ? [
        ...allEsami,
        ...Array.from({ length: MIN_COLONNE - allEsami.length }, (_, i) => ({
          nome: "",
          voto: null,
          cfu: null,
          simulato: false,
          placeholder: true,
        }))
      ]
    : allEsami;

  // Ricalcola le medie con gli esami simulati
  const mediaAritmetica = allEsami.length
    ? (allEsami.reduce((sum, e) => sum + Number(e.voto), 0) / allEsami.length).toFixed(2)
    : 0;
  const mediaPonderata = allEsami.reduce((sum, e) => sum + Number(e.voto) * Number(e.cfu), 0) /
    (allEsami.reduce((sum, e) => sum + Number(e.cfu), 0) || 1);

  return (
    <SwipeWrapperStudente>
      <div className="min-h-screen bg-white pt-20 px-6 text-[#822433] overflow-auto">
        <div className="space-y-4">
          {/* Grafico voti per materia */}
          <div className="bg-white rounded-lg p-4">
            <h2 className="text-lg font-semibold mb-2 text-center italic">Andamento Voti</h2>
            <div className="w-full">
              <Chart data={allEsamiGrafico.map(e => ({
                corso: e.nome,
                voto: e.voto,
                simulato: e.simulato,
                placeholder: e.placeholder
              }))} />
            </div>
          </div>

          <div className="bg-white rounded-lg p-4 flex flex-col md:flex-row justify-between items-stretch gap-6">
            {/* Colonna sinistra: Tabella esami compatta */}
            <div className="bg-white rounded-lg p-2 w-full max-w-md">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-base font-semibold">Esami sostenuti</h2>
                <button
                  className="bg-[#822433] text-white rounded-full w-7 h-7 flex items-center justify-center text-lg"
                  onClick={() => setShowForm(!showForm)}
                  title="Simula un nuovo esame"
                >+</button>

                <SimulExamModal
                  open={showForm}
                  onClose={() => setShowForm(false)}
                  esami={esamiSimulabili}
                  onAdd={esame => simulatiStore.simulati.push(esame)}
                />
              </div>
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
                    {allEsami.map((e, i) => (
                      <tr
                        key={i}
                        className={`border-t ${e.simulato ? "bg-yellow-50 text-yellow-800" : ""}`}
                      >
                        <td className="px-2 py-1 flex items-center gap-2">
                          {e.nome}
                          {e.simulato && (
                            <button
                              type="button"
                              className="ml-2 text-yellow-700 hover:text-yellow-900 font-bold rounded-full px-2 py-0.5 border border-yellow-300 bg-yellow-100"
                              title="Rimuovi esame simulato"
                              onClick={() => {
                                simulatiStore.simulati.splice(i - stats.esami.length, 1);
                              }}
                            >
                              -
                            </button>
                          )}
                        </td>
                        <td className="px-2 py-1">{e.voto}</td>
                        <td className="px-2 py-1">{e.cfu}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="font-bold bg-gray-50 border-t">
                      <td className="px-2 py-1">Totale</td>
                      <td className="px-2 py-1 whitespace-nowrap">
                        <span className="flex flex-col gap-1">
                          <span className="inline-block bg-gray-100 text-[#822433] rounded px-2 py-0.5 text-xs font-semibold">
                            MA: {mediaAritmetica}
                          </span>
                          <span className="inline-block bg-gray-200 text-[#822433] rounded px-2 py-0.5 text-xs font-semibold">
                            MP: {mediaPonderata.toFixed(2)}
                          </span>
                        </span>
                      </td>
                      <td className="px-2 py-1 whitespace-nowrap">
                        {allEsami.reduce((sum, e) => sum + Number(e.cfu), 0)} / {stats.cfu_totali}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          </div>
        </div>
        <div className="h-35" />
      </div>
    </SwipeWrapperStudente>
  );
}