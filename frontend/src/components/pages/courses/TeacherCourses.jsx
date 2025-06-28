import React, { useEffect, useState } from "react";
import axios from "axios";
import { EditionsModal } from "@/components/pages/courses/EditionsModal";

export default function TeacherCourses() {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [refresh, setRefresh] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    axios
      .get("http://localhost:8000/teacher/courses/full", {
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

  if (loading) return <div className="p-8 text-center">Caricamento corsi...</div>;
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
      className="bg-white border border-[#991B1B] rounded-lg shadow p-4 min-w-[220px] max-w-xs flex flex-col items-center cursor-pointer hover:bg-gray-100 transition"
      onClick={() => setSelectedCourse(corso)}
    >
      <h3 className="text-lg font-semibold text-[#991B1B] mb-2">{corso.nome}</h3>
      <div className="text-sm text-gray-700 mb-1">
        CFU: <span className="font-bold">{corso.cfu}</span>
      </div>
      <div className="text-sm text-gray-700 mb-1">
        Edizioni: <span className="font-bold">{corso.edizioni.length}</span>
      </div>
    </div>
  );

  return (
    <div className="flex flex-col p-4 min-h-screen pb-24 pt-20">
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
    </div>
  );
}