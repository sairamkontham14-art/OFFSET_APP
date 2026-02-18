DXF Circle & Arc Offset Tool

A simple Python utility to process a DXF file and generate offset versions of CIRCLE and ARC entities.
The offset entities are saved into a new DXF file and displayed in red color for easy identification.

📌 Features

Reads DXF files using ezdxf

Detects:

CIRCLE entities

ARC entities

Creates outward or inward offsets (based on offset distance)

Saves offset entities into a new DXF file

Offset entities are colored Red (Color Code: 1)

🛠 Requirements

Install the required library before running the script:

pip install ezdxf


Python version: 3.x recommended

📂 Project Structure
.
├── your_script.py
├── input.dxf
└── output.dxf

⚙️ Functions Overview
1️⃣ process_dxf(dxf_file, offset_distance)

Processes the DXF file and calculates offset entities.

Parameters:

dxf_file → Path to input DXF file

offset_distance → Offset value (positive or negative)

Returns:

List of offset entities (circles and arcs)

None if error occurs

2️⃣ add_offset_to_dxf(dxf_file, offset_entities, output_file)

Adds the offset entities into a new DXF file.

Parameters:

dxf_file → Original DXF file

offset_entities → Output from process_dxf

output_file → New DXF file path

Returns:

True if successful

False if error occurs

▶️ How to Use

Example usage:

input_file = "input.dxf"
output_file = "output.dxf"
offset_distance = 5  # Change as needed

entities = process_dxf(input_file, offset_distance)

if entities:
    add_offset_to_dxf(input_file, entities, output_file)

📐 How Offset Works

For each entity:

🔵 Circle

New Radius = Original Radius + Offset Distance

If the new radius becomes ≤ 0, the entity is ignored.

🟠 Arc

New Radius = Original Radius + Offset Distance
Start and End angles remain unchanged.

🎨 Output Behavior

Offset entities are added to the same model space

Offset entities are colored Red

Original geometry remains unchanged

⚠️ Limitations

Supports only:

CIRCLE

ARC

Does not support:

LINE

POLYLINE

SPLINE

ELLIPSE

Offset direction depends only on radius addition (not geometric side offset)

No GUI (command-line usage only)

🚀 Future Improvements

Add support for:

Lines

Polylines

Add inward/outward direction control

Add GUI interface

Add layer control for offset entities

Add batch processing

👨‍💻 Author

Developed using Python and ezdxf library for DXF manipulation.
