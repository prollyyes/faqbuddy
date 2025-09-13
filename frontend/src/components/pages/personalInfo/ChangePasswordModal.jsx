'use client'
import React, { useState } from "react";
import MobileSheet from "@/components/utils/MobileSheet";

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
    <MobileSheet open={open} onClose={onClose} title="Cambia password" footer={
      <button
        type="submit"
        form="change-password-form"
        className="w-full bg-[#991B1B] text-white rounded-lg py-2 font-semibold hover:opacity-90"
      >
        Cambia password
      </button>
    }>
        <form id="change-password-form" onSubmit={handleSubmit} className="flex flex-col gap-3">
          <input
            type="password"
            placeholder="Vecchia password"
            className="border rounded px-3 py-2"
            value={oldPassword}
            onChange={e => setOldPassword(e.target.value)}
          />
          <input
            type="password"
            placeholder="Nuova password"
            className="border rounded px-3 py-2"
            value={newPassword}
            onChange={e => setNewPassword(e.target.value)}
          />
          <input
            type="password"
            placeholder="Conferma nuova password"
            className="border rounded px-3 py-2"
            value={confirm}
            onChange={e => setConfirm(e.target.value)}
          />
          {error && <div className="text-red-600 text-sm">{error}</div>}
          {success && <div className="text-green-600 text-sm">{success}</div>}
        </form>
    </MobileSheet>
  );
}
