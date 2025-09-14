'use client'
import React, { useEffect, useState } from "react";
import MobileSheet from "@/components/utils/MobileSheet";
import { IoMdEye, IoMdEyeOff } from "react-icons/io";

const HOST = process.env.NEXT_PUBLIC_HOST;

export default function ChangePasswordModal({ open, onClose }) {
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showOld, setShowOld] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [sheetOpen, setSheetOpen] = useState(open);

  useEffect(() => {
    if (open) setSheetOpen(true);
  }, [open]);

  const softClose = () => {
    setSheetOpen(false);
    setTimeout(() => onClose?.(), 240);
  };

  if (!open && !sheetOpen) return null;

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
        softClose();
      }, 500);
    } catch (err) {
      setError("Errore: " + err.message);
    }
  };

  return (
    <MobileSheet open={sheetOpen} onClose={softClose} title="Cambia password" footer={
      <button
        type="submit"
        form="change-password-form"
        className="w-full bg-[#991B1B] text-white rounded-lg py-2 font-semibold hover:opacity-90"
      >
        Cambia password
      </button>
    }>
        <form id="change-password-form" onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div className="relative">
            <input
              type={showOld ? "text" : "password"}
              placeholder="Vecchia password"
              className="border rounded px-3 py-2 w-full pr-10"
              value={oldPassword}
              onChange={e => setOldPassword(e.target.value)}
            />
            <button
              type="button"
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500"
              onClick={() => setShowOld(v => !v)}
              aria-label={showOld ? "Nascondi password" : "Mostra password"}
            >
              {showOld ? <IoMdEyeOff size={20}/> : <IoMdEye size={20}/>} 
            </button>
          </div>

          <div className="relative">
            <input
              type={showNew ? "text" : "password"}
              placeholder="Nuova password"
              className="border rounded px-3 py-2 w-full pr-10"
              value={newPassword}
              onChange={e => setNewPassword(e.target.value)}
            />
            <button
              type="button"
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500"
              onClick={() => setShowNew(v => !v)}
              aria-label={showNew ? "Nascondi password" : "Mostra password"}
            >
              {showNew ? <IoMdEyeOff size={20}/> : <IoMdEye size={20}/>} 
            </button>
          </div>

          <div className="relative">
            <input
              type={showConfirm ? "text" : "password"}
              placeholder="Conferma nuova password"
              className="border rounded px-3 py-2 w-full pr-10"
              value={confirm}
              onChange={e => setConfirm(e.target.value)}
            />
            <button
              type="button"
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500"
              onClick={() => setShowConfirm(v => !v)}
              aria-label={showConfirm ? "Nascondi password" : "Mostra password"}
            >
              {showConfirm ? <IoMdEyeOff size={20}/> : <IoMdEye size={20}/>} 
            </button>
          </div>
          {error && <div className="text-red-600 text-sm">{error}</div>}
          {success && <div className="text-green-600 text-sm">{success}</div>}
        </form>
    </MobileSheet>
  );
}
