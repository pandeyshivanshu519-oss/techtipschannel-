import os
import requests
import time

class ThumbnailGenerator:
    def __init__(self):
        self.output_dir = os.path.join(os.getcwd(), "assets", "thumbnails")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_thumbnail(self, title, script_text, short_number):
        """
        Pollinations.ai se free thumbnail generate karta hai
        """
        print(f"🖼️ Generating Thumbnail for Short #{short_number}...")

        # Clean title for prompt
        clean_title = title.replace("😱", "").replace("🔥", "").strip()[:100]

        prompt = f"YouTube Shorts thumbnail, {clean_title}, dramatic cinematic style, bold text, shocked expression, high contrast, viral thumbnail, dark background, mysterious vibe, professional YouTube style"

        try:
            url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed={short_number}&nologo=true"

            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                thumbnail_path = os.path.join(self.output_dir, f"thumbnail_{short_number}.png")
                
                with open(thumbnail_path, "wb") as f:
                    f.write(response.content)

                print(f"✅ Thumbnail saved: thumbnail_{short_number}.png")
                return thumbnail_path
            else:
                print(f"❌ Thumbnail API error: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Thumbnail generation failed: {e}")
            return None


# For testing
if __name__ == "__main__":
    gen = ThumbnailGenerator()
    gen.generate_thumbnail(
        title="क्या आप जानते हैं? Ancient Secret",
        script_text="प्राचीन मिस्र में लोग ऐसे जादू करते थे...",
        short_number=1
    )
