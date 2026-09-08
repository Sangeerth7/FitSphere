export default function Loading({ label = "Loading FitSphere data" }) {
  return <div className="flex items-center gap-3 py-12 text-sm text-slate-500"><span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-200 border-t-teal-600" />{label}</div>;
}
