# Bilingual Lesson Planner - Frontend

Modern desktop application built with Tauri + React + TypeScript for generating bilingual weekly lesson plans.

## Features

- **Multi-User Support**: Switch between different user profiles (Wilson Rodrigues, Daniela Silva)
- **Variable Slot Configuration**: Configure 1-10 class slots per user (not fixed at 6)
- **Drag & Drop Reordering**: Easily reorder slots to control output sequence
- **Real-Time Progress**: SSE-based progress streaming during batch processing
- **Grade-Aware Processing**: Automatic adaptation based on grade level (K-12)
- **Plan History**: View and download previously generated lesson plans

## Technology Stack

- **Frontend Framework**: React 18 + TypeScript
- **Desktop Framework**: Tauri 1.5
- **Styling**: TailwindCSS + Custom UI Components
- **State Management**: Zustand
- **Drag & Drop**: @dnd-kit
- **HTTP Client**: Axios
- **Build Tool**: Vite

## Prerequisites

- Node.js 18+ and npm
- Rust 1.70+ (for Tauri)
- Python 3.11+ (for backend)

## Installation

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Backend Server

The frontend requires the FastAPI backend to be running on `http://localhost:8000`.

```bash
# From project root
cd ..
python -m uvicorn backend.api:app --reload
```

### 3. Run Development Server

```bash
npm run tauri:dev
```

This will:
- Start Vite dev server on port 1420
- Launch Tauri desktop application
- Enable hot-reload for development

## Building for Production

### Build Desktop Application

```bash
npm run tauri:build
```

This creates:
- Windows: `.exe` installer in `src-tauri/target/release/bundle/`
- Standalone executable in `src-tauri/target/release/`

### Build Web Assets Only

```bash
npm run build
```

Output: `dist/` directory

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # Reusable UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Select.tsx
│   │   │   ├── Label.tsx
│   │   │   ├── Alert.tsx
│   │   │   └── Progress.tsx
│   │   ├── UserSelector.tsx      # User management
│   │   ├── SlotConfigurator.tsx  # Slot configuration with drag-drop
│   │   ├── BatchProcessor.tsx    # Week processing with SSE
│   │   └── PlanHistory.tsx       # Generated plans list
│   ├── lib/
│   │   ├── api.ts           # API client and types
│   │   └── utils.ts         # Utility functions
│   ├── store/
│   │   └── useStore.ts      # Zustand state management
│   ├── App.tsx              # Main application
│   ├── main.tsx             # React entry point
│   └── index.css            # Global styles
├── src-tauri/
│   ├── src/
│   │   └── main.rs          # Tauri Rust entry point
│   ├── Cargo.toml           # Rust dependencies
│   └── tauri.conf.json      # Tauri configuration
├── index.html
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

## Key Components

### UserSelector
- Lists available users
- Create new user profiles
- Switch between users
- Loads user's slots and plans on selection

### SlotConfigurator
- Add/remove slots (1-10 per user)
- Configure teacher name, subject, grade, homeroom
- Drag & drop to reorder slots
- Real-time updates to backend

### BatchProcessor
- Input week date range (MM-DD-MM-DD format)
- Process all configured slots
- Real-time progress via SSE
- Download generated DOCX file
- Error handling with partial success support

### PlanHistory
- View all generated plans
- Download previous plans
- Status indicators (completed/failed/processing)

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000/api`:

- `GET /api/users` - List users
- `POST /api/users` - Create user
- `GET /api/users/{id}/slots` - Get user's slots
- `POST /api/users/{id}/slots` - Create slot
- `PUT /api/slots/{id}` - Update slot
- `DELETE /api/slots/{id}` - Delete slot
- `POST /api/process-week` - Process batch
- `GET /api/progress/{task_id}` - SSE progress stream

## Configuration

### Backend URL

Edit `src/lib/api.ts` to change the backend URL:

```typescript
const API_BASE_URL = 'http://localhost:8000/api';
```

### Tauri Permissions

Edit `src-tauri/tauri.conf.json` to modify:
- Window size and behavior
- HTTP scope (allowed domains)
- File system access
- Dialog permissions

## Development Tips

### Hot Reload
- React components hot-reload automatically
- Rust changes require restart (`npm run tauri:dev`)

### Debugging
- React DevTools: Available in development
- Console logs: Open DevTools in Tauri window (F12)
- Rust logs: Check terminal output

### State Management
- Global state: `useStore` hook (Zustand)
- Local state: React `useState`
- API calls: Direct axios calls with error handling

## Troubleshooting

### Backend Connection Failed
- Ensure backend is running on port 8000
- Check CORS configuration in backend
- Verify API_BASE_URL in `src/lib/api.ts`

### Build Errors
- Clear node_modules: `rm -rf node_modules && npm install`
- Clear Rust cache: `cd src-tauri && cargo clean`
- Update dependencies: `npm update`

### Drag & Drop Not Working
- Ensure @dnd-kit packages are installed
- Check browser console for errors
- Verify slot IDs are unique

## Performance

- **Initial Load**: < 2 seconds
- **Slot Reordering**: Instant (optimistic updates)
- **Batch Processing**: Depends on slot count and LLM speed
- **Memory Usage**: ~150MB typical

## Security

- **API Keys**: Stored in backend .env file (not in frontend)
- **CORS**: Restricted to localhost
- **File Access**: Limited to user documents folder
- **HTTP Scope**: Only localhost:8000 allowed

## License

Internal use only - Bilingual Lesson Planner Team
