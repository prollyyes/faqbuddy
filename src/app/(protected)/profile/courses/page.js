'use client'
import { useEffect, useState } from "react";
import CorsiPage from "@/components/pages/courses/student/Courses";
import TeacherCourses from "@/components/pages/courses/teacher/TeacherCourses";

const HOST = process.env.NEXT_PUBLIC_HOST;

export default function Courses() {
  const [ruolo, setRuolo] = useState(null);
  const [errore, setErrore] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;
    fetch(`${HOST}/profile/me`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => {
        if (data && data.ruolo) {
          setRuolo(data.ruolo);
        } else if (data && data.detail) {
          setErrore(data.detail);
        } else {
          setErrore("Errore sconosciuto");
        }
      });
  }, []);

  if (errore) return <div className="p-8 text-center text-red-600">{errore}</div>;
  if (!ruolo) return <div className="p-8 text-center">Caricamento...</div>;

  return ruolo === "insegnante" ? <TeacherCourses /> : <CorsiPage />;
}