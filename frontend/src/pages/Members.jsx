import { useState } from "react";
import ResourcePage from "./ResourcePage";

export default function Members() {
  const [search, setSearch] = useState("");
  const action = <div className="flex max-w-sm items-center gap-2 rounded-xl border border-slate-200 bg-white px-3"><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search members" className="w-full py-2.5 text-sm outline-none" /><span className="text-xs font-bold text-slate-400">SEARCH</span></div>;
  const endpoint = `members/${search ? `?search=${encodeURIComponent(search)}` : ""}`;
  return <ResourcePage title="Members" eyebrow="People" description="Search member profiles and review the information used for personalized plans." endpoint={endpoint} action={action} columns={[{ key: "id", label: "ID" }, { key: "user", label: "User", render: (row) => row.user || `Member #${row.id}` }, { key: "age", label: "Age" }, { key: "gender", label: "Gender" }, { key: "height", label: "Height" }, { key: "weight", label: "Weight" }, { key: "goal", label: "Goal" }]} />;
}
