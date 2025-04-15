import sys
import os
import json
from enum import Enum
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QPushButton, QFileDialog, QLabel, QSlider, QMessageBox,
                            QHBoxLayout, QFrame, QMenu, QMenuBar, QListWidget,
                            QListWidgetItem, QDockWidget, QToolButton, QStyle,
                            QComboBox, QSpinBox, QGroupBox, QGridLayout, QCheckBox,
                            QFontDialog)
from PyQt6.QtCore import Qt, QTimer, QSize, QPoint, QMimeData, QUrl
from PyQt6.QtGui import QIcon, QFont, QAction, QColor, QDrag
import vlc

class PlaybackMode(Enum):
    NORMAL = 0
    REPEAT_ONE = 1
    REPEAT_ALL = 2
    SHUFFLE = 3

class VideoAdjustment(Enum):
    CONTRAST = 'Contrast'
    BRIGHTNESS = 'Brightness'
    HUE = 'Hue'
    SATURATION = 'Saturation'
    GAMMA = 'Gamma'

class EqualizerBand:
    def __init__(self, freq, amp):
        self.frequency = freq
        self.amplitude = amp
        self.slider = None

class VideoControlPanel(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Video Controls", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Video adjustments
        adjustments_group = QGroupBox("Video Adjustments")
        adjustments_layout = QGridLayout()
        
        self.adjustment_sliders = {}
        row = 0
        for adj in VideoAdjustment:
            label = QLabel(adj.value)
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(-100, 100)
            slider.setValue(0)
            slider.valueChanged.connect(lambda v, a=adj: parent.adjustVideo(a, v))
            
            adjustments_layout.addWidget(label, row, 0)
            adjustments_layout.addWidget(slider, row, 1)
            self.adjustment_sliders[adj] = slider
            row += 1
            
        adjustments_group.setLayout(adjustments_layout)
        layout.addWidget(adjustments_group)
        
        # Video options
        options_group = QGroupBox("Video Options")
        options_layout = QVBoxLayout()
        
        self.deinterlace_cb = QCheckBox("Deinterlace")
        self.deinterlace_cb.toggled.connect(parent.toggleDeinterlace)
        options_layout.addWidget(self.deinterlace_cb)
        
        aspect_layout = QHBoxLayout()
        aspect_layout.addWidget(QLabel("Aspect Ratio:"))
        self.aspect_combo = QComboBox()
        self.aspect_combo.addItems(["Default", "16:9", "4:3", "1:1", "16:10", "2.35:1"])
        self.aspect_combo.currentTextChanged.connect(parent.setAspectRatio)
        aspect_layout.addWidget(self.aspect_combo)
        options_layout.addLayout(aspect_layout)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Reset button
        reset_button = QPushButton("Reset All")
        reset_button.clicked.connect(self.resetControls)
        layout.addWidget(reset_button)
        
        layout.addStretch()
        self.setWidget(container)
        
    def resetControls(self):
        for slider in self.adjustment_sliders.values():
            slider.setValue(0)
        self.deinterlace_cb.setChecked(False)
        self.aspect_combo.setCurrentText("Default")

class AudioEqualizerPanel(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Equalizer", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Equalizer bands
        eq_group = QGroupBox("Equalizer")
        eq_layout = QHBoxLayout()
        
        self.bands = [
            EqualizerBand(60, 0),    # Bass
            EqualizerBand(170, 0),   # Bass/Mid
            EqualizerBand(310, 0),   # Midrange
            EqualizerBand(600, 0),   # Midrange
            EqualizerBand(1000, 0),  # Midrange
            EqualizerBand(3000, 0),  # Upper Midrange
            EqualizerBand(6000, 0),  # Presence
            EqualizerBand(12000, 0), # Brilliance
            EqualizerBand(14000, 0), # Brilliance
            EqualizerBand(16000, 0), # Brilliance
        ]
        
        for band in self.bands:
            band_layout = QVBoxLayout()
            
            # Frequency label
            freq_label = QLabel(f"{band.frequency}Hz")
            freq_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Slider
            band.slider = QSlider(Qt.Orientation.Vertical)
            band.slider.setRange(-20, 20)
            band.slider.setValue(0)
            band.slider.valueChanged.connect(lambda v, b=band: parent.adjustEqualizer(b.frequency, v))
            
            # Value label
            value_label = QLabel("0 dB")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            band.slider.valueChanged.connect(lambda v, l=value_label: l.setText(f"{v} dB"))
            
            band_layout.addWidget(freq_label)
            band_layout.addWidget(band.slider)
            band_layout.addWidget(value_label)
            eq_layout.addLayout(band_layout)
            
        eq_group.setLayout(eq_layout)
        layout.addWidget(eq_group)
        
        # Presets
        presets_layout = QHBoxLayout()
        presets_layout.addWidget(QLabel("Presets:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["Flat", "Classical", "Rock", "Pop", "Jazz", "Electronic"])
        self.preset_combo.currentTextChanged.connect(self.applyPreset)
        presets_layout.addWidget(self.preset_combo)
        layout.addLayout(presets_layout)
        
        # Reset button
        reset_button = QPushButton("Reset EQ")
        reset_button.clicked.connect(self.resetEqualizer)
        layout.addWidget(reset_button)
        
        self.setWidget(container)
        
    def applyPreset(self, preset):
        try:
            # Define presets with proper dB values (-20 to +20)
            presets = {
                "Flat": [0] * 10,
                "Classical": [
                    -1, -1, 0, 0, 0, 0, -5, -5, -5, -6
                ],
                "Rock": [
                    8, 5, -5, -8, -3, 4, 8, 11, 11, 11
                ],
                "Pop": [
                    -2, -1, 0, 2, 4, 4, 2, -1, -1, -1
                ],
                "Jazz": [
                    0, 0, 0, 4, -2, -2, 0, 2, 3, 4
                ],
                "Electronic": [
                    4, 3, 1, 0, -2, 4, 6, 8, 8, 8
                ]
            }
            
            if preset in presets:
                # Apply each band value
                for band, value in zip(self.bands, presets[preset]):
                    if band.slider:
                        band.slider.setValue(value)
                        # Ensure the equalizer gets updated
                        if hasattr(self.parent(), 'adjustEqualizer'):
                            self.parent().adjustEqualizer(band.frequency, value)
                            
        except Exception as e:
            print(f"Warning: Could not apply equalizer preset: {str(e)}")

    def resetEqualizer(self):
        for band in self.bands:
            band.slider.setValue(0)
        self.preset_combo.setCurrentText("Flat")

class SubtitlePanel(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Subtitles", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Subtitle track selection
        track_layout = QHBoxLayout()
        track_layout.addWidget(QLabel("Subtitle Track:"))
        self.track_combo = QComboBox()
        self.track_combo.currentIndexChanged.connect(parent.setSubtitleTrack)
        track_layout.addWidget(self.track_combo)
        layout.addLayout(track_layout)
        
        # Load external subtitles
        load_button = QPushButton("Load Subtitles...")
        load_button.clicked.connect(parent.loadExternalSubtitles)
        layout.addWidget(load_button)
        
        # Subtitle settings
        settings_group = QGroupBox("Subtitle Settings")
        settings_layout = QGridLayout()
        
        # Font selection
        settings_layout.addWidget(QLabel("Font:"), 0, 0)
        self.font_button = QPushButton("Select Font...")
        self.font_button.clicked.connect(parent.selectSubtitleFont)
        settings_layout.addWidget(self.font_button, 0, 1)
        
        # Delay adjustment
        settings_layout.addWidget(QLabel("Delay (ms):"), 1, 0)
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(-10000, 10000)
        self.delay_spin.setSingleStep(100)
        self.delay_spin.valueChanged.connect(parent.setSubtitleDelay)
        settings_layout.addWidget(self.delay_spin, 1, 1)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        self.setWidget(container)

class MinimalButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(32, 32)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #cccccc;
                border: none;
                font-size: 16px;
                padding: 0px;
            }
            QPushButton:hover {
                color: white;
            }
            QPushButton:pressed {
                color: #999999;
            }
            QPushButton:disabled {
                color: #666666;
            }
        """)

class PlaylistWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                border: none;
                color: #cccccc;
            }
            QListWidget::item {
                height: 25px;
                padding: 5px;
                border-bottom: 1px solid #333333;
            }
            QListWidget::item:selected {
                background-color: #333333;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a;
            }
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                files.append(url.toLocalFile())
        self.parent().addFilesToPlaylist(files)

class RhythmsPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rhythms")
        self.setGeometry(100, 100, 1200, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #000000;
            }
            QFrame {
                background-color: #000000;
            }
            QLabel {
                color: #cccccc;
                font-size: 12px;
            }
            QSlider::groove:horizontal {
                border: none;
                height: 2px;
                background: #333333;
            }
            QSlider::handle:horizontal {
                background: #ffb200;
                width: 10px;
                margin: -4px 0;
                border-radius: 5px;
            }
            QSlider::sub-page:horizontal {
                background: #ffb200;
            }
            QMenuBar {
                background-color: #000000;
                color: #cccccc;
            }
            QMenuBar::item:selected {
                background-color: #333333;
            }
            QMenu {
                background-color: #000000;
                color: #cccccc;
                border: 1px solid #333333;
            }
            QMenu::item:selected {
                background-color: #333333;
            }
            QDockWidget {
                color: #cccccc;
                titlebar-close-icon: url(close.png);
                titlebar-normal-icon: url(float.png);
            }
            QDockWidget::title {
                background: #1a1a1a;
                padding-left: 5px;
                padding-top: 2px;
            }
            QToolButton {
                background-color: transparent;
                color: #cccccc;
                border: none;
                padding: 3px;
            }
            QToolButton:hover {
                background-color: #333333;
            }
            QComboBox {
                background-color: #1a1a1a;
                color: #cccccc;
                border: 1px solid #333333;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
            QSpinBox {
                background-color: #1a1a1a;
                color: #cccccc;
                border: 1px solid #333333;
                padding: 5px;
            }
        """)

        # Initialize VLC instance and media player
        try:
            self.instance = vlc.Instance()
            self.mediaplayer = self.instance.media_player_new()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize VLC: {str(e)}")
            sys.exit(1)

        # Initialize variables
        self.current_file = None
        self.playlist = []
        self.current_index = -1
        self.playback_mode = PlaybackMode.NORMAL
        self.a_point = None
        self.b_point = None
        self.ab_repeat_active = False

        # Initialize additional variables
        self.video_adjustments = {adj: 0 for adj in VideoAdjustment}
        self.equalizer = None
        self.subtitle_tracks = []
        self.current_subtitle_track = -1
        self.subtitle_font = QFont()

        self.setupUI()
        self.loadSettings()

    def setupUI(self):
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create menu bar
        self.createMenuBar()

        # Create playlist dock widget
        self.createPlaylistDock()

        # Video frame
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: #000000;")
        main_layout.addWidget(self.video_frame, stretch=1)

        # Controls container
        controls_container = self.createControlsContainer()
        main_layout.addWidget(controls_container)

        # Create context menu
        self.createContextMenu()

        # Timer for updating the UI
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_ui)

        # Set initial volume
        self.mediaplayer.audio_set_volume(50)

        # Create video control panel
        self.video_panel = VideoControlPanel(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.video_panel)
        
        # Create audio equalizer panel
        self.eq_panel = AudioEqualizerPanel(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.eq_panel)
        
        # Create subtitle panel
        self.subtitle_panel = SubtitlePanel(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.subtitle_panel)
        
        # Add View menu for showing/hiding panels
        view_menu = self.menuBar().addMenu("View")
        view_menu.addAction(self.video_panel.toggleViewAction())
        view_menu.addAction(self.eq_panel.toggleViewAction())
        view_menu.addAction(self.subtitle_panel.toggleViewAction())

    def createMenuBar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        open_action = QAction("Open File", self)
        open_action.triggered.connect(self.openFile)
        file_menu.addAction(open_action)

        open_multiple_action = QAction("Add Files to Playlist", self)
        open_multiple_action.triggered.connect(self.addFiles)
        file_menu.addAction(open_multiple_action)

        # Playback menu
        playback_menu = menubar.addMenu("Playback")
        
        self.repeat_one_action = QAction("Repeat One", self)
        self.repeat_one_action.setCheckable(True)
        self.repeat_one_action.triggered.connect(lambda: self.setPlaybackMode(PlaybackMode.REPEAT_ONE))
        
        self.repeat_all_action = QAction("Repeat All", self)
        self.repeat_all_action.setCheckable(True)
        self.repeat_all_action.triggered.connect(lambda: self.setPlaybackMode(PlaybackMode.REPEAT_ALL))
        
        self.shuffle_action = QAction("Shuffle", self)
        self.shuffle_action.setCheckable(True)
        self.shuffle_action.triggered.connect(lambda: self.setPlaybackMode(PlaybackMode.SHUFFLE))

        playback_menu.addAction(self.repeat_one_action)
        playback_menu.addAction(self.repeat_all_action)
        playback_menu.addAction(self.shuffle_action)

    def createPlaylistDock(self):
        # Create playlist dock widget
        playlist_dock = QDockWidget("Playlist", self)
        playlist_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        
        # Create playlist widget
        self.playlist_widget = PlaylistWidget(self)
        self.playlist_widget.itemDoubleClicked.connect(self.playlistItemDoubleClicked)
        
        playlist_dock.setWidget(self.playlist_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, playlist_dock)

    def createControlsContainer(self):
        container = QFrame()
        container.setMaximumHeight(90)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 0, 10, 10)
        layout.setSpacing(5)

        # Progress bar
        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setMaximum(1000)
        self.time_slider.sliderMoved.connect(self.setPosition)
        layout.addWidget(self.time_slider)

        # Control buttons row
        controls_layout = QHBoxLayout()
        
        # Playback controls
        self.play_button = MinimalButton("▶")
        self.stop_button = MinimalButton("■")
        self.prev_button = MinimalButton("⏮")
        self.next_button = MinimalButton("⏭")
        
        self.play_button.clicked.connect(self.playPause)
        self.stop_button.clicked.connect(self.stop)
        self.prev_button.clicked.connect(self.playPrevious)
        self.next_button.clicked.connect(self.playNext)

        # A-B Repeat controls
        self.a_button = MinimalButton("A")
        self.b_button = MinimalButton("B")
        self.a_button.clicked.connect(self.setPointA)
        self.b_button.clicked.connect(self.setPointB)

        # Time labels
        self.time_label = QLabel("00:00:00")
        self.total_time_label = QLabel("/ 00:00:00")

        # Playback speed
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"])
        self.speed_combo.setCurrentText("1.0x")
        self.speed_combo.currentTextChanged.connect(self.setPlaybackSpeed)

        # Volume control
        self.volume_button = MinimalButton("🔊")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.setVolume)

        # Add all controls to layout
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.prev_button)
        controls_layout.addWidget(self.next_button)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(self.a_button)
        controls_layout.addWidget(self.b_button)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(self.time_label)
        controls_layout.addWidget(self.total_time_label)
        controls_layout.addStretch(1)
        controls_layout.addWidget(self.speed_combo)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(self.volume_button)
        controls_layout.addWidget(self.volume_slider)

        layout.addLayout(controls_layout)
        return container

    def createContextMenu(self):
        self.context_menu = QMenu(self)
        self.context_menu.addAction("Open File", self.openFile)
        self.context_menu.addAction("Add to Playlist", self.addFiles)
        self.context_menu.addSeparator()
        self.context_menu.addAction("Clear Playlist", self.clearPlaylist)

    def contextMenuEvent(self, event):
        self.context_menu.exec(event.globalPos())

    def openFile(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open File", "",
                                                "Media Files (*.mp3 *.mp4 *.avi *.mkv *.wav)")
        if filename:
            self.loadMedia(filename)
            self.addToPlaylist(filename)

    def addFiles(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Add Files", "",
                                              "Media Files (*.mp3 *.mp4 *.avi *.mkv *.wav)")
        self.addFilesToPlaylist(files)

    def addFilesToPlaylist(self, files):
        for file in files:
            self.addToPlaylist(file)
        if self.current_index == -1 and self.playlist:
            self.current_index = 0
            self.loadMedia(self.playlist[0])

    def addToPlaylist(self, filename):
        self.playlist.append(filename)
        item = QListWidgetItem(os.path.basename(filename))
        self.playlist_widget.addItem(item)

    def clearPlaylist(self):
        self.playlist.clear()
        self.playlist_widget.clear()
        self.current_index = -1
        self.stop()

    def playlistItemDoubleClicked(self, item):
        index = self.playlist_widget.row(item)
        if 0 <= index < len(self.playlist):
            self.current_index = index
            self.loadMedia(self.playlist[index])

    def loadMedia(self, filename):
        try:
            self.current_file = filename
            if not hasattr(self.instance, 'media_new'):
                QMessageBox.critical(self, "Error", "VLC instance does not support media loading")
                return
                
            self.media = self.instance.media_new(filename)
            if not self.media:
                QMessageBox.critical(self, "Error", "Could not create media")
                return
                
            if not hasattr(self.mediaplayer, 'set_media'):
                QMessageBox.critical(self, "Error", "Media player does not support setting media")
                return
                
            self.mediaplayer.set_media(self.media)
            
            if hasattr(self.media, 'parse'):
                self.media.parse()

            # Set video output
            if sys.platform.startswith('win'):
                if hasattr(self.mediaplayer, 'set_hwnd'):
                    self.mediaplayer.set_hwnd(self.video_frame.winId())
            elif sys.platform.startswith('linux'):
                if hasattr(self.mediaplayer, 'set_xwindow'):
                    self.mediaplayer.set_xwindow(self.video_frame.winId())
            elif sys.platform.startswith('darwin'):
                if hasattr(self.mediaplayer, 'set_nsobject'):
                    self.mediaplayer.set_nsobject(int(self.video_frame.winId()))

            # Update window title
            self.setWindowTitle(f"Rhythms - {os.path.basename(filename)}")

            # Initialize equalizer properly
            try:
                if hasattr(self.instance, 'audio_equalizer_new'):
                    # Create a new equalizer instance
                    self.equalizer = self.instance.audio_equalizer_new()
                    if self.equalizer:
                        # Enable the equalizer
                        if hasattr(self.mediaplayer, 'set_equalizer'):
                            self.mediaplayer.set_equalizer(self.equalizer)
                        # Apply any existing band settings
                        if hasattr(self, 'eq_panel'):
                            for band in self.eq_panel.bands:
                                self.adjustEqualizer(band.frequency, band.slider.value())
            except Exception as e:
                print(f"Warning: Could not initialize equalizer: {str(e)}")

            # Start playing
            self.playPause()
            
            # Update playlist selection
            self.playlist_widget.setCurrentRow(self.current_index)
            
            # Update subtitle tracks if supported
            if hasattr(self, 'updateSubtitleTracks'):
                self.updateSubtitleTracks()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load media: {str(e)}")

    def playPause(self):
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
            self.play_button.setText("▶")
        else:
            if self.mediaplayer.play() == -1:
                return
            self.play_button.setText("⏸")
            self.timer.start()

    def stop(self):
        self.mediaplayer.stop()
        self.play_button.setText("▶")
        self.timer.stop()
        self.time_label.setText("00:00:00")
        self.ab_repeat_active = False
        self.a_point = None
        self.b_point = None
        self.a_button.setStyleSheet(self.a_button.styleSheet().replace("color: #ffb200;", ""))
        self.b_button.setStyleSheet(self.b_button.styleSheet().replace("color: #ffb200;", ""))

    def playPrevious(self):
        if self.playlist and self.current_index > 0:
            self.current_index -= 1
            self.loadMedia(self.playlist[self.current_index])

    def playNext(self):
        if self.playlist and self.current_index < len(self.playlist) - 1:
            self.current_index += 1
            self.loadMedia(self.playlist[self.current_index])

    def setVolume(self, volume):
        self.mediaplayer.audio_set_volume(volume)
        if volume == 0:
            self.volume_button.setText("🔇")
        else:
            self.volume_button.setText("🔊")

    def setPosition(self, position):
        self.mediaplayer.set_position(position / 1000.0)

    def setPlaybackSpeed(self, speed):
        speed_value = float(speed.replace('x', ''))
        self.mediaplayer.set_rate(speed_value)

    def setPlaybackMode(self, mode):
        self.playback_mode = mode
        self.repeat_one_action.setChecked(mode == PlaybackMode.REPEAT_ONE)
        self.repeat_all_action.setChecked(mode == PlaybackMode.REPEAT_ALL)
        self.shuffle_action.setChecked(mode == PlaybackMode.SHUFFLE)

    def setPointA(self):
        if self.mediaplayer.is_playing():
            self.a_point = self.mediaplayer.get_time()
            self.a_button.setStyleSheet(self.a_button.styleSheet() + "color: #ffb200;")
            self.b_point = None
            self.b_button.setStyleSheet(self.b_button.styleSheet().replace("color: #ffb200;", ""))
            self.ab_repeat_active = False

    def setPointB(self):
        if self.mediaplayer.is_playing() and self.a_point is not None:
            self.b_point = self.mediaplayer.get_time()
            if self.b_point > self.a_point:
                self.b_button.setStyleSheet(self.b_button.styleSheet() + "color: #ffb200;")
                self.ab_repeat_active = True

    def update_ui(self):
        try:
            # Check if mediaplayer exists and has the necessary methods
            if not hasattr(self.mediaplayer, 'is_playing'):
                return
                
            if not self.mediaplayer.is_playing():
                self.timer.stop()
                if hasattr(self, 'is_playing') and not self.is_playing:
                    return

                self.play_button.setText("▶")
                
                # Handle playback modes
                if self.playback_mode == PlaybackMode.REPEAT_ONE:
                    if hasattr(self.mediaplayer, 'play'):
                        self.mediaplayer.play()
                elif self.playback_mode == PlaybackMode.REPEAT_ALL and self.current_index < len(self.playlist) - 1:
                    self.playNext()
                elif self.playback_mode == PlaybackMode.REPEAT_ALL:
                    self.current_index = 0
                    self.loadMedia(self.playlist[0])
                return

            # Update time display
            if hasattr(self.mediaplayer, 'get_position'):
                media_pos = int(self.mediaplayer.get_position() * 1000)
                self.time_slider.setValue(media_pos)

            # Check A-B repeat
            if self.ab_repeat_active and self.b_point and hasattr(self.mediaplayer, 'get_time') and hasattr(self.mediaplayer, 'set_time'):
                current_time = self.mediaplayer.get_time()
                if current_time >= self.b_point:
                    self.mediaplayer.set_time(self.a_point)

            # Update time labels
            if hasattr(self.mediaplayer, 'get_time') and hasattr(self.mediaplayer, 'get_length'):
                time = self.mediaplayer.get_time() // 1000
                duration = self.mediaplayer.get_length() // 1000
                
                current = f"{time//3600:02d}:{(time%3600)//60:02d}:{time%60:02d}"
                total = f"{duration//3600:02d}:{(duration%3600)//60:02d}:{duration%60:02d}"
                
                self.time_label.setText(current)
                self.total_time_label.setText(f"/ {total}")

        except Exception as e:
            print(f"UI update error: {str(e)}")

    def loadSettings(self):
        try:
            if os.path.exists('player_settings.json'):
                with open('player_settings.json', 'r') as f:
                    settings = json.load(f)
                    self.setPlaybackMode(PlaybackMode(settings.get('playback_mode', 0)))
                    self.mediaplayer.audio_set_volume(settings.get('volume', 50))
                    self.volume_slider.setValue(settings.get('volume', 50))
                    
                    # Load video adjustments
                    if 'video_adjustments' in settings:
                        for adj_name, value in settings['video_adjustments'].items():
                            adj = VideoAdjustment[adj_name]
                            self.video_panel.adjustment_sliders[adj].setValue(value)
                            
                    # Load subtitle font
                    if 'subtitle_font' in settings:
                        font_settings = settings['subtitle_font']
                        self.subtitle_font = QFont(
                            font_settings['family'],
                            font_settings['size'],
                            QFont.Weight.Bold if font_settings['bold'] else QFont.Weight.Normal,
                            font_settings['italic']
                        )
        except Exception as e:
            print(f"Error loading settings: {str(e)}")

    def saveSettings(self):
        try:
            settings = {
                'playback_mode': self.playback_mode.value,
                'volume': self.volume_slider.value(),
                'video_adjustments': {adj.name: value for adj, value in self.video_adjustments.items()},
                'subtitle_font': {
                    'family': self.subtitle_font.family(),
                    'size': self.subtitle_font.pointSize(),
                    'bold': self.subtitle_font.bold(),
                    'italic': self.subtitle_font.italic()
                }
            }
            with open('player_settings.json', 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Error saving settings: {str(e)}")

    def closeEvent(self, event):
        self.saveSettings()
        event.accept()

    def adjustVideo(self, adjustment, value):
        self.video_adjustments[adjustment] = value
        try:
            if adjustment == VideoAdjustment.CONTRAST:
                if hasattr(self.mediaplayer, 'video_set_contrast'):
                    self.mediaplayer.video_set_contrast(value)
            elif adjustment == VideoAdjustment.BRIGHTNESS:
                if hasattr(self.mediaplayer, 'video_set_brightness'):
                    self.mediaplayer.video_set_brightness(value)
            elif adjustment == VideoAdjustment.HUE:
                if hasattr(self.mediaplayer, 'video_set_hue'):
                    self.mediaplayer.video_set_hue(value)
            elif adjustment == VideoAdjustment.SATURATION:
                if hasattr(self.mediaplayer, 'video_set_saturation'):
                    self.mediaplayer.video_set_saturation(value)
            elif adjustment == VideoAdjustment.GAMMA:
                if hasattr(self.mediaplayer, 'video_set_gamma'):
                    self.mediaplayer.video_set_gamma(value)
        except Exception as e:
            print(f"Warning: Could not adjust {adjustment.value}: {str(e)}")
            
    def toggleDeinterlace(self, enabled):
        if enabled:
            self.mediaplayer.video_set_deinterlace("blend")
        else:
            self.mediaplayer.video_set_deinterlace(None)
            
    def setAspectRatio(self, ratio):
        if ratio == "Default":
            self.mediaplayer.video_set_aspect_ratio(None)
        else:
            self.mediaplayer.video_set_aspect_ratio(ratio)
            
    def adjustEqualizer(self, freq, value):
        try:
            if not self.equalizer:
                if hasattr(self.instance, 'audio_equalizer_new'):
                    self.equalizer = self.instance.audio_equalizer_new()
                else:
                    return

            if not hasattr(self.equalizer, 'set_amp_at_index'):
                return

            # Find the closest preset frequency band
            if hasattr(self.equalizer, 'get_band_count'):
                bands = self.equalizer.get_band_count()
                closest_band = 0
                smallest_diff = float('inf')
                
                for i in range(bands):
                    if hasattr(self.equalizer, 'get_band_frequency'):
                        band_freq = self.equalizer.get_band_frequency(i)
                        diff = abs(band_freq - freq)
                        if diff < smallest_diff:
                            smallest_diff = diff
                            closest_band = i

                # Convert slider value (-20 to 20) to VLC amplitude (-20.0 to 20.0 dB)
                amp = float(value)
                self.equalizer.set_amp_at_index(amp, closest_band)
                
                # Apply the equalizer to the media player
                if hasattr(self.mediaplayer, 'set_equalizer'):
                    self.mediaplayer.set_equalizer(self.equalizer)
                
        except Exception as e:
            print(f"Warning: Could not adjust equalizer: {str(e)}")

    def updateSubtitleTracks(self):
        self.subtitle_panel.track_combo.clear()
        self.subtitle_panel.track_combo.addItem("Disabled")
        
        if self.mediaplayer.video_get_spu_count() > 0:
            description = self.mediaplayer.video_get_spu_description()
            if description:
                for d in description:
                    self.subtitle_panel.track_combo.addItem(d.decode())
                    
    def setSubtitleTrack(self, index):
        if index == 0:
            self.mediaplayer.video_set_spu(-1)
        else:
            self.mediaplayer.video_set_spu(index - 1)
            
    def loadExternalSubtitles(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Subtitles",
                                                "", "Subtitle Files (*.srt *.ass *.ssa)")
        if filename:
            self.mediaplayer.video_set_subtitle_file(filename)
            self.updateSubtitleTracks()
            
    def selectSubtitleFont(self):
        font, ok = QFontDialog.getFont(self.subtitle_font, self)
        if ok:
            self.subtitle_font = font
            # Try to apply font settings to VLC subtitles if supported
            try:
                if hasattr(self.mediaplayer, 'video_set_subtitle_text_scale'):
                    self.mediaplayer.video_set_subtitle_text_scale(font.pointSize() / 12.0)
            except Exception as e:
                print(f"Warning: Could not set subtitle font scale: {str(e)}")
            
    def setSubtitleDelay(self, delay):
        self.mediaplayer.video_set_spu_delay(delay * 1000)  # Convert to microseconds

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = RhythmsPlayer()
    player.show()
    sys.exit(app.exec()) 