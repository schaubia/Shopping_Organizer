export interface User {
  id:         number;
  email:      string;
  full_name:  string | null;
  plan:       "free" | "personal" | "family";
  created_at: string;
}

export interface Allergen {
  allergen: string;
  severity: "high" | "medium" | "low";
}

export interface PredictResult {
  food_name:    string;
  confidence:   number;
  model_used:   string;
  health_score: number | null;
  nutrients:    Record<string, number>;
  allergens:    Allergen[];
  ingredients:  string[];
}

export interface ShoppingItem {
  id:              number;
  name:            string;
  quantity:        number;
  unit:            string;
  category:        string;
  estimated_price: number | null;
  actual_price:    number | null;
  is_checked:      boolean;
  notes:           string | null;
  source_food:     string | null;
}

export interface ShoppingList {
  id:         number;
  name:       string;
  created_at: string;
  items:      ShoppingItem[];
}

export interface SpendingItem {
  name:  string;
  qty:   number;
  price: number;
}

export interface SpendingLog {
  id:          number;
  store_name:  string | null;
  total_spent: number;
  currency:    string;
  items:       SpendingItem[];
  bought_at:   string;
}

export interface SpendingSummary {
  total_spent:       number;
  average_per_trip:  number;
  num_trips:         number;
  top_categories:    { name: string; total: number }[];
  currency:          string;
}
