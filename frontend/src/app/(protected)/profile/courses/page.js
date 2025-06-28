'use client'
import { useEffect, useState } from "react";
import CorsiPage from "@/components/pages/courses/Courses";
import TeacherCourses from "@/components/pages/courses/TeacherCourses";

export default function Courses() {
  const [ruolo, setRuolo] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;
    fetch("http://localhost:8000/profile/me", {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => setRuolo(data.ruolo));
  }, []);

  if (!ruolo) return <div className="p-8 text-center">Caricamento...</div>;

  return ruolo === "insegnante" ? <TeacherCourses /> : <CorsiPage />;
}