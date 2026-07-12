import bpy
import csv
from pathlib import Path

root = Path(bpy.data.filepath).parents[2]
output = root / "engineering" / "internal_assembly_manifest.csv"
rows = []
for obj in sorted((o for o in bpy.data.objects if o.get("bb8_internal")), key=lambda o: o.name):
    dimensions = obj.dimensions
    location = obj.matrix_world.translation
    rows.append({
        "object": obj.name,
        "type": obj.type,
        "size_x_mm": round(dimensions.x * 1000, 2),
        "size_y_mm": round(dimensions.y * 1000, 2),
        "size_z_mm": round(dimensions.z * 1000, 2),
        "center_x_mm": round(location.x * 1000, 2),
        "center_y_mm": round(location.y * 1000, 2),
        "center_z_mm": round(location.z * 1000, 2),
        "notes": obj.get("material", obj.get("verified_envelope_mm", obj.get("vendor_envelope_mm",
                 obj.get("envelope_mm", obj.get("rail_size_mm", obj.get("bar_size_mm", ""))))))
    })
with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys(), lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
print("MANIFEST", output, "objects", len(rows))
