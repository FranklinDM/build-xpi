#!/usr/bin/python3

import os
import re
import xml.etree.ElementTree as ET
import zipfile

src_dir = os.environ.get("SOURCE_DIR", "src").strip()
manifest_path = os.path.join(src_dir, "install.rdf")
if not os.path.exists(manifest_path):
    raise FileNotFoundError(f"Manifest not found at {manifest_path}")

# Preserve XML namespace prefixes on write
ET.register_namespace("", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
ET.register_namespace("em", "http://www.mozilla.org/2004/em-rdf#")

ns = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "em": "http://www.mozilla.org/2004/em-rdf#",
}

tree = ET.parse(manifest_path)
root = tree.getroot()

# 1. Extract base version
version_elem = root.find(".//em:version", ns)
if version_elem is None or not version_elem.text:
    raise ValueError("Could not find <em:version> in install.rdf")
base_version = version_elem.text.strip()
is_prerelease = bool(re.search(r"[0-9](a|b|rc)[0-9]+$", base_version))
print(f"Prerelease detected: {is_prerelease}")

# 2. Append short commit hash to version if not a tagged release
ref_type = os.environ.get("REF_TYPE", "")
commit_sha = os.environ.get("SHA", "")
short_sha = commit_sha[:7] if commit_sha else "dev"

if ref_type == "tag":
    final_version = base_version
    print(f"Tagged release detected. Keeping version: {final_version}")
else:
    final_version = f"{base_version}.{short_sha}"
    print(f"Non-tag build detected. Updating version to: {final_version}")
    version_elem.text = final_version
    # Write modified install.rdf back to src/
    tree.write(manifest_path, encoding="utf-8", xml_declaration=True)

# 3. Map application GUIDs
app_map = {
    "{8de7fcbb-c55c-4fbe-bfc5-fc555c87dbc4}": "pm",  # Pale Moon
    "{ec8030f7-c20a-464f-9b0e-13a3a9e97384}": "fx",  # Firefox
    "{3550f703-e582-4d05-9a08-453d09bdfdc6}": "tb",  # Thunderbird
    "{4523665a-317f-4a66-9376-3763d1ad1978}": "am",  # Ambassador
    "{29877c1d-27df-4421-9a79-382c31470151}": "es",  # Epyrus
}

# Target applications: search for all em:id nested under em:targetApplication
detected_apps = []
for target in root.findall(".//em:targetApplication//em:id", ns):
    if target.text:
        guid = target.text.strip().lower()
        if guid in app_map and app_map[guid] not in detected_apps:
            detected_apps.append(app_map[guid])

app_suffix = "+".join(detected_apps) if detected_apps else "unknown"

package_name = os.environ.get("PACKAGE_NAME", "addon")
xpi_filename = f"{package_name}-{final_version}-{app_suffix}.xpi"
print(f"Building: {xpi_filename}")

# 4. Pack src/ contents into root of XPI
with zipfile.ZipFile(xpi_filename, "w", zipfile.ZIP_DEFLATED) as xpi:
    for root_dir, dirs, files in os.walk(src_dir):
        # Exclude git and github directories if running on repo root
        dirs[:] = [d for d in dirs if d not in (".git", ".github")]
        for file in files:
            abs_path = os.path.join(root_dir, file)
            # Prevent including the output XPI into itself if building from repo root
            if os.path.abspath(abs_path) == os.path.abspath(xpi_filename):
                continue
            arcname = os.path.relpath(abs_path, start=src_dir)
            xpi.write(abs_path, arcname)

# Pass the values cleanly to downstream steps
with open(os.environ["GITHUB_OUTPUT"], "a") as out_file:
    out_file.write(f"xpi_filename={xpi_filename}\n")
    out_file.write(f"is_prerelease={'true' if is_prerelease else 'false'}\n")
