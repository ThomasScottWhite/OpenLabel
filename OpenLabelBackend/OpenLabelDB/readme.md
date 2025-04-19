# OpenLabel - MongoDB Database Component

This is the MongoDB database implementation for our OpenLabel project, an open-source image annotation tool.

## What's This?
This code handles the database portion of our application, storing:
- User accounts and roles
- Projects and their settings
- Images (mock images for testing)
- Annotations (bounding boxes and polygons)
- Export formats (COCO, YOLO)

## File Structure
```
openlabel-db/
├── requirements.txt          # Python dependencies
├── config.py                 # MongoDB connection settings
├── app.py                    # Text interface for testing
├── managers/
│   ├── __init__.py           # Package initialization
│   ├── db_manager.py         # MongoDB connection
│   ├── user_manager.py       # User accounts
│   ├── project_manager.py    # Projects
│   ├── annotation_manager.py # Annotations
│   └── export_manager.py     # Format exports
└── tests/
    └── test_database.py      # Basic tests
```

## Quick Setup
1. Install MongoDB (local or cloud)
2. Create `.env` file:
   ```
   MONGO_URI=mongodb://localhost:27017
   DATABASE_NAME=openlabel_db
   ```
3. Install requirements:
   ```
   pip install -r requirements.txt
   ```
4. Run the test interface:
   ```
   python app.py
   ```

## What Each Manager Does
- **db_manager.py**: Sets up MongoDB connection and indexes
- **user_manager.py**: Handles users, authentication, preferences
- **project_manager.py**: Manages projects, team members, roles
- **annotation_manager.py**: Stores and retrieves annotations
- **export_manager.py**: Converts annotations to standard formats

## Testing Interface
The text interface in `app.py` lets you:
- Create/login to user accounts
- Create/edit projects
- Add test images
- Create annotations
- Export in different formats

This is just a proof-of-concept to verify the database implementation works correctly. The backend logic team will connect to these database managers to handle the actual application logic.