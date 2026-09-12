import { useCallback, useEffect, useState } from "react";
import { FiEdit2, FiEye, FiPlus, FiRefreshCw, FiSave, FiTrash2, FiX } from "react-icons/fi";
import api from "../services/api";
import Loading from "../components/Loading";
import Table from "../components/Table";
import { getRole } from "../utils/auth";
import { getRows } from "../utils/response";

const emptyForm = {
	user: "",
	specialization: "",
	experience: "",
	qualification: "",
	salary: "",
	availability: true,
};

function getErrorMessage(error, fallback) {
	const data = error.response?.data;
	if (typeof data === "string") return data;
	if (data?.detail) return data.detail;
	if (data && typeof data === "object") return Object.values(data).flat().join(" ");
	return fallback;
}

export default function Trainers() {
	const [trainers, setTrainers] = useState([]);
	const [loading, setLoading] = useState(true);
	const [saving, setSaving] = useState(false);
	const [error, setError] = useState("");
	const [success, setSuccess] = useState("");
	const [form, setForm] = useState(emptyForm);
	const [editingId, setEditingId] = useState(null);
	const [selectedTrainer, setSelectedTrainer] = useState(null);
	const [formOpen, setFormOpen] = useState(false);
	const canManage = getRole() === "admin";

	const loadTrainers = useCallback(async () => {
		setLoading(true);
		setError("");
		try {
			const response = await api.get("trainers/");
			setTrainers(getRows(response.data));
		} catch (requestError) {
			setError(getErrorMessage(requestError, "Unable to load trainers."));
		} finally {
			setLoading(false);
		}
	}, []);

	useEffect(() => {
		// The request owns the loading lifecycle for this screen.
		// eslint-disable-next-line react-hooks/set-state-in-effect
		loadTrainers();
	}, [loadTrainers]);

	const openCreate = () => {
		setEditingId(null);
		setForm(emptyForm);
		setError("");
		setSuccess("");
		setFormOpen(true);
	};

	const openEdit = (trainer) => {
		setEditingId(trainer.id);
		setForm({
			user: trainer.user ?? "",
			specialization: trainer.specialization ?? "",
			experience: trainer.experience ?? "",
			qualification: trainer.qualification ?? "",
			salary: trainer.salary ?? "",
			availability: trainer.availability ?? true,
		});
		setError("");
		setSuccess("");
		setFormOpen(true);
	};

	const handleChange = (event) => {
		const { name, value, type, checked } = event.target;
		setForm((current) => ({ ...current, [name]: type === "checkbox" ? checked : value }));
	};

	const saveTrainer = async (event) => {
		event.preventDefault();
		setSaving(true);
		setError("");
		setSuccess("");
		const payload = {
			...form,
			user: Number(form.user),
			experience: Number(form.experience),
			salary: form.salary,
		};
		try {
			if (editingId) {
				await api.patch(`trainers/${editingId}/`, payload);
				setSuccess("Trainer updated successfully.");
			} else {
				await api.post("trainers/", payload);
				setSuccess("Trainer created successfully.");
			}
			setFormOpen(false);
			setForm(emptyForm);
			await loadTrainers();
		} catch (requestError) {
			setError(getErrorMessage(requestError, "Unable to save trainer."));
		} finally {
			setSaving(false);
		}
	};

	const deleteTrainer = async (trainer) => {
		if (!window.confirm(`Delete trainer ${trainer.id}?`)) return;
		setError("");
		setSuccess("");
		try {
			await api.delete(`trainers/${trainer.id}/`);
			setSuccess("Trainer deleted successfully.");
			await loadTrainers();
		} catch (requestError) {
			setError(getErrorMessage(requestError, "Unable to delete trainer."));
		}
	};

	const columns = [
		{ key: "id", label: "ID" },
		{ key: "user", label: "User" },
		{ key: "specialization", label: "Specialization" },
		{ key: "experience", label: "Experience", render: (row) => `${row.experience} years` },
		{ key: "qualification", label: "Qualification" },
		{ key: "availability", label: "Status", render: (row) => row.availability ? "Available" : "Unavailable" },
		{ key: "actions", label: "Actions", render: (row) => <div className="flex items-center gap-1"><button onClick={() => setSelectedTrainer(row)} className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-900" title="View trainer"><FiEye size={16} /></button>{canManage && <><button onClick={() => openEdit(row)} className="rounded-lg p-2 text-slate-400 hover:bg-teal-50 hover:text-teal-700" title="Edit trainer"><FiEdit2 size={16} /></button><button onClick={() => deleteTrainer(row)} className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600" title="Delete trainer"><FiTrash2 size={16} /></button></>}</div> },
	];

	return <section className="space-y-6"><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="text-xs font-bold uppercase tracking-[0.2em] text-teal-600">People</p><h1 className="mt-2 font-display text-3xl font-bold tracking-tight text-slate-900">Trainers</h1><p className="mt-2 max-w-2xl text-sm text-slate-500">Manage the coaching team connected to member workout plans.</p></div><div className="flex gap-2">{canManage && <button onClick={openCreate} className="inline-flex items-center gap-2 rounded-xl bg-teal-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-teal-700"><FiPlus size={16} /> Add trainer</button>}<button onClick={loadTrainers} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-600 hover:border-teal-300 hover:text-teal-700"><FiRefreshCw size={16} /> Refresh</button></div></div>{error && <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}{success && <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{success}</div>}<div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">{loading ? <div className="px-5"><Loading label="Loading trainers" /></div> : <Table rows={trainers} columns={columns} empty="No trainers found" />}</div>{formOpen && <TrainerForm form={form} editingId={editingId} saving={saving} onChange={handleChange} onSubmit={saveTrainer} onClose={() => setFormOpen(false)} />}{selectedTrainer && <TrainerDetails trainer={selectedTrainer} onClose={() => setSelectedTrainer(null)} />}</section>;
}

function TrainerForm({ form, editingId, saving, onChange, onSubmit, onClose }) {
	return <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 p-5"><form onSubmit={onSubmit} className="w-full max-w-xl rounded-2xl bg-white p-6 shadow-2xl"><div className="flex items-center justify-between"><div><p className="text-xs font-bold uppercase tracking-wider text-teal-600">Trainer management</p><h2 className="mt-1 font-display text-2xl font-bold text-slate-900">{editingId ? "Edit trainer" : "Add trainer"}</h2></div><button type="button" onClick={onClose} className="rounded-lg p-2 text-slate-400 hover:bg-slate-100" title="Close"><FiX /></button></div><div className="mt-6 grid gap-4 sm:grid-cols-2"><Field label="User ID" name="user" type="number" value={form.user} onChange={onChange} required /><Field label="Specialization" name="specialization" value={form.specialization} onChange={onChange} required /><Field label="Experience (years)" name="experience" type="number" min="0" value={form.experience} onChange={onChange} required /><Field label="Salary" name="salary" type="number" min="0" step="0.01" value={form.salary} onChange={onChange} required /><Field label="Qualification" name="qualification" value={form.qualification} onChange={onChange} required /><label className="flex items-center gap-3 self-end rounded-xl border border-slate-200 px-3 py-3 text-sm font-semibold text-slate-700"><input type="checkbox" name="availability" checked={form.availability} onChange={onChange} className="h-4 w-4 accent-teal-600" /> Available for sessions</label></div><div className="mt-6 flex justify-end gap-3"><button type="button" onClick={onClose} className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-bold text-slate-600">Cancel</button><button disabled={saving} className="inline-flex items-center gap-2 rounded-xl bg-teal-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-teal-700 disabled:opacity-60"><FiSave size={16} />{saving ? "Saving..." : "Save trainer"}</button></div></form></div>;
}

function Field({ label, name, onChange, ...props }) {
	return <label className="block text-sm font-bold text-slate-700">{label}<input name={name} onChange={onChange} className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 font-normal outline-none focus:border-teal-500" {...props} /></label>;
}

function TrainerDetails({ trainer, onClose }) {
	return <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 p-5"><div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl"><div className="flex items-start justify-between"><div><p className="text-xs font-bold uppercase tracking-wider text-teal-600">Trainer details</p><h2 className="mt-1 font-display text-2xl font-bold text-slate-900">Trainer #{trainer.id}</h2></div><button onClick={onClose} className="rounded-lg p-2 text-slate-400 hover:bg-slate-100" title="Close"><FiX /></button></div><dl className="mt-6 divide-y divide-slate-100 text-sm"><Detail label="User ID" value={trainer.user} /><Detail label="Specialization" value={trainer.specialization} /><Detail label="Experience" value={`${trainer.experience} years`} /><Detail label="Qualification" value={trainer.qualification} /><Detail label="Salary" value={trainer.salary} /><Detail label="Status" value={trainer.availability ? "Available" : "Unavailable"} /></dl></div></div>;
}

function Detail({ label, value }) {
	return <div className="flex justify-between gap-4 py-3"><dt className="text-slate-400">{label}</dt><dd className="text-right font-semibold text-slate-700">{value || "-"}</dd></div>;
}
