import ezdxf
from math import cos, sin, radians
import numpy as np
from ezdxf.math import UCS, Vec3


def get_active_ucs(doc):
    """
    Get the active UCS from the DXF document
    """
    try:
        ucs_origin = doc.header.get('$UCSORG', (0, 0, 0))
        ucs_xaxis = doc.header.get('$UCSXDIR', (1, 0, 0))
        ucs_yaxis = doc.header.get('$UCSYDIR', (0, 1, 0))

        return UCS(
            origin=ucs_origin,
            ux=ucs_xaxis,
            uy=ucs_yaxis,
        )
    except Exception as e:
        print(f"Error getting UCS: {e}")
        return None


def transform_wcs_to_ucs(point, ucs):
    """
    Transform a point from WCS to UCS
    """
    try:
        if isinstance(point, tuple):
            point = Vec3(point[0], point[1], 0)

        # Transform from WCS to UCS
        ucs_point = ucs.from_wcs(point)
        return (round(ucs_point.x, 2), round(ucs_point.y, 2))
    except Exception as e:
        print(f"Error transforming point WCS to UCS: {e}")
        return point


def are_points_equal(point1, point2, tolerance=0.001):
    """
    Compare two points with a small tolerance to account for floating point precision
    """
    return (abs(point1[0] - point2[0]) < tolerance and
            abs(point1[1] - point2[1]) < tolerance)


def find_leftmost_entity(entities):
    """
    Find the entity with the leftmost starting point
    """
    return min(entities, key=lambda x: (x['start_point'][0], x['start_point'][1]))


def find_connected_entity(current_entity, remaining_entities, tolerance=0.001):
    """
    Find the entity that connects to the current entity's end point
    """
    for i, entity in enumerate(remaining_entities):
        # Check if the start point of this entity matches the end point of current entity
        if are_points_equal(current_entity['end_point'], entity['start_point'], tolerance):
            return i, entity

        # Check if the end point of this entity matches the end point of current entity
        # If so, we need to reverse this entity
        if are_points_equal(current_entity['end_point'], entity['end_point'], tolerance):
            # Create a reversed version of the entity
            reversed_entity = entity.copy()
            reversed_entity['start_point'], reversed_entity['end_point'] = entity['end_point'], entity['start_point']
            reversed_entity['start_point_wcs'], reversed_entity['end_point_wcs'] = entity['end_point_wcs'], entity[
                'start_point_wcs']
            if entity['direction']:
                reversed_entity['direction'] = "Clockwise" if entity[
                                                                  'direction'] == "Anti-clockwise" else "Anti-clockwise"
            return i, reversed_entity

    return None, None


def arrange_entities_systematically(results):
    """
    Arrange entities systematically starting from the leftmost point
    """
    if not results:
        return []

    # Start with a copy of the results
    remaining = results.copy()
    arranged = []

    # Find the leftmost entity to start with
    current = find_leftmost_entity(remaining)
    remaining.remove(current)
    arranged.append(current)

    # Continue until all entities are processed
    while remaining:
        # Find the next connected entity
        index, next_entity = find_connected_entity(arranged[-1], remaining)

        if index is not None:
            arranged.append(next_entity)
            remaining.pop(index)
        else:
            # If no connection found, start a new chain with the leftmost remaining entity
            current = find_leftmost_entity(remaining)
            remaining.remove(current)
            arranged.append(current)

    # Update serial numbers and names
    line_count = 1
    arc_count = 1
    for i, entity in enumerate(arranged):
        entity['sl_no'] = i + 1
        if entity['radius'] == 0:
            entity['name'] = f"Line{line_count}"
            line_count += 1
        else:
            entity['name'] = f"Arc{arc_count}"
            arc_count += 1

    return arranged


def generate_gcode(results, feed_rate=200, z_safe=200.0, z_cut=0.0):
    """
    Generate G-code from the arranged entities
    """
    gcode = []

    # Initial setup
    gcode.append("G00 G54 G17 G90 G40")  # Initialize: Work offset G54, XY plane, absolute programming, cancel cutter compensation
    gcode.append(f"G00 Z{z_safe}")  # Rapid move to safe Z height
    gcode.append("M6 T07")  # Tool change to tool 07
    gcode.append("G00 X100 Y100")  # Rapid move to initial XY position
    gcode.append("M03 S500")  # Start spindle clockwise at 500 RPM
    gcode.append("G00 Z2")  # Rapid move to Z2 above workpiece
    gcode.append(f"G01 Z{z_cut} F{feed_rate}")  # Plunge to Z0 at feed rate
    gcode.append("M07")  # Coolant on
    gcode.append("G01 G42 X80 Y0")  # Enable cutter compensation right, move to start point

    first_point = True

    for entity in results:
        if first_point:
            # Rapid move to start point
            gcode.append(f"G00 X{entity['start_point'][0]:.2f} Y{entity['start_point'][1]:.2f}")
            gcode.append(f"G01 Z{z_cut} F{feed_rate}")  # Plunge to Z0
            first_point = False

        if entity['radius'] == 0:  # Line
            # Linear movement to end point
            gcode.append(f"G01 X{entity['end_point'][0]:.2f} Y{entity['end_point'][1]:.2f} F{feed_rate}")

        else:  # Arc
            # Calculate arc center relative to start point (IJK format)
            i = entity['center'][0] - entity['start_point'][0]
            j = entity['center'][1] - entity['start_point'][1]

            # Choose G2 (clockwise) or G3 (counterclockwise)
            g_command = "G02" if entity['direction'] == "Clockwise" else "G03"

            # Arc movement
            gcode.append(f"{g_command} X{entity['end_point'][0]:.2f} Y{entity['end_point'][1]:.2f} "
                         f"I{i:.2f} J{j:.2f} F{feed_rate}")

    # End program
    gcode.append("G00 G40 Z200")  # Cancel cutter compensation, rapid move to safe Z height
    gcode.append("M30")  # End of program

    return gcode


def save_gcode_to_file(file_path, gcode):
    """
    Save G-code to a file
    """
    try:
        with open(file_path, 'w') as file:
            for line in gcode:
                file.write(line + "\n")
        print(f"G-code saved to {file_path}")
    except Exception as e:
        print(f"Error saving G-code: {e}")


def save_output_to_notepad(file_path, results, use_ucs=True):
    """
    Save the output to a notepad file.
    If use_ucs is True, only UCS coordinates are shown.
    If use_ucs is False, only WCS coordinates are shown.
    """
    try:
        text_content = "Vertexes and Coordinates \n\n"

        for item in results:
            if item["radius"] == 0:  # Line
                if use_ucs:
                    text_content += (
                        f"LINE: Start Point: ({item['start_point'][0]}, {item['start_point'][1]})\n"
                        f"      End Point: ({item['end_point'][0]}, {item['end_point'][1]})\n"
                    )
                else:
                    text_content += (
                        f"LINE: Start Point WCS: ({item['start_point_wcs'][0]}, {item['start_point_wcs'][1]})\n"
                        f"      End Point WCS: ({item['end_point_wcs'][0]}, {item['end_point_wcs'][1]})\n"
                    )
            elif item["radius"] > 0:  # Arc
                if use_ucs:
                    text_content += (
                        f"ARC: Start Point: ({item['start_point'][0]}, {item['start_point'][1]})\n"
                        f"     End Point: ({item['end_point'][0]}, {item['end_point'][1]})\n"
                        f"     Center: ({item['center'][0]}, {item['center'][1]})\n"
                        f"     Radius: {item['radius']}, Direction: {item['direction']}\n"
                    )
                else:
                    text_content += (
                        f"ARC: Start Point WCS: ({item['start_point_wcs'][0]}, {item['start_point_wcs'][1]})\n"
                        f"     End Point WCS: ({item['end_point_wcs'][0]}, {item['end_point_wcs'][1]})\n"
                        f"     Center WCS: ({item['center_wcs'][0]}, {item['center_wcs'][1]})\n"
                        f"     Radius: {item['radius']}, Direction: {item['direction']}\n"
                    )

        with open(file_path, 'w') as file:
            file.write(text_content)

        print(f"Output saved to {file_path}")

    except Exception as e:
        print(f"Error: {e}")


def process_dxf(file_path):
    try:
        # Load the DXF file
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()
        results = []

        # Get active UCS
        active_ucs = get_active_ucs(doc)
        if active_ucs:
            print("Active UCS found with:")
            print(f"Origin: {doc.header.get('$UCSORG', (0, 0, 0))}")
            print(f"X-axis: {doc.header.get('$UCSXDIR', (1, 0, 0))}")
            print(f"Y-axis: {doc.header.get('$UCSYDIR', (0, 1, 0))}")
        else:
            print("No active UCS found, using WCS")

        for entity in msp:
            if entity.dxftype() == 'LINE':
                start_wcs = entity.dxf.start
                end_wcs = entity.dxf.end

                start_wcs_coords = (round(start_wcs.x, 2), round(start_wcs.y, 2))
                end_wcs_coords = (round(end_wcs.x, 2), round(end_wcs.y, 2))

                if active_ucs:
                    start_ucs = transform_wcs_to_ucs(start_wcs, active_ucs)
                    end_ucs = transform_wcs_to_ucs(end_wcs, active_ucs)
                else:
                    start_ucs = start_wcs_coords
                    end_ucs = end_wcs_coords

                results.append({
                    "sl_no": 0,  # Will be updated after arrangement
                    "name": "",  # Will be updated after arrangement
                    "start_point": start_ucs,
                    "end_point": end_ucs,
                    "start_point_wcs": start_wcs_coords,
                    "end_point_wcs": end_wcs_coords,
                    "radius": 0,
                    "direction": None,
                    "center": None,
                    "center_wcs": None
                })

            elif entity.dxftype() == 'ARC':
                center_wcs = entity.dxf.center
                radius = entity.dxf.radius
                start_angle = entity.dxf.start_angle
                end_angle = entity.dxf.end_angle

                center_wcs_coords = (round(center_wcs.x, 2), round(center_wcs.y, 2))

                start_angle_rad = radians(start_angle)
                end_angle_rad = radians(end_angle)

                start_point_wcs = (
                    round(center_wcs.x + radius * cos(start_angle_rad), 2),
                    round(center_wcs.y + radius * sin(start_angle_rad), 2)
                )
                end_point_wcs = (
                    round(center_wcs.x + radius * cos(end_angle_rad), 2),
                    round(center_wcs.y + radius * sin(end_angle_rad), 2)
                )

                if active_ucs:
                    center_ucs = transform_wcs_to_ucs(center_wcs, active_ucs)
                    start_point_ucs = transform_wcs_to_ucs(start_point_wcs, active_ucs)
                    end_point_ucs = transform_wcs_to_ucs(end_point_wcs, active_ucs)
                else:
                    center_ucs = center_wcs_coords
                    start_point_ucs = start_point_wcs
                    end_point_ucs = end_point_wcs

                direction = "Clockwise" if end_angle > start_angle else "Anti-clockwise"

                results.append({
                    "sl_no": 0,  # Will be updated after arrangement
                    "name": "",  # Will be updated after arrangement
                    "start_point": start_point_ucs,
                    "end_point": end_point_ucs,
                    "start_point_wcs": start_point_wcs,
                    "end_point_wcs": end_point_wcs,
                    "radius": round(radius, 2),
                    "direction": direction,
                    "center": center_ucs,
                    "center_wcs": center_wcs_coords
                })

        return results

    except Exception as e:
        print(f"Error processing DXF: {e}")
        return str(e)


if __name__ == "__main__":
    file_path = "Trail component.dxf"
    results = process_dxf(file_path)

    if isinstance(results, list):
        # Use the systematic arrangement function
        arranged_results = arrange_entities_systematically(results)

        # Print results in a structured format
        print("\nResults:")
        print(
            f"{'SL No':<8}{'NAME':<10}{'START (UCS)':<25}{'END (UCS)':<25}{'RADIUS':<10}{'DIRECTION':<15}")
        print("-" * 140)

        for item in arranged_results:
            start_ucs = f"({item['start_point'][0]}, {item['start_point'][1]})"
            end_ucs = f"({item['end_point'][0]}, {item['end_point'][1]})"

            print(
                f"{item['sl_no']:<8}{item['name']:<10}{start_ucs:<25}{end_ucs:<25}{item['radius']:<10}",
                end="")
            if item['direction']:
                print(f"{item['direction']:<15}")
            else:
                print("")

        # Determine if UCS is active
        doc = ezdxf.readfile(file_path)
        active_ucs = get_active_ucs(doc)
        use_ucs = active_ucs is not None

        # Save original output
        save_output_to_notepad("output.txt", arranged_results, use_ucs=use_ucs)

        # Generate and save G-code
        gcode = generate_gcode(arranged_results)
        save_gcode_to_file("cnc_code.txt", gcode)
    else:
        print(f"Error: {results}")