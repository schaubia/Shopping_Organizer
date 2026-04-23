"use client";
import { useState, useEffect } from "react";
import AppLayout from "@/components/layout/AppLayout";
import { spendingApi } from "@/lib/api";
import { SpendingLog, SpendingSummary } from "@/types";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import { Plus, Store, TrendingDown, ShoppingBag, Calendar } from "lucide-react";

export default function SpendingPage() {
  const [logs,        setLogs]        = useState<SpendingLog[]>([]);
  const [summary,     setSummary]     = useState<SpendingSummary | null>(null);
  const [loading,     setLoading]     = useState(true);
  const [showLog,     setShowLog]     = useState(false);

  // New trip form
  const [storeName,    setStoreName]    = useState("");
  const [totalSpent,   setTotalSpent]   = useState("");
  const [currency,     setCurrency]     = useState("BGN");
  const [receiptNote,  setReceiptNote]  = useState("");
  const [tripItems,    setTripItems]    = useState([{ name: "", qty: 1, price: 0 }]);
  const [saving,       setSaving]       = useState(false);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [logsRes, summaryRes] = await Promise.all([
        spendingApi.getLogs(),
        spendingApi.summary(),
      ]);
      setLogs(logsRes.data);
      setSummary(summaryRes.data);
    } catch { /* not logged in */ }
    finally { setLoading(false); }
  };

  const saveTrip = async () => {
    if (!totalSpent) return;
    setSaving(true);
    try {
      const validItems = tripItems.filter((i) => i.name.trim() && i.price > 0);
      await spendingApi.logSpending({
        store_name:   storeName || null,
        total_spent:  parseFloat(totalSpent),
        currency,
        items:        validItems,
        receipt_note: receiptNote || null,
      });
      setShowLog(false);
      setStoreName(""); setTotalSpent(""); setReceiptNote("");
      setTripItems([{ name: "", qty: 1, price: 0 }]);
      await fetchData();
    } finally { setSaving(false); }
  };

  const updateTripItem = (idx: number, field: string, value: string | number) => {
    setTripItems(tripItems.map((item, i) => i === idx ? { ...item, [field]: value } : item));
  };

  const addTripItem    = () => setTripItems([...tripItems, { name: "", qty: 1, price: 0 }]);
  const removeTripItem = (idx: number) => setTripItems(tripItems.filter((_, i) => i !== idx));

  // Build monthly chart data from logs
  const monthlyData = logs.reduce((acc, log) => {
    const month = new Date(log.bought_at).toLocaleString("default", { month: "short", year: "2-digit" });
    const existing = acc.find((d) => d.month === month);
    if (existing) existing.spent += log.total_spent;
    else acc.push({ month, spent: parseFloat(log.total_spent.toFixed(2)) });
    return acc;
  }, [] as { month: string; spent: number }[]).reverse();

  const formatDate = (d: string) =>
    new Date(d).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });

  if (loading) return (
    <AppLayout>
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    </AppLayout>
  );

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Spending</h1>
        <button onClick={() => setShowLog(!showLog)} className="btn-primary flex items-center gap-2">
          <Plus size={16} /> Log trip
        </button>
      </div>

      {/* Log trip form */}
      {showLog && (
        <div className="card mb-6 space-y-4">
          <h3 className="font-semibold text-gray-700">New shopping trip</h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 font-medium">Store (optional)</label>
              <input className="input mt-1" placeholder="e.g. Kaufland" value={storeName}
                onChange={(e) => setStoreName(e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-gray-500 font-medium">Total spent *</label>
              <div className="flex gap-2 mt-1">
                <input className="input flex-1" type="number" step="0.01" placeholder="0.00"
                  value={totalSpent} onChange={(e) => setTotalSpent(e.target.value)} />
                <select className="input w-24" value={currency} onChange={(e) => setCurrency(e.target.value)}>
                  <option>BGN</option><option>EUR</option><option>USD</option>
                </select>
              </div>
            </div>
          </div>

          {/* Item breakdown */}
          <div>
            <label className="text-xs text-gray-500 font-medium">Item breakdown (optional)</label>
            <div className="mt-2 space-y-2">
              {tripItems.map((item, idx) => (
                <div key={idx} className="flex gap-2 items-center">
                  <input className="input flex-1" placeholder="Item name" value={item.name}
                    onChange={(e) => updateTripItem(idx, "name", e.target.value)} />
                  <input className="input w-16" type="number" min="1" value={item.qty}
                    onChange={(e) => updateTripItem(idx, "qty", parseInt(e.target.value) || 1)} />
                  <input className="input w-24" type="number" step="0.01" placeholder="price"
                    value={item.price || ""}
                    onChange={(e) => updateTripItem(idx, "price", parseFloat(e.target.value) || 0)} />
                  {tripItems.length > 1 && (
                    <button onClick={() => removeTripItem(idx)} className="text-red-400 hover:text-red-600 text-sm">✕</button>
                  )}
                </div>
              ))}
            </div>
            <button onClick={addTripItem} className="text-sm text-brand-600 hover:text-brand-700 mt-2 font-medium">
              + Add item
            </button>
          </div>

          <div>
            <label className="text-xs text-gray-500 font-medium">Note (optional)</label>
            <input className="input mt-1" placeholder="e.g. weekly shop" value={receiptNote}
              onChange={(e) => setReceiptNote(e.target.value)} />
          </div>

          <div className="flex gap-2 pt-2">
            <button className="btn-primary" onClick={saveTrip} disabled={saving || !totalSpent}>
              {saving ? "Saving…" : "Save trip"}
            </button>
            <button className="btn-secondary" onClick={() => setShowLog(false)}>Cancel</button>
          </div>
        </div>
      )}

      {/* Summary cards */}
      {summary && summary.num_trips > 0 && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="card text-center">
            <ShoppingBag size={24} className="mx-auto text-brand-500 mb-2" />
            <p className="text-2xl font-bold">{summary.total_spent.toFixed(2)}</p>
            <p className="text-xs text-gray-400 mt-0.5">total spent ({summary.currency})</p>
          </div>
          <div className="card text-center">
            <Calendar size={24} className="mx-auto text-blue-500 mb-2" />
            <p className="text-2xl font-bold">{summary.average_per_trip.toFixed(2)}</p>
            <p className="text-xs text-gray-400 mt-0.5">avg per trip ({summary.currency})</p>
          </div>
          <div className="card text-center">
            <Store size={24} className="mx-auto text-purple-500 mb-2" />
            <p className="text-2xl font-bold">{summary.num_trips}</p>
            <p className="text-xs text-gray-400 mt-0.5">shopping trips</p>
          </div>
        </div>
      )}

      {/* Monthly spend chart */}
      {monthlyData.length > 1 && (
        <div className="card mb-6">
          <h3 className="font-semibold mb-4 text-gray-700">Monthly spending</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={monthlyData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v: number) => [`${v.toFixed(2)} лв`, "Spent"]} />
              <Bar dataKey="spent" fill="#16a34a" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Top categories */}
      {summary && summary.top_categories.length > 0 && (
        <div className="card mb-6">
          <h3 className="font-semibold mb-4 text-gray-700 flex items-center gap-2">
            <TrendingDown size={18} className="text-brand-500" /> Top items by spend
          </h3>
          <div className="space-y-2">
            {summary.top_categories.slice(0, 8).map((cat, i) => {
              const pct = summary.total_spent > 0 ? (cat.total / summary.total_spent) * 100 : 0;
              return (
                <div key={cat.name} className="flex items-center gap-3">
                  <span className="text-xs text-gray-400 w-4">{i + 1}</span>
                  <span className="text-sm flex-1 capitalize">{cat.name}</span>
                  <div className="w-32 bg-gray-100 rounded-full h-1.5">
                    <div className="bg-brand-500 h-1.5 rounded-full" style={{ width: `${pct}%` }} />
                  </div>
                  <span className="text-sm font-medium w-16 text-right">{cat.total.toFixed(2)} лв</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Trip history */}
      <div className="card">
        <h3 className="font-semibold mb-4 text-gray-700">Trip history</h3>
        {logs.length === 0 ? (
          <div className="text-center py-10 text-gray-400">
            <ShoppingBag size={36} className="mx-auto mb-2 opacity-30" />
            <p className="text-sm">No trips logged yet. Hit "Log trip" above to start.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {logs.map((log) => (
              <div key={log.id} className="flex items-center justify-between py-3 border-b border-gray-50 last:border-0">
                <div>
                  <p className="font-medium text-sm">{log.store_name || "Shopping trip"}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{formatDate(log.bought_at)}</p>
                </div>
                <div className="text-right">
                  <p className="font-semibold">{log.total_spent.toFixed(2)} {log.currency}</p>
                  {log.items && log.items.length > 0 && (
                    <p className="text-xs text-gray-400 mt-0.5">{log.items.length} items</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
