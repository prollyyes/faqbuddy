'use client'
import React, { useState } from "react";
import axios from "axios";
import MobileSheet from "@/components/utils/MobileSheet";

const HOST = process.env.NEXT_PUBLIC_HOST;

export function AddEditionModal({ show, onClose, courses, onSuccess }) {
    const [form, setForm] = useState({
        corso_id: "",
        data: "",
        orario: "",
        esonero: false,
        mod_Esame: "",
        stato: "attivo"
    });
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    // Opzioni per la data (S1/anno, S2/anno)
    const anni = [];
    for (let anno = 2015; anno <= 2027; anno++) {
        anni.push(anno);
    }
    const semestri = ["S1", "S2"];
    const opzioniData = [];
    anni.forEach(anno => {
        semestri.forEach(sem => opzioniData.push(`${sem}/${anno}`));
    });

    const handleChange = e => {
        const { name, value, type, checked } = e.target;
        setForm(f => ({
            ...f,
            [name]: type === "checkbox" ? checked : value
        }));
    };

    const handleSubmit = async e => {
        e.preventDefault();
        setError("");
        setLoading(true);
        const token = localStorage.getItem("token");
        // Stampa il payload che verrà inviato
        console.log({
            data: form.data,
            orario: form.orario,
            esonero: form.esonero,
            mod_Esame: form.mod_Esame,
            stato: form.stato
        });
        try {
            await axios.post(
                `${HOST}/teacher/courses/${form.corso_id}/editions/add`,
                {
                    insegnante: "",
                    data: form.data,
                    orario: form.orario,
                    esonero: form.esonero,
                    mod_Esame: form.mod_Esame,
                    stato: form.stato
                },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setLoading(false);
            onSuccess();
            onClose();
        } catch (err) {
            setError("Errore durante l'aggiunta dell'edizione");
            setLoading(false);
        }
    };

    return (
        <MobileSheet open={show} onClose={onClose} title="Aggiungi nuova edizione" footer={
            <button
                type="submit"
                form="add-edition-form"
                className="w-full bg-[#991B1B] text-white rounded-lg py-2 font-semibold hover:opacity-90"
                disabled={loading}
            >
                {loading ? "Salvataggio..." : "Aggiungi edizione"}
            </button>
        }>
            <form id="add-edition-form" className="space-y-3" onSubmit={handleSubmit}>
                    <div>
                        <label className="block mb-1 font-medium text-black">Corso</label>
                        <select
                            name="corso_id"
                            value={form.corso_id}
                            onChange={handleChange}
                            required
                            className="w-full border rounded px-3 py-2 text-black"
                        >
                            <option value="">Seleziona corso</option>
                            {courses.map(c => (
                                <option key={c.id} value={c.id}>
                                    {c.nome}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="block mb-1 font-medium text-black">Semestre</label>
                        <select
                            name="data"
                            value={form.data}
                            onChange={handleChange}
                            required
                            className="w-full border rounded px-3 py-2 text-black"
                        >
                            <option value="">Seleziona semestre</option>
                            {opzioniData.map(opt => (
                                <option key={opt} value={opt}>{opt}</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="block mb-1 font-medium text-black">Orario</label>
                        <input
                            name="orario"
                            value={form.orario}
                            onChange={handleChange}
                            className="w-full border rounded px-3 py-2 text-black"
                            placeholder="Orario lezioni"
                        />
                    </div>
                    <div>
                        <label className="block mb-1 font-medium text-black">Modalità Esame</label>
                        <input
                            name="mod_Esame"
                            value={form.mod_Esame}
                            onChange={handleChange}
                            className="w-full border rounded px-3 py-2 text-black"
                            placeholder="Es: scritto, orale..."
                        />
                    </div>
                    <div className="flex items-center gap-2 text-black">
                        <input
                            type="checkbox"
                            name="esonero"
                            checked={form.esonero}
                            onChange={handleChange}
                            id="esonero"
                        />
                        <label htmlFor="esonero">Esonero previsto</label>
                    </div>
                    <div>
                        <label className="block mb-1 font-medium text-black">Stato</label>
                        <select
                            name="stato"
                            value={form.stato}
                            onChange={handleChange}
                            className="w-full border rounded px-3 py-2 text-black"
                        >
                            <option value="attivo">Attivo</option>
                            <option value="archiviato">Archiviato</option>
                            <option value="annullato">Annullato</option>
                        </select>
                    </div>
                    {error && <div className="text-red-600 text-sm">{error}</div>}
            </form>
        </MobileSheet>
    );
}
