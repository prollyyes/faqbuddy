'use client'
import React, { useEffect, useState } from "react";
import axios from "axios";
import CourseBox from "./CourseBox";
import AddCourseModal from "./AddCourseModal";
import CompleteModal from "./CompleteModal";
import ReviewModal from "./ReviewModal";
import CourseDetailModal from "./CourseDetailModal";
import AddActionModal from "./AddActionModal";
import { TbArrowLeftFromArc } from "react-icons/tb";
import SwipeWrapperStudente from "@/components/wrappers/SwipeWrapperStudente";
import RestoreConfirmModal from "./RestoreConfirmModal";
import Button from "@/components/utils/Button";

const HOST = process.env.NEXT_PUBLIC_HOST;


export default function CorsiPage() {
  const [currentCourses, setCurrentCourses] = useState([]);
  const [completedCourses, setCompletedCourses] = useState([]);
  const [showCompleteModal, setShowCompleteModal] = useState(false);
  const [courseToComplete, setCourseToComplete] = useState(null);
  const [completeVoto, setCompleteVoto] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [tab, setTab] = useState("attivi");


  // popup sposta corso tra i seguiti
  const [showRestoreConfirm, setShowRestoreConfirm] = useState(false);
  const [restoreCourse, setRestoreCourse] = useState(null);

  // Modale aggiunta corso
  const [showAddModal, setShowAddModal] = useState(false);
  const [availableCourses, setAvailableCourses] = useState([]);
  const [selectedCourseId, setSelectedCourseId] = useState(null);
  const [editions, setEditions] = useState([]);
  const [showAddEdition, setShowAddEdition] = useState(false);
  const [newEdition, setNewEdition] = useState({
    data: "",
    orario: "",
    esonero: false,
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
      `${HOST}/courses/editions/${corso.edition_id}/${encodeURIComponent(corso.edition_data)}`,
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
    fetch(`${HOST}/teachers`)
      .then(res => res.json())
      .then(data => setDocenti(data))
      .catch(() => setDocenti([]));
  }, []);

  // Handle reviews
  const [studentReviews, setStudentReviews] = useState([]);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewCourse, setReviewCourse] = useState(null);
  const actionCourseHasReview = actionCourse
    ? studentReviews.some(
        r => r.edition_id === actionCourse.edition_id && r.edition_data === actionCourse.edition_data
      )
    : false;

  const handleOpenReviewModal = (corso) => {
    setReviewCourse(corso);
    setShowReviewModal(true);
    setError("");
    setSuccess("");
  };

  // Fetch all courses && reviews on mount
  useEffect(() => {
    const token = localStorage.getItem("token");
    axios.get(`${HOST}/profile/courses/current`, {
      headers: { Authorization: `Bearer ${token}` }
    }).then(res => setCurrentCourses(res.data));

    axios.get(`${HOST}/profile/courses/completed`, {
      headers: { Authorization: `Bearer ${token}` }
    }).then(res => setCompletedCourses(res.data));

    axios.get(`${HOST}/profile/reviews`, {
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
        `${HOST}/profile/courses/${courseToComplete.edition_id}/complete`,
        {
          edition_data: courseToComplete.edition_data,
          voto: Number(completeVoto)
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSuccess("Corso completato!");
      // Aggiorna le liste
      const resCurrent = await axios.get(`${HOST}/profile/courses/current`, { headers: { Authorization: `Bearer ${token}` } });
      setCurrentCourses(resCurrent.data);
      const resCompleted = await axios.get(`${HOST}/profile/courses/completed`, { headers: { Authorization: `Bearer ${token}` } });
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
    const res = await axios.get(`${HOST}/courses/available`, {
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
    const res = await axios.get(`${HOST}/courses/${corsoId}/editions`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    setEditions(res.data);
  };

  // Iscrizione a una edizione
  const handleEnroll = async (corso_id, edition_id, edition_data) => {
    const token = localStorage.getItem("token");
    try {
      await axios.post(
        `${HOST}/courses/${corso_id}/editions/${edition_id}/enroll`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSuccess("Iscrizione avvenuta!");
      // Lascia chiudere la modale con animazione dal componente
      // Aggiorna corsi attivi
      const resCurrent = await axios.get(`${HOST}/profile/courses/current`, { headers: { Authorization: `Bearer ${token}` } });
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
      // const payload = {
      //   insegnante: insegnanteId,
      //   data: newEdition.data,
      //   orario: newEdition.orario,
      //   esonero: newEdition.esonero,
      //   mod_Esame: newEdition.mod_Esame,
      //   stato: "attivo"
      // };
      // console.log("Payload inviato:", payload);
      // Crea nuova edizione e iscrivi lo studente
      await axios.post(
        `${HOST}/courses/${selectedCourseId}/editions/add`,
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
      // Lascia chiudere la modale con animazione dal componente
      // Aggiorna corsi attivi
      const resCurrent = await axios.get(`${HOST}/profile/courses/current`, { headers: { Authorization: `Bearer ${token}` } });
      setCurrentCourses(resCurrent.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Errore durante l'aggiunta dell'edizione");
    }
  };

  
  // Funzione per disiscriversi da un corso
  const handleUnenrollCourse = async (corso) => {
    const token = localStorage.getItem("token");
    try {
      await axios.delete(
        `${HOST}/courses/editions/${corso.edition_id}/unenroll`,
        {
          data: { edition_data: corso.edition_data },
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setSuccess("Disiscrizione avvenuta!");
      // Aggiorna corsi attivi
      const resCurrent = await axios.get(`${HOST}/profile/courses/current`, { headers: { Authorization: `Bearer ${token}` } });
      setCurrentCourses(resCurrent.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Errore durante la disiscrizione");
    }
  };
  // --- Aggiungi recensione ---
  const handleAddReview = async (corso, descrizione, voto) => {
    const token = localStorage.getItem("token");
    try {
      await axios.post(
        `${HOST}/profile/reviews`,
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
      const res = await axios.get(`${HOST}/profile/reviews`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStudentReviews(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Errore durante l'invio della recensione");
    }
  };

  // Funzione per ripristinare un corso tra quelli attivi
  const handleRestoreCourse = async (corso) => {
    const token = localStorage.getItem("token");
    try {
      await axios.put(
        `${HOST}/profile/courses/${corso.edition_id}/restore`,
        { edition_data: corso.edition_data },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSuccess("Corso riportato tra quelli attivi!");
      // Aggiorna le liste
      const resCurrent = await axios.get(`${HOST}/profile/courses/current`, { headers: { Authorization: `Bearer ${token}` } });
      setCurrentCourses(resCurrent.data);
      const resCompleted = await axios.get(`${HOST}/profile/courses/completed`, { headers: { Authorization: `Bearer ${token}` } });
      setCompletedCourses(resCompleted.data);
      // Aggiorna recensioni
      const resReviews = await axios.get(`${HOST}/profile/reviews`, { headers: { Authorization: `Bearer ${token}` } });
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
    <SwipeWrapperStudente>
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
        {/* Toggle centrato; non sticky */}
        <div className="px-1 pb-3 mt-2">
          <div className="grid grid-cols-3 items-center">
            <div className="justify-self-end pr-3">
              <span className={`text-sm font-semibold ${tab === 'attivi' ? 'text-[#822433]' : 'text-gray-400'}`}>Attivi</span>
            </div>
            <div className="justify-self-center">
              <button
                type="button"
                className={`w-14 h-7 flex items-center rounded-full p-1 duration-300 ease-in-out bg-[#822433]`}
                onClick={() => setTab(prev => (prev === 'attivi' ? 'completati' : 'attivi'))}
                aria-label="Toggle Attivi/Completati"
              >
                <div
                  className={`bg-white w-5 h-5 rounded-full shadow-md transform duration-300 ease-in-out ${tab === 'completati' ? 'translate-x-7' : ''}`}
                />
              </button>
            </div>
            <div className="justify-self-start pl-3">
              <span className={`text-sm font-semibold ${tab === 'completati' ? 'text-[#822433]' : 'text-gray-400'}`}>Completati</span>
            </div>
          </div>
        </div>
        {showAddActionModal && (
          <AddActionModal
            onClose={() => setShowAddActionModal(false)}
            onReview={() => {
              handleOpenReviewModal(actionCourse);
            }}
            canAddReview={!actionCourseHasReview}
          />
        )}
        

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

        {/* Error banner in basso */}
        {error && (
          <div className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-red-600 text-white px-4 py-2 rounded-full shadow">
            {error}
          </div>
        )}

        {/* Lista unica in base al tab */}
        {tab === 'attivi' ? (
          <div className="flex flex-col items-center gap-3">
            {currentCourses.filter(c => (c.stato || '').toLowerCase() === 'attivo').length === 0 ? (
              <div className="text-center text-gray-500 py-10">
                Nessun corso attivo. Tocca "+" per aggiungerne uno.
              </div>
            ) : (
              currentCourses
                .filter(corso => (corso.stato || '').toLowerCase() === 'attivo')
                .map((corso) => (
                  <CourseBox
                    key={corso.edition_id}
                    corso={corso}
                    onClick={() => handleOpenDetailModal(corso)}
                    onUnenroll={() => handleUnenrollCourse(corso)}
                    onComplete={() => handleOpenCompleteModal(corso)}
                  />
                ))
            )}
            <div className="mt-4 w-full flex justify-center">
              <Button onClick={handleOpenAddModal}>
                Aggiungi Corso +
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            {completedCourses.length === 0 ? (
              <div className="text-center text-gray-500 py-10">
                Nessun corso completato. Completa un corso dagli attivi.
              </div>
            ) : (
              completedCourses.map((corso) => {
                const alreadyReviewed = studentReviews.some(
                  r => r.edition_id === corso.edition_id && r.edition_data === corso.edition_data
                );
                return (
                  <CourseBox
                    key={corso.edition_id}
                    corso={corso}
                    onClick={() => handleOpenDetailModal(corso)}
                  >
                    <div className="flex justify-end items-center gap-3">
                      {!alreadyReviewed ? (
                        <button
                          className="w-9 h-9 flex items-center justify-center bg-[#991B1B] text-white rounded-full hover:bg-red-800 text-xl shadow"
                          onClick={e => { e.stopPropagation(); handleOpenActionModal(corso); }}
                          title="Aggiungi"
                          aria-label="Aggiungi recensione"
                        >
                          +
                        </button>
                      ) : (
                        <span className="text-xs text-gray-500 italic">Recensione inviata</span>
                      )}
                      <button
                        className="w-9 h-9 ml-1 flex items-center justify-center rounded-full shadow hover:bg-gray-100 active:scale-95 text-black"
                        onClick={e => {
                          e.stopPropagation();
                          setRestoreCourse(corso);
                          setShowRestoreConfirm(true);
                        }}
                        title="Riporta tra gli attivi"
                      >
                        <TbArrowLeftFromArc className="w-5 h-5 text-black" />
                      </button>
                    </div>
                  </CourseBox>
                );
              })
            )}
          </div>
        )}

        <RestoreConfirmModal
          open={showRestoreConfirm}
          onClose={() => setShowRestoreConfirm(false)}
          onConfirm={async () => {
            await handleRestoreCourse(restoreCourse);
          }}
        />

        {/* quando clicco sul corso mostra i dettagli */}
        {showDetailModal && (
          <CourseDetailModal
            corso={detailCourse}
            onClose={() => setShowDetailModal(false)}
          />
        )}

        {/* Rimosso FAB fisso - il pulsante Aggiungi è sotto il toggle solo in "Attivi" */}
      </div>
    </SwipeWrapperStudente>
  );
}
