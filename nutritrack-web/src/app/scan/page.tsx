"use client";
import { useState, useRef, useCallback } from "react";
import AppLayout from "@/components/layout/AppLayout";
import HealthScoreRing from "@/components/ui/HealthScoreRing";
import AllergenBadge from "@/components/ui/AllergenBadge";
import { predictApi, shoppingApi } from "@/lib/api";
import { PredictResult, ShoppingList } from "@/types";
import { Upload, Camera, CheckCircle, Plus, ShoppingCart } from "lucide-react";

export default function ScanPage() {
  const fileInput  = useRef<HTMLInputElement>(null);
  const [preview,  setPreview]  = useState<string | null>(null);
  const [loading,  setLoading]  = useState(false);
  const [result,   setResult]   = useState<PredictResult | null>(null);
  const [error,    setError]    = useState("");
  const [addedMsg, setAddedMsg] = useState("");

  // Drag-and-drop state
  const [dragging, setDragging] = useState(false);

  const processFile = async (file: File) => {
    setPreview(URL.createObjectURL(file));
    setResult(null);
    setError("");
    setAddedMsg("");
    setLoading(true);
    try {
      const { data } = await predictApi.predict(file);
      setResult(data);
    } catch {
      setError("Recognition failed. Please try another image.");
    } finally {
      setLoading(false);
    }
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith("image/")) processFile(file);
  }, []);

  const addIngredientsToList = async () => {
    if (!result?.ingredients.length) return;
    try {
      // Get or create a default list
      let lists: ShoppingList[] = [];
      try {
        const { data } = await shoppingApi.getLists();
        lists = data;
      } catch { /* not logged in — skip */ }

      let listId: number;
      if (lists.length > 0) {
        listId = lists[0].id;
      } else {
        const { data } = await shoppingApi.createList("My List");
        listId = data.id;
      }

      const items = result.ingredients.map((name) => ({
        name,
        quantity: 1,
        unit: "pcs",
        category: "other",
        source_food: result.food_name,
      }));

      await shoppingApi.addBulk(listId, items);
      setAddedMsg(`${items.length} ingredients added to your shopping list ✓`);
    } catch {
      setAddedMsg("Sign in to save ingredients to your shopping list.");
    }
  };

  const NutrientRow = ({ label, value, unit }: { label: string; value?: number; unit: string }) =>
    value != null ? (
      <div className="flex justify-between text-sm py-1 border-b border-gray-50 last:border-0">
        <span className="text-gray-500">{label}</span>
        <span className="font-medium">{value.toFixed(1)} {unit}</span>
      </div>
    ) : null;

  return (
    <AppLayout>
      <h1 className="text-2xl font-bold mb-6">Scan Food</h1>

      {/* Upload zone */}
      <div
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors mb-6
          ${dragging ? "border-brand-500 bg-brand-50" : "border-gray-200 hover:border-brand-400 hover:bg-gray-50"}`}
        onClick={() => fileInput.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <input ref={fileInput} type="file" accept="image/*" className="hidden" onChange={onFileChange} />
        {preview ? (
          <img src={preview} alt="Preview" className="max-h-56 mx-auto rounded-lg object-contain" />
        ) : (
          <div className="space-y-3">
            <div className="flex justify-center gap-3 text-gray-300">
              <Upload size={36} />
              <Camera size={36} />
            </div>
            <p className="text-gray-500 font-medium">Drop an image here or click to upload</p>
            <p className="text-gray-400 text-sm">JPEG, PNG or WebP</p>
          </div>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <div className="card text-center py-10">
          <div className="w-10 h-10 border-4 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-gray-500">Analysing image…</p>
        </div>
      )}

      {/* Error */}
      {error && <div className="bg-red-50 border border-red-200 text-red-600 rounded-lg p-4 text-sm">{error}</div>}

      {/* Result */}
      {result && !loading && (
        <div className="space-y-4">
          {/* Header card */}
          <div className="card flex items-start gap-6">
            {result.health_score != null && <HealthScoreRing score={result.health_score} size={90} />}
            <div className="flex-1">
              <h2 className="text-2xl font-bold capitalize">{result.food_name}</h2>
              <p className="text-gray-400 text-sm mt-1">
                {(result.confidence * 100).toFixed(0)}% confidence · {result.model_used.toUpperCase()} model
              </p>
              {result.allergens.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {result.allergens.map((a) => <AllergenBadge key={a.allergen} {...a} />)}
                </div>
              )}
            </div>
          </div>

          {/* Nutrients + Ingredients side by side */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Nutrients */}
            {Object.keys(result.nutrients).length > 0 && (
              <div className="card">
                <h3 className="font-semibold mb-3 text-gray-700">Nutrition per 100g</h3>
                <NutrientRow label="Calories" value={result.nutrients.calories} unit="kcal" />
                <NutrientRow label="Protein"  value={result.nutrients.protein}  unit="g" />
                <NutrientRow label="Fat"      value={result.nutrients.fat}      unit="g" />
                <NutrientRow label="Carbs"    value={result.nutrients.carbs}    unit="g" />
                <NutrientRow label="Fibre"    value={result.nutrients.fiber}    unit="g" />
                <NutrientRow label="Sugar"    value={result.nutrients.sugar}    unit="g" />
                <NutrientRow label="Sodium"   value={result.nutrients.sodium}   unit="mg" />
              </div>
            )}

            {/* Ingredients */}
            {result.ingredients.length > 0 && (
              <div className="card">
                <h3 className="font-semibold mb-3 text-gray-700">Ingredients</h3>
                <ul className="space-y-1 mb-4">
                  {result.ingredients.map((ing) => (
                    <li key={ing} className="flex items-center gap-2 text-sm text-gray-600">
                      <span className="w-1.5 h-1.5 bg-brand-500 rounded-full flex-shrink-0" />
                      <span className="capitalize">{ing}</span>
                    </li>
                  ))}
                </ul>

                {addedMsg ? (
                  <div className="flex items-center gap-2 text-brand-600 text-sm font-medium">
                    <CheckCircle size={16} /> {addedMsg}
                  </div>
                ) : (
                  <button onClick={addIngredientsToList}
                    className="btn-primary w-full flex items-center justify-center gap-2 text-sm">
                    <ShoppingCart size={15} />
                    Add ingredients to shopping list
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Scan another */}
          <button onClick={() => { setResult(null); setPreview(null); setAddedMsg(""); }}
            className="btn-secondary flex items-center gap-2">
            <Plus size={16} /> Scan another food
          </button>
        </div>
      )}
    </AppLayout>
  );
}
