import http.server
import socketserver
import sqlite3
import json
import urllib.parse
import os
import sys
import webbrowser

# Port to run the web server on
PORT = 8000

class Course:
    """
    Represents a course object within the Student Course Management System.
    Validates and stores course code, course title, and credit units.
    """
    def __init__(self, course_code, course_title, unit):
        """
        Constructor for Course class.
        Cleans and validates the input parameters.
        Raises ValueError if any input is invalid.
        """
        # Trim whitespace and normalize casing
        self.course_code = str(course_code).strip().upper()
        self.course_title = str(course_title).strip()
        
        # Verify units is a valid integer
        try:
            self.unit = int(unit)
        except (ValueError, TypeError):
            raise ValueError("Course unit must be a valid integer.")
        
        # Validation checks
        if not self.course_code:
            raise ValueError("Course code cannot be empty.")
        if not self.course_title:
            raise ValueError("Course title cannot be empty.")
        if self.unit <= 0:
            raise ValueError("Course unit must be a positive integer greater than zero.")

    def to_dict(self):
        """
        Converts the course object attributes into a Python dictionary.
        This is helper method for json serialization.
        """
        return {
            "course_code": self.course_code,
            "course_title": self.course_title,
            "unit": self.unit
        }


class CourseManager:
    """
    Manages the collection of courses. Handles database synchronization,
    file saving and loading, and implements recursive logic.
    """
    def __init__(self, db_path="courses.db"):
        """
        Initializes the CourseManager with a database file path.
        Checks for table existence and loads existing records into the memory array.
        """
        self.db_path = db_path
        self.courses = []  # manageable internal structure (array/list)
        self._init_db()
        self.load_from_db()

    def _init_db(self):
        """
        Creates the SQLite 'courses' table if it does not already exist.
        Ensures local schema persistence.
        """
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                course_code TEXT PRIMARY KEY,
                course_title TEXT NOT NULL,
                unit INTEGER NOT NULL
            )
        """)
        connection.commit()
        connection.close()

    def load_from_db(self):
        """
        Queries all records from SQLite database and populates the internal courses array.
        """
        self.courses = []
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT course_code, course_title, unit FROM courses")
        rows = cursor.fetchall()
        for row in rows:
            # Create a Course instance and append it to our list
            course_obj = Course(row[0], row[1], row[2])
            self.courses.append(course_obj)
        connection.close()

    def add_course(self, course_code, course_title, unit):
        """
        Validates, inserts a new course into SQLite, and updates the memory array.
        Raises ValueError if the course code already exists.
        """
        new_course = Course(course_code, course_title, unit)
        
        # Check for duplicates using loop search
        for c in self.courses:
            if c.course_code == new_course.course_code:
                raise ValueError(f"Course code '{new_course.course_code}' is already registered.")

        # Persist to SQLite
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO courses (course_code, course_title, unit) VALUES (?, ?, ?)",
                (new_course.course_code, new_course.course_title, new_course.unit)
            )
            connection.commit()
        except sqlite3.IntegrityError:
            connection.close()
            raise ValueError(f"Course code '{new_course.course_code}' is already registered in database.")
        finally:
            connection.close()

        # Update local array
        self.courses.append(new_course)
        return new_course

    def edit_course(self, old_course_code, new_course_code, new_title, new_unit):
        """
        Validates the new fields and updates the course in SQLite and memory.
        If the new course code is different, checks for duplicate code.
        Raises ValueError if fields are invalid or duplicate.
        """
        old_course_code = str(old_course_code).strip().upper()
        new_course_code = str(new_course_code).strip().upper()
        new_title = str(new_title).strip()

        try:
            new_unit = int(new_unit)
        except (ValueError, TypeError):
            raise ValueError("Course unit must be a valid integer.")

        if not new_course_code:
            raise ValueError("Course code cannot be empty.")
        if not new_title:
            raise ValueError("Course title cannot be empty.")
        if new_unit <= 0:
            raise ValueError("Course unit must be a positive integer greater than zero.")

        # Find the course to check existence
        course_to_edit = None
        for c in self.courses:
            if c.course_code == old_course_code:
                course_to_edit = c
                break
        if not course_to_edit:
            raise ValueError(f"Course '{old_course_code}' not found.")

        # Check if new course code is different and already exists
        if new_course_code != old_course_code:
            for c in self.courses:
                if c.course_code == new_course_code:
                    raise ValueError(f"Course code '{new_course_code}' is already registered.")

        # Persist update to SQLite
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE courses SET course_code = ?, course_title = ?, unit = ? WHERE course_code = ?",
                (new_course_code, new_title, new_unit, old_course_code)
            )
            connection.commit()
        except sqlite3.IntegrityError:
            connection.close()
            raise ValueError(f"Course code '{new_course_code}' is already registered in database.")
        finally:
            connection.close()

        # Update in-memory object
        course_to_edit.course_code = new_course_code
        course_to_edit.course_title = new_title
        course_to_edit.unit = new_unit

        return course_to_edit

    def delete_course(self, course_code):
        """
        Deletes the course matching course_code from SQLite database and updates memory array.
        Raises ValueError if course is not found.
        """
        course_code = str(course_code).strip().upper()

        # Check if course exists in memory
        found = False
        for c in self.courses:
            if c.course_code == course_code:
                found = True
                break
        if not found:
            raise ValueError(f"Course '{course_code}' not found.")

        # Persist delete to SQLite
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM courses WHERE course_code = ?", (course_code,))
        connection.commit()
        connection.close()

        # Update local array
        self.courses = [c for c in self.courses if c.course_code != course_code]
        return True

    def search_courses(self, query):
        """
        Wrapper around recursive search algorithm.
        Returns a list of Course objects matching the query in code or title.
        """
        return self._recursive_search(self.courses, query.strip().upper(), 0)

    def _recursive_search(self, course_list, query, index):
        """
        Recursive helper function that traverses the course array.
        Accumulates and returns a list of matching courses (substring search).
        """
        # Base Case: Reached the end of the array, return empty list
        if index >= len(course_list):
            return []
        
        # Check if query matches course_code or course_title (substring and case-insensitive)
        code_match = query in course_list[index].course_code
        title_match = query in course_list[index].course_title.upper()
        
        # Recursive Case: Get matches from the rest of the array
        matches_from_rest = self._recursive_search(course_list, query, index + 1)
        
        # If current course matches, prepend it to the rest of the matches
        if code_match or title_match:
            return [course_list[index]] + matches_from_rest
        else:
            return matches_from_rest

    def compute_total_units(self):
        """
        Wrapper around recursive credit summation algorithm.
        Returns the total sum of credit units.
        """
        return self._recursive_sum_units(self.courses, 0)

    def _recursive_sum_units(self, course_list, index):
        """
        Recursive helper function that sums course units.
        Primary focus: array traversal via recursion.
        """
        # Base Case: Reached the end of the array, add zero
        if index >= len(course_list):
            return 0
        
        # Recursive Case: Add current course unit to the sum of units of remaining courses
        return course_list[index].unit + self._recursive_sum_units(course_list, index + 1)

    def save_to_file(self, filename="courses.json"):
        """
        Saves the current internal courses array to a JSON format text file.
        Provides local export utility.
        """
        try:
            # Map object array to serialization-friendly structures
            data_list = [c.to_dict() for c in self.courses]
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data_list, f, indent=4)
        except Exception as e:
            raise IOError(f"File write failure: {str(e)}")

    def load_from_file(self, filename="courses.json"):
        """
        Loads courses from a JSON file, synchronizes them into SQLite database,
        and refreshes the internal memory array.
        """
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Selected file '{filename}' does not exist.")
        
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data_list = json.load(f)
            
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            
            # Use loops to parse and merge records
            for item in data_list:
                course = Course(item.get("course_code"), item.get("course_title"), item.get("unit"))
                # Insert or replace record in database
                cursor.execute(
                    "INSERT OR REPLACE INTO courses (course_code, course_title, unit) VALUES (?, ?, ?)",
                    (course.course_code, course.course_title, course.unit)
                )
                
            connection.commit()
            connection.close()
            
            # Refresh our internal array from SQLite
            self.load_from_db()
        except Exception as e:
            raise IOError(f"File load failure: {str(e)}")


class CourseHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """
    Custom HTTP Request Handler serving static web files
    and handling REST API requests for courses.
    """
    
    # Store global reference to manager
    manager = None

    def log_message(self, format, *args):
        """
        Supresses default logging outputs to keep CLI clean.
        """
        pass

    def do_GET(self):
        """
        Handles GET requests.
        Serves HTML, CSS, Javascript files, and resolves course API requests.
        """
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        # Serve static frontend files
        if path in ["/", "/index.html"]:
            self.serve_file("frontend/index.html", "text/html")
        elif path == "/styles.css":
            self.serve_file("frontend/styles.css", "text/css")
        elif path == "/app.js":
            self.serve_file("frontend/app.js", "application/javascript")
            
        # REST API: GET all courses
        elif path == "/api/courses":
            all_courses = [c.to_dict() for c in self.manager.courses]
            self.send_json({"status": "success", "courses": all_courses})
            
        # REST API: Search course by query (code or title substring)
        elif path == "/api/courses/search":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            # Accept either 'query' or 'code' parameters for compatibility
            query = query_params.get("query", query_params.get("code", [""]))[0]
            results = self.manager.search_courses(query)
            serialized_results = [c.to_dict() for c in results]
            self.send_json({
                "status": "success", 
                "found": len(results) > 0, 
                "courses": serialized_results
            })
                
        # REST API: Compute total units
        elif path == "/api/courses/total_units":
            total = self.manager.compute_total_units()
            self.send_json({"status": "success", "total_units": total})
            
        else:
            self.send_error(404, "Page Not Found")

    def do_POST(self):
        """
        Handles POST requests.
        Decodes incoming JSON data to create courses, save, or load database states.
        """
        path = self.path
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            # REST API: ADD course
            if path == "/api/courses":
                data = json.loads(post_data)
                code = data.get("course_code")
                title = data.get("course_title")
                unit = data.get("unit")
                
                new_c = self.manager.add_course(code, title, unit)
                self.send_json({
                    "status": "success", 
                    "message": "Course added successfully.", 
                    "course": new_c.to_dict()
                })
                
            # REST API: Save to file
            elif path == "/api/courses/save":
                data = json.loads(post_data) if post_data else {}
                filename = data.get("filename", "courses.json").strip()
                if not filename:
                    filename = "courses.json"
                self.manager.save_to_file(filename)
                self.send_json({
                    "status": "success", 
                    "message": f"Courses saved successfully to '{filename}'."
                })
                
            # REST API: Load from file
            elif path == "/api/courses/load":
                data = json.loads(post_data) if post_data else {}
                filename = data.get("filename", "courses.json").strip()
                if not filename:
                    filename = "courses.json"
                self.manager.load_from_file(filename)
                self.send_json({
                    "status": "success", 
                    "message": f"Courses loaded successfully from '{filename}'."
                })
                
            else:
                self.send_error(404, "Endpoint Not Found")
                
        except ValueError as val_err:
            self.send_json({"status": "error", "message": str(val_err)}, status_code=400)
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status_code=500)

    def do_PUT(self):
        """
        Handles PUT requests.
        Decodes incoming JSON data to edit existing courses.
        """
        path = self.path
        content_length = int(self.headers.get('Content-Length', 0))
        put_data = self.rfile.read(content_length).decode('utf-8')

        try:
            # REST API: EDIT course
            if path == "/api/courses":
                data = json.loads(put_data)
                old_code = data.get("old_code")
                new_code = data.get("course_code")
                title = data.get("course_title")
                unit = data.get("unit")

                updated_c = self.manager.edit_course(old_code, new_code, title, unit)
                self.send_json({
                    "status": "success",
                    "message": "Course updated successfully.",
                    "course": updated_c.to_dict()
                })
            else:
                self.send_error(404, "Endpoint Not Found")

        except ValueError as val_err:
            self.send_json({"status": "error", "message": str(val_err)}, status_code=400)
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status_code=500)

    def do_DELETE(self):
        """
        Handles DELETE requests.
        Deletes a course using the query parameter ?code=...
        """
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        try:
            # REST API: DELETE course
            if path == "/api/courses":
                query_params = urllib.parse.parse_qs(parsed_url.query)
                code = query_params.get("code", [""])[0]
                if not code:
                    self.send_json({"status": "error", "message": "Course code parameter 'code' is required."}, status_code=400)
                    return

                self.manager.delete_course(code)
                self.send_json({
                    "status": "success",
                    "message": f"Course '{code}' deleted successfully."
                })
            else:
                self.send_error(404, "Endpoint Not Found")

        except ValueError as val_err:
            self.send_json({"status": "error", "message": str(val_err)}, status_code=400)
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status_code=500)

    def serve_file(self, filepath, content_type):
        """
        Loads a file from disk relative to main.py directory and writes to socket output.
        """
        try:
            # Safely locate filepath relative to project directory
            base_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(base_dir, filepath)
            
            with open(full_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, f"File {filepath} not found.")

    def send_json(self, response_dict, status_code=200):
        """
        Helper method to output API dictionary responses in JSON string format.
        """
        response_bytes = json.dumps(response_dict).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        # Enable CORS
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response_bytes)


def run_console_menu(manager):
    """
    Runs the interactive CLI menu loop for console-based usage of the system.
    Supports all operations via keyboard inputs.
    """
    while True:
        print("\n" + "="*50)
        print(" STUDENT COURSE MANAGEMENT SYSTEM (CLI MENU)")
        print("="*50)
        print("1. Add Course")
        print("2. View All Courses")
        print("3. Search Course by Code")
        print("4. Compute Total Credit Units")
        print("5. Save Course List to File")
        print("6. Load Course List from File")
        print("7. Edit Course")
        print("8. Delete Course")
        print("9. Exit Program")
        print("="*50)
        
        choice = input("Enter option (1-9): ").strip()
        
        try:
            if choice == "1":
                code = input("Enter course code (e.g. COS201): ").strip()
                title = input("Enter course title: ").strip()
                unit = input("Enter credit units: ").strip()
                course = manager.add_course(code, title, unit)
                print(f"\n[SUCCESS] Added: {course.course_code} - {course.course_title} ({course.unit} units)")
                
            elif choice == "2":
                print("\nRECORDED SEMESTER COURSES:")
                if not manager.courses:
                    print("No courses recorded yet.")
                else:
                    print(f"{'Code':<12} | {'Course Title':<30} | {'Units':<5}")
                    print("-" * 53)
                    # Loop over internal list structure
                    for course in manager.courses:
                        print(f"{course.course_code:<12} | {course.course_title:<30} | {course.unit:<5}")
                        
            elif choice == "3":
                query = input("Enter course code or title to search: ").strip()
                results = manager.search_courses(query)
                if results:
                    print(f"\nSEARCH RESULTS ({len(results)} matches found):")
                    print(f"{'Code':<12} | {'Course Title':<30} | {'Units':<5}")
                    print("-" * 53)
                    for course in results:
                        print(f"{course.course_code:<12} | {course.course_title:<30} | {course.unit:<5}")
                else:
                    print(f"\n[NOT FOUND] No courses matched the query '{query}'.")
                    
            elif choice == "4":
                # Compute total units recursively
                total = manager.compute_total_units()
                print(f"\nTotal Credit Units for the Semester: {total} units")
                
            elif choice == "5":
                filename = input("Enter output filename [default: courses.json]: ").strip()
                if not filename:
                    filename = "courses.json"
                manager.save_to_file(filename)
                print(f"\n[SUCCESS] Saved {len(manager.courses)} courses to file '{filename}'.")
                
            elif choice == "6":
                filename = input("Enter source filename [default: courses.json]: ").strip()
                if not filename:
                    filename = "courses.json"
                manager.load_from_file(filename)
                print(f"\n[SUCCESS] Loaded {len(manager.courses)} courses from file '{filename}'.")
                
            elif choice == "7":
                old_code = input("Enter course code of the course to edit (e.g. COS201): ").strip().upper()
                course_to_edit = None
                for c in manager.courses:
                    if c.course_code == old_code:
                        course_to_edit = c
                        break
                if not course_to_edit:
                    print(f"\n[ERROR] Course '{old_code}' not found.")
                else:
                    print(f"\nEditing Course: {course_to_edit.course_code} - {course_to_edit.course_title} ({course_to_edit.unit} units)")
                    new_code = input(f"Enter new course code [leave empty to keep '{course_to_edit.course_code}']: ").strip()
                    if not new_code:
                        new_code = course_to_edit.course_code
                        
                    new_title = input(f"Enter new course title [leave empty to keep '{course_to_edit.course_title}']: ").strip()
                    if not new_title:
                        new_title = course_to_edit.course_title
                        
                    new_unit = input(f"Enter new credit units [leave empty to keep '{course_to_edit.unit}']: ").strip()
                    if not new_unit:
                        new_unit = course_to_edit.unit
                    
                    updated = manager.edit_course(old_code, new_code, new_title, new_unit)
                    print(f"\n[SUCCESS] Updated: {updated.course_code} - {updated.course_title} ({updated.unit} units)")
                    
            elif choice == "8":
                code = input("Enter course code to delete (e.g. COS201): ").strip().upper()
                course_to_delete = None
                for c in manager.courses:
                    if c.course_code == code:
                        course_to_delete = c
                        break
                if not course_to_delete:
                    print(f"\n[ERROR] Course '{code}' not found.")
                else:
                    confirm = input(f"Are you sure you want to delete '{course_to_delete.course_code} - {course_to_delete.course_title}'? (y/N): ").strip().lower()
                    if confirm in ["y", "yes"]:
                        manager.delete_course(code)
                        print(f"\n[SUCCESS] Course '{code}' deleted successfully.")
                    else:
                        print("\nDeletion cancelled.")
                        
            elif choice == "9":
                print("\nThank you for using the Course Management System. Goodbye!")
                break
            else:
                print("\n[ERROR] Invalid option! Enter a value from 1 to 9.")
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")


def main():
    """
    Main entry point. Decides whether to start the program in
    Console CLI mode or Web Server GUI mode based on arguments.
    """
    manager = CourseManager()
    
    # Check command-line arguments for CLI mode
    if len(sys.argv) > 1 and sys.argv[1] == "--console":
        run_console_menu(manager)
    else:
        # Inject manager instance dependency into HTTP handler
        CourseHTTPRequestHandler.manager = manager
        
        # Configure socket server settings
        socketserver.TCPServer.allow_reuse_address = True
        
        with socketserver.TCPServer(("", PORT), CourseHTTPRequestHandler) as httpd:
            print("\n" + "="*60)
            print(f" STUDENT COURSE MANAGEMENT SYSTEM RUNNING")
            print(f" Web GUI: http://localhost:{PORT}")
            print(f" (To run CLI instead, execute: python main.py --console)")
            # the CLI is designed by Gemini, not me, i only edited some parts of it but i like it so i will keep it.
            print("="*60 + "\n")
            
            # Automatically launch web browser
            webbrowser.open(f"http://localhost:{PORT}")
            
            try:
                # Keep server active
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nShutting down server...")


if __name__ == "__main__":
    main()
