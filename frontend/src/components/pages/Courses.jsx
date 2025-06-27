'use client'
import React, { useEffect, useState } from "react";
import axios from "axios";

// Mostra tutte le info disponibili per ogni corso
function CourseBox({ corso, children }) {
  return (
    <div className="border rounded-lg p-4 shadow-md bg-white w-full md:w-1/2 lg:w-1/3 flex flex-col gap-2">
      <h3 className="text-lg font-bold mb-2 text-[#991B1B]">{corso.nome}</h3>
      <p className="text-sm text-gray-600 font-bold">CFU: {corso.cfu}</p>
      <p className="text-sm">Docente: {corso.docente || "N/A"}</p>
      {corso.edition_data && <p className="text-sm">Data Edizione: {corso.edition_data}</p>}
      {corso.voto !== undefined && corso.voto !== null && (
        <span className="block text-green-700 font-bold">Voto: {corso.voto}</span>
      )}
      {children}
    </div>
  );
}

// Modale popup senza overlay nero opaco
function AddCourseModal({
  availableCourses,
  selectedCourseId,
  editions,
  showAddEdition,
  newEdition,
  error,
  success,
  setShowAddModal,
  handleSelectCourse,
  handleEnroll,
  setShowAddEdition,
  handleAddEdition,
  setNewEdition
}) {

  const selectedCourse = availableCourses.find(c => c.id === selectedCourseId);

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50 backdrop-blur-sm backdrop-brightness-75 pt-25">
      <div className="relative pointer-events-auto bg-white/80 p-6 rounded-lg shadow-2xl w-[22rem] max-w-full max-h-[90vh] overflow-y-auto border-2 border-[#991B1B] backdrop-blur-md">
        <button
          className="absolute top-2 right-2 text-gray-500 hover:text-red-700 text-xl"
          onClick={() => setShowAddModal(false)}
        >
          &times;
        </button>
        <h3 className="text-lg font-bold mb-4 text-[#991B1B]">Aggiungi Corso</h3>
        {!selectedCourseId ? (
          <>
            <div className="mb-4">
              <h4 className="font-semibold mb-2">Corsi disponibili:</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {availableCourses.map(corso => (
                  <div
                    key={corso.id}
                    className="border rounded-lg p-4 shadow hover:bg-gray-100 cursor-pointer transition"
                    onClick={() => handleSelectCourse(corso.id)}
                  >
                    <div className="font-bold text-[#991B1B]">{corso.nome}</div>
                    <div className="text-sm text-gray-700">CFU: {corso.cfu}</div>
                  </div>
                ))}
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="mb-4">
              <h4 className="font-semibold mb-2">Edizioni disponibili:</h4>
              {editions.length === 0 && <div>Nessuna edizione disponibile</div>}
              <div className="grid grid-cols-1 gap-2">
                {editions.map(edition => (
                  <div
                    key={edition.id}
                    className="border rounded-lg p-3 flex items-center justify-between hover:bg-gray-100 cursor-pointer transition"
                  >
                    <span>{edition.data} - Docente: {edition.docente}</span>
                    <button
                      className="px-2 py-1 bg-green-600 text-white rounded hover:bg-green-800"
                      onClick={() => handleEnroll(selectedCourseId, edition.id, edition.data)}
                    >
                      Iscriviti
                    </button>
                  </div>
                ))}
              </div>
            </div>
            {!showAddEdition ? (
              <div className="flex justify-between">
                <button className="px-4 py-2 bg-gray-300 rounded" onClick={() => setShowAddModal(false)}>Chiudi</button>
                <button className="px-4 py-2 bg-blue-600 text-white rounded" onClick={() => setShowAddEdition(true)}>
                  Non trovi la tua edizione? Aggiungi una nuova edizione
                </button>
              </div>
            ) : (
              <form onSubmit={handleAddEdition} className="space-y-2 mt-4">
                <h4 className="font-semibold mb-2">Aggiungi nuova edizione</h4>
                <input
                  type="text"
                  required
                  placeholder="Data (es: S1/2024)"
                  className="border rounded p-2 w-full"
                  value={newEdition.data}
                  onChange={e => setNewEdition({ ...newEdition, data: e.target.value })}
                />
                <input
                  type="text"
                  required
                  placeholder="Orario"
                  className="border rounded p-2 w-full"
                  value={newEdition.orario}
                  onChange={e => setNewEdition({ ...newEdition, orario: e.target.value })}
                />

                <select
                  required
                  className="border rounded p-2 w-full"
                  value={newEdition.esonero}
                  onChange={e => setNewEdition({ ...newEdition, esonero: e.target.value === "true" })}
                >
                  <option value="">Esonero?</option>
                  <option value="true">Sì</option>
                  <option value="false">No</option>
                </select>

                <input
                  type="text"
                  required
                  placeholder="Modalità Esame"
                  className="border rounded p-2 w-full"
                  value={newEdition.mod_Esame}
                  onChange={e => setNewEdition({ ...newEdition, mod_Esame: e.target.value })}
                />

                <input
                  type="text"
                  required
                  placeholder="Nome docente"
                  className="border rounded p-2 w-full"
                  value={newEdition.docenteNome}
                  onChange={e => setNewEdition({ ...newEdition, docenteNome: e.target.value })}
                />

                <input
                  type="text"
                  required
                  placeholder="Cognome docente"
                  className="border rounded p-2 w-full"
                  value={newEdition.docenteCognome}
                  onChange={e => setNewEdition({ ...newEdition, docenteCognome: e.target.value })}
                />
                <div className="flex justify-between">
                  <button className="px-4 py-2 bg-gray-300 rounded" type="button" onClick={() => setShowAddEdition(false)}>
                    Indietro
                  </button>
                  <button className="px-4 py-2 bg-green-600 text-white rounded" type="submit">
                    Aggiungi edizione e iscriviti
                  </button>
                </div>
              </form>
            )}
          </>
        )}
        {error && (
          <div className="text-red-600 mt-2">
            {typeof error === "string"
              ? error
              : Array.isArray(error)
                ? error.map((e, i) => <div key={i}>{e.msg || JSON.stringify(e)}</div>)
                : JSON.stringify(error)}
          </div>
        )}
        {success && <div className="text-green-600 mt-2">{success}</div>}
      </div>
    </div>
  );
}

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

  // Fetch all courses
  useEffect(() => {
    const token = localStorage.getItem("token");
    axios.get("http://localhost:8000/profile/courses/current", {
      headers: { Authorization: `Bearer ${token}` }
    }).then(res => setCurrentCourses(res.data));

    axios.get("http://localhost:8000/profile/courses/completed", {
      headers: { Authorization: `Bearer ${token}` }
    }).then(res => setCompletedCourses(res.data));
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
      // Trova id insegnante
      const docenteRes = await axios.get(
        `http://localhost:8000/teachers/search?nome=${encodeURIComponent(newEdition.docenteNome)}&cognome=${encodeURIComponent(newEdition.docenteCognome)}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!docenteRes.data || !docenteRes.data.id) {
        setError("Docente non trovato");
        return;
      }
      const insegnanteId = docenteRes.data.id;
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

  // --- Modale completamento corso ---
  const CompleteModal = () => (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-40 z-50">
      <div className="bg-white p-6 rounded-lg shadow-lg w-96">
        <h3 className="text-lg font-bold mb-2 text-[#991B1B]">
          Completa il corso: {courseToComplete?.nome}
        </h3>
        <label className="block mb-2">Voto:</label>
        <input
          type="number"
          min={18}
          max={31}
          value={completeVoto}
          onChange={e => setCompleteVoto(e.target.value)}
          className="border rounded p-2 w-full mb-4"
        />
        {error && <div className="text-red-600 mb-2">{error}</div>}
        <div className="flex justify-end gap-2">
          <button
            className="px-4 py-2 bg-gray-300 rounded"
            onClick={() => setShowCompleteModal(false)}
          >
            Annulla
          </button>
          <button
            className="px-4 py-2 bg-blue-600 text-white rounded"
            onClick={handleCompleteCourse}
            disabled={
              !completeVoto ||
              isNaN(completeVoto) ||
              completeVoto < 18 ||
              completeVoto > 31
            }
          >
            Completa
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex flex-col p-4 min-h-screen pb-24 pt-20">
      {showCompleteModal && <CompleteModal />}

      {/* Pulsante centrato in alto */}
      <div className="flex justify-center mb-6 mt-8">
        <button
          className="px-4 py-2 bg-[#991B1B] text-white rounded hover:bg-red-800"
          onClick={handleOpenAddModal}
        >
          + Aggiungi Corso
        </button>
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
        />
      )}

      {success && <div className="fixed top-4 right-4 bg-green-600 text-white px-4 py-2 rounded">{success}</div>}
      {error && <div className="fixed top-4 right-4 bg-red-600 text-white px-4 py-2 rounded">{error}</div>}

      <h2 className="text-2xl font-bold text-[#991B1B] mb-4 text-center">Corsi che stai frequentando</h2>
      <div className="flex flex-wrap gap-4 justify-center">
        {currentCourses
          .filter(corso => (corso.stato || "").toLowerCase() === "attivo")
          .map((corso) => (
            <CourseBox key={corso.edition_id} corso={corso}>
              <button
                className="mt-2 px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-800"
                onClick={() => handleOpenCompleteModal(corso)}
              >
                Completa corso
              </button>
            </CourseBox>
          ))}
      </div>

      <h2 className="text-2xl font-bold text-[#991B1B] mt-16 mb-4 text-center">Corsi che hai frequentato</h2>
      <div className="flex flex-wrap gap-4 justify-center">
        {completedCourses.map((corso) => (
          <CourseBox key={corso.edition_id} corso={corso} />
        ))}
      </div>
    </div>
  );
}