import ezdxf
import math
from math import cos, sin, radians, pi


def process_dxf(dxf_file, offset_distance):
    """Process DXF file and create offset for circles and arcs"""
    try:
        print("Starting DXF processing...")
        doc = ezdxf.readfile(dxf_file)
        msp = doc.modelspace()
        offset_entities = []

        for entity in msp:
            if entity.dxftype() == "CIRCLE":
                print("Processing CIRCLE entity...")
                center = (entity.dxf.center.x, entity.dxf.center.y)
                radius = entity.dxf.radius
                new_radius = radius + offset_distance
                if new_radius > 0:
                    offset_entities.append({
                        'type': 'CIRCLE',
                        'center': center,
                        'radius': new_radius
                    })

            elif entity.dxftype() == "ARC":
                print("Processing ARC entity...")
                center = (entity.dxf.center.x, entity.dxf.center.y)
                radius = entity.dxf.radius
                start_angle = entity.dxf.start_angle
                end_angle = entity.dxf.end_angle
                new_radius = radius + offset_distance
                if new_radius > 0:
                    offset_entities.append({
                        'type': 'ARC',
                        'center': center,
                        'radius': new_radius,
                        'start_angle': start_angle,
                        'end_angle': end_angle
                    })

        print("DXF processing completed.")
        return offset_entities

    except Exception as e:
        print(f"Error processing DXF: {str(e)}")
        return None


def add_offset_to_dxf(dxf_file, offset_entities, output_file):
    """Save offset circles and arcs to new DXF"""
    try:
        doc = ezdxf.readfile(dxf_file)
        msp = doc.modelspace()

        # Add offset entities in red
        for entity in offset_entities:
            if entity['type'] == 'CIRCLE':
                msp.add_circle(
                    center=(entity['center'][0], entity['center'][1], 0),
                    radius=entity['radius'],
                    dxfattribs={'color': 1}
                )
            elif entity['type'] == 'ARC':
                msp.add_arc(
                    center=(entity['center'][0], entity['center'][1], 0),
                    radius=entity['radius'],
                    start_angle=entity['start_angle'],
                    end_angle=entity['end_angle'],
                    dxfattribs={'color': 1}
                )

        doc.saveas(output_file)
        return True

    except Exception as e:
        print(f"Error saving DXF: {str(e)}")
        return False