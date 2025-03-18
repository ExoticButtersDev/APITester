# API Tester

A cross-platform desktop application built with PyQt5 for testing REST APIs. Send HTTP requests, inspect responses (text, images, audio, files), and debug API interactions efficiently.

## Features

- **HTTP Methods**: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- **Headers Management**: Predefined/common headers or custom headers
- **Request Body**:
  - Raw text
  - Structured JSON editor with nested object/array support
- **Response Handling**:
  - Text/JSON pretty-printing
  - Image preview
  - Audio playback
  - File downloads
  - Debug info (headers, status codes, truncated body)
- Cross-platform compatibility (Windows, Linux, macOS)

## Installation

### Prerequisites
- Python 3.8+
- Windows: [Inno Setup](https://jrsoftware.org/isdl.php) (for building installer)

### Steps
1. Clone the repository:
2. Set up the virtual environment:
   Setup.bat
3. **Run the application**:
   Run.bat
4. *(Optional)* **Build executable**:
   Build.bat
5. *(Optional)* **Create installer** (Windows):
   - Compile `APITester.iss` using Inno Setup

## Usage

1. **Enter URL** and select HTTP method
2. **Headers**:
   - Use "Add Selected" for common headers
   - Use "Add Custom" for custom headers
3. **Body**:
   - Switch between *No Body*, *Text*, or *JSON* modes
   - For JSON: Add key-value pairs with type validation
4. Click **Send** to execute the request
5. View responses in tabs:
   - **Text**: Formatted JSON/text
   - **Image**: Preview of image responses
   - **Audio**: Play/pause audio files
   - **File**: Save binary responses
   - **Debug**: Request/response metadata

## Dependencies

- Python Packages (auto-installed by `Setup.bat`):
  - PyQt5==5.15.11
  - requests==2.32.
- Build Tools:
  - PyInstaller (auto-installed by `Build.bat`)
  - Inno Setup (for Windows installer)

## License

[MIT License](LICENSE)

---

**Contributions welcome!**  
Report issues or suggest features in the [GitHub Issues](https://github.com/ExoticButtersDev/APITester/issues) section.
