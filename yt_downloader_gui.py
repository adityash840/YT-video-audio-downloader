#!/usr/bin/env python3

import sys
import os
from pathlib import Path
import yt_dlp
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QProgressBar, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class DownloaderThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, url, quality=None, audio_only=False, output_path=None):
        super().__init__()
        self.url = url
        self.quality = quality
        self.audio_only = audio_only
        self.output_path = output_path or str(Path.home() / "Downloads")

    def run(self):
        try:
            if self.audio_only:
                ydl_opts = {
                    'format': 'bestaudio',
                    'progress_hooks': [self._progress_hook],
                    'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
                }
            else:
                if self.quality == "144p":
                    format_selector = 'worst[height<=144]/worst'
                elif self.quality == "240p":
                    format_selector = 'worst[height<=240]/worst'
                elif self.quality == "360p":
                    format_selector = 'best[height<=360]/best'
                elif self.quality == "480p":
                    format_selector = 'best[height<=480]/best'
                elif self.quality == "720p":
                    format_selector = 'best[height<=720]/best'
                elif self.quality == "1080p":
                    format_selector = 'best[height<=1080]/best'
                else:
                    format_selector = 'best'
                
                ydl_opts = {
                    'format': format_selector,
                    'progress_hooks': [self._progress_hook],
                    'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
                }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def _progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                p = int(float(d['_percent_str'].replace('%', '')))
                self.progress.emit(p)
            except:
                pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Video Downloader")
        self.setMinimumSize(600, 450)
        self.output_path = str(Path.home() / "Downloads")
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("YouTube URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube URL here...")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)

        # Quality selection
        quality_layout = QHBoxLayout()
        quality_label = QLabel("Video Quality:")
        self.quality_combo = QComboBox()
        self.quality_combo.addItems([
            "Best Quality",
            "1080p",
            "720p",
            "480p",
            "360p",
            "240p",
            "144p"
        ])
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_combo)
        layout.addLayout(quality_layout)

        # Audio-only checkbox
        self.audio_only_checkbox = QPushButton("Download Audio Only (Original Format)")
        self.audio_only_checkbox.setCheckable(True)
        layout.addWidget(self.audio_only_checkbox)

        # Download location
        location_layout = QHBoxLayout()
        location_label = QLabel("Save to:")
        self.location_display = QLineEdit(self.output_path)
        self.location_display.setReadOnly(True)
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_location)
        location_layout.addWidget(location_label)
        location_layout.addWidget(self.location_display)
        location_layout.addWidget(self.browse_button)
        layout.addLayout(location_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Download button
        self.download_button = QPushButton("Download")
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)

        # Status label
        self.status_label = QLabel("Ready to download")
        layout.addWidget(self.status_label)

    def browse_location(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder", self.output_path)
        if folder:
            self.output_path = folder
            self.location_display.setText(folder)

    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a YouTube URL.")
            return

        quality = None
        if self.quality_combo.currentIndex() > 0:
            quality = self.quality_combo.currentText().lower()

        audio_only = self.audio_only_checkbox.isChecked()

        self.download_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Downloading...")

        self.downloader = DownloaderThread(url, quality, audio_only, self.output_path)
        self.downloader.progress.connect(self.update_progress)
        self.downloader.finished.connect(self.download_finished)
        self.downloader.error.connect(self.download_error)
        self.downloader.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def download_finished(self):
        self.download_button.setEnabled(True)
        self.status_label.setText("Download completed!")
        QMessageBox.information(self, "Success", f"Download completed successfully!\nSaved to: {self.output_path}")

    def download_error(self, error_msg):
        self.download_button.setEnabled(True)
        self.status_label.setText("Error: " + error_msg)
        QMessageBox.critical(self, "Error", "Download failed: " + error_msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_()) 