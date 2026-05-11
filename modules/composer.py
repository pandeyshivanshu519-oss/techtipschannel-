# ================================
# FIXED COMPOSER.PY
# ================================

import os
import shutil
import subprocess
import ffmpeg
from PIL import Image, ImageDraw, ImageFont


class Composer:

    def __init__(self):
        self.temp_dir = os.path.join(os.getcwd(), "assets", "temp")
        self.final_dir = os.path.join(os.getcwd(), "assets", "final")
        self.bg_music_path = "bgmusic.mp3"
        self.font_path = self._resolve_font()

        self.loop_videos_dir = os.path.join(os.getcwd(), "assets", "loop_videos")

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
            os.path.join(os.getcwd(), "assets", "fonts", "NotoSans-Bold.ttf"),
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
            "/usr/share/fonts/noto/NotoSansDevanagari-Bold.ttf",
        ]

        for p in possible:
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

    # =========================================================
    # UTILITIES
    # =========================================================

    def get_duration(self, filepath):
        try:
            return float(ffmpeg.probe(filepath)["format"]["duration"])
        except Exception:
            return 0.0

    def _run_cmd(self, cmd, label):
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"   ⚠️ {label} ERROR:")
            print(r.stderr[-700:])
            return False
        return True

    def _is_video(self, path):
        return str(path).lower().endswith((".mp4", ".mov", ".avi", ".mkv", ".webm"))

    def _normalize_items(self, items):
        """
        Accepts:
        - list[str]
        - list[dict] with keys like path/url/file
        - str
        Returns list[str]
        """
        if items is None:
            return []

        if isinstance(items, str):
            return [items]

        if not isinstance(items, list):
            return []

        out = []
        for item in items:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                for key in ("path", "file", "url", "local_path", "src"):
                    if key in item and item[key]:
                        out.append(item[key])
                        break
        return out

    # =========================================================
    # LOOP VIDEO FETCH
    # =========================================================

    def _fetch_loop_video(self, part_num):
        exts = (".mp4", ".mov", ".avi", ".mkv", ".webm")

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

        chosen = all_videos[part_num % len(all_videos)]
        print(f"🎮 Loop video: {os.path.basename(chosen)}")
        return chosen

    # =========================================================
    # SPLIT SCREEN
    # =========================================================

    def _apply_split_screen(self, main_video, loop_video, part_num):
        out_path = os.path.join(self.temp_dir, f"split_{part_num}.mp4")
        main_dur = self.get_duration(main_video)

        cmd = [
            "ffmpeg", "-y",
            "-i", main_video,
            "-stream_loop", "-1",
            "-i", loop_video,
            "-filter_complex",
            """
            [0:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[top];
            [1:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[bottom];
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
            "-movflags", "faststart",
            out_path
        ]

        ok = self._run_cmd(cmd, "Split Screen")
        if ok and os.path.exists(out_path):
            print("✅ Split screen applied")
            return out_path

        return main_video

    # =========================================================
    # INTRO CLIP
    # =========================================================

    def _make_intro_clip(self, intro_frame_path, part_num):
        out = os.path.join(self.temp_dir, f"intro_{part_num}.mp4")
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", intro_frame_path,
            "-t", "2.0",
            "-vf", "scale=1080:1920,fps=25",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-an",
            out,
        ]
        ok = self._run_cmd(cmd, "Intro clip")
        return out if ok else None

    # =========================================================
    # SUBTITLES
    # =========================================================

    @staticmethod
    def _srt_ts(seconds):
        seconds = max(0.0, seconds)
        total_ms = int(round(seconds * 1000))
        ms = total_ms % 1000
        s = (total_ms // 1000) % 60
        m = (total_ms // 60000) % 60
        h = total_ms // 3600000
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    def _make_synced_srt(self, char_timings, intro_offset=2.0, scene_id=1):
        if not char_timings:
            return None

        srt_path = os.path.join(self.temp_dir, f"sub_{scene_id}.srt")
        entries = []
        idx = 1

        for timing in char_timings:
            tag = timing.get("tag", "NARRATOR")
            text = timing.get("text", "").strip()
            start = timing.get("start", 0.0) + intro_offset
            end = timing.get("end", 0.0) + intro_offset

            if not text or end <= start:
                continue

            name_line = "" if tag == "NARRATOR" else f"[ {tag.title()} ]"

            words = text.split()
            chunks, cur = [], []
            for w in words:
                cur.append(w)
                if len(cur) >= 5:
                    chunks.append(" ".join(cur))
                    cur = []
            if cur:
                chunks.append(" ".join(cur))

            dur_per_chunk = max((end - start) / max(len(chunks), 1), 0.5)

            for ci, chunk in enumerate(chunks):
                cs = start + ci * dur_per_chunk
                ce = min(cs + dur_per_chunk - 0.05, end)
                sub_text = f"{name_line}\n{chunk}" if name_line else chunk
                entries.append((idx, cs, ce, sub_text))
                idx += 1

        if not entries:
            return None

        with open(srt_path, "w", encoding="utf-8") as f:
            for i, cs, ce, sub_text in entries:
                f.write(f"{i}\n{self._srt_ts(cs)} --> {self._srt_ts(ce)}\n{sub_text}\n\n")

        return srt_path

    def _burn_subtitles(self, src, srt_path, dst):
        if not self.font_path:
            shutil.copy2(src, dst)
            return False

        safe_srt = srt_path.replace("\\", "/")
        safe_font = self.font_path.replace("\\", "/")
        if len(safe_srt) >= 2 and safe_srt[1] == ":":
            safe_srt = safe_srt[0] + "\\:" + safe_srt[2:]

        style = (
            f"fontfile={safe_font},"
            "FontSize=20,"
            "PrimaryColour=&H00FFFFFF,"
            "SecondaryColour=&H0000FFFF,"
            "OutlineColour=&H00000000,"
            "BackColour=&H90000000,"
            "Bold=1,"
            "Outline=3,"
            "Shadow=1,"
            "Alignment=2,"
            "MarginV=130,"
            "MarginL=40,"
            "MarginR=40"
        )

        cmd = [
            "ffmpeg", "-y", "-i", src,
            "-vf", f"subtitles='{safe_srt}':force_style='{style}'",
            "-c:v", "libx264",
            "-c:a", "copy",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            dst,
        ]
        ok = self._run_cmd(cmd, "Subtitles")
        if not ok:
            shutil.copy2(src, dst)
        return ok

    # =========================================================
    # BADGE ON IMAGE
    # =========================================================

    def _burn_badge_on_image(self, img_path, out_path, top_text, part_num, total_parts):
        if self._is_video(img_path):
            print("   🎥 Video detected — skipping image overlay")
            return img_path

        try:
            img = Image.open(img_path).convert("RGB")
        except Exception as e:
            print(f"   ❌ Failed opening image: {e}")
            return img_path

        W, H = img.size
        draw = ImageDraw.Draw(img, "RGBA")

        draw.rectangle([(0, 0), (W, 82)], fill=(0, 0, 0, 215))

        mf = self._pil_font(26)
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            draw.text((20 + dx, 24 + dy), top_text, font=mf, fill=(0, 0, 0, 255))

        draw.text((20, 24), top_text, font=mf, fill=(255, 255, 255, 255))

        part_str = f"PART {part_num}"
        pf = self._pil_font(22)
        pb = draw.textbbox((0, 0), part_str, font=pf)
        pw = pb[2] - pb[0]
        ph = pb[3] - pb[1]
        bx = W - pw - 36
        by = 16

        draw.rounded_rectangle(
            [bx - 10, by - 6, bx + pw + 10, by + ph + 6],
            radius=8,
            fill=(255, 210, 0, 255)
        )

        draw.text((bx, by), part_str, font=pf, fill=(20, 20, 20))
        img.save(out_path, "JPEG", quality=92)
        return out_path

    # =========================================================
    # IMAGE -> VIDEO
    # =========================================================

    def _image_to_video_kenburns(self, img_path, duration, out_path, zoom_dir="in"):
        fps = 25
        frames = max(int(duration * fps), 1)

        z_expr = "min(zoom+0.0005,1.10)" if zoom_dir == "in" else "max(zoom-0.0005,1.0)"

        vf = (
            f"scale=1200:2133,"
            f"zoompan=z='{z_expr}':"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s=1080x1920:fps={fps},"
            f"fps={fps}"
        )

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img_path,
            "-vf", vf,
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            out_path
        ]
        return self._run_cmd(cmd, "KenBurns")

    # =========================================================
    # VIDEO -> PORTRAIT
    # =========================================================

    def _clip_to_portrait(self, clip_path, duration, out_path):
        cmd = [
            "ffmpeg", "-y",
            "-i", clip_path,
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=25",
            "-t", str(duration),
            "-an",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            out_path
        ]
        return self._run_cmd(cmd, "Portrait Clip")

    # =========================================================
    # BUILD VISUAL SEQUENCE
    # =========================================================

    def _build_visual_sequence(self, image_paths, mood_clips, total_dur, part_num, movie_name, total_parts):
        image_paths = self._normalize_items(image_paths)
        mood_clips = self._normalize_items(mood_clips)

        visuals = []
        for v in image_paths:
            visuals.append(v)
        for m in mood_clips:
            visuals.append(m)

        if not visuals:
            print("❌ No visuals found")
            return None

        # Full audio duration cover karne ke liye
        dur_per = total_dur / max(len(visuals), 1)
        if dur_per < 1.0:
            dur_per = 1.0

        print(f"🎬 Total visuals: {len(visuals)}")
        print(f"⏱️ Duration per visual: {dur_per:.2f}s")

        segments = []

        for idx, vpath in enumerate(visuals):
            seg = os.path.join(self.temp_dir, f"seg_{part_num}_{idx}.mp4")

            if self._is_video(vpath):
                print(f"🎥 Processing video clip {idx + 1}")
                ok = self._clip_to_portrait(vpath, dur_per, seg)
            else:
                print(f"🖼️ Processing image {idx + 1}")
                overlay = os.path.join(self.temp_dir, f"ov_{part_num}_{idx}.jpg")
                self._burn_badge_on_image(vpath, overlay, movie_name, part_num, total_parts)
                ok = self._image_to_video_kenburns(
                    overlay,
                    dur_per,
                    seg,
                    zoom_dir="in" if idx % 2 == 0 else "out"
                )

            if ok and os.path.exists(seg):
                segments.append(seg)
                print("✅ Segment created")
            else:
                print("❌ Segment failed")

        if not segments:
            print("❌ No segments rendered")
            return None

        if len(segments) == 1:
            return segments[0]

        list_file = os.path.join(self.temp_dir, f"list_{part_num}.txt")
        with open(list_file, "w", encoding="utf-8") as f:
            for p in segments:
                f.write(f"file '{p}'\n")

        out = os.path.join(self.temp_dir, f"visual_{part_num}.mp4")
        ok = self._run_cmd([
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            out
        ], "Concat")

        if ok and os.path.exists(out):
            final_dur = self.get_duration(out)
            print(f"✅ Final visual duration: {final_dur:.2f}s")
            return out

        print("⚠️ Concat failed — using first segment")
        return segments[0]

    # =========================================================
    # PROCESS SCENE
    # =========================================================

    def process_scene(self, scene, image_paths, mood_clips, intro_frame_path=None, is_first=False):
        part_num = scene.get("part_number", 1)
        movie_name = scene.get("movie", "Tech")
        audio_path = scene.get("audio_path")
        total_dur = float(scene.get("duration", 60))
        script_text = scene.get("text", "")

        image_paths = self._normalize_items(image_paths)
        mood_clips = self._normalize_items(mood_clips)

        if not audio_path or not os.path.exists(audio_path):
            print("❌ Audio missing")
            return None

        visual = self._build_visual_sequence(
            image_paths,
            mood_clips,
            total_dur,
            part_num,
            movie_name,
            scene.get("total_parts", 100)
        )

        if not visual:
            print("❌ Visual build failed")
            return None

        # Optional intro prepend
        if intro_frame_path and os.path.exists(intro_frame_path):
            intro_clip = self._make_intro_clip(intro_frame_path, part_num)
            if intro_clip and os.path.exists(intro_clip):
                combined_list = os.path.join(self.temp_dir, f"combined_list_{part_num}.txt")
                combined_vid = os.path.join(self.temp_dir, f"combined_{part_num}.mp4")
                with open(combined_list, "w", encoding="utf-8") as f:
                    f.write(f"file '{intro_clip}'\n")
                    f.write(f"file '{visual}'\n")
                ok = self._run_cmd([
                    "ffmpeg", "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", combined_list,
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-preset", "fast",
                    combined_vid,
                ], "Prepend intro")
                if ok and os.path.exists(combined_vid):
                    visual = combined_vid

        final_path = os.path.join(self.temp_dir, f"scene_{part_num}.mp4")

        # Audio + video muxing; keep full audio duration
        try:
            v_in = ffmpeg.input(visual)
            a_in = ffmpeg.input(audio_path)

            (
                ffmpeg
                .output(
                    v_in.video,
                    a_in.audio,
                    final_path,
                    vcodec="libx264",
                    acodec="aac",
                    pix_fmt="yuv420p",
                    preset="medium",
                    movflags="faststart",
                    t=total_dur + 0.25
                )
                .run(overwrite_output=True, quiet=True)
            )
        except Exception as e:
            print(f"   ❌ Audio mix failed: {e}")
            return None

        # Subtitles
        char_timings = scene.get("char_timings", [])
        actual_dur = self.get_duration(final_path)

        if not char_timings and script_text:
            dur = max(actual_dur - 0.5, 1.0)
            char_timings = [{
                "tag": "NARRATOR",
                "text": script_text,
                "start": 0.0,
                "end": dur
            }]

        srt = self._make_synced_srt(char_timings, intro_offset=0.0, scene_id=part_num)
        if srt:
            subbed_path = os.path.join(self.temp_dir, f"subbed_{part_num}.mp4")
            ok = self._burn_subtitles(final_path, srt, subbed_path)
            if ok and os.path.exists(subbed_path):
                shutil.copy2(subbed_path, final_path)

        # Split screen using loop video if available
        loop_video = self._fetch_loop_video(part_num)
        if loop_video and os.path.exists(loop_video):
            split = self._apply_split_screen(final_path, loop_video, part_num)
            if split and os.path.exists(split):
                shutil.copy2(split, final_path)
                print("   🎬 Split screen applied")
        else:
            print("   ℹ️ No loop video — normal output")

        final_len = self.get_duration(final_path)
        print(f"   ✅ Part {part_num} done ({final_len:.1f}s)")
        return final_path

    # =========================================================
    # RENDER ALL
    # =========================================================

    def render_all_scenes(self, script_data, image_paths_list, mood_clips_list=None, intro_frame_path=None):
        rendered = []

        if mood_clips_list is None:
            mood_clips_list = []

        # Allow single-scene flat list too
        image_paths_list = self._normalize_items(image_paths_list) if isinstance(image_paths_list, str) else image_paths_list
        if isinstance(image_paths_list, list) and image_paths_list and all(isinstance(x, (str, dict)) for x in image_paths_list):
            image_paths_list = [image_paths_list]

        if isinstance(mood_clips_list, list) and mood_clips_list and all(isinstance(x, (str, dict)) for x in mood_clips_list):
            mood_clips_list = [mood_clips_list]

        for i, scene in enumerate(script_data):
            imgs = image_paths_list[i] if i < len(image_paths_list) else []
            moods = mood_clips_list[i] if i < len(mood_clips_list) else []

            path = self.process_scene(
                scene,
                imgs,
                moods,
                intro_frame_path=intro_frame_path,
                is_first=(i == 0)
            )

            if path:
                rendered.append(path)

        return rendered

    # =========================================================
    # FINAL OUTPUT
    # =========================================================

    def concatenate_with_transitions(self, video_paths, output_filename="final_short.mp4"):
        print("🎬 Finalizing video...")

        output_path = os.path.join(self.final_dir, output_filename)

        if not video_paths:
            return None

        if len(video_paths) == 1:
            shutil.copy2(video_paths[0], output_path)
            print(f"✅ FINAL: {output_path}")
            return output_path

        # Stable concat for multiple scenes
        list_file = os.path.join(self.temp_dir, "final_concat.txt")
        with open(list_file, "w", encoding="utf-8") as f:
            for p in video_paths:
                f.write(f"file '{p}'\n")

        ok = self._run_cmd([
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c", "copy",
            output_path
        ], "Final Concat")

        if ok and os.path.exists(output_path):
            print(f"✅ FINAL: {output_path}")
            return output_path

        # Fallback re-encode concat if copy fails
        try:
            inputs = [ffmpeg.input(p) for p in video_paths]
            v = inputs[0].video
            a = inputs[0].audio

            for nxt in inputs[1:]:
                v = ffmpeg.concat(v, nxt.video, v=1, a=0).node[0]
                a = ffmpeg.concat(a, nxt.audio, v=0, a=1).node[0]

            (
                ffmpeg.output(
                    v,
                    a,
                    output_path,
                    vcodec="libx264",
                    acodec="aac",
                    pix_fmt="yuv420p",
                    preset="medium",
                    movflags="faststart",
                )
                .run(overwrite_output=True, quiet=True)
            )

            print(f"✅ FINAL: {output_path}")
            return output_path

        except Exception as e:
            print(f"❌ Final stitch error: {e}")
            return None
