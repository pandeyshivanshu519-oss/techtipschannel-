import os
import json
import time
import random
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class ContentBrain:

    def __init__(self):
        self.history_file = "topics_history.json"
        self.history = self.load_history()

        self.tech_categories = [
            "Android Hidden Features",
            "AI Tools",
            "ChatGPT Tricks",
            "Cybersecurity",
            "Instagram Tricks",
            "WhatsApp Tricks",
            "Gaming Optimization",
            "Laptop Tips",
            "Coding Basics",
            "Tech Facts",
            "Productivity Apps",
            "Future AI",
            "Phone Settings",
            "Internet Tricks",
            "WiFi Tips",
            "Computer Hacks",
            "Gadgets",
            "Smartphone Features",
            "Social Media Growth",
            "YouTube Tips"
        ]

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"used_topics": [], "used_categories": []}

    def save_history(self, title, category):
        try:
            if "used_topics" not in self.history:
                self.history["used_topics"] = []
            if "used_categories" not in self.history:
                self.history["used_categories"] = []

            if title and title not in self.history["used_topics"]:
                self.history["used_topics"].append(title)

            if category:
                self.history["used_categories"].append(category)

            self.history["used_topics"]      = self.history["used_topics"][-300:]
            self.history["used_categories"]  = self.history["used_categories"][-50:]

            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=4, ensure_ascii=False)

        except Exception as e:
            print(f"❌ Failed saving history: {e}")

    def get_next_category(self):
        if "used_categories" not in self.history:
            self.history["used_categories"] = []

        recent    = self.history["used_categories"][-5:]
        available = [c for c in self.tech_categories if c not in recent]

        if not available:
            available = self.tech_categories

        return random.choice(available)

    def generate_script(self):

        category = self.get_next_category()

        print(f"🧠 Selected Category: {category}")
        print("🚀 Generating Problem-Solving Tech Short...")

        used_topics = self.history.get("used_topics", [])[-30:]
        used_str    = ", ".join(used_topics) if used_topics else "none"

        prompt = f"""
Tu ek elite viral Hindi tech YouTube Shorts creator hai.

CATEGORY: {category}

TASK:
Ek ultra-viral, problem-solving tech short script generate kar.

════════════════════════════════════════
SCRIPT FORMAT — STRICTLY FOLLOW THIS:
════════════════════════════════════════

STRUCTURE (is exact order mein):

1. PROBLEM (2-3 lines)
   - Real problem jo viewer face karta hai
   - Relatable, specific, frustrating
   - Example: "Kya tera phone slow ho gaya hai? Apps open hone mein time lagta hai? Battery bhi jaldi khatam hoti hai?"

2. REASON (1-2 lines)
   - Short explanation kyun hota hai ye
   - Example: "Kyunki background mein 20+ apps chal rahi hain silently."

3. SOLUTION — STEP BY STEP (3-5 steps)
   - Numbered steps, action-oriented
   - Exact settings/menu names batao
   - Example:
     "Step 1: Settings kholo.
      Step 2: Battery & Performance jaao.
      Step 3: Background apps restrict karo.
      Step 4: Done. Phone restart karo."

4. RESULT (1-2 lines)
   - Kya fayda milega exactly
   - Measurable result batao
   - Example: "Iske baad phone 2x fast chalega aur battery 30% zyada chalegi."

5. CTA (1 line)
   - Strong call to action
   - Example: "Abhi try karo aur comment mein batao kitna fast hua!"

════════════════════════════════════════
TONE & STYLE RULES:
════════════════════════════════════════
- Hinglish — simple Hindi + English mix
- Direct, punchy, no fluff
- NO greetings, NO "Hello doston", NO "Aaj main bataunga"
- Start DIRECTLY with the problem
- Every line must earn its place — no filler
- Conversational but confident
- Sound like a friend giving advice, not a teacher
- Max 55 seconds when read aloud

════════════════════════════════════════
VISUAL TERMS (Pexels search):
════════════════════════════════════════
- visual_1: Scene jo PROBLEM show kare
- visual_2: Scene jo SOLUTION/RESULT show kare
- English only, 3-5 words, realistic searchable terms
- No abstract words

GOOD EXAMPLES:
"person frustrated slow phone"
"smartphone settings menu screen"
"person typing fast laptop"
"wifi router close up"
"android phone battery settings"

════════════════════════════════════════
AVOID REPEATING THESE TOPICS:
{used_str}
════════════════════════════════════════

RETURN ONLY VALID JSON — NO MARKDOWN, NO EXPLANATION:

[
  {{
    "id": 1,
    "category": "{category}",
    "title": "SEO title under 60 chars — problem + solution format",
    "text": "Full problem-solving script in Hinglish, 45-55 seconds",
    "hook_text": "One-line hook that creates instant curiosity",
    "visual_1": "pexels search term for problem scene",
    "visual_2": "pexels search term for solution scene"
  }}
]
"""

        models = [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-1.5-flash"
        ]

        for model_name in models:
            for attempt in range(3):
                try:
                    print(f"🔄 {model_name} Attempt {attempt+1}/3")

                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config={
                            "response_mime_type": "application/json",
                            "temperature": 1.0
                        }
                    )

                    clean = (
                        response.text
                        .strip()
                        .replace("```json", "")
                        .replace("```", "")
                        .strip()
                    )

                    result = json.loads(clean)

                    if isinstance(result, dict):
                        result = [result]

                    title         = result[0].get("title", "")
                    category_name = result[0].get("category", category)

                    self.save_history(title, category_name)

                    print(f"✅ SUCCESS with {model_name}")
                    print(f"📌 Category : {category_name}")
                    print(f"🎬 Title    : {title}")
                    print(f"📽️ visual_1 : {result[0].get('visual_1')}")
                    print(f"📽️ visual_2 : {result[0].get('visual_2')}")

                    return result

                except Exception as e:
                    err = str(e)
                    print(f"❌ Failed {model_name}: {err[:200]}")

                    if any(x in err for x in ["503", "429", "overloaded", "high demand"]):
                        print("⏳ Waiting before retry...")
                        time.sleep(12)
                        continue
                    break

        print("❌ All models failed.")
        return None


if __name__ == "__main__":
    brain  = ContentBrain()
    output = brain.generate_script()

    if output:
        with open("latest_script.json", "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4, ensure_ascii=False)
        print("✅ latest_script.json saved")
