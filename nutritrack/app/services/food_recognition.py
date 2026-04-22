"""
Food recognition service.
Core logic migrated from HealthyFood/streamlit_app.py — models and USDA integration are unchanged.
The only difference: no Streamlit decorators (@st.cache_resource → functools.lru_cache).
"""
from __future__ import annotations

import os
import logging
import functools
import requests
from typing import Optional

import numpy as np
from PIL import Image

log = logging.getLogger(__name__)

USDA_API_KEY   = os.getenv("USDA_API_KEY", "DEMO_KEY")
USDA_SEARCH    = "https://api.nal.usda.gov/fdc/v1/foods/search"
CACHE_TTL      = 86_400          # 24 h — kept from original app


# ─────────────────────────────────────────────
# Allergen map (ported from original app)
# ─────────────────────────────────────────────
ALLERGEN_MAP: dict[str, list[str]] = {
    "gluten":     ["wheat","bread","pasta","flour","barley","rye","oat","cracker","muffin","cake","cookie","pizza","burger bun"],
    "dairy":      ["milk","cheese","butter","cream","yogurt","ice cream","whey","casein","lactose"],
    "eggs":       ["egg","omelette","frittata","quiche","mayonnaise","meringue","custard"],
    "peanuts":    ["peanut","peanut butter","groundnut"],
    "tree_nuts":  ["almond","cashew","walnut","pistachio","hazelnut","pecan","macadamia","brazil nut"],
    "soy":        ["soy","tofu","tempeh","edamame","miso","soy sauce"],
    "fish":       ["salmon","tuna","cod","tilapia","bass","flounder","haddock","halibut","mahi","trout","fish"],
    "shellfish":  ["shrimp","crab","lobster","clam","oyster","scallop","mussel","prawn"],
    "sesame":     ["sesame","tahini","hummus"],
    "corn":       ["corn","maize","polenta","grits","cornmeal","popcorn","tortilla"],
    "sulfites":   ["wine","dried fruit","vinegar","pickled"],
    "mustard":    ["mustard"],
    "gluten_free":[]
}

ALLERGEN_SEVERITY: dict[str, str] = {
    "gluten": "high", "dairy": "high", "eggs": "high",
    "peanuts": "high", "tree_nuts": "high", "shellfish": "high",
    "fish": "medium", "soy": "medium", "sesame": "medium",
    "corn": "low", "sulfites": "low", "mustard": "low",
}

# ─────────────────────────────────────────────
# Ingredient database (80+ dishes, from original app)
# ─────────────────────────────────────────────
INGREDIENT_DB: dict[str, list[str]] = {
    # Breakfast
    "pancakes":         ["flour","eggs","milk","butter","sugar","baking powder","salt"],
    "waffles":          ["flour","eggs","milk","butter","sugar","vanilla","baking powder"],
    "french toast":     ["bread","eggs","milk","butter","cinnamon","sugar","vanilla"],
    "eggs benedict":    ["english muffin","eggs","canadian bacon","hollandaise sauce"],
    "omelette":         ["eggs","butter","salt","pepper"],
    "scrambled eggs":   ["eggs","butter","milk","salt","pepper"],
    "granola":          ["oats","honey","nuts","dried fruit","oil"],
    "acai bowl":        ["acai","banana","berries","granola","honey"],
    # Italian
    "pizza":            ["dough","tomato sauce","mozzarella","olive oil","basil"],
    "pasta":            ["pasta","olive oil","garlic","salt","pepper"],
    "spaghetti bolognese":["spaghetti","ground beef","tomato sauce","onion","garlic","carrot"],
    "carbonara":        ["pasta","eggs","pancetta","parmesan","black pepper"],
    "lasagna":          ["lasagna sheets","beef","tomato sauce","béchamel","parmesan"],
    "risotto":          ["arborio rice","broth","onion","white wine","parmesan","butter"],
    # American
    "burger":           ["beef patty","bun","lettuce","tomato","onion","pickles","ketchup","mustard"],
    "hot dog":          ["sausage","bun","mustard","ketchup","relish"],
    "grilled cheese":   ["bread","cheese","butter"],
    "mac and cheese":   ["macaroni","cheddar","milk","butter","flour"],
    "fried chicken":    ["chicken","flour","eggs","breadcrumbs","oil","spices"],
    "bbq ribs":         ["pork ribs","bbq sauce","garlic","onion","spices"],
    "club sandwich":    ["bread","turkey","bacon","lettuce","tomato","mayo"],
    # Asian
    "sushi":            ["sushi rice","nori","fish","avocado","cucumber","soy sauce"],
    "ramen":            ["noodles","broth","pork","soft egg","nori","green onion"],
    "pad thai":         ["rice noodles","shrimp","tofu","bean sprouts","peanuts","fish sauce","lime"],
    "fried rice":       ["rice","eggs","soy sauce","vegetables","sesame oil","green onion"],
    "dumplings":        ["dough","pork","cabbage","ginger","soy sauce","sesame oil"],
    "spring rolls":     ["rice paper","vegetables","shrimp","vermicelli","herbs"],
    "pho":              ["rice noodles","beef broth","beef slices","bean sprouts","basil","lime"],
    "bibimbap":         ["rice","beef","vegetables","egg","gochujang","sesame oil"],
    # Mexican
    "tacos":            ["tortilla","meat","lettuce","tomato","cheese","salsa","sour cream"],
    "burrito":          ["flour tortilla","beans","rice","meat","cheese","salsa","guacamole"],
    "nachos":           ["tortilla chips","cheese","jalapeños","sour cream","guacamole","salsa"],
    "guacamole":        ["avocado","lime","cilantro","onion","tomato","salt"],
    "quesadilla":       ["flour tortilla","cheese","chicken","peppers","onion"],
    "enchiladas":       ["corn tortillas","chicken","cheese","enchilada sauce","onion"],
    # Salads / Soups
    "caesar salad":     ["romaine","croutons","parmesan","caesar dressing","lemon"],
    "greek salad":      ["cucumber","tomato","feta","olives","red onion","olive oil","oregano"],
    "tomato soup":      ["tomatoes","onion","garlic","broth","cream","basil","olive oil"],
    "chicken soup":     ["chicken","carrots","celery","onion","noodles","broth","parsley"],
    "minestrone":       ["vegetables","beans","pasta","tomatoes","broth","parmesan"],
    # Desserts
    "chocolate cake":   ["flour","sugar","cocoa","eggs","butter","milk","baking powder"],
    "cheesecake":       ["cream cheese","sugar","eggs","graham cracker crust","vanilla"],
    "tiramisu":         ["ladyfingers","mascarpone","eggs","sugar","espresso","cocoa"],
    "crème brûlée":     ["cream","egg yolks","sugar","vanilla"],
    "ice cream":        ["cream","milk","sugar","eggs","vanilla"],
    "brownie":          ["chocolate","butter","sugar","eggs","flour","cocoa"],
    # Healthy / Other
    "avocado toast":    ["bread","avocado","lemon","salt","pepper","red pepper flakes"],
    "smoothie bowl":    ["banana","berries","yogurt","granola","honey","chia seeds"],
    "falafel":          ["chickpeas","parsley","onion","garlic","cumin","flour","oil"],
    "hummus":           ["chickpeas","tahini","lemon","garlic","olive oil","cumin"],
    "shakshuka":        ["eggs","tomatoes","peppers","onion","garlic","spices"],
    "stir fry":         ["vegetables","soy sauce","garlic","ginger","oil","cornstarch"],
    "salmon":           ["salmon fillet","lemon","olive oil","dill","garlic","salt","pepper"],
    "grilled chicken":  ["chicken breast","olive oil","garlic","herbs","lemon","salt","pepper"],
}


# ─────────────────────────────────────────────
# Model loaders (lazy, cached — no Streamlit needed)
# ─────────────────────────────────────────────

@functools.lru_cache(maxsize=1)
def _load_vit():
    """ViT model for complex prepared dishes (nateraw/food)."""
    from transformers import AutoFeatureExtractor, AutoModelForImageClassification
    name = "nateraw/food"
    extractor = AutoFeatureExtractor.from_pretrained(name)
    model     = AutoModelForImageClassification.from_pretrained(name)
    log.info("ViT model loaded.")
    return extractor, model


@functools.lru_cache(maxsize=1)
def _load_resnet():
    """ResNet50 for simple foods and ingredients."""
    from tensorflow.keras.applications.resnet50 import ResNet50
    model = ResNet50(weights="imagenet", include_top=True, input_shape=(224, 224, 3))
    log.info("ResNet50 model loaded.")
    return model


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _is_complex_dish(name: str) -> bool:
    """Quick heuristic — complex dishes use ViT, simple ingredients use ResNet."""
    complex_keywords = {
        "pizza","burger","sandwich","sushi","ramen","pasta","lasagna",
        "stir fry","curry","casserole","risotto","soup","salad","tacos",
        "burrito","fried rice","pad thai","bibimbap","pho","dumplings",
        "cake","pie","tart","pudding","brownie","cheesecake","tiramisu",
    }
    return any(kw in name.lower() for kw in complex_keywords)


def detect_allergens(food_name: str) -> list[dict]:
    """Return list of {allergen, severity} for a food name."""
    name_lower = food_name.lower()
    found = []
    for allergen, keywords in ALLERGEN_MAP.items():
        if any(kw in name_lower for kw in keywords):
            found.append({
                "allergen":  allergen,
                "severity":  ALLERGEN_SEVERITY.get(allergen, "low"),
            })
    return found


def get_usda_nutrition(food_name: str) -> Optional[dict]:
    """Fetch nutrition data from USDA FoodData Central."""
    try:
        resp = requests.get(
            USDA_SEARCH,
            params={
                "api_key":  USDA_API_KEY,
                "query":    food_name,
                "dataType": ["Foundation", "SR Legacy"],
                "pageSize": 1,
            },
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("foods"):
            return None

        food = data["foods"][0]
        nutrients: dict[str, float] = {}
        for n in food.get("foodNutrients", []):
            name   = n.get("nutrientName", "")
            amount = n.get("value", 0)
            if "Energy"       in name: nutrients["calories"]  = amount
            elif "Protein"    in name: nutrients["protein"]   = amount
            elif "Total lipid"in name: nutrients["fat"]       = amount
            elif "Carbohydrate"in name: nutrients["carbs"]    = amount
            elif "Fiber"      in name: nutrients["fiber"]     = amount
            elif "Sugars"     in name: nutrients["sugar"]     = amount
            elif "Sodium"     in name: nutrients["sodium"]    = amount
        return nutrients
    except Exception as exc:
        log.warning("USDA lookup failed for '%s': %s", food_name, exc)
        return None


def calculate_health_score(nutrients: dict) -> float:
    """
    Score 1–10 from nutrient profile.
    Identical algorithm to the original HealthyFood app.
    """
    score = 5.0
    protein = nutrients.get("protein", 0)
    fiber   = nutrients.get("fiber", 0)
    fat     = nutrients.get("fat", 0)
    sugar   = nutrients.get("sugar", 0)
    sodium  = nutrients.get("sodium", 0)
    cals    = nutrients.get("calories", 0)

    if protein > 20: score += 1.5
    elif protein > 10: score += 0.75

    if fiber > 5: score += 2
    elif fiber > 2: score += 1

    if fat > 20: score -= 1.5
    elif fat > 10: score -= 0.5

    if sugar > 25: score -= 2
    elif sugar > 15: score -= 1

    if sodium > 800: score -= 1.5
    elif sodium > 400: score -= 0.5

    if cals > 600: score -= 1
    elif cals < 200 and protein > 5: score += 0.5

    return round(max(1.0, min(10.0, score)), 1)


# ─────────────────────────────────────────────
# Main prediction function
# ─────────────────────────────────────────────

def predict_food(image: Image.Image) -> dict:
    """
    Run food recognition on a PIL Image.
    Returns: {food_name, confidence, model_used, health_score, nutrients, allergens, ingredients}
    """
    import torch

    # ── ViT prediction ──
    extractor, vit_model = _load_vit()
    inputs  = extractor(images=image, return_tensors="pt")
    with torch.no_grad():
        logits = vit_model(**inputs).logits
    probs      = torch.softmax(logits, dim=-1)[0]
    top_idx    = int(probs.argmax())
    confidence = float(probs[top_idx])
    vit_label  = vit_model.config.id2label[top_idx].replace("_", " ").lower()

    # ── Optionally cross-check with ResNet for simple foods ──
    model_used = "vit"
    food_name  = vit_label

    if not _is_complex_dish(vit_label) or confidence < 0.5:
        try:
            from tensorflow.keras.applications.resnet50 import preprocess_input, decode_predictions
            rn_model  = _load_resnet()
            img_array = np.array(image.resize((224, 224))).astype("float32")
            img_array = preprocess_input(np.expand_dims(img_array, axis=0))
            preds     = rn_model.predict(img_array, verbose=0)
            decoded   = decode_predictions(preds, top=1)[0][0]
            rn_label  = decoded[1].replace("_", " ").lower()
            rn_conf   = float(decoded[2])

            if rn_conf > confidence:
                food_name  = rn_label
                confidence = rn_conf
                model_used = "resnet"
            else:
                model_used = "both"
        except Exception as exc:
            log.warning("ResNet inference failed: %s", exc)

    # ── Nutrition & scoring ──
    nutrients    = get_usda_nutrition(food_name) or {}
    health_score = calculate_health_score(nutrients) if nutrients else None
    allergens    = detect_allergens(food_name)

    # ── Ingredient suggestion ──
    ingredients = _get_ingredients(food_name)

    return {
        "food_name":    food_name,
        "confidence":   round(confidence, 4),
        "model_used":   model_used,
        "health_score": health_score,
        "nutrients":    nutrients,
        "allergens":    allergens,
        "ingredients":  ingredients,
    }


def _get_ingredients(food_name: str) -> list[str]:
    """Return known ingredients or an empty list."""
    name_lower = food_name.lower()
    for key in INGREDIENT_DB:
        if key in name_lower or name_lower in key:
            return INGREDIENT_DB[key]
    return []
