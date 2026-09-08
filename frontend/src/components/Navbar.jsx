import { FiLogOut, FiMenu } from "react-icons/fi";
import { useNavigate } from "react-router-dom";
import { getRole, getUsername, logout } from "../utils/auth";

export default function Navbar({ onMenu }) {
  const navigate = useNavigate();
  const handleLogout = () => { logout(); navigate("/login"); };
  return <header className="flex h-20 items-center justify-between border-b border-slate-200 bg-white px-5 sm:px-8"><button className="text-slate-500 lg:hidden" onClick={onMenu} aria-label="Open navigation"><FiMenu size={22} /></button><div className="ml-auto flex items-center gap-4"><div className="hidden text-right sm:block"><p className="text-sm font-bold text-slate-800">{getUsername()}</p><p className="text-xs capitalize text-slate-400">{getRole()} account</p></div><div className="grid h-10 w-10 place-items-center rounded-full bg-amber-100 font-bold text-amber-800">{getUsername().slice(0, 1).toUpperCase()}</div><button onClick={handleLogout} className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-900" title="Sign out"><FiLogOut size={18} /></button></div></header>;
}
