'use client'
import React, { useEffect, useState } from "react";
import Chart from "@/components/pages/stats/ExamsChart";

export default function EsamiPage() {
  const [stats, setStats] = useState(null);
  const [simulati, setSimulati] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [newExam, setNewExam] = useState({ nome: "", voto: "", cfu: "" });

  useEffect(() => {
    const token = localStorage.getItem("token");
    fetch("http://localhost:8000/profile/stats", {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => setStats(data));
  }, []);
  if (!stats) return <div className="p-8 text-center">Caricamento statistiche...</div>;

  // Unisci esami reali e simulati
  const allEsami = [
    ...stats.esami.map((nome, i) => ({
      nome,
      voto: stats.voti[i],
      cfu: stats.cfu[i],
      simulato: false
    })),
    ...simulati.map(e => ({ ...e, simulato: true }))
  ];


  // Ricalcola le medie con gli esami simulati
  const mediaAritmetica = allEsami.length
    ? (allEsami.reduce((sum, e) => sum + Number(e.voto), 0) / allEsami.length).toFixed(2)
    : 0;
  const mediaPonderata = allEsami.reduce((sum, e) => sum + Number(e.voto) * Number(e.cfu), 0) /
    (allEsami.reduce((sum, e) => sum + Number(e.cfu), 0) || 1);

  return (
    <div className="min-h-screen bg-white pt-30 px-6 text-[#822433] overflow-auto">
      <div className="space-y-4">
        {/* Grafico voti per materia */}
        <div className="bg-white rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-2 text-center">Andamento Voti</h2>
          <div className="w-full">
            <Chart data={allEsami.map(e => ({ corso: e.nome, voto: e.voto, simulato: e.simulato }))} />
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
            </div>
            {showForm && (
              <form
                className="flex gap-2 mb-2"
                onSubmit={e => {
                  e.preventDefault();
                  setSimulati([...simulati, { ...newExam, voto: Number(newExam.voto), cfu: Number(newExam.cfu) }]);
                  setNewExam({ nome: "", voto: "", cfu: "" });
                  setShowForm(false);
                }}
              >
                <input
                  required
                  className="border rounded px-2 py-1 text-sm"
                  placeholder="Nome"
                  value={newExam.nome}
                  onChange={e => setNewExam({ ...newExam, nome: e.target.value })}
                />
                <input
                  required
                  type="number"
                  min={18}
                  max={30}
                  className="border rounded px-2 py-1 text-sm w-16"
                  placeholder="Voto"
                  value={newExam.voto}
                  onChange={e => setNewExam({ ...newExam, voto: e.target.value })}
                />
                <input
                  required
                  type="number"
                  min={1}
                  className="border rounded px-2 py-1 text-sm w-16"
                  placeholder="CFU"
                  value={newExam.cfu}
                  onChange={e => setNewExam({ ...newExam, cfu: e.target.value })}
                />
                <button className="bg-[#822433] text-white rounded px-2 py-1 text-sm" type="submit">OK</button>
              </form>
            )}
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
                              setSimulati(simulati.filter((_, idx) => idx !== i - stats.esami.length));
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
  );
}