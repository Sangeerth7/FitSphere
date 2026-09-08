import { NavLink } from "react-router-dom";
import { FiActivity, FiBarChart2, FiCalendar, FiCreditCard, FiGrid, FiHeart, FiUsers, FiUserCheck } from "react-icons/fi";
import { getRole } from "../utils/auth";

const items = [
  ["Dashboard", "/", FiGrid],
  ["Members", "/members", FiUsers],
  ["Trainers", "/trainers", FiUserCheck],
  ["Membership Plans", "/plans", FiBarChart2],
  ["Enrollments", "/enrollments", FiHeart],
  ["Payments", "/payments", FiCreditCard],
  ["Attendance", "/attendance", FiCalendar],
  ["Workout Plans", "/workouts", FiActivity],
  ["Diet Plans", "/diets", FiHeart],
];

export default function Sidebar() {
  const role = getRole();
  const visibleItems = items.filter(([, path]) => path !== "/plans" || role === "admin");
  return <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white lg:block">
    <div className="flex h-full min-h-screen flex-col p-5">
      <div className="mb-10 flex items-center gap-3 px-2"><div className="grid h-10 w-10 place-items-center rounded-xl bg-teal-600 text-lg font-black text-white">F</div><div><p className="font-display text-xl font-bold tracking-tight text-slate-900">FitSphere</p><p className="text-[10px] font-bold uppercase tracking-[0.2em] text-teal-600">Gym operations</p></div></div>
      <nav className="space-y-1">{visibleItems.map(([label, path, Icon]) => <NavLink key={path} to={path} className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition ${isActive ? "bg-teal-50 text-teal-700" : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"}`}><Icon size={18} />{label}</NavLink>)}</nav>
      <div className="mt-auto rounded-2xl bg-slate-900 p-4 text-white"><p className="text-xs font-bold uppercase tracking-widest text-teal-300">Workspace</p><p className="mt-2 text-sm text-slate-300">Signed in as {role}</p></div>
    </div>
  </aside>;
}
