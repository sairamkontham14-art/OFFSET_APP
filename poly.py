import ezdxf
from math import sqrt
import tkinter as tk
from tkinter import simpledialog


def process_dxf(dxf_file, offset_distance):
    """Processes the DXF file, extracts polygons and applies offset."""
    try:
        print("Starting DXF processing...")
        doc, polygons, offset_polygons = extract_2d_coordinates_and_apply_offset(dxf_file, offset_distance)
        print("DXF processing completed.")

        if not polygons:
            print("Error: No valid polygons found in the DXF file")
            return None, None, None

        if not offset_polygons:
            print("Error: Failed to generate offset polygons")
            return None, None, None

        for polygon in offset_polygons:
            if not polygon:
                print("Error: Empty polygon found in offset results")
                return None, None, None

        return doc, polygons, offset_polygons

    except Exception as e:
        print(f"Error processing DXF: {str(e)}")
        return None, None, None

def round_coordinates(coord, decimals=2):
    """Helper function to round coordinates to the specified number of decimals."""
    if isinstance(coord, ezdxf.math.Vec3):  # Convert Vec3 to tuple
        coord = (coord.x, coord.y, coord.z)
    if isinstance(coord, tuple):
        return tuple(round(c, decimals) for c in coord[:2])  # Strip the z-coordinate
    elif isinstance(coord, list):
        return [round(c, decimals) for c in coord]
    else:
        return round(coord, decimals)

def group_lines_into_polygon(lines):
    """Group line endpoints into sets representing polygon sides."""
    if not lines:
        return []

    polygons = []
    unvisited_lines = set(lines)

    while unvisited_lines:
        current_line = unvisited_lines.pop()
        current_polygon = [current_line]

        while True:
            found = False
            for other_line in list(unvisited_lines):
                if current_line[1] == other_line[0]:
                    current_polygon.append(other_line)
                    unvisited_lines.remove(other_line)
                    current_line = other_line
                    found = True
                    break
                elif current_line[1] == other_line[1]:
                    flipped_line = (other_line[1], other_line[0])
                    current_polygon.append(flipped_line)
                    unvisited_lines.remove(other_line)
                    current_line = flipped_line
                    found = True
                    break
            if not found:
                break

        if len(current_polygon) > 1 and current_polygon[-1][1] == current_polygon[0][0]:
            polygons.append(current_polygon)

    return polygons

def calculate_offset(line, distance):
    """Calculate the offset of a line by a given distance."""
    try:
        (x1, y1), (x2, y2) = line  # Unpack 2D points
    except ValueError:
        raise ValueError(f"Invalid line format: {line}")

    # Calculate the unit vector perpendicular to the line
    dx, dy = x2 - x1, y2 - y1
    length = sqrt(dx ** 2 + dy ** 2)
    if length == 0:
        raise ValueError("Cannot offset a line with zero length")
    unit_perpendicular = (-dy / length, dx / length)

    # Offset both points by the perpendicular vector
    offset_start = (x1 + unit_perpendicular[0] * distance, y1 + unit_perpendicular[1] * distance)
    offset_end = (x2 + unit_perpendicular[0] * distance, y2 + unit_perpendicular[1] * distance)

    return round_coordinates(offset_start), round_coordinates(offset_end)

def extract_2d_coordinates_and_apply_offset(dxf_file, offset_distance):
    try:
        # Load the DXF file
        doc = ezdxf.readfile(dxf_file)

        # Get the modelspace where all entities are stored
        modelspace = doc.modelspace()

        # Extract lines
        lines = []
        for entity in modelspace:
            if entity.dxftype() == "LINE":
                start_point = round_coordinates(entity.dxf.start)
                end_point = round_coordinates(entity.dxf.end)
                lines.append((start_point, end_point))

        # Group lines into polygons
        polygons = group_lines_into_polygon(lines)

        # Apply offset to each line in the polygons
        offset_polygons = []
        for polygon in polygons:
            offset_polygon = [calculate_offset(line, offset_distance) for line in polygon]
            offset_polygons.append(offset_polygon)

        return doc, polygons, offset_polygons

    except Exception as e:
        print(f"Error reading DXF file: {e}")
        return None, None, None

def add_offset_lines_to_dxf(dxf_file, offset_polygons, color=1):
    """Add offset lines to the DXF file and set their color to red (Color 1)."""
    if offset_polygons is None:
        print("Error: No offset polygons provided")
        return False

    try:
        # Create a new DXF document
        doc = ezdxf.new()
        msp = doc.modelspace()

        # Read the original DXF file to copy original geometry
        original_doc = ezdxf.readfile(dxf_file)
        original_msp = original_doc.modelspace()

        # Copy original geometry
        for entity in original_msp:
            if entity.dxftype() == "LINE":
                start_point = (entity.dxf.start.x, entity.dxf.start.y, 0)
                end_point = (entity.dxf.end.x, entity.dxf.end.y, 0)
                msp.add_line(start_point, end_point)

        # Add the offset lines in red
        for polygon in offset_polygons:
            for offset_line in polygon:
                start_point = (offset_line[0][0], offset_line[0][1], 0)
                end_point = (offset_line[1][0], offset_line[1][1], 0)
                msp.add_line(start_point, end_point, dxfattribs={'color': color})

        # Generate output filename with full path
        import os
        dir_path = os.path.dirname(dxf_file)
        base_name = os.path.basename(dxf_file)
        output_file = os.path.join(dir_path, "offset_" + base_name)

        # Save as a new DXF file
        doc.saveas(output_file)
        print(f"Offset lines added and saved to {output_file}")
        return True

    except Exception as e:
        print(f"Error adding offset lines: {str(e)}")
        return False

def create_offset_endpoints_set(offset_polygons):
    """Create a set of two offset endpoints for each line in the offset polygons."""
    offset_endpoints_sets = []
    for polygon in offset_polygons:
        for offset_line in polygon:
            offset_endpoints_sets.append(set(offset_line))  # Add the two endpoints as a set
    return offset_endpoints_sets

def calculate_line_equation(offset_line):
    """Calculate the equation of a line in the form Ax + By + C = 0"""
    (x1, y1), (x2, y2) = offset_line
    A = (y2 - y1)
    B = -(x2 - x1)
    C = A * x1 + B * y1
    return (A, B, C)

def create_equations_of_adjacent_lines(offset_polygons):
    """Create sets of two adjacent line equations for each polygon in the offset polygons."""
    adjacent_line_equations_sets = []

    for polygon in offset_polygons:
        for i in range(len(polygon)):
            # Get the two consecutive lines in the polygon
            line1 = polygon[i]
            line2 = polygon[(i + 1) % len(polygon)]  # Wrap around to the first line at the end of the polygon

            # Calculate the equations of the two lines
            equation1 = calculate_line_equation(line1)
            equation2 = calculate_line_equation(line2)

            # Add the pair of equations as a set
            adjacent_line_equations_sets.append((equation1, equation2))

    return adjacent_line_equations_sets

def solve_line_equations(eq1, eq2):
    """Solve the system of two linear equations to find the intersection point (x, y)."""
    A1, B1, C1 = eq1
    A2, B2, C2 = eq2

    # Calculate the determinant of the coefficient matrix
    denominator = A1 * B2 - A2 * B1

    # Check if the lines are parallel (denominator == 0)
    if denominator == 0:
        return None  # Lines are parallel, no intersection point

    # Calculate x and y using Cramer's rule
    x = (B1 * (-C2) - B2 * (-C1)) / denominator
    y = (A2 * (-C1) - A1 * (-C2)) / denominator

    return (x, y)

def find_intersection_points_of_adjacent_lines(adjacent_equations_sets):
    intersection_points = []
    for eq1, eq2 in adjacent_equations_sets:
        intersection = solve_line_equations(eq1, eq2)
        if intersection:
            # Round intersection points to 2 decimal places
            rounded_intersection = (round(intersection[0], 2), round(intersection[1], 2))
            intersection_points.append(rounded_intersection)
    return intersection_points

def add_line_equation_to_dxf(modelspace, line, offset_distance, color=1):
    """Add offset lines to the DXF modelspace without equations."""
    for offset_line in line:
        start_point, end_point = offset_line
        # Add the line to the modelspace (no need for equation text)
        modelspace.add_line(start_point, end_point, dxfattribs={'color': color})

        # Remove the part where equations were being added:
        # modelspace.add_text(equation_text, dxfattribs={'height': 1.0, 'insert': mid_point})

def add_offset_lines_and_equations_to_dxf(dxf_file, offset_polygons, color=1):
    """Add only offset lines to the DXF file (no equations)."""
    try:
        doc, polygons, _ = extract_2d_coordinates_and_apply_offset(dxf_file, 5)  # Assuming a 5mm offset
        if doc is None:
            return

        # Get the modelspace where entities are added
        modelspace = doc.modelspace()

        # Add the offset lines to the modelspace
        for polygon in offset_polygons:
            add_line_equation_to_dxf(modelspace, polygon, 5, color)  # This function now adds only lines

        # Save the updated DXF file
        output_file = "updated_with_offset_lines_" + dxf_file  # Updated file name without equations
        doc.saveas(output_file)
        print(f"Offset lines added to {output_file}")
    except Exception as e:
        print(f"Error adding offset lines: {e}")

if __name__ == "__main__":
    # Ask the user for input
    dxf_file_path = "polygon.dxf"  # Replace with your DXF file name
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    offset_distance_mm = None

    while offset_distance_mm is None:
        try:
            user_input = 0
            if user_input is None:
                print("Operation cancelled.")
                exit(0)
            offset_distance_mm = float(user_input)
        except ValueError as ve:
            print(f"Invalid input: {ve}")
            offset_distance_mm = None  # Reset to re-prompt the user
    else:
        doc, polygons, offset_polygons = extract_2d_coordinates_and_apply_offset(dxf_file_path, offset_distance_mm)

        if polygons and offset_polygons:
            print("Original Polygons:")
            for i, polygon in enumerate(polygons, start=1):
                print(f"Polygon {i}:")
                for line in polygon:
                    print(f"  Line: {line}")

            print("\nOffset Polygons:")
            for i, offset_polygon in enumerate(offset_polygons, start=1):
                print(f"Offset Polygon {i}:")
                for line in offset_polygon:
                    print(f"  Offset Line: {line}")

            # Create and print set of offset endpoints
            offset_endpoints_sets = create_offset_endpoints_set(offset_polygons)
            print("\nSet of Offset Endpoints:")
            for idx, endpoints in enumerate(offset_endpoints_sets, start=1):
                print(f"Offset Endpoints Set {idx}: {endpoints}")

            def create_set_of_adjacent_intersection_points(intersection_points):
                adjacent_intersection_sets = []

                # Loop through the intersection points to group adjacent pairs
                for i in range(len(intersection_points)):
                    point1 = intersection_points[i]
                    point2 = intersection_points[(i + 1) % len(intersection_points)]  # Wrap around to form a closed loop

                    # Add as a set (unordered pair)
                    adjacent_intersection_sets.append({point1, point2})

                return adjacent_intersection_sets

            # Create sets of adjacent line equations
            equations_sets = create_equations_of_adjacent_lines(offset_polygons)
            print("\nSets of Two Adjacent Line Equations:")
            for idx, equations in enumerate(equations_sets, start=1):
                eq1, eq2 = equations
                print(
                    f"Set {idx}: Line 1 Equation: {eq1[0]}x + {eq1[1]}y + {eq1[2]} = 0, Line 2 Equation: {eq2[0]}x + {eq2[1]}y + {eq2[2]} = 0")

            # Find intersection points of adjacent lines
            intersection_points = find_intersection_points_of_adjacent_lines(equations_sets)
            print("\nIntersection Points of Adjacent Lines:")
            for idx, point in enumerate(intersection_points, start=1):
                print(f"Intersection {idx}: {point}")

            def add_lines_between_intersections(modelspace, adjacent_intersection_sets, color=1):
                """Add lines between adjacent intersection points in the DXF modelspace."""
                for adjacent_set in adjacent_intersection_sets:
                    # Convert the set to a list to get the two points
                    intersection_points = list(adjacent_set)

                    # Ensure there are exactly two points in the set
                    if len(intersection_points) == 2:
                        start_point, end_point = intersection_points
                        # Add a line between the two points in the modelspace
                        modelspace.add_line(start_point, end_point, dxfattribs={'color': color})

            # Create a set of adjacent intersection points
            adjacent_intersection_sets = create_set_of_adjacent_intersection_points(intersection_points)
            print("\nSet of Adjacent Intersection Points:")
            for idx, adjacent_set in enumerate(adjacent_intersection_sets, start=1):
                print(f"Set {idx}: {adjacent_set}")
                # Get the modelspace where entities are added
                doc, polygons, offset_polygons = extract_2d_coordinates_and_apply_offset(dxf_file_path, offset_distance_mm)

                if doc:
                    modelspace = doc.modelspace()

                    # Add lines between adjacent intersection points
                    add_lines_between_intersections(modelspace, adjacent_intersection_sets, color=1)

                    # Save the updated DXF file
                    output_file = "updated_with_intersection_lines_" + dxf_file_path
                    doc.saveas(output_file)
                    print(f"Lines between adjacent intersection points added to {output_file}")
