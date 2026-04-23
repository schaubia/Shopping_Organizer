"use client";
import { useState, useEffect } from "react";
import AppLayout from "@/components/layout/AppLayout";
import { shoppingApi } from "@/lib/api";
import { ShoppingList, ShoppingItem } from "@/types";
import { Plus, Trash2, Check, ChevronDown, ChevronRight, ShoppingBag } from "lucide-react";
import clsx from "clsx";

const CATEGORIES = ["produce", "dairy", "meat", "grains", "other"];
const UNITS       = ["pcs", "g", "kg", "ml", "l"];

export default function ShoppingPage() {
  const [lists,       setLists]       = useState<ShoppingList[]>([]);
  const [activeList,  setActiveList]  = useState<number | null>(null);
  const [loading,     setLoading]     = useState(true);
  const [newListName, setNewListName] = useState("");
  const [showNewList, setShowNewList] = useState(false);
  const [newItem,     setNewItem]     = useState({ name: "", quantity: 1, unit: "pcs", category: "other", estimated_price: "" });
  const [showNewItem, setShowNewItem] = useState(false);

  useEffect(() => { fetchLists(); }, []);

  const fetchLists = async () => {
    setLoading(true);
    try {
      const { data } = await shoppingApi.getLists();
      setLists(data);
      if (data.length > 0 && !activeList) setActiveList(data[0].id);
    } catch { /* not logged in */ }
    finally { setLoading(false); }
  };

  const currentList = lists.find((l) => l.id === activeList);

  const createList = async () => {
    if (!newListName.trim()) return;
    const { data } = await shoppingApi.createList(newListName.trim());
    setLists([...lists, { ...data, items: [] }]);
    setActiveList(data.id);
    setNewListName("");
    setShowNewList(false);
  };

  const deleteList = async (id: number) => {
    await shoppingApi.deleteList(id);
    const updated = lists.filter((l) => l.id !== id);
    setLists(updated);
    if (activeList === id) setActiveList(updated[0]?.id ?? null);
  };

  const addItem = async () => {
    if (!newItem.name.trim() || activeList == null) return;
    const payload = {
      ...newItem,
      estimated_price: newItem.estimated_price ? parseFloat(newItem.estimated_price) : null,
    };
    const { data } = await shoppingApi.addItem(activeList, payload);
    setLists(lists.map((l) => l.id === activeList ? { ...l, items: [...l.items, data] } : l));
    setNewItem({ name: "", quantity: 1, unit: "pcs", category: "other", estimated_price: "" });
    setShowNewItem(false);
  };

  const toggleCheck = async (item: ShoppingItem) => {
    if (!currentList) return;
    const { data } = await shoppingApi.updateItem(currentList.id, item.id, { is_checked: !item.is_checked });
    setLists(lists.map((l) => l.id === activeList
      ? { ...l, items: l.items.map((i) => i.id === item.id ? data : i) }
      : l));
  };

  const updatePrice = async (item: ShoppingItem, price: string) => {
    if (!currentList) return;
    const val = parseFloat(price);
    if (isNaN(val)) return;
    const { data } = await shoppingApi.updateItem(currentList.id, item.id, { actual_price: val });
    setLists(lists.map((l) => l.id === activeList
      ? { ...l, items: l.items.map((i) => i.id === item.id ? data : i) }
      : l));
  };

  const deleteItem = async (item: ShoppingItem) => {
    if (!currentList) return;
    await shoppingApi.deleteItem(currentList.id, item.id);
    setLists(lists.map((l) => l.id === activeList
      ? { ...l, items: l.items.filter((i) => i.id !== item.id) }
      : l));
  };

  const totalEstimated = currentList?.items.reduce((s, i) => s + (i.estimated_price ?? 0) * i.quantity, 0) ?? 0;
  const totalActual    = currentList?.items.reduce((s, i) => s + (i.actual_price    ?? 0) * i.quantity, 0) ?? 0;
  const checkedCount   = currentList?.items.filter((i) => i.is_checked).length ?? 0;

  // Group items by category
  const grouped = CATEGORIES.reduce((acc, cat) => {
    const items = currentList?.items.filter((i) => i.category === cat) ?? [];
    if (items.length > 0) acc[cat] = items;
    return acc;
  }, {} as Record<string, ShoppingItem[]>);

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
        <h1 className="text-2xl font-bold">Shopping List</h1>
        <button onClick={() => setShowNewList(!showNewList)} className="btn-primary flex items-center gap-2">
          <Plus size={16} /> New list
        </button>
      </div>

      {/* New list form */}
      {showNewList && (
        <div className="card mb-4 flex gap-2">
          <input className="input flex-1" placeholder="List name…" value={newListName}
            onChange={(e) => setNewListName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && createList()} />
          <button className="btn-primary" onClick={createList}>Create</button>
        </div>
      )}

      {lists.length === 0 ? (
        <div className="card text-center py-16 text-gray-400">
          <ShoppingBag size={48} className="mx-auto mb-3 opacity-30" />
          <p className="font-medium">No lists yet</p>
          <p className="text-sm mt-1">Create your first shopping list above</p>
        </div>
      ) : (
        <div className="flex gap-6">
          {/* List selector */}
          <div className="w-44 flex-shrink-0 space-y-1">
            {lists.map((l) => (
              <div key={l.id}
                className={clsx("flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer text-sm group",
                  l.id === activeList ? "bg-brand-50 text-brand-700 font-medium" : "hover:bg-gray-50 text-gray-600")}
                onClick={() => setActiveList(l.id)}>
                <span className="truncate">{l.name}</span>
                <button onClick={(e) => { e.stopPropagation(); deleteList(l.id); }}
                  className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600 transition-opacity">
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>

          {/* Active list */}
          {currentList && (
            <div className="flex-1 min-w-0">
              {/* Summary bar */}
              <div className="card mb-4 flex items-center gap-6 py-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-brand-600">{checkedCount}/{currentList.items.length}</p>
                  <p className="text-xs text-gray-400 mt-0.5">items done</p>
                </div>
                <div className="h-10 w-px bg-gray-100" />
                <div className="text-center">
                  <p className="text-lg font-semibold">{totalEstimated.toFixed(2)} лв</p>
                  <p className="text-xs text-gray-400 mt-0.5">estimated</p>
                </div>
                {totalActual > 0 && (
                  <>
                    <div className="h-10 w-px bg-gray-100" />
                    <div className="text-center">
                      <p className="text-lg font-semibold text-green-600">{totalActual.toFixed(2)} лв</p>
                      <p className="text-xs text-gray-400 mt-0.5">actual</p>
                    </div>
                  </>
                )}
              </div>

              {/* Items by category */}
              <div className="card">
                {Object.entries(grouped).map(([cat, items]) => (
                  <div key={cat} className="mb-4 last:mb-0">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2 capitalize">{cat}</h4>
                    <div className="space-y-1">
                      {items.map((item) => (
                        <div key={item.id}
                          className={clsx("flex items-center gap-3 p-2 rounded-lg transition-colors group",
                            item.is_checked ? "opacity-50" : "hover:bg-gray-50")}>
                          {/* Checkbox */}
                          <button onClick={() => toggleCheck(item)}
                            className={clsx("w-5 h-5 rounded border-2 flex-shrink-0 flex items-center justify-center transition-colors",
                              item.is_checked ? "bg-brand-500 border-brand-500 text-white" : "border-gray-300 hover:border-brand-400")}>
                            {item.is_checked && <Check size={12} />}
                          </button>

                          {/* Name + qty */}
                          <span className={clsx("flex-1 text-sm capitalize", item.is_checked && "line-through")}>
                            {item.name}
                          </span>
                          <span className="text-xs text-gray-400">{item.quantity} {item.unit}</span>

                          {/* Actual price input */}
                          <input
                            type="number" step="0.01" placeholder="price"
                            defaultValue={item.actual_price ?? ""}
                            onBlur={(e) => updatePrice(item, e.target.value)}
                            className="w-20 text-xs border border-gray-200 rounded px-2 py-1 text-right focus:outline-none focus:ring-1 focus:ring-brand-400"
                          />
                          <span className="text-xs text-gray-400">лв</span>

                          {/* Delete */}
                          <button onClick={() => deleteItem(item)}
                            className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600 transition-opacity">
                            <Trash2 size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}

                {/* Add item form */}
                {showNewItem ? (
                  <div className="mt-4 border-t border-gray-100 pt-4 space-y-3">
                    <div className="grid grid-cols-2 gap-2">
                      <input className="input col-span-2" placeholder="Item name" value={newItem.name}
                        onChange={(e) => setNewItem({ ...newItem, name: e.target.value })} />
                      <div className="flex gap-2">
                        <input className="input w-20" type="number" min="0.1" step="0.1" value={newItem.quantity}
                          onChange={(e) => setNewItem({ ...newItem, quantity: parseFloat(e.target.value) })} />
                        <select className="input" value={newItem.unit}
                          onChange={(e) => setNewItem({ ...newItem, unit: e.target.value })}>
                          {UNITS.map((u) => <option key={u}>{u}</option>)}
                        </select>
                      </div>
                      <div className="flex gap-2">
                        <select className="input" value={newItem.category}
                          onChange={(e) => setNewItem({ ...newItem, category: e.target.value })}>
                          {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
                        </select>
                        <input className="input w-24" type="number" step="0.01" placeholder="est. лв"
                          value={newItem.estimated_price}
                          onChange={(e) => setNewItem({ ...newItem, estimated_price: e.target.value })} />
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button className="btn-primary" onClick={addItem}>Add item</button>
                      <button className="btn-secondary" onClick={() => setShowNewItem(false)}>Cancel</button>
                    </div>
                  </div>
                ) : (
                  <button onClick={() => setShowNewItem(true)}
                    className="mt-4 flex items-center gap-2 text-sm text-brand-600 hover:text-brand-700 font-medium border-t border-gray-100 pt-4 w-full">
                    <Plus size={16} /> Add item
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </AppLayout>
  );
}
