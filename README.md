# Student Course Management System (SCMS)

A lightweight, high-performance course registration and academic tracking system built for **COS 201: Computer Programming II** lab assessment at Miva Open University.

This application runs in **dual-modes**: a sleek, modern **Web Dashboard GUI** (with glassmorphism styling) and an interactive **Console CLI**.

---

## 🚀 Key Features

1. **Add Course**: Register courses with Course Code, Course Title, and Credit Units.
2. **View All Courses**: View a formatted data grid of all registered courses with active count indicators.
3. **Search Courses (Case-Insensitive Substring)**: Recursively traverses the course registry array to find matches on both *Course Code* and *Course Title* (e.g., searching `COS` or `101` matches `COS101`).
4. **Compute Semester Credit Units**: Recursively sums the credit units of all courses.
5. **Edit Course**: Update details (code, title, units) of any registered course (propagates to database and memory).
6. **Delete Course**: Remove any course from memory and persistent storage.
7. **Save to File**: Exports the active registry to a structured JSON file.
8. **Load from File**: Imports courses from a JSON file, merges them into the SQLite database, and refreshes the system.
9. **Data Persistence**: Backed by a local SQLite database (`courses.db`) that synchronizes with memory states automatically.

---

## 🛠️ Technology Stack & Architecture

- **Backend**: Python 3.12+ (Standard libraries only: `sqlite3`, `http.server`, `json`, `urllib.parse`, `webbrowser`)
- **Frontend**: Vanilla HTML5, Vanilla CSS3 (modern responsive design, Glassmorphism, HSL indigo-teal styling), Vanilla ES6 JavaScript (Asynchronous fetch REST API integration, modal state transitions, toast alerts)
- **Database**: SQLite3 for persistent local records
- **Design Philosophy**: Minimal external imports, native recursive array traversal algorithms, and clean separation of concerns.

---

## ⚙️ Quick Start

No external dependencies are required. Just run python directly:

### 1. Launch Web GUI Mode (Default)
Runs a local server and automatically launches the web interface in your default browser:
```powershell
python main.py
```
*Access manually at:* [http://localhost:8000](http://localhost:8000)

### 2. Launch Console CLI Mode
Runs the interactive command-line interface in your terminal:
```powershell
python main.py --console
```

---

## 🧪 Running Automated Tests

Run the built-in test suites to verify functionality:

### Unit & Algorithmic Tests
Verifies recursive search/sum unit logic:
```powershell
python C:\Users\otito\.gemini\antigravity\brain\2375a55b-7814-4066-b09b-24de8b2ce1a1\scratch\verify_app.py
```

### Integration & API Tests
Verifies the HTTP server routing, JSON payloads, and REST endpoints:
```powershell
python C:\Users\otito\.gemini\antigravity\brain\2375a55b-7814-4066-b09b-24de8b2ce1a1\scratch\test_api.py
```

---

## 📁 File Structure

- `main.py`: Contains models (`Course`), controllers (`CourseManager`), HTTP routing logic, and the Console CLI loop.
- `frontend/`:
  - `index.html`: Web structure, input forms, cards, and modal dialogs.
  - `styles.css`: Glassmorphism styles, dark theme variables, responsive design, and animations.
  - `app.js`: DOM event listeners, AJAX fetch operations, and UI rendering algorithms.
- `courses.db`: Local SQLite database (auto-generated).
- `courses.json`: Exported data registry format (auto-generated).
