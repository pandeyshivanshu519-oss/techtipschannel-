import os
import re
import random
import subprocess
import ffmpeg

class Composer:
    def __init__(self):
        self.temp_dir = os.path.join(os.getcwd(), "assets", "temp")
        self.final_dir = os.path.join(os.getcwd(), "assets", "final")
        self.avatar_path = os.path.join(os.getcwd(), "assets", "avatar", "avatars.mp4")
        self.bg_music_path = "bgmusic.mp3"
        self.font_path = os.path.join(os.getcwd(), "assets", "fonts", "NotoSans-Bold.ttf")

        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.final_dir, exist_ok=True)

        self.transitions = ['fade', 'wipeleft', 'wiperight', 'slideleft', 'slideright']

        # ── Subtitle style ──────────────────────────────────────────────
        # Bold white text, black outline, yellow highlight for keywords
        self.subtitle_style = (
            "FontName=Noto Sans,"
            "FontSize=18,"
            "PrimaryColour=&H00FFFFFF,"   # white text
            "OutlineColour=&H00000000,"   # black outline
            "BackColour=&H80000000,"      # semi-transparent bg bar
            "Bold=1,"
            "Outline=2,"
            "Shadow=1,"
            "Alignment=2,"               # centre-bottom
            "MarginV=60"                 # above bottom edge
        )

    # ────────────────────────────────────────────────────────────────────
    # HELPERS
    # ────────────────────────────────────────────────────────────────────

    def get_duration(self, filepath):
        try:
            probe = ffmpeg.probe(filepath)
            return float(probe['format']['duration'])
        except Exception:
            return 0.0

    def _font_arg(self):
        """Return fontfile= arg only when the custom font exists."""
        if os.path.exists(self.font_path):
            return f"fontfile={self.font_path}:"
        return ""

    def _chunk_text(self, text, max_chars=40):
        """
        Split a long script into short subtitle lines (≤max_chars each).
        Breaks on word boundaries so no word is cut in half.
        """
        words = text.split()
        lines, current = [], []
        for word in words:
            if sum(len(w) for w in current) + len(current) + len(word) <= max_chars:
                current.append(word)
            else:
                if current:
                    lines.append(" ".join(current))
                current = [word]
        if current:
            lines.append(" ".join(current))
        return lines

    def _make_subtitle_file(self, text, duration, scene_id):
        """
        Build a .srt subtitle file timed to fill the whole scene duration.
        Returns path to the .srt file.
        """
        lines = self._chunk_text(text, max_chars=38)
        if not lines:
            return None

        srt_path = os.path.join(self.temp_dir, f"sub_{scene_id}.srt")
        time_per_line = duration / len(lines)

        def fmt(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds - int(seconds)) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        with open(srt_path, "w", encoding="utf-8") as f:
            for i, line in enumerate(lines):
                start = i * time_per_line
                end = min((i + 1) * time_per_line, duration - 0.05)
                f.write(f"{i+1}\n{fmt(start)} --> {fmt(end)}\n{line}\n\n")

        return srt_path

    def _burn_subtitles(self, input_video, srt_path, output_path):
        """
        Burn .srt subtitles into video using FFmpeg subtitles filter.
        Falls back gracefully if font is missing.
        """
        font_arg = self._font_arg()
        style = (
            f"{font_arg}"
            "FontSize=18,"
            "PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,"
            "BackColour=&H80000000,"
            "Bold=1,"
            "Outline=2,"
            "Shadow=1,"
            "Alignment=2,"
            "MarginV=60"
        )
        # Escape Windows-style path backslashes for FFmpeg filter
        safe_srt = srt_path.replace("\\", "/").replace(":", "\\:")
        vf = f"subtitles='{safe_srt}':force_style='{style}'"

        cmd = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-vf", vf,
            "-c:v", "libx264",
            "-c:a", "copy",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"   ⚠️ Subtitle burn failed, keeping raw video.\n{result.stderr[-300:]}")
            import shutil
            shutil.copy2(input_video, output_path)

    def _add_hook_text(self, input_video, hook_line, output_path):
        """
        Burn a bold HOOK text in the top-centre for the first 3 seconds.
        Example: 'क्या आप जानते हैं? 😱'
        """
        font_arg = self._font_arg()
        # Escape special chars for drawtext
        safe_text = hook_line.replace("'", "\\'").replace(":", "\\:")

        vf = (
            f"drawtext="
            f"{font_arg}"
            f"text='{safe_text}':"
            f"fontsize=28:"
            f"fontcolor=white:"
            f"borderw=3:"
            f"bordercolor=black:"
            f"x=(w-text_w)/2:"
            f"y=80:"
            f"enable='between(t,0,3)'"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-vf", vf,
            "-c:v", "libx264",
            "-c:a", "copy",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"   ⚠️ Hook text burn failed.\n{result.stderr[-200:]}")
            import shutil
            shutil.copy2(input_video, output_path)

    def _add_channel_watermark(self, input_video, channel_name, output_path):
        """
        Add a small semi-transparent channel name watermark at top-right.
        Visible for the entire video.
        """
        font_arg = self._font_arg()
        safe_name = channel_name.replace("'", "\\'").replace(":", "\\:")

        vf = (
            f"drawtext="
            f"{font_arg}"
            f"text='{safe_name}':"
            f"fontsize=14:"
            f"fontcolor=white@0.7:"
            f"borderw=2:"
            f"bordercolor=black@0.5:"
            f"x=w-text_w-20:"
            f"y=30"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-vf", vf,
            "-c:v", "libx264",
            "-c:a", "copy",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"   ⚠️ Watermark burn failed.\n{result.stderr[-200:]}")
            import shutil
            shutil.copy2(input_video, output_path)

    # ────────────────────────────────────────────────────────────────────
    # SCENE RENDERING
    # ────────────────────────────────────────────────────────────────────

    def process_scene(self, scene, video_pair, is_avatar=False):
        scene_id    = scene.get('id', 1)
        audio_path  = scene.get('audio_path')
        total_dur   = scene.get('duration', 0)
        script_text = scene.get('text', '')
        is_first    = scene.get('is_first', False)

        if not audio_path or not os.path.exists(audio_path):
            print(f"   ⚠️ Audio missing for Scene {scene_id}")
            return None

        raw_path      = os.path.join(self.temp_dir, f"scene_{scene_id}_raw.mp4")
        subbed_path   = os.path.join(self.temp_dir, f"scene_{scene_id}_sub.mp4")
        hooked_path   = os.path.join(self.temp_dir, f"scene_{scene_id}_hook.mp4")
        output_path   = os.path.join(self.temp_dir, f"scene_{scene_id}.mp4")

        # ── 1. Build raw scene (video + audio mix) ──────────────────────
        try:
            voice_audio = ffmpeg.input(audio_path)

            if os.path.exists(self.bg_music_path):
                bg_music = (
                    ffmpeg.input(self.bg_music_path, stream_loop=-1)
                    .filter('volume', 0.15)
                    .filter('atrim', duration=total_dur + 1)
                )
                audio_stream = ffmpeg.filter(
                    [voice_audio, bg_music], 'amix', inputs=2, duration='first'
                )
            else:
                audio_stream = voice_audio

            if is_avatar and os.path.exists(self.avatar_path):
                print(f"   ⚙️ Scene {scene_id}: 🤖 Avatar Mode")
                video_stream = (
                    ffmpeg.input(self.avatar_path, stream_loop=-1)
                    .trim(duration=total_dur + 0.5)
                    .setpts('PTS-STARTPTS')
                    .filter('scale', 1080, 1920, force_original_aspect_ratio='increase')
                    .filter('crop', 1080, 1920)
                    .filter('fps', fps=30)
                )
            else:
                print(f"   ⚙️ Scene {scene_id}: 🎞️ A/B Split Mode")
                path_a, path_b = video_pair
                dur_a = total_dur / 2
                dur_b = total_dur / 2 + 0.3

                stream_a = (
                    ffmpeg.input(path_a, stream_loop=-1)
                    .trim(duration=dur_a).setpts('PTS-STARTPTS')
                    .filter('scale', 1080, 1920).filter('crop', 1080, 1920)
                    .filter('fps', fps=30)
                )
                stream_b = (
                    ffmpeg.input(path_b, stream_loop=-1)
                    .trim(duration=dur_b).setpts('PTS-STARTPTS')
                    .filter('scale', 1080, 1920).filter('crop', 1080, 1920)
                    .filter('fps', fps=30)
                )
                video_stream = ffmpeg.concat(stream_a, stream_b, v=1, a=0)

            (
                ffmpeg.output(
                    video_stream, audio_stream, raw_path,
                    vcodec='libx264', acodec='aac',
                    pix_fmt='yuv420p', preset='medium', movflags='faststart'
                ).run(overwrite_output=True, quiet=True)
            )

        except Exception as e:
            print(f"❌ Render Fail Scene {scene_id}: {e}")
            return None

        # ── 2. Burn subtitles ───────────────────────────────────────────
        current = raw_path
        if script_text.strip():
            srt_path = self._make_subtitle_file(script_text, total_dur, scene_id)
            if srt_path:
                self._burn_subtitles(current, srt_path, subbed_path)
                current = subbed_path
                print(f"   ✅ Scene {scene_id}: subtitles burned")

        # ── 3. Hook text on FIRST scene only ───────────────────────────
        if is_first:
            self._add_hook_text(current, "क्या आप जानते हैं? 😱", hooked_path)
            current = hooked_path
            print(f"   ✅ Scene {scene_id}: hook text added")

        # ── 4. Copy final scene to output_path ─────────────────────────
        if current != output_path:
            import shutil
            shutil.copy2(current, output_path)

        return output_path

    # ────────────────────────────────────────────────────────────────────
    # RENDER ALL SCENES
    # ────────────────────────────────────────────────────────────────────

    def render_all_scenes(self, script_data, video_pairs):
        rendered_paths = []
        avatar_indices = []

        if len(script_data) >= 4 and os.path.exists(self.avatar_path):
            valid_range = list(range(1, len(script_data) - 1))
            count = min(2, len(valid_range))
            avatar_indices = random.sample(valid_range, count)
            print(f"🎲 Avatar injected in scenes: {[i+1 for i in avatar_indices]}")

        for i, scene in enumerate(script_data):
            scene['is_first'] = (i == 0)          # mark first scene for hook
            current_pair = video_pairs[i]
            is_avatar = i in avatar_indices

            if is_avatar:
                current_pair = (self.avatar_path, None)

            output_path = self.process_scene(scene, current_pair, is_avatar)
            if output_path:
                rendered_paths.append(output_path)

        return rendered_paths

    # ────────────────────────────────────────────────────────────────────
    # CONCATENATE + WATERMARK
    # ────────────────────────────────────────────────────────────────────

    def concatenate_with_transitions(
        self,
        video_paths,
        output_filename="final_short.mp4",
        channel_name="@HindiFacts"
    ):
        print("🎬 Stitching final video with transitions...")

        output_path = os.path.join(self.final_dir, output_filename)
        no_wm_path  = os.path.join(self.final_dir, "final_nowm.mp4")

        # Remove stale files
        for p in (output_path, no_wm_path):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

        if not video_paths:
            return None

        # ── xfade stitching ─────────────────────────────────────────────
        input1   = ffmpeg.input(video_paths[0])
        v_stream = input1.video
        a_stream = input1.audio
        current_dur = self.get_duration(video_paths[0])

        for i in range(1, len(video_paths)):
            nxt      = ffmpeg.input(video_paths[i])
            next_dur = self.get_duration(video_paths[i])
            trans    = 0.5
            offset   = max(current_dur - trans, 0.1)
            effect   = random.choice(self.transitions)

            v_stream = ffmpeg.filter(
                [v_stream, nxt.video], 'xfade',
                transition=effect, duration=trans, offset=offset
            )
            a_stream = ffmpeg.filter(
                [a_stream, nxt.audio], 'acrossfade', d=trans
            )
            current_dur = current_dur + next_dur - trans

        try:
            (
                ffmpeg.output(
                    v_stream, a_stream, no_wm_path,
                    vcodec='libx264', acodec='aac',
                    pix_fmt='yuv420p', preset='medium', movflags='faststart'
                ).run(overwrite_output=True, quiet=False)
            )
        except Exception as e:
            print(f"❌ Stitching Error: {e}")
            return None

        # ── Add channel watermark ────────────────────────────────────────
        print("🏷️ Adding channel watermark...")
        self._add_channel_watermark(no_wm_path, channel_name, output_path)

        # Clean temp no-watermark file
        try:
            os.remove(no_wm_path)
        except Exception:
            pass

        print(f"✅ FINAL VIDEO SAVED: {output_path}")
        return output_path
        
