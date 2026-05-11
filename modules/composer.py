# ================================
# FIXED COMPOSER.PY
# ================================

import os
import shutil
import random
import subprocess
import ffmpeg
from PIL import Image, ImageDraw, ImageFont


class Composer:

    def __init__(self):

        self.temp_dir = os.path.join(os.getcwd(), "assets", "temp")
        self.final_dir = os.path.join(os.getcwd(), "assets", "final")

        self.bg_music_path = "bgmusic.mp3"

        self.font_path = self._resolve_font()

        self.loop_videos_dir = os.path.join(
            os.getcwd(),
            "assets",
            "loop_videos"
        )

        os.makedirs(self.loop_videos_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.final_dir, exist_ok=True)

        if self.font_path:
            print(f"✅ Font: {self.font_path}")
        else:
            print("⚠️ No font — PIL default")

    # =========================================================
    # FONT
    # =========================================================

    def _resolve_font(self):

        possible = [
            os.path.join(
                os.getcwd(),
                "assets",
                "fonts",
                "NotoSans-Bold.ttf"
            ),

            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",

            "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",

            "/usr/share/fonts/noto/NotoSansDevanagari-Bold.ttf",
        ]

        for p in possible:

            if os.path.exists(p) and os.path.getsize(p) > 10000:
                return p

        return None

    def _pil_font(self, size):

        if self.font_path:

            try:
                return ImageFont.truetype(self.font_path, size)

            except Exception:
                pass

        return ImageFont.load_default()

    # =========================================================
    # UTILITIES
    # =========================================================

    def get_duration(self, filepath):

        try:
            return float(
                ffmpeg.probe(filepath)["format"]["duration"]
            )

        except Exception:
            return 0.0

    def _run_cmd(self, cmd, label):

        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if r.returncode != 0:

            print(f"⚠️ {label} ERROR:")
            print(r.stderr[-500:])

            return False

        return True

    # =========================================================
    # LOOP VIDEO FETCH
    # =========================================================

    def _fetch_loop_video(self, part_num):

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

            print("⚠️ No loop videos found")

            return None

        chosen = all_videos[
            part_num % len(all_videos)
        ]

        print(f"🎮 Loop video: {os.path.basename(chosen)}")

        return chosen

    # =========================================================
    # SPLIT SCREEN
    # =========================================================

    def _apply_split_screen(
        self,
        main_video,
        loop_video,
        part_num
    ):

        out_path = os.path.join(
            self.temp_dir,
            f"split_{part_num}.mp4"
        )

        main_dur = self.get_duration(main_video)

        cmd = [
            "ffmpeg", "-y",

            "-i", main_video,

            "-stream_loop", "-1",
            "-i", loop_video,

            "-filter_complex",

            """
            [0:v]scale=1080:960:force_original_aspect_ratio=increase,
                  crop=1080:960[top];

            [1:v]scale=1080:960:force_original_aspect_ratio=increase,
                  crop=1080:960[bottom];

            [top][bottom]vstack=inputs=2[outv];

            [0:a]volume=1.0[outa]
            """,

            "-map", "[outv]",
            "-map", "[outa]",

            "-t", str(main_dur),

            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",

            "-c:a", "aac",
            "-b:a", "192k",

            "-pix_fmt", "yuv420p",

            out_path
        ]

        ok = self._run_cmd(cmd, "Split Screen")

        if ok and os.path.exists(out_path):

            print("✅ Split screen applied")

            return out_path

        return main_video

    # =========================================================
    # FIXED IMAGE BADGE
    # =========================================================

    def _burn_badge_on_image(
        self,
        img_path,
        out_path,
        top_text,
        part_num,
        total_parts
    ):

        # =====================================================
        # VIDEO DETECT
        # =====================================================

        if img_path.lower().endswith(
            (".mp4", ".mov", ".avi", ".mkv")
        ):

            print("🎥 Video detected — skipping image overlay")

            return img_path

        # =====================================================
        # OPEN IMAGE
        # =====================================================

        try:

            img = Image.open(img_path).convert("RGB")

        except Exception as e:

            print(f"❌ Failed opening image: {e}")

            return img_path

        W, H = img.size

        draw = ImageDraw.Draw(img, "RGBA")

        # =====================================================
        # TOP BAR
        # =====================================================

        draw.rectangle(
            [(0, 0), (W, 82)],
            fill=(0, 0, 0, 215)
        )

        mf = self._pil_font(26)

        # Shadow
        for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:

            draw.text(
                (20 + dx, 24 + dy),
                top_text,
                font=mf,
                fill=(0,0,0,255)
            )

        draw.text(
            (20, 24),
            top_text,
            font=mf,
            fill=(255,255,255,255)
        )

        # =====================================================
        # PART BADGE
        # =====================================================

        part_str = f"PART {part_num}"

        pf = self._pil_font(22)

        pb = draw.textbbox(
            (0,0),
            part_str,
            font=pf
        )

        pw = pb[2] - pb[0]
        ph = pb[3] - pb[1]

        bx = W - pw - 36
        by = 16

        draw.rounded_rectangle(
            [bx-10, by-6, bx+pw+10, by+ph+6],
            radius=8,
            fill=(255, 210, 0, 255)
        )

        draw.text(
            (bx, by),
            part_str,
            font=pf,
            fill=(20,20,20)
        )

        # =====================================================
        # SAVE
        # =====================================================

        img.save(out_path, "JPEG", quality=92)

        return out_path

    # =========================================================
    # CLIP TO PORTRAIT
    # =========================================================

    def _clip_to_portrait(
        self,
        clip_path,
        duration,
        out_path
    ):

        cmd = [
            "ffmpeg", "-y",

            "-i", clip_path,

            "-vf",
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=25",

            "-t", str(duration),

            "-an",

            "-c:v", "libx264",

            "-pix_fmt", "yuv420p",

            "-preset", "fast",

            out_path
        ]

        return self._run_cmd(cmd, "Portrait Clip")

    # =========================================================
    # BUILD VISUALS
    # =========================================================

    def _build_visual_sequence(
        self,
        image_paths,
        mood_clips,
        total_dur,
        part_num,
        movie_name,
        total_parts
    ):

        visuals = []

        for v in image_paths:
            visuals.append(v)

        for m in mood_clips:
            visuals.append(m)

        if not visuals:

            return None

        dur_per = max(
            3.5,
            min(total_dur / len(visuals), 8.0)
        )

        segments = []

        for idx, vpath in enumerate(visuals):

            seg = os.path.join(
                self.temp_dir,
                f"seg_{part_num}_{idx}.mp4"
            )

            # =================================================
            # VIDEO
            # =================================================

            if vpath.lower().endswith(
                (".mp4", ".mov", ".avi", ".mkv")
            ):

                ok = self._clip_to_portrait(
                    vpath,
                    dur_per,
                    seg
                )

            # =================================================
            # IMAGE
            # =================================================

            else:

                overlay = os.path.join(
                    self.temp_dir,
                    f"ov_{part_num}_{idx}.jpg"
                )

                self._burn_badge_on_image(
                    vpath,
                    overlay,
                    movie_name,
                    part_num,
                    total_parts
                )

                ok = self._clip_to_portrait(
                    overlay,
                    dur_per,
                    seg
                )

            if ok and os.path.exists(seg):
                segments.append(seg)

        if not segments:
            return None

        if len(segments) == 1:
            return segments[0]

        list_file = os.path.join(
            self.temp_dir,
            f"list_{part_num}.txt"
        )

        with open(list_file, "w") as f:

            for p in segments:
                f.write(f"file '{p}'\n")

        out = os.path.join(
            self.temp_dir,
            f"visual_{part_num}.mp4"
        )

        ok = self._run_cmd([
            "ffmpeg",
            "-y",

            "-f", "concat",

            "-safe", "0",

            "-i", list_file,

            "-c:v", "libx264",

            "-pix_fmt", "yuv420p",

            "-preset", "fast",

            out
        ], "Concat")

        if ok:
            return out

        return segments[0]

    # =========================================================
    # PROCESS SCENE
    # =========================================================

    def process_scene(
        self,
        scene,
        image_paths,
        mood_clips,
        intro_frame_path=None,
        is_first=False
    ):

        part_num = scene.get("part_number", 1)

        movie_name = scene.get("movie", "Tech")

        audio_path = scene.get("audio_path")

        total_dur = scene.get("duration", 30)

        if not audio_path or not os.path.exists(audio_path):

            print("❌ Audio missing")

            return None

        visual = self._build_visual_sequence(
            image_paths,
            mood_clips,
            total_dur,
            part_num,
            movie_name,
            100
        )

        if not visual:

            print("❌ Visual build failed")

            return None

        final_path = os.path.join(
            self.temp_dir,
            f"scene_{part_num}.mp4"
        )

        try:

            (
                ffmpeg
                .output(
                    ffmpeg.input(visual).video,
                    ffmpeg.input(audio_path).audio,
                    final_path,

                    vcodec="libx264",

                    acodec="aac",

                    pix_fmt="yuv420p",

                    shortest=None
                )
                .run(
                    overwrite_output=True,
                    quiet=True
                )
            )

        except Exception as e:

            print(f"❌ Scene render failed: {e}")

            return None

        loop_video = self._fetch_loop_video(part_num)

        if loop_video and os.path.exists(loop_video):

            split = self._apply_split_screen(
                final_path,
                loop_video,
                part_num
            )

            if split and os.path.exists(split):

                shutil.copy2(split, final_path)

        print(f"✅ Scene {part_num} rendered")

        return final_path

    # =========================================================
    # RENDER ALL
    # =========================================================

    def render_all_scenes(
        self,
        script_data,
        image_paths_list,
        mood_clips_list,
        intro_frame_path=None
    ):

        rendered = []

        for i, scene in enumerate(script_data):

            imgs = (
                image_paths_list[i]
                if i < len(image_paths_list)
                else []
            )

            moods = (
                mood_clips_list[i]
                if i < len(mood_clips_list)
                else []
            )

            path = self.process_scene(
                scene,
                imgs,
                moods
            )

            if path:
                rendered.append(path)

        return rendered

    # =========================================================
    # FINAL OUTPUT
    # =========================================================

    def concatenate_with_transitions(
        self,
        video_paths,
        output_filename="final_short.mp4"
    ):

        print("🎬 Finalizing video...")

        output_path = os.path.join(
            self.final_dir,
            output_filename
        )

        if not video_paths:
            return None

        if len(video_paths) == 1:

            shutil.copy2(
                video_paths[0],
                output_path
            )

            print(f"✅ FINAL: {output_path}")

            return output_path

        list_file = os.path.join(
            self.temp_dir,
            "final_concat.txt"
        )

        with open(list_file, "w") as f:

            for p in video_paths:
                f.write(f"file '{p}'\n")

        ok = self._run_cmd([
            "ffmpeg",
            "-y",

            "-f", "concat",

            "-safe", "0",

            "-i", list_file,

            "-c:v", "libx264",

            "-c:a", "aac",

            "-pix_fmt", "yuv420p",

            output_path

        ], "Final Concat")

        if ok:

            print(f"✅ FINAL: {output_path}")

            return output_path

        return None
