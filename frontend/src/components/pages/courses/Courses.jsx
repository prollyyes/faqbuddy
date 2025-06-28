'use client'
import React, { useEffect, useState } from "react";
import axios from "axios";
import CourseBox from "./CourseBox";
import AddCourseModal from "./AddCourseModal";
import CompleteModal from "./CompleteModal";
import ReviewModal from "./ReviewModal";
import CourseDetailModal from "./CourseDetailModal";
import AddActionModal from "./AddActionModal";


export default function CorsiPage() {
  const [currentCourses, setCurrentCourses] = useState([]);
  const [completedCourses, setCompletedCourses] = useState([]);
  const [showCompleteModal, setShowCompleteModal] = useState(false);
  const [courseToComplete, setCourseToComplete] = useState(null);
  const [completeVoto, setCompleteVoto] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Modale aggiunta corso
  const [showAddModal, setShowAddModal] = useState(false);
  const [availableCourses, setAvailableCourses] = useState([]);
  const [selectedCourseId, setSelectedCourseId] = useState(null);
  const [editions, setEditions] = useState([]);
  const [showAddEdition, setShowAddEdition] = useState(false);
  const [newEdition, setNewEdition] = useState({
    data: "",
    orario: "",
    esonero: "",
    mod_Esame: "",
    docenteNome: "",
    docenteCognome: ""
  });

  // Modale dettaglio corso, quando clicchi su un corso
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [detailCourse, setDetailCourse] = useState(null);

  const handleOpenDetailModal = async (corso) => {
    const token = localStorage.getItem("token");
    const res = await axios.get(
      `http://localhost:8000/courses/editions/${corso.edition_id}/${encodeURIComponent(corso.edition_data)}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    setDetailCourse(res.data);
    setShowDetailModal(true);
  };

  // Modale AddActionModal 
  const [showAddActionModal, setShowAddActionModal] = useState(false);
  const [actionCourse, setActionCourse] = useState(null);


  // Fetch all teachers for the dropdown in the add course modal
  const [docenti, setDocenti] = useState([]);
  useEffect(() => {
    fetch("http://localhost:8000/teachers")
      .then(res => res.json())
      .then(data => setDocenti(data))
      .catch(() => setDocenti([]));
  }, []);

  // Handle reviews
  const [studentReviews, setStudentReviews] = useState([]);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewCourse, setReviewCourse] = useState(null);

  const handleOpenReviewModal = (corso) => {
    setReviewCourse(corso);
    setShowReviewModal(true);
    setError("");
    setSuccess("");
  };

  // Fetch all courses && reviews on mount
  useEffect(() => {
    const token = localStorage.getItem("token");
    axios.get("http://localhost:8000/profile/courses/current", {
      headers: { Authorization: `Bearer ${token}` }
    }).then(res => setCurrentCourses(res.data));

    axios.get("http://localhost:8000/profile/courses/completed", {
      headers: { Authorization: `Bearer ${token}` }
    }).then(res => setCompletedCourses(res.data));

    axios.get("http://localhost:8000/profile/reviews", {
      headers: { Authorization: `Bearer ${token}` }
    }).then(res => setStudentReviews(res.data));
  }, []);

  // --- Completa corso ---
  const handleOpenCompleteModal = (corso) => {
    setCourseToComplete(corso);
    setCompleteVoto("");
    setShowCompleteModal(true);
    setError("");
    setSuccess("");
  };

  const handleCompleteCourse = async () => {
    const token = localStorage.getItem("token");
    if (!completeVoto || isNaN(completeVoto) || completeVoto < 18 || completeVoto > 31) {
      setError("Inserisci un voto valido (18-31)");
      return;
    }
    try {
      await axios.put(
        `http://localhost:8000/profile/courses/${courseToComplete.edition_id}/complete`,
        {
          edition_data: courseToComplete.edition_data,
          voto: Number(completeVoto)
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setShowCompleteModal(false);
      setSuccess("Corso completato!");
      // Aggiorna le liste
      const resCurrent = await axios.get("http://localhost:8000/profile/courses/current", { headers: { Authorization: `Bearer ${token}` } });
      setCurrentCourses(resCurrent.data);
      const resCompleted = await axios.get("http://localhost:8000/profile/courses/completed", { headers: { Authorization: `Bearer ${token}` } });
      setCompletedCourses(resCompleted.data);
    } catch (err) {
      setError("Errore durante il completamento del corso");
    }
  };

  // --- Modale aggiunta corso ---
  const handleOpenAddModal = async () => {
    setShowAddModal(true);
    setSelectedCourseId(null);
    setEditions([]);
    setShowAddEdition(false);
    setError("");
    setSuccess("");
    setNewEdition({
      data: "",
      orario: "",
      esonero: "",
      mod_Esame: "",
      docenteNome: "",
      docenteCognome: ""
    });
    // Carica i corsi disponibili
    const token = localStorage.getItem("token");
    const res = await axios.get("http://localhost:8000/courses/available", {
      headers: { Authorization: `Bearer ${token}` }
    });
    setAvailableCourses(res.data);
  };

  // Quando clicchi su un corso, mostra le sue edizioni
  const handleSelectCourse = async (corsoId) => {
    setSelectedCourseId(corsoId);
    setShowAddEdition(false);
    setNewEdition({
      data: "",
      orario: "",
      esonero: "",
      mod_Esame: "",
      docenteNome: "",
      docenteCognome: ""
    });
    const token = localStorage.getItem("token");
    const res = await axios.get(`http://localhost:8000/courses/${corsoId}/editions`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    setEditions(res.data);
  };

  // Iscrizione a una edizione
  const handleEnroll = async (corso_id, edition_id, edition_data) => {
    const token = localStorage.getItem("token");
    try {
      await axios.post(
        `http://localhost:8000/courses/${corso_id}/editions/${edition_id}/enroll`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSuccess("Iscrizione avvenuta!");
      // Non chiudere la modale subito, lascia che l'utente decida
      // setShowAddModal(false);
      // Aggiorna corsi attivi
      const resCurrent = await axios.get("http://localhost:8000/profile/courses/current", { headers: { Authorization: `Bearer ${token}` } });
      setCurrentCourses(resCurrent.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Errore durante l'iscrizione");
    }
  };

  // --- Aggiungi nuova edizione ---
  const handleAddEdition = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem("token");
    try {
      const insegnanteId = newEdition.docenteId;
      // Crea nuova edizione e iscrivi lo studente
      await axios.post(
        `http://localhost:8000/courses/${selectedCourseId}/editions/add`,
        {
          insegnante: insegnanteId,
          data: newEdition.data,
          orario: newEdition.orario,
          esonero: newEdition.esonero, // booleano!
          mod_Esame: newEdition.mod_Esame,
          stato: "attivo"
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSuccess("Edizione aggiunta e iscritto!");
      // Non chiudere la modale subito, lascia che l'utente decida
      // setShowAddModal(false);
      // Aggiorna corsi attivi
      const resCurrent = await axios.get("http://localhost:8000/profile/courses/current", { headers: { Authorization: `Bearer ${token}` } });
      setCurrentCourses(resCurrent.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Errore durante l'aggiunta dell'edizione");
    }
  };

  // --- Aggiungi recensione ---
  const handleAddReview = async (corso, descrizione, voto) => {
    const token = localStorage.getItem("token");
    try {
      await axios.post(
        "http://localhost:8000/profile/reviews",
        {
          edition_id: corso.edition_id,
          edition_data: corso.edition_data,
          descrizione,
          voto
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSuccess("Recensione aggiunta!");
      // Aggiorna le recensioni
      const res = await axios.get("http://localhost:8000/profile/reviews", {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStudentReviews(res.data);
      setShowReviewModal(false);
    } catch (err) {
      setError(err.response?.data?.detail || "Errore durante l'invio della recensione");
    }
  };

  // Funzione per ripristinare un corso tra quelli attivi
  const handleRestoreCourse = async (corso) => {
    const token = localStorage.getItem("token");
    try {
      await axios.put(
        `http://localhost:8000/profile/courses/${corso.edition_id}/restore`,
        { edition_data: corso.edition_data },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSuccess("Corso riportato tra quelli attivi!");
      // Aggiorna le liste
      const resCurrent = await axios.get("http://localhost:8000/profile/courses/current", { headers: { Authorization: `Bearer ${token}` } });
      setCurrentCourses(resCurrent.data);
      const resCompleted = await axios.get("http://localhost:8000/profile/courses/completed", { headers: { Authorization: `Bearer ${token}` } });
      setCompletedCourses(resCompleted.data);
      // Aggiorna recensioni
      const resReviews = await axios.get("http://localhost:8000/profile/reviews", { headers: { Authorization: `Bearer ${token}` } });
      setStudentReviews(resReviews.data);
    } catch (err) {
      setError("Errore durante il ripristino del corso");
    }
  };

  const handleOpenActionModal = (corso) => {
    setActionCourse(corso);
    setShowAddActionModal(true);
    setError("");
    setSuccess("");
  };

  return (
    <div className="flex flex-col p-4 min-h-screen pb-24 pt-20">
      {showCompleteModal && (
        <CompleteModal
          courseToComplete={courseToComplete}
          completeVoto={completeVoto}
          setCompleteVoto={setCompleteVoto}
          error={error}
          setShowCompleteModal={setShowCompleteModal}
          handleCompleteCourse={handleCompleteCourse}
        />
      )}

      {/* Pulsante centrato in alto */}
      <div className="flex justify-center mb-6 mt-8">
        <button
          className="px-4 py-2 bg-[#991B1B] text-white rounded hover:bg-red-800"
          onClick={handleOpenAddModal}
        >
          + Aggiungi Corso
        </button>
      {showAddActionModal && (
        <AddActionModal
          onClose={() => setShowAddActionModal(false)}
          onReview={() => {
            setShowAddActionModal(false);
            handleOpenReviewModal(actionCourse);
          }}
          onMaterial={() => {
            setShowAddActionModal(false);
            // Qui puoi aprire la modale per l'upload dei materiali
            alert("Funzionalità aggiungi materiale non ancora implementata!");
          }}
        />
      )}
      </div>

      {showAddModal && (
        <AddCourseModal
          availableCourses={availableCourses}
          selectedCourseId={selectedCourseId}
          editions={editions}
          showAddEdition={showAddEdition}
          newEdition={newEdition}
          error={error}
          success={success}
          setShowAddModal={setShowAddModal}
          handleSelectCourse={handleSelectCourse}
          handleEnroll={handleEnroll}
          setShowAddEdition={setShowAddEdition}
          handleAddEdition={handleAddEdition}
          setNewEdition={setNewEdition}
          docenti={docenti}
        />
      )}
      {showReviewModal && (
        <ReviewModal
          corso={reviewCourse}
          onClose={() => setShowReviewModal(false)}
          onSubmit={handleAddReview}
          error={error}
        />
      )}

      {success && <div className="fixed top-4 right-4 bg-green-600 text-white px-4 py-2 rounded">{success}</div>}
      {error && <div className="fixed top-4 right-4 bg-red-600 text-white px-4 py-2 rounded">{error}</div>}

      <h2 className="text-2xl font-bold text-[#991B1B] mb-4 text-center">Corsi che stai frequentando</h2>
      <div className="flex flex-wrap gap-4 justify-center">
        {currentCourses
          .filter(corso => (corso.stato || "").toLowerCase() === "attivo")
          .map((corso) => (
            <CourseBox
              key={corso.edition_id}
              corso={corso}
              onClick={() => handleOpenDetailModal(corso)}
            >
              <div className="flex justify-end">
                <button
                  className="w-8 h-8 flex items-center justify-center bg-[#991B1B] text-white rounded-full hover:bg-red-800 text-xl shadow"
                  style={{ marginTop: "-0.5rem", marginRight: "-0.5rem" }}
                  onClick={e => { e.stopPropagation(); handleOpenCompleteModal(corso); }}
                  title="Completa corso"
                >
                  ✓
                </button>
              </div>
            </CourseBox>
          ))}
      </div>

      <h2 className="text-2xl font-bold text-[#991B1B] mt-16 mb-4 text-center">Corsi che hai frequentato</h2>
      <div className="flex flex-wrap gap-4 justify-center">
        {completedCourses.map((corso) => {
          const alreadyReviewed = studentReviews.some(
            r => r.edition_id === corso.edition_id && r.edition_data === corso.edition_data
          );
          return (
            <CourseBox
              key={corso.edition_id}
              corso={corso}
              onClick={() => handleOpenDetailModal(corso)}
            >
              <div className="flex justify-end items-center gap-5">
                {!alreadyReviewed && (
                  <button
                    className="w-8 h-8 flex items-center justify-center bg-[#991B1B] text-white rounded-full hover:bg-red-800 text-xl shadow"
                    style={{ marginTop: "-0.5rem", marginRight: "-0.5rem" }}
                    onClick={e => { e.stopPropagation(); handleOpenActionModal(corso); }}
                    title="Aggiungi"
                  >
                    +
                  </button>
                )}
                {alreadyReviewed && (
                  <span className="text-sm text-gray-500 mr-2">Recensione inviata</span>
                )}
                {/* Pulsante ripristina */}
                <button
                  className="w-8 h-8 flex items-center justify-center text-black rounded-ful text-xl shadow"
                  style={{ marginTop: "-0.5rem", marginRight: "-0.5rem" }}
                  onClick={e => { e.stopPropagation(); handleRestoreCourse(corso); }}
                  title="Riporta tra i corsi attivi"
                >
                  <span role="img" aria-label="modifica">↩</span>
                </button>
              </div>
            </CourseBox>
          );
        })}
        {showDetailModal && (
          <CourseDetailModal
            corso={detailCourse}
            onClose={() => setShowDetailModal(false)}
          />
        )}
      </div>
    </div>
  );
}