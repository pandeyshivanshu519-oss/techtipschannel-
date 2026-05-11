import asyncio
import time
from modules.brain import ContentBrain
from modules.asset_manager import AssetManager
from modules.audio import AudioEngine
from modules.composer import Composer
from modules.thumbnail import ThumbnailGenerator
import os
import shutil


def clean_cache():

    print("🧹 Cleaning workspace...")

    folders_to_clean = [
        os.path.join(os.getcwd(), "assets", "audio_clips"),
        os.path.join(os.getcwd(), "assets", "video_clips"),
        os.path.join(os.getcwd(), "assets", "temp")
    ]

    for folder in folders_to_clean:

        if not os.path.exists(folder):
            continue

        if "assets" not in folder:
            continue

        for filename in os.listdir(folder):

            file_path = os.path.join(folder, filename)

            try:

                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)

                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)

            except Exception as e:
                print(f"❌ Failed deleting {file_path}: {e}")

    print("✅ Cache cleaned")


async def create_one_short(short_number):

    print(f"\n🚀 STARTING TECH SHORT #{short_number}\n")

    # ==========================================
    # BRAIN
    # ==========================================

    brain = ContentBrain()

    try:

        script_data = brain.generate_script()

        if not script_data:
            print("❌ Script generation failed")
            return False

    except Exception as e:

        print(f"❌ Brain Error: {e}")
        return False

    # ==========================================
    # AUDIO
    # ==========================================

    audio_engine = AudioEngine()

    try:

        script_data = await audio_engine.process_script(script_data)

    except Exception as e:

        print(f"❌ Audio Error: {e}")
        return False

    # ==========================================
    # ASSETS
    # ==========================================

    asset_manager = AssetManager()

    assets_map = asset_manager.get_videos(script_data)

    # ==========================================
    # COMPOSER
    # ==========================================

    composer = Composer()

    final_scene_paths = composer.render_all_scenes(
        script_data,
        assets_map
    )

    if not final_scene_paths:
        print("❌ Scene generation failed")
        return False

    composer.concatenate_with_transitions(final_scene_paths)

    print("✅ Final video rendered")

    # ==========================================
    # CLEAN CACHE
    # ==========================================

    clean_cache()

    # ==========================================
    # THUMBNAIL
    # ==========================================

    print("🖼️ Generating Thumbnail...")

    thumbnail_gen = ThumbnailGenerator()

    scene = script_data[0]

    thumbnail_path = thumbnail_gen.generate_thumbnail(
        title=scene.get("title", "Tech Secret"),
        script_text=scene.get("text", ""),
        short_number=short_number
    )

    # ==========================================
    # YOUTUBE SEO
    # ==========================================

    print("📤 Uploading to YouTube...")

    try:

        from modules.uploader import YouTubeUploader

        uploader = YouTubeUploader()

        script_text = scene.get("text", "")
        title = scene.get("title", "Viral Tech Trick")

        seo_title = f"{title} 😱 | Tech Secrets"

        category = scene.get("category", "Tech")

        description = f"""
🔥 Daily Viral Tech Shorts

{script_text[:700]}

⚡ Topics Covered:
Android Tricks
AI Tools
ChatGPT Hacks
Instagram Tricks
WhatsApp Tips
Cybersecurity
Laptop Tips
Gaming Tricks
Future Technology

📌 Category:
{category}

👍 Like karo agar useful laga
🔔 Subscribe karo daily tech secrets ke liye

DISCLAIMER:
This video is made for educational and informational purposes only.

#TechHacks
#AndroidTips
#AITools
#ChatGPT
#TechShorts
#HiddenFeatures
#MobileTricks
#CyberSecurity
#TechHindi
#AI
#TechNews
#InstagramTips
#WhatsAppTricks
#LaptopTips
#Smartphone
"""

        tags = [
            "tech hacks",
            "android tricks",
            "chatgpt tricks",
            "ai tools",
            "mobile tips",
            "cybersecurity",
            "tech shorts",
            "viral tech",
            "instagram tricks",
            "gaming setup",
            "laptop tips",
            "hidden features",
            "future technology",
            "whatsapp tricks",
            "youtube shorts"
        ]

        video_path = "assets/final/final_short.mp4"

        video_id = uploader.upload(
            video_path=video_path,
            title=seo_title[:100],
            description=description,
            thumbnail_path=thumbnail_path,
            tags=tags,
            privacy="public"
        )

        if video_id:

            print("\n✅ VIDEO UPLOADED SUCCESSFULLY!")
            print(f"🔗 https://youtu.be/{video_id}")

            return True

        else:

            print("❌ Upload failed")
            return False

    except Exception as e:

        print(f"❌ Upload Error: {e}")

        return False


async def main():

    print("🚀 VIRAL TECH CHANNEL MODE ACTIVATED...\n")

    short_count = 0

    start_time = time.time()

    # ==========================================
    # CONTINUOUS MODE
    # ==========================================

    while True:

        short_count += 1

        success = await create_one_short(
            short_number=short_count
        )

        if success:
            print(f"✅ TECH SHORT #{short_count} COMPLETED")

        else:
            print(f"⚠️ TECH SHORT #{short_count} FAILED")

        # ==========================================
        # WAIT TIME
        # ==========================================

        print("\n⏳ Waiting 30 minutes before next upload...\n")

        await asyncio.sleep(1800)

        # ==========================================
        # GITHUB LIMIT SAFETY
        # ==========================================

        if time.time() - start_time > 19800:

            print("⏹️ Max runtime reached")

            break


if __name__ == "__main__":

    asyncio.run(main())