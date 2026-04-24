# 🛒 Smart Shopping Assistant

A Streamlit application powered by Claude AI that helps you plan meals, optimise your grocery shopping, and avoid unnecessary spending.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🍽️ **Meal Planning** | Enter any meals in free text — the AI extracts every ingredient automatically |
| 🔁 **Ingredient Deduplication** | Ingredients shared across meals are merged into one entry with the total quantity needed |
| 🏠 **Pantry Tracker** | Add items you already have at home — they are filtered out of your shopping list |
| 💰 **Budget Estimator** | Price estimates in BGN based on typical Billa / Lidl / Kaufland Bulgaria prices |
| 💡 **Recipe Suggestions** | AI suggests complementary meals that reuse the same ingredients to minimise waste |
| 🧾 **Money-Saving Tips** | Personalised tips generated for your specific shopping list |
| ✅ **Interactive Checklist** | Check off items as you shop — remaining cost updates in real time |
| 📄 **PDF & Text Export** | Download a printable shopping list (PDF with category grouping, or plain text) |

---

## 📁 Project Structure

```
smart_shopping/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
└── .streamlit/
    └── secrets.toml.example    # Template for API key configuration
```

---

## 🚀 Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/your-username/smart-shopping-assistant.git
cd smart-shopping-assistant
```

### 2. Create a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure your API key

Create the secrets file:
```bash
mkdir .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` and add your Anthropic API key:
```toml
ANTHROPIC_API_KEY = "sk-ant-your-key-here"
```

> You can get an API key at [console.anthropic.com](https://console.anthropic.com)

### 5. Run the app
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## ☁️ Deploy on Streamlit Community Cloud

1. Push the project to a **public GitHub repository** (do not include `.streamlit/secrets.toml`)
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **New app**
3. Select your repository and set the main file to `app.py`
4. In **Settings → Secrets**, paste:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-your-key-here"
   ```
5. Click **Deploy** — the app will be live in under a minute

> ⚠️ Never commit your `secrets.toml` to GitHub. Add it to `.gitignore`:
> ```
> .streamlit/secrets.toml
> ```

---

## 🧭 How to Use

### Step 1 — Enter your meals
Type the meals you want to prepare in the text area, one per line or comma-separated:
```
Pasta Bolognese
Chicken vegetable soup
Greek salad
Scrambled eggs with peppers
Pan-fried salmon with rice
```

Set the number of people, the number of days you are planning for, and your budget in BGN.

### Step 2 — Manage your pantry *(optional)*
Use the left sidebar to add ingredients you already have at home (e.g. olive oil, salt, pasta). These will be automatically excluded from the shopping list.

### Step 3 — Generate and review
Click **Generate My Shopping List**. The AI will:
- Extract all ingredients per meal
- Merge duplicates across meals
- Estimate prices in BGN
- Group items by supermarket category
- Suggest extra meals and money-saving tips

### Step 4 — Shop and export
Check off items as you add them to your cart. When done, download your list as a **PDF** (for printing) or a **text file**.

---

## 🛠️ Tech Stack

- **[Streamlit](https://streamlit.io)** — UI framework
- **[Anthropic Claude](https://anthropic.com)** — AI meal parsing, ingredient extraction, price estimation
- **[fpdf2](https://py-fpdf2.readthedocs.io)** — PDF generation

---

## 📦 requirements.txt

```
streamlit>=1.32.0
anthropic>=0.25.0
fpdf2>=2.7.9
```

---

## 🔒 Privacy

No data is stored. All processing happens within your Streamlit session. Meal inputs are sent to the Anthropic API solely to generate the ingredient list and are not retained.

---

## 🗺️ Roadmap Ideas

- [ ] Weekly meal calendar view
- [ ] Bulgarian language support
- [ ] Save and reload favourite meal plans
- [ ] Supermarket-specific price profiles (Billa vs Lidl vs Kaufland)
- [ ] Nutritional summary per meal plan
- [ ] Share shopping list via link or QR code

---

## 📄 License

MIT — free to use, modify, and distribute.
