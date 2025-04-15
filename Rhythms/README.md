# Rhythms Media Player

A modern, feature-rich media player built with Python, VLC, and PyQt6. Rhythms offers a sleek dark interface with advanced playback controls, video adjustments, audio equalization, and subtitle support.


## Features

### Core Functionality
- 🎵 Play various audio and video formats (MP3, MP4, AVI, MKV, WAV, etc.)
- 📋 Playlist management with drag-and-drop support
- ⏯️ Basic controls (play, pause, stop, next, previous)
- 🔊 Volume control
- 🎚️ Seekbar for navigation
- 🔁 Multiple playback modes (Normal, Repeat One, Repeat All, Shuffle)
- 🎯 A-B repeat functionality

### Video Features
- 🎨 Video adjustments:
  - Contrast
  - Brightness
  - Hue
  - Saturation
  - Gamma
- 📺 Deinterlacing support
- 🖼️ Adjustable aspect ratio
- 🎬 Hardware acceleration support

### Audio Features
- 🎛️ 10-band equalizer
- 📊 Preset equalizer settings:
  - Flat
  - Classical
  - Rock
  - Pop
  - Jazz
  - Electronic

### Subtitle Support
- 📝 Load external subtitle files
- 🔤 Customizable subtitle font
- ⏱️ Adjustable subtitle delay
- 💬 Multiple subtitle track support

## Requirements

- Python 3.8 or higher
- VLC Media Player
- PyQt6
- python-vlc
- NumPy

## Installation

1. Clone the repository:
```bash
git clone https://github.com/MMHT2000/Rhythms-Music-Player.git
cd rhythms
```

2. Install required packages:
```bash
pip install PyQt6 python-vlc numpy
```

3. Ensure VLC Media Player is installed on your system:
- Windows: Download from [videolan.org](https://www.videolan.org/)
- Linux: `sudo apt-get install vlc`
- macOS: Download from [videolan.org](https://www.videolan.org/)

## Usage

Run the player:
```bash
python rhythms.py
```

### Keyboard Shortcuts
- Space: Play/Pause
- Ctrl+O: Open file
- Ctrl+L: Load subtitle file
- Ctrl+Q: Quit
- Right Arrow: Forward 5 seconds
- Left Arrow: Backward 5 seconds
- Up Arrow: Volume up
- Down Arrow: Volume down

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- VLC Media Player for the underlying media playback engine
- PyQt6 for the GUI framework
- All contributors and users of the project

## Support

If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/yourusername/rhythms/issues) page
2. Create a new issue with detailed information about your problem
3. Include your system information and steps to reproduce the issue

---

Made with ❤️ by [Your Name] 
