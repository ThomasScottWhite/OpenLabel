# OpenLabel Frontend

Frontend application for the OpenLabel

## Features

- React-based UI built with TypeScript and Bootstrap
- Multi-modal annotation support\*
  - Image classification
  - Object detection
  - Text classification
- Project management\*
  - Create and configure annotation projects
  - Track annotation progress
  - Upload files for annotation
  - Export annotations in standard formats

## Getting Started

### Prerequisites

- npm
- Backend server running (see the main project README)

### Installation

1. Clone the repository (if you haven't already)
2. Navigate to the OpenLabelFrontend directory:

```bash
cd OpenLabelFrontend
```

3. Install dependencies:

```bash
npm install
```

### Development

Run the development server:

```bash
npm run dev
```

This will start the Vite development server, usually at http://localhost:5173.

### Building for Production

```bash
npm run build
```

The build artifacts will be stored in the `dist/` directory.

## Project Structure

- `src/` - Source code
  - `annotators/` - Components for different annotation types
  - `App.tsx` - Main application component
  - `ProjectPage.tsx` - Project details and file management
  - `Projects.tsx` - Project listing and creation
  - `Annotator.tsx` - Main annotation interface
  - `Login.tsx` & `CreateAccount.tsx` - Authentication components
