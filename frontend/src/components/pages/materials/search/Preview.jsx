import React from 'react';
import { FaStar } from 'react-icons/fa';

function MaterialsPreview({ items, hasSearched, onShowAll, onShowItem, buildMaterialData, courseName, editionLabel }) {
  if (!items.length) {
    return hasSearched ? (
      <p className="text-sm text-[#a25966]">Nessun materiale trovato.</p>
    ) : (
      <p className="text-sm text-[#a25966]">Imposta i filtri e premi Cerca.</p>
    );
  }

  const preview = items.slice(0, 3);
  return (
    <div className="space-y-2">
      {preview.map((item, idx) => {
        const data = buildMaterialData(item, courseName, editionLabel, idx);
        return (
          <button
            key={idx}
            className="w-full text-left rounded-xl border border-[#f0d6db] bg-white px-4 py-3 shadow-sm hover:shadow-md transition active:scale-[0.99]"
            onClick={() => onShowItem(data)}
          >
            <p className="text-sm font-semibold break-all line-clamp-2">{data.displayName}</p>
            <div className="mt-2 flex items-center justify-between text-xs text-[#a25966]">
              <span>{data.tipo}</span>
              <span>{data.verificato ? 'verificato ✅' : 'non verificato'}</span>
            </div>
          </button>
        );
      })}
      {items.length > 3 && (
        <button type="button" className="w-full text-xs text-[#822433] underline" onClick={onShowAll}>
          Apri elenco completo
        </button>
      )}
    </div>
  );
}

function InfoPreview({ items, hasSearched, onShowAll, onShowItem }) {
  if (!items.length) {
    return hasSearched ? (
      <p className="text-sm text-[#a25966]">Nessuna informazione trovata.</p>
    ) : (
      <p className="text-sm text-[#a25966]">Esegui una ricerca per vedere i dati.</p>
    );
  }

  const preview = items.slice(0, 2);
  return (
    <div className="space-y-2">
      {preview.map((record, idx) => {
        const data = Array.isArray(record) ? record : Object.values(record);
        return (
          <button
            key={idx}
            className="w-full text-left rounded-xl border border-[#f0d6db] bg-white px-4 py-3 shadow-sm hover:shadow-md transition active:scale-[0.99]"
            onClick={() =>
              onShowItem({
                titolo: data[0],
                categoria: data[1],
                docenteNome: data[2],
                docenteCognome: data[3],
                email: data[4],
                cfu: data[5],
                idoneita: data[6],
                orario: data[7],
                esonero: data[8],
                modalitaEsame: data[9],
                prerequisiti: data[10],
                frequenza: data[11],
              })
            }
          >
            <p className="text-sm font-semibold">{data[0]}</p>
            <p className="mt-2 text-xs text-[#a25966]">
              {data[2] || data[3] ? `${data[2] ?? ''} ${data[3] ?? ''}`.trim() : 'Docente non disponibile'}
            </p>
          </button>
        );
      })}
      {items.length > 2 && (
        <button type="button" className="w-full text-xs text-[#822433] underline" onClick={onShowAll}>
          Apri elenco completo
        </button>
      )}
    </div>
  );
}

function ReviewsPreview({ items, hasSearched, onShowAll, onShowItem }) {
  if (!items.length) {
    return hasSearched ? (
      <p className="text-sm text-[#a25966]">Nessuna review trovata.</p>
    ) : (
      <p className="text-sm text-[#a25966]">Attiva il filtro Review e premi Cerca.</p>
    );
  }

  const preview = items.slice(0, 3);
  return (
    <div className="space-y-2">
      {preview.map((record, idx) => {
        const descrizione = record.descrizione ?? record[0];
        const voto = record.voto ?? record[1];
        return (
          <button
            key={idx}
            className="w-full text-left rounded-xl border border-[#f0d6db] bg-white px-4 py-3 shadow-sm hover:shadow-md transition active:scale-[0.99]"
            onClick={() => onShowItem({ descrizione, voto })}
          >
            <p className="text-sm font-semibold line-clamp-3">{descrizione}</p>
            <div className="mt-2 flex items-center gap-1 text-xs text-[#a25966]">
              {[...Array(Number(voto))].map((_, starIdx) => (
                <FaStar key={starIdx} color="#991B1B" size={14} />
              ))}
            </div>
          </button>
        );
      })}
      {items.length > 3 && (
        <button type="button" className="w-full text-xs text-[#822433] underline" onClick={onShowAll}>
          Apri elenco completo
        </button>
      )}
    </div>
  );
}

export { MaterialsPreview, InfoPreview, ReviewsPreview };
