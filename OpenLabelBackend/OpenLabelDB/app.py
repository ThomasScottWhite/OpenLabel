import os
import sys
import json
from datetime import datetime
from pyfiglet import Figlet
from tabulate import tabulate
import getpass
from bson.objectid import ObjectId

# Import managers
from config import MONGO_URI, DATABASE_NAME
from managers.db_manager import MongoDBManager
from managers.user_manager import UserManager
from managers.project_manager import ProjectManager
from managers.annotation_manager import AnnotationManager
from managers.export_manager import ExportManager

# Initialize managers
db_manager = MongoDBManager(MONGO_URI, DATABASE_NAME)
user_manager = UserManager(db_manager)
project_manager = ProjectManager(db_manager)
annotation_manager = AnnotationManager(db_manager)
export_manager = ExportManager(db_manager)

# Initialize roles
db_manager.initialize_roles()

# Global session state
current_user = None
current_project = None

# Helper functions
def print_header(text):
    """Print a header with a divider"""
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80)

def print_success(text):
    """Print a success message"""
    print(f"\n✅ {text}")

def print_error(text):
    """Print an error message"""
    print(f"\n❌ {text}")

def print_info(text):
    """Print an info message"""
    print(f"\nℹ️ {text}")

def object_id_to_str(obj):
    """Convert ObjectId to string in a dictionary"""
    if isinstance(obj, dict):
        return {k: object_id_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [object_id_to_str(i) for i in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return obj

def format_datetime(dt):
    """Format datetime object"""
    if dt is None:
        return "Never"
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# Menu functions
def main_menu():
    """Display main menu"""
    while True:
        print_header("OPENLABEL DATABASE TESTING INTERFACE")
        
        if current_user:
            user_role = db_manager.db.roles.find_one({"_id": current_user["roleId"]})
            print(f"Logged in as: {current_user['username']} (Role: {user_role['name']})")
        else:
            print("Not logged in")
        
        if current_project:
            print(f"Current project: {current_project['name']}")
        
        print("\nMAIN MENU:")
        print("1. User Management")
        print("2. Project Management")
        print("3. Annotation Management")
        print("4. Export Management")
        print("0. Exit")
        
        choice = input("\nEnter your choice: ")
        
        if choice == "1":
            user_menu()
        elif choice == "2":
            project_menu()
        elif choice == "3":
            if not current_user:
                print_error("You must log in first")
                continue
            if not current_project:
                print_error("You must select a project first")
                continue
            annotation_menu()
        elif choice == "4":
            if not current_user:
                print_error("You must log in first")
                continue
            if not current_project:
                print_error("You must select a project first")
                continue
            export_menu()
        elif choice == "0":
            print("Goodbye!")
            sys.exit(0)
        else:
            print_error("Invalid choice")

def user_menu():
    """Display user management menu"""
    global current_user
    
    while True:
        print_header("USER MANAGEMENT")
        
        print("\nUSER MENU:")
        print("1. Register new user")
        print("2. Login")
        print("3. List users")
        print("4. Update current user")
        print("5. View user preferences")
        print("6. Update user preferences")
        print("0. Back to main menu")
        
        choice = input("\nEnter your choice: ")
        
        if choice == "1":
            # Register new user
            try:
                username = input("Username: ")
                email = input("Email: ")
                password = getpass.getpass("Password: ")
                first_name = input("First name: ")
                last_name = input("Last name: ")
                
                print("\nAvailable roles:")
                roles = list(db_manager.db.roles.find())
                for i, role in enumerate(roles):
                    print(f"{i+1}. {role['name']}")
                
                role_choice = int(input("\nSelect role (number): ")) - 1
                role_name = roles[role_choice]["name"]
                
                user_id = user_manager.create_user(
                    username, email, password, first_name, last_name, role_name
                )
                
                print_success(f"User created with ID: {user_id}")
            except Exception as e:
                print_error(f"Error creating user: {str(e)}")
        
        elif choice == "2":
            # Login
            try:
                username = input("Username: ")
                password = getpass.getpass("Password: ")
                
                user = user_manager.authenticate_user(username, password)
                
                if user:
                    current_user = user
                    print_success(f"Logged in as {username}")
                else:
                    print_error("Invalid username or password")
            except Exception as e:
                print_error(f"Error logging in: {str(e)}")
        
        elif choice == "3":
            # List users
            try:
                users = user_manager.get_users()
                
                if not users:
                    print_info("No users found")
                    continue
                
                table_data = []
                for user in users:
                    role = db_manager.db.roles.find_one({"_id": user["roleId"]})
                    role_name = role["name"] if role else "Unknown"
                    
                    table_data.append([
                        str(user["_id"]),
                        user["username"],
                        user["email"],
                        f"{user['firstName']} {user['lastName']}",
                        role_name,
                        format_datetime(user.get("lastLogin"))
                    ])
                
                headers = ["ID", "Username", "Email", "Name", "Role", "Last Login"]
                print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))
                
            except Exception as e:
                print_error(f"Error listing users: {str(e)}")
        
        elif choice == "4":
            # Update current user
            if not current_user:
                print_error("You must log in first")
                continue
                
            try:
                print("\nUpdate user information (leave blank to keep current value)")
                
                email = input(f"Email [{current_user['email']}]: ")
                password = getpass.getpass("New Password (leave blank to keep current): ")
                first_name = input(f"First name [{current_user['firstName']}]: ")
                last_name = input(f"Last name [{current_user['lastName']}]: ")
                
                update_data = {}
                
                if email:
                    update_data["email"] = email
                if password:
                    update_data["password"] = password
                if first_name:
                    update_data["firstName"] = first_name
                if last_name:
                    update_data["lastName"] = last_name
                
                if update_data:
                    success = user_manager.update_user(current_user["_id"], update_data)
                    
                    if success:
                        print_success("User updated successfully")
                        # Refresh current user
                        current_user = user_manager.get_user_by_id(current_user["_id"])
                    else:
                        print_error("Failed to update user")
                else:
                    print_info("No changes to update")
                
            except Exception as e:
                print_error(f"Error updating user: {str(e)}")
        
        elif choice == "5":
            # View user preferences
            if not current_user:
                print_error("You must log in first")
                continue
                
            try:
                preferences = user_manager.get_user_preferences(current_user["_id"])
                
                if not preferences:
                    print_info("No preferences found")
                    continue
                
                print_header("USER PREFERENCES")
                
                print("\nKeyboard Shortcuts:")
                for key, value in preferences["keyboardShortcuts"].items():
                    print(f"  {key}: {value}")
                
                print("\nUI Preferences:")
                for key, value in preferences["uiPreferences"].items():
                    print(f"  {key}: {value}")
                
            except Exception as e:
                print_error(f"Error getting preferences: {str(e)}")
        
        elif choice == "6":
            # Update user preferences
            if not current_user:
                print_error("You must log in first")
                continue
                
            try:
                preferences = user_manager.get_user_preferences(current_user["_id"])
                
                if not preferences:
                    print_error("No preferences found")
                    continue
                
                print("\nUpdate UI preferences (leave blank to keep current value)")
                
                theme = input(f"Theme [{preferences['uiPreferences']['theme']}]: ")
                language = input(f"Language [{preferences['uiPreferences']['language']}]: ")
                color = input(f"Annotation Default Color [{preferences['uiPreferences']['annotationDefaultColor']}]: ")
                
                updates = {}
                
                if theme or language or color:
                    ui_updates = {}
                    if theme:
                        ui_updates["theme"] = theme
                    if language:
                        ui_updates["language"] = language
                    if color:
                        ui_updates["annotationDefaultColor"] = color
                    
                    updates["uiPreferences"] = ui_updates
                
                if updates:
                    success = user_manager.update_user_preferences(
                        current_user["_id"], updates
                    )
                    
                    if success:
                        print_success("Preferences updated successfully")
                    else:
                        print_error("Failed to update preferences")
                else:
                    print_info("No changes to update")
                
            except Exception as e:
                print_error(f"Error updating preferences: {str(e)}")
        
        elif choice == "0":
            # Back to main menu
            return
        
        else:
            print_error("Invalid choice")

def project_menu():
    """Display project management menu"""
    global current_project
    
    while True:
        print_header("PROJECT MANAGEMENT")
        
        print("\nPROJECT MENU:")
        print("1. Create new project")
        print("2. List projects")
        print("3. Select project")
        print("4. Update current project")
        print("5. View project members")
        print("6. Add project member")
        print("0. Back to main menu")
        
        choice = input("\nEnter your choice: ")
        
        if choice == "1":
            # Create new project
            if not current_user:
                print_error("You must log in first")
                continue
                
            try:
                name = input("Project name: ")
                description = input("Description: ")
                is_public = input("Public project? (y/n): ").lower() == 'y'
                
                print("\nAnnotation types (comma-separated):")
                print("Available types: boundingBox, polygon, segmentation")
                annotation_types_input = input("Types [boundingBox,polygon]: ")
                
                annotation_types = ["boundingBox", "polygon"]
                if annotation_types_input:
                    annotation_types = [t.strip() for t in annotation_types_input.split(",")]
                
                project_id = project_manager.create_project(
                    name, description, current_user["_id"], is_public, annotation_types
                )
                
                print_success(f"Project created with ID: {project_id}")
                
                # Set as current project
                current_project = project_manager.get_project_by_id(project_id)
                
            except Exception as e:
                print_error(f"Error creating project: {str(e)}")
        
        elif choice == "2":
            # List projects
            if not current_user:
                print_error("You must log in first")
                continue
                
            try:
                projects = project_manager.get_projects_by_user(current_user["_id"])
                
                if not projects:
                    print_info("No projects found")
                    continue
                
                table_data = []
                for project in projects:
                    # Get creator name
                    creator = user_manager.get_user_by_id(project["createdBy"])
                    creator_name = creator["username"] if creator else "Unknown"
                    
                    # Get member count
                    member_count = len(project["members"])
                    
                    # Check if this is the current project
                    is_current = current_project and current_project["_id"] == project["_id"]
                    
                    table_data.append([
                        str(project["_id"]),
                        project["name"],
                        project["description"][:30] + "..." if len(project["description"]) > 30 else project["description"],
                        creator_name,
                        member_count,
                        format_datetime(project["createdAt"]),
                        "✓" if is_current else ""
                    ])
                
                headers = ["ID", "Name", "Description", "Creator", "Members", "Created", "Current"]
                print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))
                
            except Exception as e:
                print_error(f"Error listing projects: {str(e)}")
        
        elif choice == "3":
            # Select project
            if not current_user:
                print_error("You must log in first")
                continue
                
            try:
                projects = project_manager.get_projects_by_user(current_user["_id"])
                
                if not projects:
                    print_info("No projects found")
                    continue
                
                print("\nAvailable projects:")
                for i, project in enumerate(projects):
                    print(f"{i+1}. {project['name']}")
                
                project_choice = int(input("\nSelect project (number): ")) - 1
                selected_project = projects[project_choice]
                
                current_project = selected_project
                print_success(f"Selected project: {current_project['name']}")
                
            except Exception as e:
                print_error(f"Error selecting project: {str(e)}")
        
        elif choice == "4":
            # Update current project
            if not current_user:
                print_error("You must log in first")
                continue
                
            if not current_project:
                print_error("No project selected")
                continue
                
            try:
                print("\nUpdate project information (leave blank to keep current value)")
                
                name = input(f"Name [{current_project['name']}]: ")
                description = input(f"Description [{current_project['description']}]: ")
                is_public = input(f"Public project? (y/n) [{'y' if current_project['settings']['isPublic'] else 'n'}]: ")
                
                update_data = {}
                settings_update = {}
                
                if name:
                    update_data["name"] = name
                if description:
                    update_data["description"] = description
                if is_public:
                    settings_update["isPublic"] = is_public.lower() == 'y'
                
                if settings_update:
                    update_data["settings"] = settings_update
                
                if update_data:
                    success = project_manager.update_project(
                        current_project["_id"], update_data, current_user["_id"]
                    )
                    
                    if success:
                        print_success("Project updated successfully")
                        # Refresh current project
                        current_project = project_manager.get_project_by_id(current_project["_id"])
                    else:
                        print_error("Failed to update project")
                else:
                    print_info("No changes to update")
                
            except Exception as e:
                print_error(f"Error updating project: {str(e)}")
        
        elif choice == "5":
            # View project members
            if not current_user:
                print_error("You must log in first")
                continue
                
            if not current_project:
                print_error("No project selected")
                continue
                
            try:
                members = project_manager.get_project_members(current_project["_id"])
                
                if not members:
                    print_info("No members found")
                    continue
                
                table_data = []
                for member in members:
                    table_data.append([
                        str(member["userId"]),
                        member["username"],
                        member["roleName"],
                        format_datetime(member["joinedAt"])
                    ])
                
                headers = ["User ID", "Username", "Role", "Joined"]
                print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))
                
            except Exception as e:
                print_error(f"Error listing members: {str(e)}")
        
        elif choice == "6":
            # Add project member
            if not current_user:
                print_error("You must log in first")
                continue
                
            if not current_project:
                print_error("No project selected")
                continue
                
            try:
                # List available users
                all_users = user_manager.get_users()
                
                # Filter out users already in the project
                project_members = project_manager.get_project_members(current_project["_id"])
                project_user_ids = [str(member["userId"]) for member in project_members]
                
                available_users = [u for u in all_users if str(u["_id"]) not in project_user_ids]
                
                if not available_users:
                    print_info("No available users to add")
                    continue
                
                print("\nAvailable users:")
                for i, user in enumerate(available_users):
                    print(f"{i+1}. {user['username']} ({user['email']})")
                
                user_choice = int(input("\nSelect user (number): ")) - 1
                selected_user = available_users[user_choice]
                
                # Available roles
                print("\nAvailable roles:")
                roles = list(db_manager.db.roles.find())
                for i, role in enumerate(roles):
                    print(f"{i+1}. {role['name']}")
                
                role_choice = int(input("\nSelect role (number): ")) - 1
                role_name = roles[role_choice]["name"]
                
                success = project_manager.add_project_member(
                    current_project["_id"], selected_user["_id"], 
                    role_name, current_user["_id"]
                )
                
                if success:
                    print_success(f"Added {selected_user['username']} to project with role {role_name}")
                else:
                    print_error("Failed to add member")
                
            except Exception as e:
                print_error(f"Error adding member: {str(e)}")
        
        elif choice == "0":
            # Back to main menu
            return
        
        else:
            print_error("Invalid choice")

def annotation_menu():
    """Display annotation management menu"""
    while True:
        print_header("ANNOTATION MANAGEMENT")
        
        print("\nANNOTATION MENU:")
        print("1. Create mock image")
        print("2. List images")
        print("3. Create bounding box annotation")
        print("4. Create polygon annotation")
        print("5. List annotations for an image")
        print("6. List all annotations in project")
        print("7. Update annotation")
        print("8. Delete annotation")
        print("0. Back to main menu")
        
        choice = input("\nEnter your choice: ")
        
        if choice == "1":
            # Create mock image
            try:
                filename = input("Image filename (e.g., test.jpg): ")
                width = int(input("Width (pixels): "))
                height = int(input("Height (pixels): "))
                
                image_id = annotation_manager.create_mock_image(
                    current_project["_id"], filename, width, height, current_user["_id"]
                )
                
                print_success(f"Mock image created with ID: {image_id}")
                
            except Exception as e:
                print_error(f"Error creating mock image: {str(e)}")
        
        elif choice == "2":
            # List images
            try:
                images = annotation_manager.get_images_by_project(current_project["_id"])
                
                if not images:
                    print_info("No images found in this project")
                    continue
                
                table_data = []
                for image in images:
                    # Get annotation count
                    annotation_count = db_manager.db.annotations.count_documents({
                        "imageId": image["_id"]
                    })
                    
                    table_data.append([
                        str(image["_id"]),
                        image["filename"],
                        f"{image['width']}x{image['height']}",
                        image["status"],
                        annotation_count,
                        format_datetime(image["uploadedAt"])
                    ])
                
                headers = ["ID", "Filename", "Dimensions", "Status", "Annotations", "Uploaded"]
                print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))
                
            except Exception as e:
                print_error(f"Error listing images: {str(e)}")
        
        elif choice == "3":
            # Create bounding box annotation
            try:
                # List available images
                images = annotation_manager.get_images_by_project(current_project["_id"])
                
                if not images:
                    print_info("No images found in this project")
                    continue
                
                print("\nAvailable images:")
                for i, image in enumerate(images):
                    print(f"{i+1}. {image['filename']} ({image['width']}x{image['height']})")
                
                image_choice = int(input("\nSelect image (number): ")) - 1
                selected_image = images[image_choice]
                
                # Get bounding box coordinates
                print(f"\nImage dimensions: {selected_image['width']}x{selected_image['height']}")
                print("Enter bounding box coordinates:")
                
                x = int(input("X position: "))
                y = int(input("Y position: "))
                width = int(input("Width: "))
                height = int(input("Height: "))
                
                # Get label
                label = input("Object label (e.g., car, person): ")
                
                coordinates = {
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height
                }
                
                annotation_id = annotation_manager.create_bounding_box(
                    selected_image["_id"], current_project["_id"], 
                    label, coordinates, current_user["_id"]
                )
                
                print_success(f"Bounding box annotation created with ID: {annotation_id}")
                
            except Exception as e:
                print_error(f"Error creating annotation: {str(e)}")
        
        elif choice == "4":
            # Create polygon annotation
            try:
                # List available images
                images = annotation_manager.get_images_by_project(current_project["_id"])
                
                if not images:
                    print_info("No images found in this project")
                    continue
                
                print("\nAvailable images:")
                for i, image in enumerate(images):
                    print(f"{i+1}. {image['filename']} ({image['width']}x{image['height']})")
                
                image_choice = int(input("\nSelect image (number): ")) - 1
                selected_image = images[image_choice]
                
                # Get polygon points
                print(f"\nImage dimensions: {selected_image['width']}x{selected_image['height']}")
                print("Enter polygon points (minimum 3):")
                
                points = []
                point_count = int(input("Number of points: "))
                
                for i in range(point_count):
                    x = int(input(f"Point {i+1} X: "))
                    y = int(input(f"Point {i+1} Y: "))
                    points.append({"x": x, "y": y})
                
                # Get label
                label = input("Object label (e.g., car, person): ")
                
                annotation_id = annotation_manager.create_polygon(
                    selected_image["_id"], current_project["_id"], 
                    label, points, current_user["_id"]
                )
                
                print_success(f"Polygon annotation created with ID: {annotation_id}")
                
            except Exception as e:
                print_error(f"Error creating annotation: {str(e)}")
        
        elif choice == "5":
            # List annotations for an image
            try:
                # List available images
                images = annotation_manager.get_images_by_project(current_project["_id"])
                
                if not images:
                    print_info("No images found in this project")
                    continue
                
                print("\nAvailable images:")
                for i, image in enumerate(images):
                    print(f"{i+1}. {image['filename']} ({image['width']}x{image['height']})")
                
                image_choice = int(input("\nSelect image (number): ")) - 1
                selected_image = images[image_choice]
                
                annotations = annotation_manager.get_annotations_by_image(selected_image["_id"])
                
                if not annotations:
                    print_info(f"No annotations found for {selected_image['filename']}")
                    continue
                
                table_data = []
                for ann in annotations:
                    creator = user_manager.get_user_by_id(ann["createdBy"])
                    creator_name = creator["username"] if creator else "Unknown"
                    
                    coordinates_str = ""
                    if ann["type"] == "boundingBox":
                        c = ann["coordinates"]
                        coordinates_str = f"x:{c['x']}, y:{c['y']}, w:{c['width']}, h:{c['height']}"
                    elif ann["type"] == "polygon":
                        points = ann["coordinates"]["points"]
                        coordinates_str = f"{len(points)} points"
                    
                    table_data.append([
                        str(ann["_id"]),
                        ann["type"],
                        ann["label"],
                        coordinates_str,
                        creator_name,
                        format_datetime(ann["createdAt"])
                    ])
                
                headers = ["ID", "Type", "Label", "Coordinates", "Creator", "Created"]
                print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))
                
            except Exception as e:
                print_error(f"Error listing annotations: {str(e)}")
        
        elif choice == "6":
            # List all annotations in project
            try:
                annotations = annotation_manager.get_annotations_by_project(current_project["_id"])
                
                if not annotations:
                    print_info("No annotations found in this project")
                    continue
                
                table_data = []
                for ann in annotations:
                    # Get image
                    image = db_manager.db.images.find_one({"_id": ann["imageId"]})
                    image_name = image["filename"] if image else "Unknown"
                    
                    creator = user_manager.get_user_by_id(ann["createdBy"])
                    creator_name = creator["username"] if creator else "Unknown"
                    
                    table_data.append([
                        str(ann["_id"])[:8] + "...",  # Truncated ID
                        image_name,
                        ann["type"],
                        ann["label"],
                        creator_name,
                        format_datetime(ann["createdAt"])
                    ])
                
                headers = ["ID", "Image", "Type", "Label", "Creator", "Created"]
                print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))
                
                print(f"\nTotal annotations: {len(annotations)}")
                
            except Exception as e:
                print_error(f"Error listing annotations: {str(e)}")
        
        elif choice == "7":
            # Update annotation
            try:
                # List available images
                images = annotation_manager.get_images_by_project(current_project["_id"])
                
                if not images:
                    print_info("No images found in this project")
                    continue
                
                print("\nAvailable images:")
                for i, image in enumerate(images):
                    print(f"{i+1}. {image['filename']} ({image['width']}x{image['height']})")
                
                image_choice = int(input("\nSelect image (number): ")) - 1
                selected_image = images[image_choice]
                
                annotations = annotation_manager.get_annotations_by_image(selected_image["_id"])
                
                if not annotations:
                    print_info(f"No annotations found for {selected_image['filename']}")
                    continue
                
                print("\nAvailable annotations:")
                for i, ann in enumerate(annotations):
                    print(f"{i+1}. {ann['type']} - {ann['label']}")
                
                ann_choice = int(input("\nSelect annotation (number): ")) - 1
                selected_ann = annotations[ann_choice]
                
                # Update options
                print("\nUpdate annotation (leave blank to keep current value)")
                
                label = input(f"Label [{selected_ann['label']}]: ")
                
                update_data = {}
                
                if label:
                    update_data["label"] = label
                
                if update_data:
                    success = annotation_manager.update_annotation(
                        selected_ann["_id"], update_data, current_user["_id"]
                    )
                    
                    if success:
                        print_success("Annotation updated successfully")
                    else:
                        print_error("Failed to update annotation")
                else:
                    print_info("No changes to update")
                
            except Exception as e:
                print_error(f"Error updating annotation: {str(e)}")
        
        elif choice == "8":
            # Delete annotation
            try:
                # List available images
                images = annotation_manager.get_images_by_project(current_project["_id"])
                
                if not images:
                    print_info("No images found in this project")
                    continue
                
                print("\nAvailable images:")
                for i, image in enumerate(images):
                    print(f"{i+1}. {image['filename']} ({image['width']}x{image['height']})")
                
                image_choice = int(input("\nSelect image (number): ")) - 1
                selected_image = images[image_choice]
                
                annotations = annotation_manager.get_annotations_by_image(selected_image["_id"])
                
                if not annotations:
                    print_info(f"No annotations found for {selected_image['filename']}")
                    continue
                
                print("\nAvailable annotations:")
                for i, ann in enumerate(annotations):
                    print(f"{i+1}. {ann['type']} - {ann['label']}")
                
                ann_choice = int(input("\nSelect annotation to delete (number): ")) - 1
                selected_ann = annotations[ann_choice]
                
                confirm = input(f"\nAre you sure you want to delete this {selected_ann['type']} annotation? (y/n): ")
                
                if confirm.lower() == 'y':
                    success = annotation_manager.delete_annotation(
                        selected_ann["_id"], current_user["_id"]
                    )
                    
                    if success:
                        print_success("Annotation deleted successfully")
                    else:
                        print_error("Failed to delete annotation")
                else:
                    print_info("Deletion cancelled")
                
            except Exception as e:
                print_error(f"Error deleting annotation: {str(e)}")
        
        elif choice == "0":
            # Back to main menu
            return
        
        else:
            print_error("Invalid choice")

def export_menu():
    """Display export management menu"""
    while True:
        print_header("EXPORT MANAGEMENT")
        
        print("\nEXPORT MENU:")
        print("1. Export annotations in COCO format")
        print("2. Export annotations in YOLO format")
        print("0. Back to main menu")
        
        choice = input("\nEnter your choice: ")
        
        if choice == "1":
            # Export COCO
            try:
                coco_data = export_manager.export_coco(current_project["_id"])
                
                output_file = input("Output JSON file name [coco_export.json]: ")
                if not output_file:
                    output_file = "coco_export.json"
                
                # Ensure file has .json extension
                if not output_file.endswith(".json"):
                    output_file += ".json"
                
                with open(output_file, "w") as f:
                    json.dump(object_id_to_str(coco_data), f, indent=2)
                
                print_success(f"Exported COCO annotations to {output_file}")
                print(f"  Total images: {len(coco_data['images'])}")
                print(f"  Total annotations: {len(coco_data['annotations'])}")
                print(f"  Total categories: {len(coco_data['categories'])}")
                
            except Exception as e:
                print_error(f"Error exporting COCO: {str(e)}")
        
        elif choice == "2":
            # Export YOLO
            try:
                yolo_data = export_manager.export_yolo(current_project["_id"])
                
                output_dir = input("Output directory [yolo_export]: ")
                if not output_dir:
                    output_dir = "yolo_export"
                
                # Create directory if it doesn't exist
                os.makedirs(output_dir, exist_ok=True)
                
                # Write classes file
                with open(os.path.join(output_dir, "classes.txt"), "w") as f:
                    f.writelines(yolo_data["classes.txt"])
                
                # Write annotation files
                file_count = 0
                for filename, annotations in yolo_data.items():
                    if filename == "classes.txt":
                        continue
                    
                    # Create annotation file with same name but .txt extension
                    base_name = os.path.splitext(filename)[0]
                    ann_filename = base_name + ".txt"
                    
                    with open(os.path.join(output_dir, ann_filename), "w") as f:
                        for line in annotations:
                            f.write(line + "\n")
                    
                    file_count += 1
                
                print_success(f"Exported YOLO annotations to {output_dir}")
                print(f"  Classes file: classes.txt")
                print(f"  Annotation files: {file_count}")
                
            except Exception as e:
                print_error(f"Error exporting YOLO: {str(e)}")
        
        elif choice == "0":
            # Back to main menu
            return
        
        else:
            print_error("Invalid choice")

# Main entry point
if __name__ == "__main__":
    try:
        f = Figlet(font='slant')
        print(f.renderText('OpenLabel DB'))
        print("MongoDB Database Testing Interface")
        print(f"Connected to: {MONGO_URI}")
        print(f"Database: {DATABASE_NAME}")
        main_menu()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {str(e)}")