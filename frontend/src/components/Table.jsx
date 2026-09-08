import Loading from "./Loading";

export default function Table({ columns, rows, loading, empty = "No records found" }) {
  if (loading) return <Loading />;
  return <div className="overflow-x-auto"><table className="w-full min-w-[640px] text-left text-sm"><thead><tr className="border-b border-slate-200 text-xs uppercase tracking-wider text-slate-400">{columns.map((column) => <th key={column.key} className="px-5 py-4 font-bold">{column.label}</th>)}</tr></thead><tbody className="divide-y divide-slate-100">{rows.length ? rows.map((row, index) => <tr key={row.id || index} className="hover:bg-slate-50">{columns.map((column) => <td key={column.key} className="px-5 py-4 text-slate-600">{column.render ? column.render(row) : row[column.key] ?? "-"}</td>)}</tr>) : <tr><td className="px-5 py-12 text-center text-slate-400" colSpan={columns.length}>{empty}</td></tr>}</tbody></table></div>;
}
