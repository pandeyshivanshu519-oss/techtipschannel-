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

        return {
            "used_topics": [],
            "used_categories": []
        }

    def save_history(self, title, category):
        try:
            if title and title not in self.history["used_topics"]:
                self.history["used_topics"].append(title)

            if category:
                self.history["used_categories"].append(category)

            self.history["used_topics"] = self.history["used_topics"][-300:]
            self.history["used_categories"] = self.history["used_categories"][-50:]

            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=4, ensure_ascii=False)

        except Exception as e:
            print(f"❌ Failed saving history: {e}")

    def get_next_category(self):
        recent = self.history.get("used_categories", [])[-5:]

        available = [c for c in self.tech_categories if c not in recent]

        if not available:
            available = self.tech_categories

        return random.choice(available)

    def generate_script(self):

        category = self.get_next_category()

        print(f"🧠 Selected Category: {category}")
        print("🚀 Generating Viral Tech Short...")

        used_topics = self.history.get("used_topics", [])[-30:]
        used_str = ", ".join(used_topics) if used_topics else "none"

        prompt = f"""
You are an elite viral Hindi tech YouTube Shorts creator.

Generate ONE highly engaging, ultra-viral, fast-paced tech short script for YouTube Shorts.

CATEGORY:
{category}

STYLE:
- Hinglish language
- High retention
- Fast pacing
- Human conversational tone
- Curiosity driven
- Useful and practical
- Modern Gen-Z style

TOPICS CAN INCLUDE:
- Android hidden features
- AI tools
- ChatGPT tricks
- cybersecurity
- Instagram tricks
- WhatsApp tricks
- coding
- gaming
- gadgets
- laptop tips
- WiFi tricks
- mobile settings
- apps
- social media hacks
- future technology
- productivity tools

STRICT RULES:
- Script should be 45-60 seconds
- First line MUST create curiosity
- Every sentence should feel punchy
- No boring intros
- No greetings
- Avoid robotic tone
- Add practical value
- Use very simple Hindi + English mix
- Make it sound like a viral reel creator

HOOK EXAMPLES:
- "99% log ye setting nahi jaante..."
- "Ye AI tool tumhara kaam aadha kar dega..."
- "Agar tum Android use karte ho toh ye dekho..."
- "Phone slow ho raha hai? Ye karo..."
- "Hackers se bachna hai toh ye setting ON karo..."

IMPORTANT:
Do NOT repeat these topics:
{used_str}

VISUAL KEYWORD RULES:
- visual_1 and visual_2 are Pexels search terms
- Must be REAL objects/scenes
- 3-5 words only
- English only
- No abstract words

GOOD EXAMPLES:
"person using smartphone"
"rgb gaming keyboard"
"laptop coding screen"
"mobile app scrolling"
"person typing laptop"
"smartphone home screen"
"wifi router blinking"
"artificial intelligence screen"

RETURN ONLY VALID JSON:

[
  {{
    "id": 1,
    "category": "{category}",
    "title": "Ultra catchy SEO title under 60 characters",
    "text": "Full viral Hinglish script",
    "hook_text": "Very short viral hook text",
    "visual_1": "realistic pexels search term",
    "visual_2": "another realistic pexels search term"
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
                            "temperature": 1.1
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

                    title = result[0].get("title", "")
                    category_name = result[0].get("category", category)

                    self.save_history(title, category_name)

                    print(f"✅ SUCCESS with {model_name}")
                    print(f"📌 Category: {category_name}")
                    print(f"🎬 Title: {title}")
                    print(f"📽️ visual_1: {result[0].get('visual_1')}")
                    print(f"📽️ visual_2: {result[0].get('visual_2')}")

                    return result

                except Exception as e:

                    err = str(e)

                    print(f"❌ Failed {model_name}: {err[:200]}")

                    if (
                        "503" in err
                        or "429" in err
                        or "overloaded" in err
                        or "high demand" in err
                    ):
                        print("⏳ Waiting before retry...")
                        time.sleep(12)
                        continue

                    break

        print("❌ All models failed.")
        return None


if __name__ == "__main__":

    brain = ContentBrain()

    output = brain.generate_script()

    if output:
        with open("latest_script.json", "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4, ensure_ascii=False)

        print("✅ latest_script.json saved")