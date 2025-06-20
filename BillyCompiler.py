import sys
import os
import subprocess
import shutil
import re
import traceback
import random
import json
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, 
                             QLabel, QProgressBar, QMessageBox, QTextEdit, QFrame,
                             QSlider, QSpinBox, QLineEdit, QScrollArea)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

# --- FFmpeg Availability Check ---
def check_ffmpeg():
    """Checks if ffmpeg and ffprobe are installed and available in the system's PATH."""
    return shutil.which("ffmpeg"), shutil.which("ffprobe")

# --- Media Info Probe ---
def get_media_info(filepath, ffprobe_path):
    """Uses ffprobe to check if a file has an audio stream."""
    command = [ffprobe_path, '-v', 'quiet', '-print_format', 'json', '-show_streams', '-select_streams', 'a', filepath]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        info = json.loads(result.stdout)
        return {'has_audio': bool(info.get('streams'))}
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
        return {'has_audio': False}

# --- Worker Thread for FFmpeg Processing ---
class VideoWorker(QThread):
    progress = pyqtSignal(int, str)
    log_message = pyqtSignal(str)
    finished = pyqtSignal(str, bool) 

    def __init__(self, settings, video_files, ffprobe_path):
        super().__init__()
        self.settings = settings
        self.video_files = video_files
        self.ffprobe_path = ffprobe_path
        self.video_info_cache = {}

    def run(self):
        temp_dir = os.path.join(self.settings['output_folder'], "temp_clips")
        try:
            self.log_message.emit("Preparing for generation...")
            os.makedirs(temp_dir, exist_ok=True)
            
            self.log_message.emit("Scanning video files for audio information...")
            self._cache_video_info()

            scenes = self._plan_scenes()
            if not scenes:
                self.finished.emit("Failed to plan any scenes. Check your duration settings.", False)
                return

            clip_paths = []
            total_scenes = len(scenes)

            # STAGE 1: Create each scene as a separate temporary file
            for i, scene in enumerate(scenes):
                self.progress.emit(int((i / total_scenes) * 100), f"Processing Scene {i+1}/{total_scenes} ({scene['type']})")
                output_clip_path = os.path.join(temp_dir, f"clip_{i:04d}.ts")
                self._create_scene_clip(scene, output_clip_path)
                clip_paths.append(output_clip_path)

            # STAGE 2: Concatenate all temporary clips
            self.progress.emit(95, "Concatenating all scenes...")
            concat_list_path = os.path.join(temp_dir, "concat_list.txt")
            with open(concat_list_path, "w", encoding='utf-8') as f:
                for path in clip_paths:
                    f.write(f"file '{os.path.basename(path)}'\n")
            
            final_command = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_list_path,
                '-c', 'copy', self.settings['output_path']
            ]
            self.log_message.emit(f"\nFinal concatenation command: {' '.join(final_command)}")
            
            # Execute the final concatenation
            process = subprocess.Popen(
                final_command, cwd=temp_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
                encoding='utf-8', errors='ignore'
            )
            for line in process.stdout: self.log_message.emit(line.strip())
            process.wait()

            if process.returncode == 0:
                self.progress.emit(100, "Done!")
                self.finished.emit("Video generation successful!", True)
            else:
                self.finished.emit(f"Final concatenation failed with exit code {process.returncode}.", False)

        except Exception as e:
            self.finished.emit(f"An error occurred: {e}\n{traceback.format_exc()}", False)
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def _cache_video_info(self):
        for vid in self.video_files:
            if vid not in self.video_info_cache:
                self.video_info_cache[vid] = get_media_info(vid, self.ffprobe_path)

    def _plan_scenes(self):
        scene_duration = self.settings['scene_duration']
        if scene_duration <= 0: return []
        num_scenes = self.settings['total_duration'] // scene_duration
        scenes, available_layouts = [], ['2x2', '3x3']
        for _ in range(num_scenes):
            if random.randint(1, 100) <= self.settings['layout_mix']:
                scenes.append({'type': random.choice(available_layouts)})
            else:
                scenes.append({'type': 'single'})
        return scenes

    def _create_scene_clip(self, scene, output_path):
        target_res = '1280x720'
        scene_duration = str(self.settings['scene_duration'])
        
        inputs, video_filters, audio_filters = [], [], []
        
        # Determine videos needed for the scene
        req_vids = 1
        if scene['type'] == '2x2': req_vids = 4
        elif scene['type'] == '3x3': req_vids = 9
        
        if len(self.video_files) < req_vids:
            scene_vids = [random.choice(self.video_files) for _ in range(req_vids)]
        else:
            scene_vids = random.sample(self.video_files, req_vids)
        
        # Add inputs
        for path in scene_vids: inputs.extend(['-i', path])

        # Build video filter chain
        if scene['type'] == 'single':
            video_filters.append(f"[0:v]scale={target_res}:force_original_aspect_ratio=decrease,pad={target_res}:-1:-1:color=black,setpts=PTS-STARTPTS[vout]")
        else: # Grids
            grid_dim = 2 if scene['type'] == '2x2' else 3
            tile_w, tile_h = 1280 // grid_dim, 720 // grid_dim
            for i in range(req_vids):
                video_filters.append(f"[{i}:v]scale={tile_w}:{tile_h}:force_original_aspect_ratio=decrease,pad={tile_w}:{tile_h}:-1:-1:color=black,setpts=PTS-STARTPTS[v{i}]")
            
            rows = [f"{''.join([f'[v{r*grid_dim+c}]' for c in range(grid_dim)])}hstack=inputs={grid_dim}[row{r}]" for r in range(grid_dim)]
            video_filters.extend(rows)
            video_filters.append(f"{''.join([f'[row{r}]' for r in range(grid_dim)])}vstack=inputs={grid_dim}[vout]")

        # Build audio filter chain
        vids_with_audio = [i for i, v in enumerate(scene_vids) if self.video_info_cache.get(v, {}).get('has_audio')]
        if vids_with_audio:
            audio_mix_inputs = "".join([f"[{i}:a]" for i in vids_with_audio])
            audio_filters.append(f"{audio_mix_inputs}amix=inputs={len(vids_with_audio)},volume={self.settings['clip_vol']}[aout]")
            map_audio = ['-map', '[aout]']
        else:
            map_audio = ['-an'] # No audio

        command = ['ffmpeg', '-y'] + inputs + [
            '-filter_complex', ";".join(video_filters + audio_filters),
            '-map', '[vout]'] + map_audio + [
            '-t', scene_duration,
            '-c:v', 'libx264', '-c:a', 'aac', '-preset', 'medium', '-pix_fmt', 'yuv420p',
            output_path
        ]
        
        subprocess.run(command, capture_output=True)


# --- Main Application Window ---
class App(QWidget):
    def __init__(self):
        super().__init__()
        self.ffmpeg_path, self.ffprobe_path = check_ffmpeg()
        
        self.video_files, self.destination_folder = [], os.getcwd()
        
        self.initUI()
        if not self.ffmpeg_path or not self.ffprobe_path:
            self.show_ffmpeg_warning()

    def initUI(self):
        self.setWindowTitle('Video Compiler')
        self.setGeometry(100, 100, 700, 700)
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer_layout.addWidget(scroll_area)
        
        container_widget = QWidget()
        scroll_area.setWidget(container_widget)
        
        main_layout = QVBoxLayout(container_widget)

        # --- Sections ---
        main_layout.addWidget(self.create_section_header("1. Sources"))
        self.video_folder_label = QLabel('No source folder selected')
        main_layout.addWidget(self.create_file_select_button('Select Source Folder (Recursive)', self.select_source_folder, self.video_folder_label))
        main_layout.addWidget(self.create_separator())

        main_layout.addWidget(self.create_section_header("2. Output & Layout"))
        
        duration_layout = QHBoxLayout()
        self.total_length_spinbox = QSpinBox(); self.total_length_spinbox.setRange(1, 7200); self.total_length_spinbox.setValue(120); self.total_length_spinbox.setSuffix(" s")
        duration_layout.addWidget(QLabel("Total Video Length:")); duration_layout.addWidget(self.total_length_spinbox)
        self.clip_length_spinbox = QSpinBox(); self.clip_length_spinbox.setRange(1, 60); self.clip_length_spinbox.setValue(6); self.clip_length_spinbox.setSuffix(" s")
        duration_layout.addWidget(QLabel("Clip Length:")); duration_layout.addWidget(self.clip_length_spinbox)
        main_layout.addLayout(duration_layout)
        
        main_layout.addWidget(self.create_slider_group("Layout Mix (Single Clips <-> Grids)", 50, "layoutmix_slider"))
        
        self.dest_folder_label = QLabel(f"Destination: {self.destination_folder}")
        main_layout.addWidget(self.dest_folder_label)
        dest_button = QPushButton("Select Destination Folder"); dest_button.clicked.connect(self.select_dest_folder)
        main_layout.addWidget(dest_button)
        
        name_layout = QHBoxLayout()
        self.output_name_edit = QLineEdit("compilation.mp4")
        name_layout.addWidget(QLabel("Output Filename:")); name_layout.addWidget(self.output_name_edit)
        main_layout.addLayout(name_layout)
        main_layout.addWidget(self.create_separator())

        main_layout.addWidget(self.create_section_header("3. Audio"))
        main_layout.addWidget(self.create_slider_group("Clip Audio Volume", 100, "clipvolume_slider"))
        
        main_layout.addStretch()
        
        # --- Bottom Controls ---
        self.generate_button = QPushButton('Generate Video')
        self.generate_button.setStyleSheet("background-color: #22c55e; color: white; font-weight: bold; padding: 10px; border-radius: 5px; font-size: 16px;")
        self.generate_button.clicked.connect(self.generate_video)
        outer_layout.addWidget(self.generate_button)

        self.status_label = QLabel("Ready."); outer_layout.addWidget(self.status_label)
        self.progress_bar = QProgressBar(); outer_layout.addWidget(self.progress_bar)
        
        self.log_box = QTextEdit(); self.log_box.setReadOnly(True); self.log_box.setFont(QFont("Courier New", 9)); self.log_box.setStyleSheet("background-color: #1f2937; color: #d1d5db; border-radius: 5px;"); self.log_box.setMaximumHeight(200)
        outer_layout.addWidget(QLabel("FFmpeg Log:")); outer_layout.addWidget(self.log_box)

    def create_section_header(self, text):
        label = QLabel(text); label.setFont(QFont("Inter", 12, QFont.Weight.Bold)); return label

    def create_separator(self):
        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine); line.setFrameShadow(QFrame.Shadow.Sunken); return line

    def create_slider_group(self, title, initial_value, attr_name):
        container = QWidget(); layout = QHBoxLayout(container)
        label_text = title.split('(')[0].strip()
        label = QLabel(f"{label_text}: {initial_value}%")
        slider = QSlider(Qt.Orientation.Horizontal); slider.setRange(0, 100); slider.setValue(initial_value)
        slider.valueChanged.connect(lambda val, l=label, t=label_text: l.setText(f"{t}: {val}%"))
        layout.addWidget(label); layout.addWidget(slider)
        setattr(self, attr_name, slider)
        return container

    def create_file_select_button(self, text, callback, label_widget):
        button = QPushButton(text); button.clicked.connect(lambda: callback(label_widget))
        container = QWidget(); layout = QVBoxLayout(container); layout.setContentsMargins(0,0,0,0)
        layout.addWidget(button); layout.addWidget(label_widget)
        return container
        
    def select_source_folder(self, label):
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            label.setText(f"Folder: {os.path.basename(folder)}")
            self.video_files = [os.path.join(r, f) for r, _, fs in os.walk(folder) for f in fs if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))]
            self.video_folder_label.setText(f"{len(self.video_files)} videos found in {os.path.basename(folder)}")

    def select_dest_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder: self.destination_folder = folder; self.dest_folder_label.setText(f"Destination: {folder}")
            
    def generate_video(self):
        if not self.ffmpeg_path or not self.ffprobe_path: self.show_ffmpeg_warning(); return
        if not self.video_files: QMessageBox.critical(self, "Input Error", "Please select a source folder."); return

        self.log_box.clear(); self.progress_bar.setValue(0); self.generate_button.setEnabled(False)

        settings = {
            "layout_mix": self.layoutmix_slider.value(),
            "clip_vol": self.clipvolume_slider.value() / 100.0,
            "total_duration": self.total_length_spinbox.value(),
            "scene_duration": self.clip_length_spinbox.value(),
            "output_folder": self.destination_folder,
            "output_path": os.path.join(self.destination_folder, self.output_name_edit.text())
        }

        self.worker = VideoWorker(settings, self.video_files, self.ffprobe_path)
        self.worker.log_message.connect(self.log_box.append)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def update_progress(self, value, text):
        self.progress_bar.setValue(value)
        self.status_label.setText(text)

    def on_finished(self, message, success):
        self.generate_button.setEnabled(True)
        self.status_label.setText("Finished.")
        if success:
            QMessageBox.information(self, "Success", message)
            try:
                if sys.platform == "win32": os.startfile(self.destination_folder)
                elif sys.platform == "darwin": subprocess.Popen(["open", self.destination_folder])
                else: subprocess.Popen(["xdg-open", self.destination_folder])
            except Exception as e:
                self.log_box.append(f"\nCould not open output folder: {e}")
        else: QMessageBox.critical(self, "Error", message)
            
    def show_ffmpeg_warning(self):
        msg = QMessageBox(self); msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText("FFmpeg and FFprobe Not Found")
        msg.setInformativeText("This application requires FFmpeg and FFprobe to be installed and accessible in your system's PATH.\n\nPlease download it from ffmpeg.org and follow their installation instructions.\n\nAfter installing, you may need to restart this application.")
        msg.setWindowTitle("FFmpeg Installation Required"); msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec())
