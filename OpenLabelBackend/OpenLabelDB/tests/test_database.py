import unittest
import os
import sys
import datetime
from bson.objectid import ObjectId
from pymongo import MongoClient
import bcrypt

# Add parent directory to path to import managers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from managers.db_manager import MongoDBManager
from managers.user_manager import UserManager
from managers.project_manager import ProjectManager
from managers.annotation_manager import AnnotationManager
from managers.export_manager import ExportManager

class TestDatabaseManagers(unittest.TestCase):
    """Test cases for the MongoDB managers"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database and managers"""
        # Use a test database
        cls.db_manager = MongoDBManager("mongodb://localhost:27017", "openlabel_test_db")
        cls.user_manager = UserManager(cls.db_manager)
        cls.project_manager = ProjectManager(cls.db_manager)
        cls.annotation_manager = AnnotationManager(cls.db_manager)
        cls.export_manager = ExportManager(cls.db_manager)
        
        # Initialize roles
        cls.db_manager.initialize_roles()
    
    @classmethod
    def tearDownClass(cls):
        """Drop test database after tests"""
        cls.db_manager.client.drop_database("openlabel_test_db")
    
    def setUp(self):
        """Clear collections before each test"""
        self.db_manager.db.users.delete_many({})
        self.db_manager.db.userPreferences.delete_many({})
        self.db_manager.db.projects.delete_many({})
        self.db_manager.db.images.delete_many({})
        self.db_manager.db.annotations.delete_many({})
    
    def test_user_creation(self):
        """Test user creation and authentication"""
        # Create a test user
        user_id = self.user_manager.create_user(
            "testuser", "test@example.com", "password123", 
            "Test", "User", "annotator"
        )
        
        # Check if user exists
        user = self.db_manager.db.users.find_one({"_id": user_id})
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "testuser")
        self.assertEqual(user["email"], "test@example.com")
        
        # Check if password is hashed
        self.assertTrue(bcrypt.checkpw("password123".encode('utf-8'), user["password"]))
        
        # Test authentication
        auth_user = self.user_manager.authenticate_user("testuser", "password123")
        self.assertIsNotNone(auth_user)
        
        # Test wrong password
        auth_user = self.user_manager.authenticate_user("testuser", "wrongpassword")
        self.assertIsNone(auth_user)
    
    def test_user_preferences(self):
        """Test user preferences"""
        # Create a test user
        user_id = self.user_manager.create_user(
            "prefuser", "pref@example.com", "password123", 
            "Pref", "User", "annotator"
        )
        
        # Check if preferences were created automatically
        prefs = self.user_manager.get_user_preferences(user_id)
        self.assertIsNotNone(prefs)
        self.assertEqual(prefs["uiPreferences"]["theme"], "light")
        
        # Update preferences
        updates = {
            "uiPreferences": {
                "theme": "dark"
            }
        }
        result = self.user_manager.update_user_preferences(user_id, updates)
        self.assertTrue(result)
        
        # Check if preferences were updated
        prefs = self.user_manager.get_user_preferences(user_id)
        self.assertEqual(prefs["uiPreferences"]["theme"], "dark")
    
    def test_project_creation(self):
        """Test project creation and management"""
        # Create a test user
        user_id = self.user_manager.create_user(
            "projectuser", "project@example.com", "password123", 
            "Project", "User", "admin"
        )
        
        # Create a project
        project_id = self.project_manager.create_project(
            "Test Project", "A test project", user_id, False, ["boundingBox"]
        )
        
        # Check if project exists
        project = self.db_manager.db.projects.find_one({"_id": project_id})
        self.assertIsNotNone(project)
        self.assertEqual(project["name"], "Test Project")
        
        # Check if user is a member with admin role
        self.assertEqual(len(project["members"]), 1)
        self.assertEqual(project["members"][0]["userId"], user_id)
        
        # Get project by user
        user_projects = self.project_manager.get_projects_by_user(user_id)
        self.assertEqual(len(user_projects), 1)
        self.assertEqual(user_projects[0]["_id"], project_id)
    
    def test_project_members(self):
        """Test project member management"""
        # Create users
        admin_id = self.user_manager.create_user(
            "admin", "admin@example.com", "password123", 
            "Admin", "User", "admin"
        )
        annotator_id = self.user_manager.create_user(
            "annotator", "annotator@example.com", "password123", 
            "Anno", "Tator", "annotator"
        )
        
        # Create a project
        project_id = self.project_manager.create_project(
            "Member Test", "Testing project members", admin_id
        )
        
        # Add annotator to project
        result = self.project_manager.add_project_member(
            project_id, annotator_id, "annotator", admin_id
        )
        self.assertTrue(result)
        
        # Get project members
        members = self.project_manager.get_project_members(project_id)
        self.assertEqual(len(members), 2)
        
        # Check roles
        admin_member = next((m for m in members if str(m["userId"]) == str(admin_id)), None)
        annotator_member = next((m for m in members if str(m["userId"]) == str(annotator_id)), None)
        
        self.assertIsNotNone(admin_member)
        self.assertIsNotNone(annotator_member)
        self.assertEqual(admin_member["roleName"], "admin")
        self.assertEqual(annotator_member["roleName"], "annotator")
    
    def test_annotations(self):
        """Test annotation creation and management"""
        # Create user
        user_id = self.user_manager.create_user(
            "annouser", "anno@example.com", "password123", 
            "Anno", "User", "annotator"
        )
        
        # Create project
        project_id = self.project_manager.create_project(
            "Anno Test", "Testing annotations", user_id
        )
        
        # Create mock image
        image_id = self.annotation_manager.create_mock_image(
            project_id, "test.jpg", 800, 600, user_id
        )
        
        # Create bounding box annotation
        bbox_id = self.annotation_manager.create_bounding_box(
            image_id, project_id, "car", 
            {"x": 100, "y": 100, "width": 200, "height": 150}, 
            user_id
        )
        
        # Create polygon annotation
        polygon_id = self.annotation_manager.create_polygon(
            image_id, project_id, "person", 
            [{"x": 300, "y": 300}, {"x": 350, "y": 300}, {"x": 325, "y": 350}],
            user_id
        )
        
        # Get annotations for image
        annotations = self.annotation_manager.get_annotations_by_image(image_id)
        self.assertEqual(len(annotations), 2)
        
        # Check image status
        image = self.db_manager.db.images.find_one({"_id": image_id})
        self.assertEqual(image["status"], "annotated")
        
        # Delete an annotation
        result = self.annotation_manager.delete_annotation(bbox_id, user_id)
        self.assertTrue(result)
        
        # Check remaining annotations
        annotations = self.annotation_manager.get_annotations_by_image(image_id)
        self.assertEqual(len(annotations), 1)
    
    def test_export_formats(self):
        """Test annotation export formats"""
        # Create test data
        user_id = self.user_manager.create_user(
            "exporter", "export@example.com", "password123", 
            "Export", "User", "annotator"
        )
        
        project_id = self.project_manager.create_project(
            "Export Test", "Testing exports", user_id
        )
        
        image1_id = self.annotation_manager.create_mock_image(
            project_id, "img1.jpg", 800, 600, user_id
        )
        
        image2_id = self.annotation_manager.create_mock_image(
            project_id, "img2.jpg", 1024, 768, user_id
        )
        
        # Add annotations
        self.annotation_manager.create_bounding_box(
            image1_id, project_id, "car", 
            {"x": 100, "y": 100, "width": 200, "height": 150}, 
            user_id
        )
        
        self.annotation_manager.create_bounding_box(
            image1_id, project_id, "person", 
            {"x": 400, "y": 200, "width": 100, "height": 200}, 
            user_id
        )
        
        self.annotation_manager.create_polygon(
            image2_id, project_id, "dog", 
            [{"x": 300, "y": 300}, {"x": 350, "y": 300}, {"x": 325, "y": 350}],
            user_id
        )
        
        # Test COCO export
        coco_data = self.export_manager.export_coco(project_id)
        
        # Check COCO structure
        self.assertIn("images", coco_data)
        self.assertIn("annotations", coco_data)
        self.assertIn("categories", coco_data)
        
        self.assertEqual(len(coco_data["images"]), 2)
        self.assertEqual(len(coco_data["annotations"]), 3)
        self.assertEqual(len(coco_data["categories"]), 3)
        
        # Test YOLO export
        yolo_data = self.export_manager.export_yolo(project_id)
        
        # Check YOLO structure
        self.assertIn("classes.txt", yolo_data)
        self.assertIn("img1.jpg", yolo_data)
        self.assertIn("img2.jpg", yolo_data)
        
        self.assertEqual(len(yolo_data["classes.txt"]), 3)  # 3 classes
        self.assertEqual(len(yolo_data["img1.jpg"]), 2)     # 2 annotations
        self.assertEqual(len(yolo_data["img2.jpg"]), 1)     # 1 annotation

if __name__ == "__main__":
    unittest.main()