import React from 'react';
import { FaStar } from 'react-icons/fa';

function MaterialsPreview({ items, hasSearched, onShowItem, buildMaterialData }) {

  return (
    <div className="space-y-2">
      {items.map((item, idx) => {
        const data = buildMaterialData(item, idx);
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
    </div>
  );
}

function InfoPreview({ items, hasSearched, onShowItem }) {

  return (
    <div className="space-y-2">
      {items.map((record, idx) => {
        const data = Array.isArray(record) ? record : Object.values(record);
        // data[0]=nomeCorso, data[1]=edizione, data[2]=docenteNome, data[3]=docenteCognome, see /getInfoCorso in backend
        return (
          <button
            key={idx}
            className="w-full text-left rounded-xl border border-[#f0d6db] bg-white px-4 py-3 shadow-sm hover:shadow-md transition active:scale-[0.99]"
            onClick={() =>
              onShowItem({
                nomeCorso: data[0],
                edizione: data[1],
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
            <p className="text-sm font-semibold">
              {data[0]} <span className="text-xs text-[#a25966]">({data[1]})</span>
            </p>
            <p className="mt-2 text-xs text-[#a25966]">
              {data[2] || data[3] ? `${data[2] ?? ''} ${data[3] ?? ''}`.trim() : 'Docente non disponibile'}
            </p>
          </button>
        );
      })}
    </div>
  );
}
function ReviewsPreview({ items, hasSearched, onShowItem }) {

  return (
    <div className="space-y-2">
      {items.map((record, idx) => {
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
    </div>
  );
}

export { MaterialsPreview, InfoPreview, ReviewsPreview };
