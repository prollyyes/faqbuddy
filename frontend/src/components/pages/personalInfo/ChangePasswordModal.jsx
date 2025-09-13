import React, { useState } from "react";

const HOST = process.env.NEXT_PUBLIC_HOST;

export default function ChangePasswordModal({ open, onClose }) {
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  if (!open) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (!oldPassword || !newPassword || !confirm) {
      setError("Compila tutti i campi");
      return;
    }
    if (newPassword !== confirm) {
      setError("Le nuove password non coincidono");
      return;
    }
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${HOST}/profile/change-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          old_password: oldPassword,
          new_password: newPassword,
        }),
      });
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg);
      }
      setSuccess("Password cambiata con successo!");
      setTimeout(() => {
        setSuccess("");
        onClose();
      }, 1200);
    } catch (err) {
      setError("Errore: " + err.message);
    }
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50 backdrop-blur-sm backdrop-brightness-75">
      <div className="relative bg-white/90 p-6 rounded-lg shadow-2xl w-[22rem] max-w-full border-2 border-[#991B1B]">
        <button
          className="absolute top-2 right-2 text-gray-500 hover:text-red-700 text-xl"
          onClick={onClose}
          aria-label="Chiudi"
        >
          &times;
        </button>
        <h2 className="text-lg font-bold mb-4 text-[#991B1B]">Cambia password</h2>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <input
            type="password"
            placeholder="Vecchia password"
            className="border rounded px-2 py-1"
            value={oldPassword}
            onChange={e => setOldPassword(e.target.value)}
          />
          <input
            type="password"
            placeholder="Nuova password"
            className="border rounded px-2 py-1"
            value={newPassword}
            onChange={e => setNewPassword(e.target.value)}
          />
          <input
            type="password"
            placeholder="Conferma nuova password"
            className="border rounded px-2 py-1"
            value={confirm}
            onChange={e => setConfirm(e.target.value)}
          />
          {error && <div className="text-red-600 text-sm">{error}</div>}
          {success && <div className="text-green-600 text-sm">{success}</div>}
          <button
            type="submit"
            className="bg-[#991B1B] text-white rounded px-3 py-1 mt-3 hover:bg-red-800"
          >
            Cambia password
          </button>
        </form>
      </div>
    </div>
  );
}