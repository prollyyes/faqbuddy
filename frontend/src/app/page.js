"use client";
import { useState, useEffect, useRef } from "react";

export default function Home() {
  const [input, setInput] = useState("");
  const [result, setResult] = useState(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [elapsed, setElapsed] = useState(null);
  const [inlineSuggestion, setInlineSuggestion] = useState("");
  const [data, setData] = useState(null);

  // Inline autocomplete logic
  useEffect(() => {
    if (input.length > 0) {
      fetch(`http://localhost:8000/autocomplete?q=${encodeURIComponent(input)}`)
        .then((res) => res.json())
        .then((data) => {
          const sug = (data.suggestions || []).find(s => s.toLowerCase().startsWith(input.toLowerCase()));
          setInlineSuggestion(sug && sug.length > input.length ? sug : "");
        })
        .catch(() => setInlineSuggestion(""));
    } else {
      setInlineSuggestion("");
    }
  }, [input]);

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
      setData(data);
    } catch (err) {
      setResult("Errore nella richiesta");
      setQuery("");
      setData(null);
    }
    const end = performance.now();
    setElapsed(((end - start) / 1000).toFixed(2));
    setLoading(false);
  };

  // Ref per focus input
  const inputRef = useRef(null);

  return (
    <main className="min-h-screen flex flex-col items-center justify-start bg-white py-12">
      <div className="w-full max-w-xl bg-white rounded-lg shadow p-8 text-black">
        <h1 className="text-2xl font-bold mb-6 text-center text-black">FAQBuddy</h1>
        
        <form onSubmit={handleSubmit} className="mb-4">
          <div
            className="flex-1 border border-gray-300 rounded px-3 py-2 focus-within:ring-2 focus-within:ring-blue-400 bg-white flex items-center relative"
            style={{
              minHeight: "2.5rem",
              fontSize: "1rem",
              cursor: "text",
              fontFamily: "inherit",
              overflow: "hidden",
            }}
            onClick={() => inputRef.current && inputRef.current.focus()}
          >
            {/* Testo digitato + suggerimento inline, tutto in una sola riga */}
            <span
              style={{
                position: "absolute",
                left: 12, // px-3 = 12px
                top: "50%",
                transform: "translateY(-50%)",
                fontFamily: "inherit",
                fontSize: "1rem",
                pointerEvents: "none",
                color: "#111",
                whiteSpace: "pre",
                zIndex: 1,
              }}
            >
              {input}
              <span style={{ color: "#bbb" }}>
                {inlineSuggestion && inlineSuggestion.startsWith(input) ? inlineSuggestion.slice(input.length) : ""}
              </span>
            </span>
            {/* Input vero, trasparente sopra */}
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Fai una domanda..."
              autoComplete="off"
              style={{
                position: "absolute",
                left: 0,
                top: 0,
                width: "100%",
                height: "100%",
                background: "transparent",
                color: "transparent",
                caretColor: "#111",
                border: "none",
                outline: "none",
                fontFamily: "inherit",
                fontSize: "1rem",
                zIndex: 2,
                boxSizing: "border-box",
                paddingLeft: 12,
                paddingRight: 12,
              }}
              onKeyDown={e => {
                if (e.key === "Tab" && inlineSuggestion && inlineSuggestion.startsWith(input)) {
                  e.preventDefault();
                  setInput(inlineSuggestion);
                }
              }}
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition mt-2 w-full"
          >
            {loading ? "Attendi..." : "Invia"}
          </button>
        </form>
        {elapsed && (
          <div className="mb-2 text-sm text-black">
            Tempo di risposta: <span className="font-mono">{elapsed} s</span>
          </div>
        )}

        {data && (
          <div className="mt-6 w-full">
            <div className="font-semibold text-black mb-2">Dettaglio risposta backend:</div>
            <div className="bg-gray-50 rounded p-3 text-black text-sm overflow-x-auto">
              {Object.entries(data).map(([key, value]) => (
                <div key={key} className="mb-1">
                  <span className="font-mono font-semibold">{key}:</span>{" "}
                  {typeof value === "object" && value !== null ? (
                    <pre className="inline bg-gray-100 rounded p-1">{JSON.stringify(value, null, 2)}</pre>
                  ) : (
                    <span>{String(value)}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}