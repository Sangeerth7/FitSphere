import { useState } from "react";
import { Outlet } from "react-router-dom";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";

export default function DashboardLayout() {
  const [menuOpen, setMenuOpen] = useState(false);
  return <div className="flex min-h-screen bg-[#f6f8f7]"><Sidebar />{menuOpen && <div className="fixed inset-0 z-40 bg-slate-950/30 lg:hidden" onClick={() => setMenuOpen(false)}><div className="h-full w-72 bg-white p-4" onClick={(event) => event.stopPropagation()}><Sidebar /></div></div>}<div className="min-w-0 flex-1"><Navbar onMenu={() => setMenuOpen(true)} /><main className="mx-auto max-w-[1440px] p-5 sm:p-8"><Outlet /></main></div></div>;
}
