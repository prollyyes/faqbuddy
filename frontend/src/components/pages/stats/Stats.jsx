'use client'
import React, { useEffect, useMemo, useState } from "react";
import Chart from "@/components/pages/stats/ExamsChart";
import SimulExamModal from "./SimulExamModal";
import { simulatiStore } from "@/components/store/store";
import { useSnapshot } from "valtio";
import SwipeWrapperStudente from "@/components/wrappers/SwipeWrapperStudente";
import ProgressRing from "@/components/utils/ProgressRing";

const HOST = process.env.NEXT_PUBLIC_HOST;

export default function EsamiPage() {
  const [stats, setStats] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [esamiSimulabili, setEsamiSimulabili] = useState([]);
  const [filter, setFilter] = useState('all'); // all | real | simulated
  const simulatiSnap = useSnapshot(simulatiStore);
  const isLoading = !stats;

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

  // Dati reali e simulati (safe su loading)
  const realEsami = useMemo(() => {
    if (!stats) return [];
    return stats.esami.map((nome, i) => ({
      nome,
      voto: stats.voti[i],
      cfu: stats.cfu[i],
    }));
  }, [stats]);

  const allEsami = useMemo(() => ([
    ...realEsami.map(e => ({ ...e, simulato: false })),
    ...simulatiSnap.simulati.map(e => ({ ...e, simulato: true }))
  ]), [realEsami, simulatiSnap.simulati]);

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

  // Medie reali e con simulazioni
  const simulatedEsami = simulatiSnap.simulati;

  const mediaAritmeticaReale = realEsami.length
    ? (realEsami.reduce((sum, e) => sum + Number(e.voto), 0) / realEsami.length)
    : 0;
  const mediaAritmeticaTot = allEsami.length
    ? (allEsami.reduce((sum, e) => sum + Number(e.voto), 0) / allEsami.length)
    : 0;

  const mediaPonderataReale = realEsami.reduce((sum, e) => sum + Number(e.voto) * Number(e.cfu), 0) /
    (realEsami.reduce((sum, e) => sum + Number(e.cfu), 0) || 1);
  const mediaPonderataTot = allEsami.reduce((sum, e) => sum + Number(e.voto) * Number(e.cfu), 0) /
    (allEsami.reduce((sum, e) => sum + Number(e.cfu), 0) || 1);

  const cfuReali = realEsami.reduce((sum, e) => sum + Number(e.cfu), 0);
  const cfuTotali = stats?.cfu_totali || 0;
  const cfuConSimulati = allEsami.reduce((sum, e) => sum + Number(e.cfu), 0);

  const filteredEsami = useMemo(() => {
    if (filter === 'real') return allEsami.filter(e => !e.simulato);
    if (filter === 'simulated') return allEsami.filter(e => e.simulato);
    return allEsami;
  }, [allEsami, filter]);

  // Rimuove un esame simulato cercandolo nella store per valori
  const removeSimulato = (exam) => {
    const idx = simulatiStore.simulati.findIndex(s =>
      s.nome === exam.nome && Number(s.voto) === Number(exam.voto) && Number(s.cfu) === Number(exam.cfu)
    );
    if (idx !== -1) simulatiStore.simulati.splice(idx, 1);
  };

  return (
    <SwipeWrapperStudente>
      <div className="min-h-screen bg-white pt-20 pb-24 px-4 text-[#822433]">
        {isLoading ? (
          <div className="space-y-4 animate-pulse mt-4">
            <div className="h-5 bg-gray-200 rounded w-24" />
            <div className="h-40 bg-gray-200 rounded" />
            <div className="h-5 bg-gray-200 rounded w-32" />
            <div className="h-48 bg-gray-200 rounded" />
          </div>
        ) : (
          <>
            {/* KPI compact header */}
            <section className="mt-4">
              <div className="flex items-center justify-between">
                <h1 className="text-lg font-semibold">Statistiche</h1>
              </div>
              <div className="mt-3 grid grid-cols-3 gap-3">
                <div className="col-span-1 flex items-center justify-center">
                  <ProgressRing current={cfuReali} total={cfuTotali} type="CFU" />
                </div>
              <div className="col-span-2 grid grid-cols-2 gap-2">
                <div className="rounded-lg border border-gray-200 p-3">
                  <div className="text-[10px] text-gray-500 uppercase">MA</div>
                  <div className="text-xl font-bold">{mediaAritmeticaReale.toFixed(2)}</div>
                  {Math.abs(mediaAritmeticaTot - mediaAritmeticaReale) > 0.009 && (
                    <div className="text-[11px] text-amber-700 mt-1">Sim: {mediaAritmeticaTot.toFixed(2)}</div>
                  )}
                </div>
                <div className="rounded-lg border border-gray-200 p-3">
                  <div className="text-[10px] text-gray-500 uppercase">MP</div>
                  <div className="text-xl font-bold">{mediaPonderataReale.toFixed(2)}</div>
                  {Math.abs(mediaPonderataTot - mediaPonderataReale) > 0.009 && (
                    <div className="text-[11px] text-amber-700 mt-1">Sim: {mediaPonderataTot.toFixed(2)}</div>
                  )}
                </div>
              </div>
              </div>
            </section>

            {/* Chart */}
            <section className="mt-5">
              <div className="rounded-lg border border-gray-200 p-3">
                <h2 className="text-sm font-semibold mb-2">Andamento voti</h2>
                <div className="w-full">
                  <Chart data={allEsamiGrafico.map(e => ({
                    corso: e.nome,
                    voto: e.voto,
                    simulato: e.simulato,
                    placeholder: e.placeholder
                  }))} />
                </div>
              </div>
            </section>

            {/* Filters */}
            <section className="mt-5">
              <div className="inline-flex bg-gray-100 rounded-full p-1 text-sm">
                <button
                  className={`px-3 py-1 rounded-full ${filter==='all' ? 'bg-white shadow text-[#822433]' : 'text-gray-500'}`}
                  onClick={() => setFilter('all')}
                >Tutti</button>
                <button
                  className={`px-3 py-1 rounded-full ${filter==='real' ? 'bg-white shadow text-[#822433]' : 'text-gray-500'}`}
                  onClick={() => setFilter('real')}
                >Reali</button>
                <button
                  className={`px-3 py-1 rounded-full ${filter==='simulated' ? 'bg-white shadow text-[#822433]' : 'text-gray-500'}`}
                  onClick={() => setFilter('simulated')}
                >Simulati {simulatiSnap.simulati.length ? `(${simulatiSnap.simulati.length})` : ''}</button>
              </div>
            </section>

            {/* Primary action */}
            <section className="mt-5">
              <button
                className="w-full bg-[#822433] text-white rounded-xl py-3 text-center shadow active:opacity-90"
                onClick={() => setShowForm(true)}
              >
                Simula esame
              </button>
            </section>

            {/* Exams list */}
            <section className="mt-4">
              <div className="space-y-2">
                {filteredEsami.map((e, i) => (
                  <div
                    key={`${e.nome}-${i}`}
                    className={`flex items-center justify-between rounded-lg border ${e.simulato ? 'border-amber-200 bg-amber-50' : 'border-gray-200 bg-white'} px-3 py-2`}
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium truncate">{e.nome}</p>
                        {e.simulato && (
                          <span className="text-[10px] font-semibold text-amber-800 bg-amber-100 border border-amber-200 rounded-full px-2 py-0.5">Simulato</span>
                        )}
                      </div>
                      <p className="text-xs text-gray-500 mt-0.5">CFU {e.cfu}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-base font-bold">{e.voto}</span>
                      {e.simulato && (
                        <button
                          type="button"
                          aria-label="Rimuovi esame simulato"
                          className="w-8 h-8 rounded-full border border-amber-300 text-amber-700 bg-amber-100 text-lg leading-none"
                      onClick={() => removeSimulato(e)}
                      >
                        −
                      </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <SimulExamModal
              open={showForm}
              onClose={() => setShowForm(false)}
              esami={esamiSimulabili}
              onAdd={esame => simulatiStore.simulati.push(esame)}
            />
          </>
        )}
      </div>
    </SwipeWrapperStudente>
  );
}
