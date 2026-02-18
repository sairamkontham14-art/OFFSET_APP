import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QPushButton, QLabel, QVBoxLayout, QWidget, QLineEdit, QTextEdit, QHBoxLayout, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
import ezdxf
import poly
import comp_poly
import arc_circle
from styles import get_stylesheet, DARK_THEME, LIGHT_THEME

# File to store previous files log
PREVIOUS_FILES_LOG = "previous_files_log.txt"

def resource_path(relative_path):
    """Get the absolute path to a resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class ThemeToggleButton(QPushButton):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.is_dark_theme = True  # Start with dark theme
        self.setIcon(QIcon(resource_path("icons/moon.png")))  # Set moon icon for dark mode
        self.setFixedSize(60, 60)
        self.setIconSize(self.size())
        self.clicked.connect(self.toggle_theme)

    def toggle_theme(self):
        try:
            """Toggle between dark and light themes."""
            self.is_dark_theme = not self.is_dark_theme
            new_theme = DARK_THEME if self.is_dark_theme else LIGHT_THEME

            # Apply the new theme
            self.app.setStyleSheet(get_stylesheet(new_theme))

            # Update the icon
            self.setIcon(QIcon(resource_path("icons/sun.png" if self.is_dark_theme else "icons/moon.png")))

            # Update the figure and axes colors (if applicable)
            if hasattr(self.parent(), 'figure'):
                self.parent().figure.patch.set_facecolor(new_theme['figure_bg'])
                ax = self.parent().figure.gca()
                ax.set_facecolor(new_theme['plot_bg'])
                self.parent().canvas.draw()

        except Exception as e:
            print(f"Error toggling theme: {e}")

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Feature Recognition")
        self.setGeometry(100, 100, 1400, 900)  # Larger default size
        self.setup_ui()

    def setup_ui(self):
        # Create main widget with horizontal layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(1500)
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(10)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)

        # Add logo and title
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        logo_label = QLabel()
        logo_pixmap = QPixmap(resource_path("icons/logo.png"))
        logo_label.setPixmap(logo_pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(logo_label)
        title_label = QLabel("Feature Recognition")
        title_label.setObjectName("sidebarTitle")
        title_label.setStyleSheet("font-size:34px; font-weight: bold;adding-left: 10px;")  # Adjusted font size and padding)
        header_layout.addWidget(title_label)
        sidebar_layout.addWidget(header_widget)

        # Add menu buttons
        for button_text, slot in [
            ("Polygon Offset", self.open_offset_page),
            ("Circle/Arc Offset", self.open_arc_circle_page),
            ("Vertex/Coordinates", self.open_vertex_page)
        ]:
            button = QPushButton(button_text)
            button.setObjectName("menuButton")
            button.setStyleSheet("font-size: 24px;")
            button.clicked.connect(slot)
            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch()

        # Add theme toggle button at bottom
        self.theme_button = ThemeToggleButton(self, QApplication.instance())
        sidebar_layout.addWidget(self.theme_button)

        main_layout.addWidget(sidebar)

        # Create content area
        self.content_widget = QWidget()
        self.content_widget.setObjectName("contentArea")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(10)
        self.content_layout.setContentsMargins(10, 10, 10, 10)

        # Add previous files section
        self.previous_files_label = QLabel("Previous Files")
        self.previous_files_label.setObjectName("sidebarTitle")
        self.previous_files_label.setStyleSheet("font-size: 28px;")
        self.content_layout.addWidget(self.previous_files_label)

        # Add a list widget to display previous files
        self.previous_files_list = QListWidget()
        self.previous_files_list.setObjectName("fileList")
        self.previous_files_list.setStyleSheet("font-size: 20px;")
        self.content_layout.addWidget(self.previous_files_list)

        # Load previous files from log
        self.load_previous_files()

        main_layout.addWidget(self.content_widget)

    def load_previous_files(self):
        """Load previous files from the log file and display them in the list."""
        if os.path.exists(PREVIOUS_FILES_LOG):
            with open(PREVIOUS_FILES_LOG, "r") as file:
                for line in file:
                    item = QListWidgetItem(line.strip())
                    self.previous_files_list.addItem(item)

    def log_previous_file(self, file_path):
        """Log the file path, date, and time to the previous files log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{file_path} - {timestamp}"
        with open(PREVIOUS_FILES_LOG, "a") as file:
            file.write(log_entry + "\n")

        # Update the previous files list
        self.previous_files_list.addItem(QListWidgetItem(log_entry))

    def open_offset_page(self):
        offset_widget = OffsetWidget(self)
        self.setCentralWidget(offset_widget)

    def open_vertex_page(self):
        vertex_widget = VertexWidget(self)
        self.setCentralWidget(vertex_widget)

    def open_arc_circle_page(self):
        arc_circle_widget = ArcCircleWidget(self)
        self.setCentralWidget(arc_circle_widget)

class OffsetWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent_app = parent
        layout = QVBoxLayout()

        # Initialize the _is_dark attribute based on the current theme
        self._is_dark = True  # Default to dark theme

        # Header with logo, title, and theme toggle
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        logo_label = QLabel()
        logo_pixmap = QPixmap(resource_path("icons/logo.png"))
        logo_label.setPixmap(logo_pixmap.scaled(124, 124, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(logo_label)
        title_label = QLabel("Feature Recognition")
        title_label.setObjectName("sidebarTitle")
        title_label.setStyleSheet("font-size: 34px; font-weight: bold; padding-left: 10px;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        self.theme_button = ThemeToggleButton(self, QApplication.instance())
        header_layout.addWidget(self.theme_button)
        layout.addWidget(header_widget)

        # Main content area
        main_content = QWidget()
        main_content_layout = QHBoxLayout(main_content)

        # Menu section
        menu_widget = QWidget()
        menu_layout = QVBoxLayout(menu_widget)
        menu_layout.setSpacing(50)
        menu_layout.setContentsMargins(10, 10, 10, 10)

        self.load_button = QPushButton("Load DXF")
        self.load_button.setFixedSize(400, 40)
        self.load_button.setStyleSheet("font-size: 21px;")
        self.load_button.clicked.connect(self.load_dxf)
        menu_layout.addWidget(self.load_button)

        self.save_button = QPushButton("Save Offset DXF")
        self.save_button.setFixedSize(400, 40)
        self.save_button.setStyleSheet("font-size: 21px;")
        self.save_button.clicked.connect(self.save_dxf)
        menu_layout.addWidget(self.save_button)

        back_button = QPushButton("Back to Home")
        back_button.setFixedSize(400, 40)
        back_button.setStyleSheet("font-size: 21px;")
        back_button.clicked.connect(self.go_back)
        menu_layout.addWidget(back_button)

        menu_layout.addStretch()
        main_content_layout.addWidget(menu_widget)

        # Workspace section
        workspace_widget = QWidget()
        workspace_layout = QVBoxLayout(workspace_widget)

        # Input field for offset distance
        self.offset_input = QLineEdit()
        self.offset_input.setPlaceholderText("Enter offset value (e.g., 5)")
        self.offset_input.setStyleSheet("font-size: 22px;")
        workspace_layout.addWidget(self.offset_input)

        # Preview button
        self.preview_button = QPushButton("Preview Offset")
        self.preview_button.setStyleSheet("font-size: 24px;")
        self.preview_button.clicked.connect(self.preview_offset)
        workspace_layout.addWidget(self.preview_button)

        # Canvas for polygon
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)

        workspace_layout.addWidget(self.canvas)

        main_content_layout.addWidget(workspace_widget)
        layout.addWidget(main_content)

        self.setLayout(layout)
        self.dxf_file = None
        self.offset_result = None

    def load_dxf(self):
        try:
            print("Opening file dialog...")
            self.dxf_file, _ = QFileDialog.getOpenFileName(self, "Open DXF File", "", "DXF Files (*.dxf)")
            if self.dxf_file:
                print(f"Loaded DXF: {self.dxf_file}")
                self.parent_app.log_previous_file(self.dxf_file)
        except Exception as e:
            print(f"Error loading DXF file: {e}")

    def preview_offset(self):
        try:
            if not self.dxf_file or not self.offset_input.text():
                print("DXF file or offset value missing.")
                return

            # Update figure and axes colors based on current theme
            current_theme = DARK_THEME if self._is_dark else LIGHT_THEME
            self.figure.patch.set_facecolor(current_theme['figure_bg'])
            ax = self.figure.gca()
            ax.set_facecolor(current_theme['plot_bg'])

            # Update grid colors
            ax.grid(True, color=current_theme['plot_grid'], linestyle='--', alpha=0.5)

            # Update spine colors
            for spine in ax.spines.values():
                spine.set_color(current_theme['plot_fg'])

            # Update tick colors
            ax.tick_params(colors=current_theme['plot_fg'])

            # Use theme-appropriate colors for plotting
            original_color = 'white' if self._is_dark else 'black'
            offset_color = '#0078D4'  # Accent color for offset lines

            offset_value = float(self.offset_input.text())
            _, _, offset_polygons = poly.process_dxf(self.dxf_file, offset_value)

            self.offset_result = offset_polygons
            self.intersection_points_per_polygon = []

            self.figure.clear()
            ax = self.figure.add_subplot(111)

            # Store all x and y coordinates for auto-scaling
            all_x_coords = []
            all_y_coords = []

            # Plot original geometry
            doc = ezdxf.readfile(self.dxf_file)
            msp = doc.modelspace()
            for entity in msp:
                if entity.dxftype() == "LINE":
                    start = entity.dxf.start
                    end = entity.dxf.end
                    ax.plot([start.x, end.x], [start.y, end.y], 'b-', label='Original')
                    all_x_coords.extend([start.x, end.x])
                    all_y_coords.extend([start.y, end.y])

            # Calculate intersection points for offset polygons
            if offset_polygons:
                for polygon in offset_polygons:
                    # Create equations for adjacent lines
                    equations_sets = poly.create_equations_of_adjacent_lines([polygon])

                    # Find intersection points
                    intersection_points = poly.find_intersection_points_of_adjacent_lines(equations_sets)
                    self.intersection_points_per_polygon.append(intersection_points)

                    # Plot lines between intersection points
                    if intersection_points:
                        for i in range(len(intersection_points)):
                            start_point = intersection_points[i]
                            end_point = intersection_points[(i + 1) % len(intersection_points)]

                            ax.plot([start_point[0], end_point[0]],
                                    [start_point[1], end_point[1]],
                                    'r-', label='Offset')

                            all_x_coords.extend([start_point[0], end_point[0]])
                            all_y_coords.extend([start_point[1], end_point[1]])

                        # Plot intersection points
                        intersection_x = [p[0] for p in intersection_points]
                        intersection_y = [p[1] for p in intersection_points]
                        ax.plot(intersection_x, intersection_y, 'ro', markersize=4)

            # Adjust the view to fit all entities with padding
            if all_x_coords and all_y_coords:
                x_min, x_max = min(all_x_coords), max(all_x_coords)
                y_min, y_max = min(all_y_coords), max(all_y_coords)

                # Add 10% padding
                x_padding = (x_max - x_min) * 0.1
                y_padding = (y_max - y_min) * 0.1

                ax.set_xlim(x_min - x_padding, x_max + x_padding)
                ax.set_ylim(y_min - y_padding, y_max + y_padding)

            ax.set_title("Offset Preview")
            ax.set_aspect('equal')
            ax.grid(True)
            # Remove duplicate labels
            handles, labels = ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax.legend(by_label.values(), by_label.keys())

            self.canvas.draw()

        except Exception as e:
            print(f"Error in preview_offset: {e}")

    def save_dxf(self):
        if not self.dxf_file or not self.offset_input.text() or not hasattr(self, 'intersection_points_per_polygon'):
            print("DXF file, offset value, or intersection points missing.")
            return

        try:
            # Open file dialog for save location
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Offset DXF",
                "",
                "DXF Files (*.dxf)"
            )

            if not file_path:  # User cancelled the dialog
                return

            # Ensure the file has .dxf extension
            if not file_path.lower().endswith('.dxf'):
                file_path += '.dxf'

            # Create a new DXF document
            doc = ezdxf.new()
            msp = doc.modelspace()

            # Copy original geometry from source file
            original_doc = ezdxf.readfile(self.dxf_file)
            original_msp = original_doc.modelspace()

            # Copy original lines
            for entity in original_msp:
                if entity.dxftype() == "LINE":
                    start_point = (entity.dxf.start.x, entity.dxf.start.y, 0)
                    end_point = (entity.dxf.end.x, entity.dxf.end.y, 0)
                    msp.add_line(start_point, end_point)

            # Add offset lines using intersection points
            for intersection_points in self.intersection_points_per_polygon:
                if intersection_points:
                    for i in range(len(intersection_points)):
                        start_point = intersection_points[i]
                        end_point = intersection_points[(i + 1) % len(intersection_points)]

                        # Add 3D coordinates (z=0) for DXF
                        start_point_3d = (start_point[0], start_point[1], 0)
                        end_point_3d = (end_point[0], end_point[1], 0)

                        # Add the line to the modelspace in red (color=1)
                        msp.add_line(start_point_3d, end_point_3d, dxfattribs={'color': 1})

            # Save the new DXF file
            doc.saveas(file_path)
            print(f"Offset drawing saved to {file_path}")

        except Exception as e:
            print(f"Error saving DXF: {str(e)}")

    def go_back(self):
        self.parent_app.setup_ui()

class VertexWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent_app = parent
        layout = QVBoxLayout()

        # Header with logo, title, and theme toggle
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        logo_label = QLabel()
        logo_pixmap = QPixmap(resource_path("icons/logo.png"))
        logo_label.setPixmap(logo_pixmap.scaled(124, 124, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(logo_label)
        title_label = QLabel("Feature Recognition")
        title_label.setStyleSheet("font-size: 34px; font-weight: bold; padding-left: 10px;")
        title_label.setObjectName("sidebarTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        self.theme_button = ThemeToggleButton(self, QApplication.instance())
        header_layout.addWidget(self.theme_button)
        layout.addWidget(header_widget)

        # Main content area
        main_content = QWidget()
        main_content_layout = QHBoxLayout(main_content)

        # Menu section
        menu_widget = QWidget()
        menu_layout = QVBoxLayout(menu_widget)
        menu_layout.setSpacing(50)
        menu_layout.setContentsMargins(10, 10, 10, 10)

        self.load_button = QPushButton("Load DXF")
        self.load_button.clicked.connect(self.load_dxf)
        self.load_button.setStyleSheet("font-size: 21px;")  # I
        menu_layout.addWidget(self.load_button)

        self.save_button1 = QPushButton("Save Coordinates as TXT")
        self.save_button1.setStyleSheet("font-size: 21px;")  # I
        self.save_button1.clicked.connect(lambda: self.save_output(self.vertex_result, "Coordinates"))
        menu_layout.addWidget(self.save_button1)

        self.save_button2 = QPushButton("Save G-code as TXT")
        self.save_button2.setStyleSheet("font-size: 21px;")  # I
        self.save_button2.clicked.connect(lambda: self.save_gcode(self.gcode_result, "G-code"))
        menu_layout.addWidget(self.save_button2)

        back_button = QPushButton("Back to Home")
        back_button.clicked.connect(self.go_back)
        back_button.setStyleSheet("font-size: 21px;")  # I
        menu_layout.addWidget(back_button)

        menu_layout.addStretch()
        main_content_layout.addWidget(menu_widget)

        # Workspace section
        workspace_widget = QWidget()
        workspace_layout = QVBoxLayout(workspace_widget)
        coordinates_label = QLabel("Coordinates:")
        coordinates_label.setStyleSheet("font-size: 28px; ")  # Increased font size and bold
        workspace_layout.addWidget(coordinates_label)

        # Text preview area for Output 1 (Coordinates)
        self.output_text1 = QTextEdit()
        self.output_text1.setReadOnly(True)

        self.output_text1.setStyleSheet("font-size: 21px;")  # I

        workspace_layout.addWidget(self.output_text1)

        # Text preview area for Output 2 (G-code)
        self.output_text2 = QTextEdit()
        self.output_text2.setReadOnly(True)

        gcode_label = QLabel("G-code:")
        gcode_label.setStyleSheet("font-size: 28px;")  # Increased font size and bold
        workspace_layout.addWidget(gcode_label)
        self.output_text2.setStyleSheet("font-size: 21px;")  # I

        workspace_layout.addWidget(self.output_text2)

        main_content_layout.addWidget(workspace_widget)
        layout.addWidget(main_content)

        self.setLayout(layout)
        self.dxf_file = None
        self.vertex_result = None
        self.gcode_result = None

    def load_dxf(self):
        try:
            print("Opening file dialog...")
            self.dxf_file, _ = QFileDialog.getOpenFileName(self, "Open DXF File", "", "DXF Files (*.dxf)")
            if self.dxf_file:
                print(f"Loaded DXF: {self.dxf_file}")
                # Assuming comp_poly.process_dxf returns a tuple with two outputs
                self.vertex_result = comp_poly.process_dxf(self.dxf_file)
                if isinstance(self.vertex_result, list):
                    arranged_results = comp_poly.arrange_entities_systematically(self.vertex_result)
                    self.gcode_result = comp_poly.generate_gcode(arranged_results)
                    self.display_output(self.output_text1, arranged_results)
                    self.display_gcode(self.output_text2, self.gcode_result)
                self.parent_app.log_previous_file(self.dxf_file)
        except Exception as e:
            print(f"Error loading DXF file: {e}")

    def display_output(self, output_text, result):
        output_text.clear()
        if result:
            header = f"{'SL No':<8}{'NAME':<15}{'START POINT':<30}{'END POINT':<30}{'RADIUS':<30}{'DIRECTION':<30}{'CENTER':<20}"
            output_text.append(header)
            output_text.append('-' * 192)

            for item in result:
                line = (f"{item['sl_no']:<12}{item['name']:<16}"
                        f"{str(item['start_point']):<33}{str(item['end_point']):<40}"
                        f"{item['radius']:<33}{str(item['direction']):<30}"
                        f"{str(item['center']):<20}")
                output_text.append(line)

    def display_gcode(self, output_text, gcode):
        output_text.clear()
        if gcode:
            for line in gcode:
                output_text.append(line)

    def save_output(self, result, output_name):
        if not result:
            print(f"No data to save for {output_name}.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, f"Save {output_name}", "", "Text Files (*.txt)")
        if save_path:
            comp_poly.save_output_to_notepad(save_path, result)

    def save_gcode(self, gcode, output_name):
        if not gcode:
            print(f"No data to save for {output_name}.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, f"Save {output_name}", "", "Text Files (*.txt)")
        if save_path:
            comp_poly.save_gcode_to_file(save_path, gcode)

    def go_back(self):
        self.parent_app.setup_ui()

class ArcCircleWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent_app = parent
        layout = QVBoxLayout()

        # Header with logo, title, and theme toggle
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        logo_label = QLabel()
        logo_pixmap = QPixmap(resource_path("icons/logo.png"))
        logo_label.setPixmap(logo_pixmap.scaled(124, 124, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(logo_label)
        title_label = QLabel("Feature Recognition")
        title_label.setStyleSheet("font-size: 34px; font-weight: bold; padding-left: 10px;")
        title_label.setObjectName("sidebarTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        self.theme_button = ThemeToggleButton(self, QApplication.instance())
        header_layout.addWidget(self.theme_button)
        layout.addWidget(header_widget)

        # Main content area
        main_content = QWidget()
        main_content_layout = QHBoxLayout(main_content)

        # Menu section
        menu_widget = QWidget()
        menu_layout = QVBoxLayout(menu_widget)
        menu_layout.setSpacing(50)
        menu_layout.setContentsMargins(10, 10, 10, 10)

        self.load_button = QPushButton("Load DXF")
        self.load_button.setFixedSize(400, 40)
        self.load_button.setStyleSheet("font-size: 21px;")
        self.load_button.clicked.connect(self.load_dxf)
        menu_layout.addWidget(self.load_button)

        self.save_button = QPushButton("Save Offset DXF")
        self.save_button.setFixedSize(400, 40)
        self.save_button.setStyleSheet("font-size: 21px;")
        self.save_button.clicked.connect(self.save_dxf)
        menu_layout.addWidget(self.save_button)

        back_button = QPushButton("Back to Home")
        back_button.setFixedSize(400, 40)
        back_button.setStyleSheet("font-size: 21px;")
        back_button.clicked.connect(self.go_back)
        menu_layout.addWidget(back_button)

        menu_layout.addStretch()
        main_content_layout.addWidget(menu_widget)

        # Workspace section
        workspace_widget = QWidget()
        workspace_layout = QVBoxLayout(workspace_widget)

        # Input field for offset distance
        self.offset_input = QLineEdit()
        self.offset_input.setPlaceholderText("Enter offset value (e.g., 5)")
        self.offset_input.setStyleSheet("font-size: 22px;")
        workspace_layout.addWidget(self.offset_input)

        # Preview button
        self.preview_button = QPushButton("Preview Offset")
        self.preview_button.setStyleSheet("font-size: 24px;")
        self.preview_button.clicked.connect(self.preview_offset)
        workspace_layout.addWidget(self.preview_button)

        # Canvas for circle/arc
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        workspace_layout.addWidget(self.canvas)

        main_content_layout.addWidget(workspace_widget)
        layout.addWidget(main_content)

        self.setLayout(layout)
        self.dxf_file = None

    def load_dxf(self):
        try:
            print("Opening file dialog...")
            self.dxf_file, _ = QFileDialog.getOpenFileName(self, "Open DXF File", "", "DXF Files (*.dxf)")
            if self.dxf_file:
                print(f"Loaded DXF: {self.dxf_file}")
                self.parent_app.log_previous_file(self.dxf_file)
        except Exception as e:
            print(f"Error loading DXF file: {e}")

    def preview_offset(self):
        if not self.dxf_file or not self.offset_input.text():
            print("DXF file or offset value missing.")
            return

        offset_value = float(self.offset_input.text())
        self.offset_entities = arc_circle.process_dxf(self.dxf_file, offset_value)

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Store all x and y coordinates for auto-scaling
        all_x_coords = []
        all_y_coords = []

        # Plot original geometry
        doc = ezdxf.readfile(self.dxf_file)
        msp = doc.modelspace()

        for entity in msp:
            if entity.dxftype() == "CIRCLE":
                circle = plt.Circle(
                    (entity.dxf.center.x, entity.dxf.center.y),
                    entity.dxf.radius,
                    fill=False, color='blue'
                )
                ax.add_artist(circle)
                all_x_coords.extend([entity.dxf.center.x - entity.dxf.radius,
                                     entity.dxf.center.x + entity.dxf.radius])
                all_y_coords.extend([entity.dxf.center.y - entity.dxf.radius,
                                     entity.dxf.center.y + entity.dxf.radius])
            elif entity.dxftype() == "ARC":
                arc = plt.matplotlib.patches.Arc(
                    (entity.dxf.center.x, entity.dxf.center.y),
                    2 * entity.dxf.radius,
                    2 * entity.dxf.radius,
                    theta1=entity.dxf.start_angle,
                    theta2=entity.dxf.end_angle,
                    color='blue'
                )
                ax.add_artist(arc)
                all_x_coords.extend([entity.dxf.center.x - entity.dxf.radius,
                                     entity.dxf.center.x + entity.dxf.radius])
                all_y_coords.extend([entity.dxf.center.y - entity.dxf.radius,
                                     entity.dxf.center.y + entity.dxf.radius])

        # Plot offset geometry
        if self.offset_entities:
            for entity in self.offset_entities:
                if entity['type'] == 'CIRCLE':
                    circle = plt.Circle(
                        entity['center'],
                        entity['radius'],
                        fill=False, color='red'
                    )
                    ax.add_artist(circle)
                    all_x_coords.extend([entity['center'][0] - entity['radius'],
                                         entity['center'][0] + entity['radius']])
                    all_y_coords.extend([entity['center'][1] - entity['radius'],
                                         entity['center'][1] + entity['radius']])
                elif entity['type'] == 'ARC':
                    arc = plt.matplotlib.patches.Arc(
                        entity['center'],
                        2 * entity['radius'],
                        2 * entity['radius'],
                        theta1=entity['start_angle'],
                        theta2=entity['end_angle'],
                        color='red'
                    )
                    ax.add_artist(arc)
                    all_x_coords.extend([entity['center'][0] - entity['radius'],
                                         entity['center'][0] + entity['radius']])
                    all_y_coords.extend([entity['center'][1] - entity['radius'],
                                         entity['center'][1] + entity['radius']])

        # Adjust the view to fit all entities with padding
        if all_x_coords and all_y_coords:
            x_min, x_max = min(all_x_coords), max(all_x_coords)
            y_min, y_max = min(all_y_coords), max(all_y_coords)

            # Add 10% padding
            x_padding = (x_max - x_min) * 0.1
            y_padding = (y_max - y_min) * 0.1

            ax.set_xlim(x_min - x_padding, x_max + x_padding)
            ax.set_ylim(y_min - y_padding, y_max + y_padding)

        ax.set_aspect('equal')
        ax.grid(True)

        # Add legend
        blue_line = plt.Line2D([0], [0], color='blue', label='Original')
        red_line = plt.Line2D([0], [0], color='red', label='Offset')
        ax.legend(handles=[blue_line, red_line])

        self.canvas.draw()

    def save_dxf(self):
        if not self.dxf_file or not self.offset_entities:
            print("DXF file or offset entities missing.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Offset DXF",
            "",
            "DXF Files (*.dxf)"
        )

        if file_path:
            if not file_path.lower().endswith('.dxf'):
                file_path += '.dxf'

            success = arc_circle.add_offset_to_dxf(
                self.dxf_file,
                self.offset_entities,
                file_path
            )

            if success:
                print(f"Offset drawing saved to {file_path}")

    def go_back(self):
        self.parent_app.setup_ui()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Apply global stylesheet
    app.setStyleSheet(get_stylesheet(DARK_THEME))

    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec_())