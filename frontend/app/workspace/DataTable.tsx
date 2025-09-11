"use client"

import React from "react"

export interface RegistrationRecord {
  id: string;
  name: string;
  address: string;
  ward: string;
  page_number: number;
  row_number: number;
}

export interface MatchRecord {
  registration_id: string;
  registered_name: string;
  registered_address: string;
  match_rank: number;
  name_distance: number;
  address_distance: number;
}

interface OCRResult {
  name: string;
  address: string;
  ward: string;
  page_number: number;
  row_number: number;
}

interface DataTableProps {
  dataLoading: boolean;
  registrationData: RegistrationRecord[];
  mappedMatches: MatchRecord[];
  selectedMatchRanks: Record<string, number>;
  setSelectedMatchRanks: React.Dispatch<React.SetStateAction<Record<string, number>>>;
  ocrResults: OCRResult[];
}

const DataTable = (props: DataTableProps) => {
  const {
    dataLoading,
    registrationData,
    mappedMatches,
    selectedMatchRanks,
    setSelectedMatchRanks,
    ocrResults
  } = props;

  return (
    <table className="w-full text-sm">
      <thead className="bg-slate-100 sticky top-0 z-10">
        <tr>
          <th className="sticky left-0 z-20 bg-slate-100 text-left p-3 font-medium text-slate-700 border-b border-slate-200">Name</th>
          <th className="text-left p-3 font-medium text-slate-700 border-b border-slate-200">OCR Name</th>
          <th className="text-right p-3 font-medium text-slate-700 border-b border-slate-200">Name Distance</th>
          <th className="sticky left-[180px] z-10 bg-slate-100 text-left p-3 font-medium text-slate-700 border-b border-slate-200">Address</th>
          <th className="text-left p-3 font-medium text-slate-700 border-b border-slate-200">OCR Address</th>
          <th className="text-right p-3 font-medium text-slate-700 border-b border-slate-200">Address Distance</th>
          <th className="text-left p-3 font-medium text-slate-700 border-b border-slate-200">Ward</th>
          <th className="text-right p-3 font-medium text-slate-700 border-b border-slate-200">Page</th>
          <th className="text-right p-3 font-medium text-slate-700 border-b border-slate-200">Row</th>
          <th className="text-center p-3 font-medium text-slate-700 border-b border-slate-200">Match Rank</th>
        </tr>
      </thead>
      <tbody>
        {dataLoading ? (
          Array.from({ length: 10 }).map((_, index) => (
            <tr key={index} className="border-b border-slate-100">
              <td className="p-3 text-slate-300" colSpan={10}>Loading...</td>
            </tr>
          ))
        ) : registrationData.length > 0 ? (
          registrationData.map((record: RegistrationRecord, index: number) => {
            const matches = mappedMatches
              .filter((m: MatchRecord) => m.registration_id === record.id)
              .sort((a: MatchRecord, b: MatchRecord) => a.match_rank - b.match_rank)
              .slice(0, 5);

            const selectedRank = selectedMatchRanks[record.id] || 1;
            const selectedMatch = matches.find((m: MatchRecord) => m.match_rank === selectedRank) || matches[0];

            return (
              <tr
                key={record.id || index}
                className={
                  `border-b border-slate-100 hover:bg-slate-50` +
                  (index % 2 === 0 ? ' bg-white' : ' bg-slate-50')
                }
              >
                <td className="sticky left-0 z-10 bg-inherit p-3 text-slate-600 font-semibold">{record.name || '—'}</td>
                <td className="p-3 text-slate-600">{selectedMatch?.registered_name || '—'}</td>
                <td className="p-3 text-slate-600 text-right">{selectedMatch?.name_distance ?? '—'}</td>
                <td className="sticky left-[180px] z-0 bg-inherit p-3 text-slate-600">{record.address || '—'}</td>
                <td className="p-3 text-slate-600">{selectedMatch?.registered_address || '—'}</td>
                <td className="p-3 text-slate-600 text-right">{selectedMatch?.address_distance ?? '—'}</td>
                <td className="p-3 text-slate-600">{record.ward || '—'}</td>
                <td className="p-3 text-slate-600 text-right">{record.page_number || '—'}</td>
                <td className="p-3 text-slate-600 text-right">{record.row_number || '—'}</td>
                <td className="p-3 text-slate-600 text-center">
                  {matches.length > 1 ? (
                    <select
                      className="border rounded px-1 py-0.5 text-xs"
                      value={selectedRank}
                      onChange={e =>
                        setSelectedMatchRanks((prev: Record<string, number>) => ({
                          ...prev,
                          [record.id]: Number(e.target.value)
                        }))
                      }
                    >
                      {matches.map((m: MatchRecord, matchIndex: number) => (
                        <option key={`${record.id}-${m.match_rank}-${matchIndex}`} value={m.match_rank}>
                          {`Rank ${m.match_rank}: ${m.registered_name || '—'} — ${m.registered_address || '—'}`}
                        </option>
                      ))}
                    </select>
                  ) : (
                    selectedMatch?.match_rank || '—'
                  )}
                </td>
              </tr>
            );
          })
        ) : ocrResults.length > 0 ? (
          ocrResults.map((result: OCRResult, index: number) => (
            <tr key={index} className="border-b border-slate-100 hover:bg-slate-50">
              <td className="p-3 text-slate-600">{result.name}</td>
              <td className="p-3 text-slate-300">—</td>
              <td className="p-3 text-slate-300 text-right">—</td>
              <td className="p-3 text-slate-600">{result.address}</td>
              <td className="p-3 text-slate-300">—</td>
              <td className="p-3 text-slate-300 text-right">—</td>
              <td className="p-3 text-slate-600">{result.ward}</td>
              <td className="p-3 text-slate-600 text-right">{result.page_number}</td>
              <td className="p-3 text-slate-600 text-right">{result.row_number}</td>
              <td className="p-3 text-slate-300 text-center">—</td>
            </tr>
          ))
        ) : (
          <>
            <tr className="border-b border-slate-100">
              <td className="p-3 text-slate-300 text-center" colSpan={10}>
                No registration data found. Upload and process petitions to see data here.
              </td>
            </tr>
            {Array.from({ length: 19 }).map((_, index) => (
              <tr key={index} className="border-b border-slate-100">
                <td className="p-3 text-slate-300" colSpan={10}>—</td>
              </tr>
            ))}
          </>
        )}
      </tbody>
    </table>
  )
}

export default DataTable; 