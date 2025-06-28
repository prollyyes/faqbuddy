const currentCourses = [
  { nome: "Analisi Matematica I", cfu: 9, docente: "Prof. Rossi" },
  { nome: "Fondamenti di Informatica", cfu: 6, docente: "Prof.ssa Bianchi" },
  { nome: "Fisica I", cfu: 6, docente: "Prof. Verdi" },
  { nome: "Algebra Lineare", cfu: 6, docente: "Prof. Neri" },
];

const completedCourses = [
  { nome: "Sistemi Operativi", cfu: 9, docente: "Prof.ssa Gialli" },
  { nome: "Elettronica", cfu: 6, docente: "Prof. Blu" },
  { nome: "Controlli Automatici", cfu: 9, docente: "Prof. Marrone" },
];

function CourseBox({ nome, cfu, docente }) {
  return (
    <div className="border rounded-lg p-4 shadow-md bg-white w-full md:w-1/2 lg:w-1/3 hover:shadow-lg hover:scale-105 transition-transform duration-200">
      <h3 className="text-lg font-bold mb-2 text-[#991B1B]">{nome}</h3>
      <p className="text-sm text-gray-600 font-bold">CFU: {cfu} | Docente: {docente}</p>
    </div>
  );
}

export default function CorsiPage() {
  return (
    <div className="flex flex-col p-4 min-h-screen pb-24">
      <h2 className="text-2xl font-bold text-[#991B1B] mt-28 mb-4">Corsi che stai frequentando</h2>
      <div className="flex flex-wrap gap-4">
        {currentCourses.map((corso, index) => (
          <CourseBox key={index} nome={corso.nome} cfu={corso.cfu} docente={corso.docente} />
        ))}
      </div>

      <h2 className="text-2xl font-bold text-[#991B1B] mt-16 mb-4">Corsi che hai frequentato</h2>
      <div className="flex flex-wrap gap-4">
        {completedCourses.map((corso, index) => (
          <CourseBox key={`completed-${index}`} nome={corso.nome} cfu={corso.cfu} docente={corso.docente} />
        ))}
      </div>
    </div>
  );
}