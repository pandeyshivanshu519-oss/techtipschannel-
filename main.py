import asyncio
import time
import os
import shutil

from modules.brain    import ContentBrain
from modules.audio    import AudioEngine
from modules.composer import Composer
from modules.thumbnail import ThumbnailGenerator


def clean_cache():
    print("🧹 Cleaning up temporary files...")

    folders_to_clean = [
        os.path.join(os.getcwd(), "assets", "audio_clips"),
        os.path.join(os.getcwd(), "assets", "video_clips"),
        os.path.join(os.getcwd(), "assets", "temp"),
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
                print(f"   Failed to delete {file_path}: {e}")

    print("✅ Workspace cleaned!")


async def create_one_short(short_number):
    print(f"🚀 Starting New Short Generation #{short_number}...")

    # ══════════════════════════════════════════
    # STEP 1 — BRAIN: Script generate karo
    # ══════════════════════════════════════════
    brain = ContentBrain()

    try:
        script_data = brain.generate_script()
        if not script_data:
            print("❌ Script generation failed")
            return False
    except Exception as e:
        print(f"❌ Brain Error: {e}")
        return False

    # ══════════════════════════════════════════
    # STEP 2 — AUDIO: TTS generate karo
    # ══════════════════════════════════════════
    audio_engine = AudioEngine()

    try:
        script_data = await audio_engine.process_script(script_data)
    except Exception as e:
        print(f"❌ Audio Error: {e}")
        return False

    # ══════════════════════════════════════════
    # STEP 3 — COMPOSER: Visuals + Video banao
    # (AssetManager ki zaroorat nahi —
    #  Composer khud Pollinations + Pexels handle karta hai)
    # ══════════════════════════════════════════
    composer = Composer()

    final_scene_paths = composer.render_all_scenes(script_data)

    if not final_scene_paths:
        print("❌ Failed to generate scenes")
        return False

    # ══════════════════════════════════════════
    # STEP 4 — FINAL VIDEO: Scenes stitch karo
    # ══════════════════════════════════════════
    final_video = composer.concatenate_with_transitions(final_scene_paths)

    if not final_video:
        print("❌ Final video stitching failed")
        return False

    clean_cache()
    print("✅ Short successfully created!")

    # ══════════════════════════════════════════
    # STEP 5 — THUMBNAIL
    # ══════════════════════════════════════════
    print("🖼️ Generating Thumbnail...")

    try:
        thumbnail_gen  = ThumbnailGenerator()
        thumbnail_path = thumbnail_gen.generate_thumbnail(
            title=script_data[0].get("title", "Tech Secrets"),
            script_text=script_data[0].get("text", ""),
            short_number=short_number,
        )
    except Exception as e:
        print(f"⚠️ Thumbnail Error: {e}")
        thumbnail_path = None

    # ══════════════════════════════════════════
    # STEP 6 — YOUTUBE UPLOAD
    # ══════════════════════════════════════════
    print("📤 Uploading to YouTube...")

    try:
        from modules.uploader import YouTubeUploader

        uploader    = YouTubeUploader()
        scene       = script_data[0] if isinstance(script_data, list) else script_data
        script_text = scene.get("text", "Tech Secrets")
        category    = scene.get("category", "Tech")
        title       = f"🔥 {scene.get('title', 'Viral Tech Trick')}"

        description = f"""
🔥 Yeh Tech Hack Aaj Hi Try Karo!

{script_text[:500]}...

⚡ Topics Covered:
Android Tricks | AI Tools | ChatGPT Hacks
Instagram Tricks | WhatsApp Tips | Cybersecurity
Laptop Tips | Gaming Tricks | Future Technology

📌 Category: {category}

👍 Like karo agar useful laga
🔔 Subscribe karo daily tech secrets ke liye

DISCLAIMER: This video is for educational purposes only.

#TechHacks #AndroidTips #AITools #ChatGPT #TechShorts
#HiddenFeatures #MobileTricks #CyberSecurity #TechHindi
#AI #TechNews #InstagramTips #WhatsAppTricks #LaptopTips
#Smartphone #YouTubeShorts #ViralTech #TechTips
"""

        tags = [
            "tech hacks", "android tricks", "chatgpt tricks",
            "ai tools", "mobile tips", "cybersecurity",
            "tech shorts", "viral tech", "instagram tricks",
            "gaming setup", "laptop tips", "hidden features",
            "future technology", "whatsapp tricks", "youtube shorts",
        ]

        video_id = uploader.upload(
            video_path=final_video,
            title=title[:100],
            description=description,
            thumbnail_path=thumbnail_path,
            tags=tags,
            privacy="public",
        )

        if video_id:
            print("✅ VIDEO UPLOADED SUCCESSFULLY!")
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
    print("Will keep generating fresh shorts until GitHub stops the job...\n")

    short_count = 0
    start_time  = time.time()

    while True:
        short_count += 1
        print(f"\n🔄 === Generating Short #{short_count} ===\n")

        success = await create_one_short(short_number=short_count)

        if success:
            print(f"✅ Short #{short_count} completed & uploaded!")
        else:
            print(f"⚠️ Short #{short_count} had some issues. Continuing...")

        print("⏳ Waiting 15 minutes before next short...\n")
        await asyncio.sleep(900)

        if time.time() - start_time > 19800:
            print("⏹️ Maximum runtime reached. Stopping now...")
            break


if __name__ == "__main__":
    asyncio.run(main())
