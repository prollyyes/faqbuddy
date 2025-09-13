import React from "react";
import Button from "@/components/utils/Button";
import { IoClose } from "react-icons/io5";

export default function RestoreConfirmModal({ open, onClose, onConfirm }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm backdrop-brightness-75">
      <div className="relative bg-white border-2 border-[#991B1B] rounded-lg shadow-2xl p-6 w-80 max-w-full text-center">
        <button
          className="absolute top-2 right-2 text-2xl text-[#822433] hover:text-[#a00028] font-black focus:outline-none"
          onClick={onClose}
          aria-label="Chiudi"
        >
          <IoClose />
        </button>
        <h3 className="text-lg font-black mb-2 text-[#991B1B]">Sei sicuro?</h3>
        <p className="text-sm text-gray-700 mb-4">
          Ripristinando questo corso tra gli attivi <span className="font-semibold text-[#991B1B]">tutte le recensioni e i materiali caricati andranno persi</span>.<br />
          Vuoi continuare?
        </p>
        <div className="flex justify-center gap-4 mt-4">
          {/* <Button variant="outline" className="px-4 py-2" onClick={onClose}>
            Annulla
          </Button> */}
          <Button className="px-4 py-2" onClick={onConfirm}>
            Continua
          </Button>
        </div>
      </div>
    </div>
  );
}