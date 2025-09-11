# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

social-auto-upload is a Python-based automation tool for uploading videos to multiple Chinese and international social media platforms (抖音, Bilibili, 小红书, 快手, 视频号, 百家号, TikTok). It features both web UI (Vue 3 + Flask) and CLI interfaces.

## Development Commands

### Backend Development
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers (required)
playwright install chromium firefox

# Configure environment
cp conf.example.py conf.py
# Edit conf.py to set LOCAL_CHROME_PATH to your Chrome installation

# Initialize database (if needed)
cd db && python createTable.py

# Run Flask backend server
python sau_backend.py  # Runs on http://localhost:5409

# Run CLI interface
python cli_main.py
```

### Frontend Development
```bash
cd sau_frontend
npm install
npm run dev     # Development server on http://localhost:5173
npm run build   # Production build
```

## Architecture Overview

### Technology Stack
- **Backend**: Python 3.10+, Flask, Playwright, SQLite, SQLAlchemy
- **Frontend**: Vue 3, Vite, Element Plus, Pinia, Vue Router
- **Browser Automation**: Playwright with stealth techniques
- **Database**: SQLite with two main tables (user_info, file_records)

### Core Components

**Uploader Modules** (`uploader/`): Platform-specific upload implementations
- Each platform has its own uploader directory (e.g., `douyin_uploader/`, `tk_uploader/`)
- Uploaders handle platform-specific authentication, file processing, and submission

**Backend API** (`sau_backend.py`): Flask server providing REST endpoints
- File upload endpoint with 160MB limit
- Cookie validation and management
- Video posting APIs for each platform
- CORS enabled for frontend communication

**Authentication** (`myUtils/`): Cookie-based authentication system
- `auth.py`: Cookie validation and management
- `login.py`: Platform-specific login automation (11,787 lines)
- Cookie files stored in `cookies/` directory (gitignored)

**Utilities** (`utils/`): Shared functionality
- `constant.py`: Platform constants and configurations (8,360 lines)
- `base_social_media.py`: Common social media platform definitions
- `stealth.min.js`: Browser stealth automation script

### Key Development Patterns

1. **Platform Integration**: Each platform has its own uploader module following similar patterns but with platform-specific implementations
2. **Cookie Management**: Authentication relies on cookie files stored locally, generated via platform-specific scripts in `examples/`
3. **File Organization**: Videos stored in `videoFile/` directory, cookies in `cookiesFile/` directory
4. **Scheduling**: Built-in cron-like scheduling functionality for timed uploads
5. **Error Handling**: Platform-specific error handling with retry mechanisms

### API Structure

Backend endpoints follow RESTful conventions:
- `/upload` - File upload
- `/api/login/*` - Platform authentication
- `/api/post/*` - Video posting operations
- `/api/validate/*` - Cookie validation

Frontend communicates via Axios with request/response interceptors for authentication.

## Important Configuration

**conf.py Requirements**:
- `LOCAL_CHROME_PATH`: Must be set to local Chrome installation path
- `XHS_SERVER`: Xiaohongshu server endpoint (default: http://127.0.0.1:11901)
- `BASE_DIR`: Project root directory (auto-configured)

**Required Directories**:
- `cookiesFile/`: Store cookie files (create if not exists)
- `videoFile/`: Store video files for upload (create if not exists)

## Platform-Specific Notes

- **TikTok**: Uses Firefox browser (legacy implementation)
- **Other platforms**: Use Chromium with stealth techniques
- **Authentication**: Each platform requires specific cookie generation scripts in `examples/`
- **File formats**: Primary support for .mp4 videos, some platforms support custom thumbnails (.png)
- **Scheduling**: Default scheduling calculates "next day" timing based on project background

## Development Workflow

1. **Adding New Platform**: Create new uploader module in `uploader/`, implement platform-specific authentication and upload logic
2. **Testing Upload**: Use example scripts in `examples/` directory for each platform
3. **Frontend Integration**: Add corresponding API calls and UI components in Vue frontend
4. **Database Updates**: Modify `db/createTable.py` if new data structures needed

## Security Considerations

- Cookie files contain sensitive authentication data - never commit to version control
- File upload limited to 160MB to prevent abuse
- CORS enabled for development - configure appropriately for production
- Browser automation uses stealth techniques to avoid detection