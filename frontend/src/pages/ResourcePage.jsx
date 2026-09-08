import { useCallback, useEffect, useState } from "react";
import { FiRefreshCw } from "react-icons/fi";
import api from "../services/api";
import Table from "../components/Table";
import { getRows } from "../utils/response";

export default function ResourcePage({ title, eyebrow, description, endpoint, columns, action }) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { const response = await api.get(endpoint); setRows(getRows(response.data)); }
    catch (requestError) { setError(requestError.response?.data?.detail || "Unable to load this module from the API."); }
    finally { setLoading(false); }
  }, [endpoint]);
  // The fetch callback owns the loading lifecycle for this resource.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { load(); }, [load]);
  return <section className="space-y-6"><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="text-xs font-bold uppercase tracking-[0.2em] text-teal-600">{eyebrow || "Operations"}</p><h1 className="mt-2 font-display text-3xl font-bold tracking-tight text-slate-900">{title}</h1><p className="mt-2 max-w-2xl text-sm text-slate-500">{description}</p></div><button onClick={load} className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-600 hover:border-teal-300 hover:text-teal-700"><FiRefreshCw size={16} /> Refresh</button></div>{error && <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}{action}<div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"><Table rows={rows} columns={columns} loading={loading} /></div></section>;
}
