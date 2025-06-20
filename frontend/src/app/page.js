"use client";
import { useState } from "react";

export default function Home() {
  const [input, setInput] = useState("");
  const [result, setResult] = useState(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [elapsed, setElapsed] = useState(null);

  const [data, setData] = useState(null);
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setQuery("");
    setElapsed(null);
    setData(null);
    const start = performance.now();
    try {
      const res = await fetch("http://localhost:8000/t2sql", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: input }),
      });
      const data = await res.json();
      setResult(data.result);
      setQuery(data.query);
      setData(data); // salva tutta la risposta per info extra
    } catch (err) {
      setResult("Errore nella richiesta");
      setQuery("");
      setData(null);
    }
    const end = performance.now();
    setElapsed(((end - start) / 1000).toFixed(2));
    setLoading(false);
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-start bg-white py-12">
      <div className="w-full max-w-xl bg-white rounded-lg shadow p-8 text-black">
        <h1 className="text-2xl font-bold mb-6 text-center text-black">FAQBuddy</h1>
        <form onSubmit={handleSubmit} className="flex gap-2 mb-4">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Fai una domanda..."
            className="flex-1 border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 text-black bg-white"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition"
          >
            {loading ? "Attendi..." : "Invia"}
          </button>
        </form>
        {elapsed && (
          <div className="mb-2 text-sm text-black">
            Tempo di risposta: <span className="font-mono">{elapsed} s</span>
          </div>
        )}
        {query && (
          <div className="mb-4">
            <div className="font-semibold text-black">Query SQL generata:</div>
            <pre className="bg-gray-100 rounded p-2 mt-1 text-sm overflow-x-auto text-black">{query}</pre>
          </div>
        )}        
        {result && (
          <div>
            <div className="font-semibold text-black">Risultato:</div>
            {Array.isArray(result) ? (
              <pre className="bg-gray-100 rounded p-2 mt-1 text-sm overflow-x-auto text-black">
                {JSON.stringify(result, null, 2)}
              </pre>
            ) : (
              <pre className="bg-gray-100 rounded p-2 mt-1 text-sm overflow-x-auto text-black">{result}</pre>
            )}
            {/* Mostra info aggiuntive se presenti */}
            <div className="mt-4 text-black text-sm">
              {data?.chosen && (
                <div>
                  <span className="font-semibold">Pipeline scelta:</span> {data.chosen}
                </div>
              )}
              {data?.ml_model && (
                <div>
                  <span className="font-semibold">ML model:</span> {data.ml_model}
                </div>
              )}
              {typeof data?.ml_confidence === "number" && (
                <div>
                  <span className="font-semibold">Confidenza ML:</span> {data.ml_confidence.toFixed(2)}
                </div>
              )}
              {data?.retrieval_time && (
                <div>
                  <span className="font-semibold">Retrieval time (RAG):</span> {data.retrieval_time}s
                </div>
              )}
              {data?.generation_time && (
                <div>
                  <span className="font-semibold">Generation time (RAG):</span> {data.generation_time}s
                </div>
              )}
              {data?.total_time && (
                <div>
                  <span className="font-semibold">Total time (RAG):</span> {data.total_time}s
                </div>
              )}
              {data?.context_used && (
                <div>
                  <span className="font-semibold">Context usato (RAG):</span>
                  <pre className="bg-gray-100 rounded p-2 mt-1 text-xs overflow-x-auto text-black">{data.context_used}</pre>
                </div>
              )}
            </div>
          </div>
        )}        
      </div>
    </main>
  );
}