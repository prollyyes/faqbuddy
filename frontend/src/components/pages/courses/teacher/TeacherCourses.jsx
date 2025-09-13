import React, { useEffect, useState } from "react";
import axios from "axios";
import { EditionsModal } from "@/components/pages/courses/teacher/EditionsModal";
import { AddEditionModal } from "@/components/pages/courses/teacher/AddEditionModal";

const HOST = process.env.NEXT_PUBLIC_HOST;

export default function TeacherCourses() {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [refresh, setRefresh] = useState(false);

  // Stato per la modale
  const [showAddModal, setShowAddModal] = useState(false);
  const [allCourses, setAllCourses] = useState([]);

  useEffect(() => {
    const token = localStorage.getItem("token");
    axios
      .get(`${HOST}/teacher/courses/full`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      .then(res => {
        setCourses(res.data);
        setLoading(false);
      })
      .catch(() => {
        setError("Errore nel caricamento dei corsi");
        setLoading(false);
      });
  }, [refresh]);

  // Carica tutti i corsi insegnati per la select della modale
  const openAddModal = async () => {
    setShowAddModal(true);
    const token = localStorage.getItem("token");
    try {
      const res = await axios.get(`${HOST}/courses/all`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAllCourses(res.data);
    } catch {
      setAllCourses([]);
    }
  };

  if (loading) return <div className="p-8 text-center italic">Caricamento corsi...</div>;
  if (error) return <div className="p-8 text-center text-red-600">{error}</div>;

  // Split courses
  const activeCourses = courses.filter(corso =>
    corso.edizioni.some(ed => ed.stato === "attivo")
  );
  const pastCourses = courses.filter(
    corso => corso.edizioni.every(ed => ed.stato !== "attivo")
  );

  const renderCourseBox = corso => (
    <div
      key={corso.id}
      className="bg-white border border-[#991B1B] rounded-lg shadow p-4 min-w-[220px] max-w-xs w-64 h-32 flex flex-col justify-between cursor-pointer hover:bg-gray-100 transition"
      onClick={() => setSelectedCourse(corso)}
      style={{ aspectRatio: "4/3" }}
    >
      <div className="flex items-start">
        <h3 className="text-lg font-semibold text-[#991B1B]">{corso.nome}</h3>
      </div>
      <div className="flex justify-end items-end gap-4 mt-auto">
        <div className="text-xs text-gray-700">
          CFU: <span className="font-bold">{corso.cfu}</span>
        </div>
        <div className="text-xs text-gray-700">
          Edizioni: <span className="font-bold">{corso.edizioni.length}</span>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex flex-col p-4 min-h-screen pb-24 pt-20">
      <div className="flex justify-end mb-4">
        <button
          className="bg-[#991B1B] text-white rounded-full w-10 h-10 flex items-center justify-center text-2xl shadow hover:bg-red-800 transition"
          onClick={openAddModal}
          title="Aggiungi nuova edizione"
        >
          +
        </button>
      </div>
      <h2 className="text-2xl font-bold text-[#991B1B] mb-6 text-center">Corsi che insegni</h2>
      <div className="flex flex-wrap gap-4 justify-center mb-10">
        {activeCourses.length === 0 && (
          <div className="text-gray-500 text-center">Nessun corso attivo trovato.</div>
        )}
        {activeCourses.map(renderCourseBox)}
      </div>
      <h2 className="text-2xl font-bold text-[#991B1B] mb-6 text-center">Corsi che hai insegnato</h2>
      <div className="flex flex-wrap gap-4 justify-center">
        {pastCourses.length === 0 && (
          <div className="text-gray-500 text-center">Nessun corso archiviato/annullato trovato.</div>
        )}
        {pastCourses.map(renderCourseBox)}
      </div>
      {selectedCourse && (
        <EditionsModal
          corso={selectedCourse}
          onClose={() => setSelectedCourse(null)}
          onUpdateStato={() => setRefresh(r => !r)}
        />
      )}
      <AddEditionModal
        show={showAddModal}
        onClose={() => setShowAddModal(false)}
        courses={allCourses}
        onSuccess={() => setRefresh(r => !r)}
      />
    </div>
  );
}