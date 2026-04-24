import streamlit as st
import anthropic
import json
import re
from collections import defaultdict
from datetime import datetime

st.set_page_config(
    page_title="🛒 Smart Shopping Assistant",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* General */
[data-testid="stAppViewContainer"] { background-color: #f4f7f4; }
[data-testid="stSidebar"] { background-color: #1a3c2a; color: white; }
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] .stTextInput input { color: #1a3c2a !important; }
[data-testid="stSidebar"] .stButton button { background: #4caf50; color: white !important; border: none; }

/* Cards */
.meal-card {
    background: white;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 8px 0;
    border-left: 5px solid #4caf50;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.category-header {
    background: linear-gradient(90deg, #e8f5e9, #f4f7f4);
    border-left: 4px solid #4caf50;
    padding: 8px 14px;
    border-radius: 6px;
    font-weight: 700;
    font-size: 1.05em;
    margin: 14px 0 6px 0;
    color: #1a3c2a;
}
.tip-box {
    background: #fffde7;
    border: 1px solid #f9a825;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 6px 0;
}
.suggestion-box {
    background: #e3f2fd;
    border: 1px solid #1976d2;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 6px 0;
}
.total-banner {
    background: linear-gradient(135deg, #2e7d32, #4caf50);
    color: white;
    border-radius: 12px;
    padding: 18px 24px;
    text-align: center;
    font-size: 1.4em;
    font-weight: 700;
    margin: 16px 0;
}
div[data-testid="stMetric"] {
    background: white;
    border-radius: 10px;
    padding: 12px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────
for key, default in {
    'pantry': [],
    'meals_data': None,
    'checked_items': set(),
    'generation_done': False,
    'budget_limit': 100,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Constants ─────────────────────────────────────────────────────────────────
CATEGORY_ICONS = {
    'Meat & Fish': '🥩',
    'Dairy & Eggs': '🥛',
    'Vegetables': '🥦',
    'Fruits': '🍎',
    'Bread & Bakery': '🍞',
    'Pantry & Dry Goods': '🫙',
    'Frozen': '🧊',
    'Beverages': '🥤',
    'Snacks & Sweets': '🍫',
    'Cleaning & Household': '🧹',
    'Other': '📦',
}

CATEGORY_ORDER = list(CATEGORY_ICONS.keys())


# ── Helper: call Claude ───────────────────────────────────────────────────────
def generate_shopping_plan(meals_text: str, num_people: int, num_days: int,
                            pantry: list, include_suggestions: bool, budget: int) -> dict:
    client = anthropic.Anthropic()
    pantry_note = (
        f"\nThe person already has these items at home — do NOT include them in the shopping list: "
        f"{', '.join(pantry)}"
        if pantry else ""
    )
    suggestion_note = (
        "Also suggest 2–3 complementary meal ideas that would reuse many of the same ingredients."
        if include_suggestions else "Do not add meal suggestions."
    )

    prompt = f"""I need to prepare the following meals for {num_people} people over {num_days} days:
{meals_text}
{pantry_note}

Tasks:
1. For each meal, list all ingredients with realistic quantities for {num_people} people.
2. Deduplicate ingredients shared across meals — if two meals both need onions, combine them into ONE entry in the shopping list with the total quantity needed.
3. Estimate prices in BGN (Bulgarian Lev) using typical Billa / Lidl / Kaufland Bulgaria prices (2024–2025).
4. Group each ingredient into one of these categories: Meat & Fish, Dairy & Eggs, Vegetables, Fruits, Bread & Bakery, Pantry & Dry Goods, Frozen, Beverages, Snacks & Sweets, Cleaning & Household, Other.
5. {suggestion_note}
6. Provide 3 money-saving tips for this specific shopping list.
7. Keep total cost within approximately {budget} BGN if possible.

Return ONLY a valid JSON object — no markdown, no explanation, no code fences. Structure:
{{
  "meals": [
    {{
      "name": "Meal Name",
      "servings": {num_people},
      "ingredients": ["500g ground beef", "2 onions", "3 garlic cloves"]
    }}
  ],
  "shopping_list": [
    {{
      "name": "ingredient name in English",
      "quantity": "500g",
      "category": "Meat & Fish",
      "price_bgn": 8.50,
      "used_in": ["Meal 1", "Meal 2"]
    }}
  ],
  "total_estimate": 47.80,
  "suggestions": ["Suggestion 1", "Suggestion 2"],
  "money_saving_tips": ["Tip 1", "Tip 2", "Tip 3"]
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r'^```json\s*', '', raw)
    raw = re.sub(r'^```\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    return json.loads(raw)


# ── Helper: generate PDF bytes ────────────────────────────────────────────────
def build_pdf(categories: dict, total: float, checked: set) -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_fill_color(46, 125, 50)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 14, "  Smart Shopping List", ln=True, fill=True)
    pdf.ln(1)

    # Meta
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%d %b %Y  %H:%M')}    |    Estimated total: {total:.2f} BGN", ln=True)
    pdf.ln(4)

    for category, items in sorted(categories.items(), key=lambda x: CATEGORY_ORDER.index(x[0]) if x[0] in CATEGORY_ORDER else 99):
        cat_total = sum(i.get('price_bgn', 0) for i in items)

        # Category header
        pdf.set_fill_color(232, 245, 233)
        pdf.set_text_color(27, 94, 32)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 9, f"  {CATEGORY_ICONS.get(category, '')}  {category}   ({cat_total:.2f} BGN)", ln=True, fill=True)
        pdf.ln(1)

        pdf.set_text_color(40, 40, 40)
        pdf.set_font("Helvetica", "", 11)
        for item in items:
            mark = "[x]" if item['name'] in checked else "[ ]"
            name = item['name']
            qty = item.get('quantity', '')
            price = item.get('price_bgn', 0)

            pdf.cell(12, 8, mark)
            pdf.cell(110, 8, f"{name}  —  {qty}")
            pdf.cell(0, 8, f"{price:.2f} BGN", ln=True, align="R")
        pdf.ln(3)

    # Total
    pdf.set_fill_color(46, 125, 50)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 12, f"  TOTAL ESTIMATE:   {total:.2f} BGN", ln=True, fill=True, align="R")

    return bytes(pdf.output())


# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Pantry Manager
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🏠 My Pantry")
    st.caption("Add items you already have — they'll be excluded from your shopping list.")
    st.divider()

    col_a, col_b = st.columns([3, 1])
    pantry_input = col_a.text_input("", placeholder="e.g. olive oil", label_visibility="collapsed")
    if col_b.button("Add", key="add_pantry"):
        val = pantry_input.strip()
        if val and val.lower() not in [p.lower() for p in st.session_state.pantry]:
            st.session_state.pantry.append(val)
            st.rerun()

    if st.session_state.pantry:
        st.markdown("**Items at home:**")
        for i, item in enumerate(st.session_state.pantry):
            c1, c2 = st.columns([4, 1])
            c1.write(f"✅ {item}")
            if c2.button("✕", key=f"del_{i}"):
                st.session_state.pantry.pop(i)
                st.rerun()
    else:
        st.info("Nothing added yet.")

    st.divider()
    if st.button("🔄 Start Over", use_container_width=True):
        for k in ['meals_data', 'checked_items', 'generation_done']:
            st.session_state[k] = None if k == 'meals_data' else (set() if k == 'checked_items' else False)
        st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# MAIN — Header
# ════════════════════════════════════════════════════════════════════════════
st.markdown("# 🛒 Smart Shopping Assistant")
st.caption("Tell me what you want to cook → get an optimised, deduplicated shopping list with prices and a printable PDF.")


# ════════════════════════════════════════════════════════════════════════════
# STEP 1 — Meal Input Form
# ════════════════════════════════════════════════════════════════════════════
if not st.session_state.generation_done:
    st.markdown("### 🍽️ Step 1 — What do you want to cook?")

    col_left, col_right = st.columns([3, 1], gap="large")

    with col_left:
        meals_input = st.text_area(
            "Enter meals (one per line or comma-separated):",
            placeholder="Pasta Bolognese\nChicken vegetable soup\nGreek salad\nScrambled eggs with vegetables\nPan-fried salmon",
            height=180,
        )

    with col_right:
        num_people = st.number_input("👥 People", min_value=1, max_value=12, value=2, step=1)
        num_days = st.number_input("📅 Days to plan", min_value=1, max_value=14, value=5, step=1)
        include_suggestions = st.checkbox("💡 Suggest extra meals", value=True,
                                           help="AI will suggest complementary meals that reuse your ingredients")
        budget = st.slider("💰 Budget limit (BGN)", 20, 300, 100, step=5)
        st.session_state.budget_limit = budget

    st.markdown("")
    if st.button("🚀 Generate My Shopping List", type="primary", use_container_width=True):
        if not meals_input.strip():
            st.warning("Please enter at least one meal first!")
        else:
            with st.spinner("🤖 Analysing meals, deduplicating ingredients, estimating prices…"):
                try:
                    data = generate_shopping_plan(
                        meals_input, num_people, num_days,
                        st.session_state.pantry, include_suggestions, budget
                    )
                    st.session_state.meals_data = data
                    st.session_state.generation_done = True
                    st.session_state.checked_items = set()
                    st.rerun()
                except json.JSONDecodeError as e:
                    st.error(f"Couldn't parse AI response as JSON. Try again. ({e})")
                except Exception as e:
                    st.error(f"Something went wrong: {e}")


# ════════════════════════════════════════════════════════════════════════════
# STEP 2 & 3 — Results
# ════════════════════════════════════════════════════════════════════════════
else:
    data = st.session_state.meals_data or {}
    shopping_list = data.get('shopping_list', [])
    total = data.get('total_estimate', sum(i.get('price_bgn', 0) for i in shopping_list))
    budget = st.session_state.budget_limit

    # Group by category
    categories: dict[str, list] = defaultdict(list)
    for item in shopping_list:
        categories[item.get('category', 'Other')].append(item)

    # ── Metrics row ──────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🍽️ Meals planned", len(data.get('meals', [])))
    c2.metric("🧾 Items to buy", len(shopping_list))
    delta_color = "normal" if total <= budget else "inverse"
    c3.metric("💰 Estimated total", f"{total:.2f} BGN",
              delta=f"{budget - total:+.2f} vs budget", delta_color=delta_color)
    c4.metric("✅ Checked off", f"{len(st.session_state.checked_items)}/{len(shopping_list)}")

    st.markdown("")

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab_list, tab_meals, tab_tips = st.tabs(["🛒 Shopping List", "🍽️ Meals Detail", "💡 Tips & Ideas"])

    # ── TAB 1: Shopping List ─────────────────────────────────────────────────
    with tab_list:
        if not shopping_list:
            st.warning("No items in shopping list. Try again with different meals.")
        else:
            for category in CATEGORY_ORDER:
                items = categories.get(category)
                if not items:
                    continue

                cat_total = sum(i.get('price_bgn', 0) for i in items)
                icon = CATEGORY_ICONS.get(category, '📦')

                st.markdown(f"<div class='category-header'>{icon} {category} &nbsp;&nbsp; <span style='color:#555;font-weight:400'>({len(items)} items · {cat_total:.2f} BGN)</span></div>", unsafe_allow_html=True)

                for item in items:
                    key = item['name']
                    checked = key in st.session_state.checked_items

                    col1, col2, col3, col4 = st.columns([0.4, 3.2, 1.4, 1.0])

                    new_val = col1.checkbox("", value=checked, key=f"chk_{key}", label_visibility="collapsed")
                    if new_val != checked:
                        if new_val:
                            st.session_state.checked_items.add(key)
                        else:
                            st.session_state.checked_items.discard(key)
                        st.rerun()

                    name_display = f"~~{key}~~" if checked else f"**{key}**"
                    col2.markdown(f"{name_display} &nbsp; `{item.get('quantity','')}`")
                    if item.get('used_in'):
                        col2.caption(f"↳ {', '.join(item['used_in'])}")

                    col3.markdown(f"🏷️ **{item.get('price_bgn', 0):.2f} BGN**")

            st.markdown("")

            # Remaining total
            remaining = sum(
                i.get('price_bgn', 0)
                for i in shopping_list
                if i['name'] not in st.session_state.checked_items
            )

            if len(st.session_state.checked_items) > 0:
                st.markdown(f"""
                <div class='total-banner'>
                    Total: {total:.2f} BGN &nbsp;|&nbsp; 
                    Still needed: {remaining:.2f} BGN &nbsp;|&nbsp; 
                    In cart: {total - remaining:.2f} BGN
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='total-banner'>Estimated Total: {total:.2f} BGN</div>", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 📄 Export")

            col_pdf, col_txt = st.columns(2)

            # PDF export
            with col_pdf:
                if st.button("🖨️ Generate PDF", use_container_width=True):
                    try:
                        pdf_bytes = build_pdf(dict(categories), total, st.session_state.checked_items)
                        st.download_button(
                            label="⬇️ Download PDF",
                            data=pdf_bytes,
                            file_name=f"shopping_list_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except ImportError:
                        st.error("fpdf2 not installed. Use the text download instead.")

            # Text export (always available)
            with col_txt:
                lines = [
                    "SMART SHOPPING LIST",
                    f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}",
                    f"Estimated total: {total:.2f} BGN",
                    "=" * 45, ""
                ]
                for category in CATEGORY_ORDER:
                    items = categories.get(category)
                    if not items:
                        continue
                    cat_total = sum(i.get('price_bgn', 0) for i in items)
                    lines.append(f"\n{CATEGORY_ICONS.get(category,'')} {category.upper()}  ({cat_total:.2f} BGN)")
                    lines.append("-" * 35)
                    for item in items:
                        mark = "[x]" if item['name'] in st.session_state.checked_items else "[ ]"
                        lines.append(f"  {mark}  {item['name']} — {item.get('quantity','')}  ...  {item.get('price_bgn',0):.2f} BGN")
                lines += ["", "=" * 45, f"TOTAL: {total:.2f} BGN"]

                st.download_button(
                    label="📝 Download as Text",
                    data="\n".join(lines),
                    file_name=f"shopping_list_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

    # ── TAB 2: Meals Detail ──────────────────────────────────────────────────
    with tab_meals:
        meals = data.get('meals', [])
        if not meals:
            st.info("No meal data available.")
        else:
            ncols = min(len(meals), 3)
            cols = st.columns(ncols)
            for i, meal in enumerate(meals):
                with cols[i % ncols]:
                    st.markdown(f"<div class='meal-card'><b>🍽️ {meal['name']}</b><br><small>{meal.get('servings', '')} servings</small></div>", unsafe_allow_html=True)
                    for ing in meal.get('ingredients', []):
                        st.write(f"• {ing}")
                    st.markdown("")

    # ── TAB 3: Tips & Suggestions ────────────────────────────────────────────
    with tab_tips:
        suggestions = data.get('suggestions', [])
        tips = data.get('money_saving_tips', [])

        if suggestions:
            st.markdown("### 💡 Meal Ideas That Reuse Your Ingredients")
            st.caption("These recipes would share many items you're already buying — minimal extra cost!")
            for s in suggestions:
                st.markdown(f"<div class='suggestion-box'>🍳 {s}</div>", unsafe_allow_html=True)
            st.markdown("")

        if tips:
            st.markdown("### 💰 Money-Saving Tips")
            for tip in tips:
                st.markdown(f"<div class='tip-box'>✅ {tip}</div>", unsafe_allow_html=True)

        if not suggestions and not tips:
            st.info("No tips generated. Re-run with a new meal plan to get suggestions.")
