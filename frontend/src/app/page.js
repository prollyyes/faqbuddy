"use client";
import { useState } from "react";

export default function Home() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  async function sendMessage(e) {
    e.preventDefault();
    if (!input.trim()) return;
    setLoading(true);
    setMessages((msgs) => [...msgs, { role: "user", text: input }]);
    const res = await fetch("http://localhost:8000/classify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: input }),
    });
    const data = await res.json();
    setMessages((msgs) => [
      ...msgs,
      {
        role: "bot",
        text: (
          <>
            <div>
              <b>Chosen:</b> {data.chosen}
              {data.fallback_used ? (
                <span className="ml-2 text-yellow-700">(Fallback on LLM)</span>
              ) : (
                <span className="ml-2 text-green-700">(ML used)</span>
              )}
            </div>
            <div>
              <b>ML:</b> {data.ml_model}{" "}
              <span className="text-xs text-gray-500">
                (confidence: {(data.ml_confidence * 100).toFixed(1)}%)
              </span>
            </div>
            <div>
              <b>Gemma3:4b:</b> {data.gemma3_4b ?? <span className="text-gray-400">n/a</span>}
            </div>
          </>
        ),
      },
    ]);
    setInput("");
    setLoading(false);
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8 bg-gray-100">
      <h1 className="text-2xl font-bold mb-4 text-black">Chatbot Classificatore</h1>
      <div className="w-full max-w-xl bg-white rounded shadow p-4 mb-4 min-h-[300px]">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`mb-2 ${
              msg.role === "user" ? "text-blue-700" : "text-green-700"
            }`}
          >
            <b>{msg.role === "user" ? "Tu" : "Bot"}:</b>{" "}
            {typeof msg.text === "string" ? msg.text : msg.text}
          </div>
        ))}
        {loading && <div className="text-gray-800">Sto pensando...</div>}
      </div>
      <form onSubmit={sendMessage} className="flex w-full max-w-xl">
        <input
          className="flex-1 border rounded-l px-3 py-2 text-black"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Scrivi una domanda..."
          disabled={loading}
        />
        <button
          className="bg-blue-600 text-white px-4 py-2 rounded-r"
          type="submit"
          disabled={loading}
        >
          Invia
        </button>
      </form>
    </div>
  );
}