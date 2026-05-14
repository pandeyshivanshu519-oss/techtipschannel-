import os
import shutil
import random
import subprocess
import requests
import ffmpeg
from PIL import Image, ImageDraw, ImageFont


class Composer:

    def __init__(self):
        self.temp_dir        = os.path.join(os.getcwd(), "assets", "temp")
        self.final_dir       = os.path.join(os.getcwd(), "assets", "final")
        self.loop_videos_dir = os.path.join(os.getcwd(), "assets", "loop_videos")
        self.bg_music_path   = "bgmusic.mp3"
        self.font_path       = self._resolve_font()

        os.makedirs(self.temp_dir,        exist_ok=True)
        os.makedirs(self.final_dir,       exist_ok=True)
        os.makedirs(self.loop_videos_dir, exist_ok=True)

        if self.font_path:
            print(f"✅ Font: {self.font_path}")
        else:
            print("⚠️  No font — PIL default")

    # ─────────────────────────────────────────────────────────────────
    # FONT
    # ─────────────────────────────────────────────────────────────────

    def _resolve_font(self):
        candidates = [
            os.path.join(os.getcwd(), "assets", "fonts", "NotoSans-Bold.ttf"),
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
            "/usr/share/fonts/noto/NotoSansDevanagari-Bold.ttf",
        ]
        for p in candidates:
            if os.path.exists(p) and os.path.getsize(p) > 10_000:
                return p
        return None

    def _pil_font(self, size):
        if self.font_path:
            try:
                return ImageFont.truetype(self.font_path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    # ─────────────────────────────────────────────────────────────────
    # UTILITIES
    # ─────────────────────────────────────────────────────────────────

    def get_duration(self, filepath):
        try:
            return float(ffmpeg.probe(filepath)["format"]["duration"])
        except Exception:
            return 0.0

    def _run_cmd(self, cmd, label=""):
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"   ⚠️ {label}:\n{r.stderr[-300:]}")
            return False
        return True

    # ─────────────────────────────────────────────────────────────────
    # POLLINATIONS — AI Image Generation
    # ─────────────────────────────────────────────────────────────────

    def _fetch_pollinations_image(self, prompt, scene_id, img_idx):
        """
        Pollinations FLUX se AI image generate karo.
        Tech + cinematic style, portrait format (1080x1920).
        """
        full_prompt = (
            f"{prompt}, ultra realistic, cinematic lighting, "
            f"tech aesthetic, 4K quality, vertical composition"
        )
        encoded  = requests.utils.quote(full_prompt)
        url      = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?width=1080&height=1920&nologo=true&model=flux"
        )
        out_path = os.path.join(
            self.temp_dir, f"pollinations_{scene_id}_{img_idx}.jpg"
        )

        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                with open(out_path, "wb") as f:
                    f.write(r.content)
                print(f"   🎨 Pollinations image {img_idx+1} generated")
                return out_path
        except Exception as e:
            print(f"   ⚠️ Pollinations failed: {e}")

        return None

    # ─────────────────────────────────────────────────────────────────
    # PEXELS — Stock Video Download
    # ─────────────────────────────────────────────────────────────────

    def _fetch_pexels_clip(self, query, scene_id, clip_idx):
        """
        Pexels se portrait stock video download karo.
        """
        api_key = os.getenv("PEXELS_API_KEY", "")
        if not api_key:
            print("   ⚠️ PEXELS_API_KEY not set")
            return None

        headers = {"Authorization": api_key}
        params  = {
            "query":       query,
            "per_page":    5,
            "orientation": "portrait",
            "size":        "medium"
        }

        try:
            r    = requests.get(
                "https://api.pexels.com/videos/search",
                headers=headers, params=params, timeout=10
            )
            data = r.json()
            videos = data.get("videos", [])

            if not videos:
                simple = query.split()[-1]
                if simple != query:
                    print(f"   ⚠️ No results '{query}', retrying '{simple}'")
                    return self._fetch_pexels_clip(simple, scene_id, clip_idx)
                return None

            valid  = [v for v in videos if v.get("duration", 0) >= 4] or videos
            chosen = random.choice(valid)
            files  = sorted(
                chosen["video_files"],
                key=lambda x: x["width"] * x["height"], reverse=True
            )
            dl_url = files[0]["link"]

            out_path = os.path.join(
                self.temp_dir, f"pexels_{scene_id}_{clip_idx}.mp4"
            )
            with requests.get(dl_url, stream=True, timeout=20) as dl:
                dl.raise_for_status()
                with open(out_path, "wb") as f:
                    for chunk in dl.iter_content(8192):
                        f.write(chunk)

            print(f"   🎬 Pexels clip downloaded: '{query}'")
            return out_path

        except Exception as e:
            print(f"   ⚠️ Pexels error: {e}")
            return None

    # ─────────────────────────────────────────────────────────────────
    # LOOP VIDEO — Brainrot bottom half
    # ─────────────────────────────────────────────────────────────────

    def _fetch_loop_video(self, scene_index):
        """
        assets/loop_videos/ folder se rotation-based video pick karo.
        Koi bhi .mp4/.mov/.avi/.mkv automatically pick hogi.
        Hardcoded name ki zaroorat nahi.
        """
        exts = (".mp4", ".mov", ".avi", ".mkv")
        try:
            all_videos = sorted([
                os.path.join(self.loop_videos_dir, f)
                for f in os.listdir(self.loop_videos_dir)
                if f.lower().endswith(exts)
            ])
        except Exception:
            all_videos = []

        if not all_videos:
            print("   ⚠️  No loop videos in assets/loop_videos/")
            print("   💡 Add: subway.mp4, minecraft.mp4, satisfying.mp4 etc.")
            return None

        chosen = all_videos[scene_index % len(all_videos)]
        name   = os.path.basename(chosen)
        idx    = scene_index % len(all_videos) + 1
        print(f"   🎮 Loop video [{idx}/{len(all_videos)}]: {name}")
        return chosen

    # ─────────────────────────────────────────────────────────────────
    # SPLIT SCREEN — Top: content, Bottom: loop video
    # ─────────────────────────────────────────────────────────────────

    def _apply_split_screen(self, main_video, loop_video, scene_id):
        """
        1080x1920 brainrot split screen:
        - Top 960px   : main content
        - Bottom 960px: loop video (auto-looped)
        """
        out_path = os.path.join(self.temp_dir, f"split_{scene_id}.mp4")
        main_dur = self.get_duration(main_video)

        print(f"   🎬 Applying brainrot split screen...")

        cmd = [
            "ffmpeg", "-y",
            "-i", main_video,
            "-stream_loop", "-1",
            "-i", loop_video,
            "-filter_complex",
            (
                "[0:v]scale=1080:960:force_original_aspect_ratio=increase,"
                "crop=1080:960,setsar=1[top];"
                "[1:v]scale=1080:960:force_original_aspect_ratio=increase,"
                "crop=1080:960,setsar=1[bottom];"
                "[top][bottom]vstack=inputs=2[outv];"
                "[0:a]volume=1.0[outa]"
            ),
            "-map", "[outv]",
            "-map", "[outa]",
            "-t",        str(main_dur),
            "-c:v",      "libx264",
            "-preset",   "fast",
            "-crf",      "23",
            "-c:a",      "aac",
            "-b:a",      "192k",
            "-r",        "30",
            "-pix_fmt",  "yuv420p",
            "-movflags", "faststart",
            out_path
        ]

        ok = self._run_cmd(cmd, "Split screen")
        if ok and os.path.exists(out_path):
            print(f"   ✅ Split screen done")
            return out_path

        print(f"   ⚠️ Split screen failed — using original")
        return main_video

    # ─────────────────────────────────────────────────────────────────
    # SUBTITLES
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _srt_ts(seconds):
        seconds  = max(0.0, seconds)
        total_ms = int(round(seconds * 1000))
        ms = total_ms % 1000
        s  = (total_ms // 1000) % 60
        m  = (total_ms // 60000) % 60
        h  = total_ms // 3600000
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    def _make_srt(self, text, duration, scene_id):
        words = text.split()
        if not words:
            return None

        srt_path       = os.path.join(self.temp_dir, f"sub_{scene_id}.srt")
        words_per_line = 5
        chunks         = []

        for i in range(0, len(words), words_per_line):
            chunks.append(" ".join(words[i:i + words_per_line]))

        time_per_chunk = duration / max(len(chunks), 1)

        with open(srt_path, "w", encoding="utf-8") as f:
            for i, chunk in enumerate(chunks):
                start = i * time_per_chunk
                end   = min((i + 1) * time_per_chunk - 0.05, duration - 0.1)
                f.write(
                    f"{i+1}\n"
                    f"{self._srt_ts(start)} --> {self._srt_ts(end)}\n"
                    f"{chunk}\n\n"
                )

        return srt_path

    def _burn_subtitles(self, src, srt_path, dst):
        if not self.font_path:
            shutil.copy2(src, dst)
            return False

        safe_srt  = srt_path.replace("\\", "/")
        safe_font = self.font_path.replace("\\", "/")

        if len(safe_srt) >= 2 and safe_srt[1] == ":":
            safe_srt = safe_srt[0] + "\\:" + safe_srt[2:]

        style = (
            f"fontfile={safe_font},"
            "FontSize=16,"
            "PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,"
            "BackColour=&H90000000,"
            "Bold=1,"
            "Outline=2,"
            "Shadow=1,"
            "Alignment=2,"
            "MarginV=80,"
            "MarginL=30,"
            "MarginR=30"
        )

        cmd = [
            "ffmpeg", "-y", "-i", src,
            "-vf", f"subtitles='{safe_srt}':force_style='{style}'",
            "-c:v", "libx264", "-c:a", "copy",
            "-pix_fmt", "yuv420p", "-preset", "fast", dst,
        ]
        ok = self._run_cmd(cmd, "Subtitles")
        if not ok:
            shutil.copy2(src, dst)
        return ok

    # ─────────────────────────────────────────────────────────────────
    # KEN BURNS — Image → Video with cinematic zoom
    # ─────────────────────────────────────────────────────────────────

    def _image_to_kenburns(self, img_path, duration, out_path, zoom_dir="in"):
        fps    = 25
        frames = int(duration * fps)
        z_expr = (
            "min(zoom+0.0003,1.08)" if zoom_dir == "in"
            else "max(zoom-0.0003,1.0)"
        )
        vf = (
            f"scale=1200:2133,"
            f"zoompan=z='{z_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s=1080x1920:fps={fps},"
            f"setpts=PTS-STARTPTS,fps={fps}"
        )
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", img_path,
            "-vf", vf,
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast", out_path,
        ]
        return self._run_cmd(cmd, "KenBurns")

    def _clip_to_portrait(self, clip_path, duration, out_path):
        cmd = [
            "ffmpeg", "-y", "-i", clip_path,
            "-vf", (
                "scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,fps=25"
            ),
            "-t", str(duration), "-an",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "fast", out_path,
        ]
        return self._run_cmd(cmd, "Clip→Portrait")

    # ─────────────────────────────────────────────────────────────────
    # BUILD VISUAL — Pollinations images + Pexels clips
    # ─────────────────────────────────────────────────────────────────

    def _build_visual(self, scene, total_dur):
        """
        4 segments banata hai:
        1. Pollinations AI image (visual_1) — Ken Burns zoom in
        2. Pexels clip (visual_1)
        3. Pollinations AI image (visual_2) — Ken Burns zoom out
        4. Pexels clip (visual_2)
        Concatenate karke ek visual track return karta hai.
        """
        scene_id = scene.get("id", 1)
        v1       = scene.get("visual_1", "smartphone tech")
        v2       = scene.get("visual_2", "person computer")
        segments = []
        dur_each = max(total_dur / 4, 3.0)

        # Segment 1 — AI image visual_1
        img1 = self._fetch_pollinations_image(v1, scene_id, 0)
        if img1:
            seg1 = os.path.join(self.temp_dir, f"seg_{scene_id}_1.mp4")
            if self._image_to_kenburns(img1, dur_each, seg1, "in"):
                segments.append(seg1)

        # Segment 2 — Pexels clip visual_1
        clip1 = self._fetch_pexels_clip(v1, scene_id, 0)
        if clip1:
            seg2 = os.path.join(self.temp_dir, f"seg_{scene_id}_2.mp4")
            if self._clip_to_portrait(clip1, dur_each, seg2):
                segments.append(seg2)

        # Segment 3 — AI image visual_2
        img2 = self._fetch_pollinations_image(v2, scene_id, 1)
        if img2:
            seg3 = os.path.join(self.temp_dir, f"seg_{scene_id}_3.mp4")
            if self._image_to_kenburns(img2, dur_each, seg3, "out"):
                segments.append(seg3)

        # Segment 4 — Pexels clip visual_2
        clip2 = self._fetch_pexels_clip(v2, scene_id, 1)
        if clip2:
            seg4 = os.path.join(self.temp_dir, f"seg_{scene_id}_4.mp4")
            if self._clip_to_portrait(clip2, dur_each, seg4):
                segments.append(seg4)

        if not segments:
            print(f"   ❌ No visuals found for Scene {scene_id}")
            return None

        if len(segments) == 1:
            return segments[0]

        list_file = os.path.join(self.temp_dir, f"seglist_{scene_id}.txt")
        with open(list_file, "w") as f:
            for p in segments:
                f.write(f"file '{p}'\n")

        out = os.path.join(self.temp_dir, f"visual_{scene_id}.mp4")
        ok  = self._run_cmd([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", list_file,
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "fast", out,
        ], "Concat segments")

        return out if (ok and os.path.exists(out)) else segments[0]

    # ─────────────────────────────────────────────────────────────────
    # PROCESS SCENE
    # ─────────────────────────────────────────────────────────────────

    def process_scene(self, scene, scene_index=0):
        scene_id   = scene.get("id", 1)
        audio_path = scene.get("audio_path")
        total_dur  = scene.get("duration", 0)
        script_txt = scene.get("text", "")

        if not audio_path or not os.path.exists(audio_path):
            print(f"   ⚠️ Audio missing for Scene {scene_id}")
            return None

        nosub_path  = os.path.join(self.temp_dir, f"nosub_{scene_id}.mp4")
        subbed_path = os.path.join(self.temp_dir, f"subbed_{scene_id}.mp4")
        final_path  = os.path.join(self.temp_dir, f"scene_{scene_id}.mp4")

        # ── Step 1: Build visual ──────────────────────────────────────
        print(f"   🖼️  Building visuals Scene {scene_id}...")
        visual = self._build_visual(scene, total_dur)
        if not visual:
            return None

        # ── Step 2: Mix voice + bg music ─────────────────────────────
        try:
            voice = ffmpeg.input(audio_path)
            vis   = ffmpeg.input(visual)

            if os.path.exists(self.bg_music_path):
                bg = (
                    ffmpeg.input(self.bg_music_path, stream_loop=-1)
                    .filter("volume", 0.10)
                    .filter("atrim", duration=total_dur + 2)
                )
                audio_out = ffmpeg.filter(
                    [voice, bg], "amix", inputs=2, duration="first"
                )
            else:
                audio_out = voice

            (
                ffmpeg.output(
                    vis.video, audio_out, nosub_path,
                    vcodec="libx264", acodec="aac",
                    pix_fmt="yuv420p", preset="medium",
                    movflags="faststart",
                    shortest=None
                ).run(overwrite_output=True, quiet=True)
            )

        except Exception as e:
            print(f"   ❌ Audio mix failed Scene {scene_id}: {e}")
            return None

        # ── Step 3: Burn subtitles ────────────────────────────────────
        actual_dur = self.get_duration(nosub_path)
        srt        = self._make_srt(script_txt, actual_dur, scene_id)

        if srt:
            ok      = self._burn_subtitles(nosub_path, srt, subbed_path)
            current = (
                subbed_path if (ok and os.path.exists(subbed_path))
                else nosub_path
            )
            if ok:
                print(f"   ✅ Scene {scene_id}: subtitles burned")
        else:
            current = nosub_path

        if current != final_path:
            shutil.copy2(current, final_path)

        # ── Step 4: Brainrot split screen ────────────────────────────
        loop_video = self._fetch_loop_video(scene_index)
        if loop_video and os.path.exists(loop_video):
            split = self._apply_split_screen(final_path, loop_video, scene_id)
            if split and os.path.exists(split):
                shutil.copy2(split, final_path)
                print(f"   🎮 Brainrot split screen applied!")
        else:
            print(f"   ℹ️  No loop video — normal output")

        print(f"   ✅ Scene {scene_id} complete ({total_dur:.1f}s)")
        return final_path

    # ─────────────────────────────────────────────────────────────────
    # RENDER ALL
    # ─────────────────────────────────────────────────────────────────

    def render_all_scenes(self, script_data):
        """
        Sirf script_data pass karo.
        Composer khud visuals fetch karta hai (Pollinations + Pexels).
        """
        rendered = []
        for i, scene in enumerate(script_data):
            print(f"\n🎬 Processing Scene {i+1}/{len(script_data)}...")
            path = self.process_scene(scene, scene_index=i)
            if path:
                rendered.append(path)
            else:
                print(f"   ⚠️ Scene {i+1} failed, skipping")
        return rendered

    # ─────────────────────────────────────────────────────────────────
    # FINAL CONCATENATE
    # ─────────────────────────────────────────────────────────────────

    def concatenate_with_transitions(
        self,
        video_paths,
        output_filename="final_short.mp4",
        channel_name="@TechShorts"
    ):
        print("\n🎬 Stitching final video...")
        output_path = os.path.join(self.final_dir, output_filename)

        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except Exception:
                pass

        if not video_paths:
            return None

        if len(video_paths) == 1:
            shutil.copy2(video_paths[0], output_path)
            print(f"✅ FINAL VIDEO: {output_path}")
            return output_path

        inp         = ffmpeg.input(video_paths[0])
        v_stream    = inp.video
        a_stream    = inp.audio
        current_dur = self.get_duration(video_paths[0])

        for i in range(1, len(video_paths)):
            nxt      = ffmpeg.input(video_paths[i])
            next_dur = self.get_duration(video_paths[i])
            trans    = 0.5
            offset   = max(current_dur - trans, 0.1)

            v_stream = ffmpeg.filter(
                [v_stream, nxt.video], "xfade",
                transition="fade", duration=trans, offset=offset
            )
            a_stream = ffmpeg.filter(
                [a_stream, nxt.audio], "acrossfade", d=trans
            )
            current_dur += next_dur - trans

        try:
            (
                ffmpeg.output(
                    v_stream, a_stream, output_path,
                    vcodec="libx264", acodec="aac",
                    pix_fmt="yuv420p", preset="medium",
                    movflags="faststart"
                ).run(overwrite_output=True, quiet=False)
            )
        except Exception as e:
            print(f"❌ Stitching error: {e}")
            return None

        print(f"✅ FINAL VIDEO: {output_path}")
        return output_path
