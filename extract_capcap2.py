import zipfile
import os

zip_path = r"c:\Users\Nguyen Trong Khoi\Downloads\CAPCAP\CapCap_2.zip"
extract_dir = r"c:\Users\Nguyen Trong Khoi\Downloads\CAPCAP\CapCap_2_extracted"

os.makedirs(extract_dir, exist_ok=True)
print(f"Opening {zip_path}...")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    namelist = zip_ref.namelist()
    print(f"Total files: {len(namelist)}")
    print("Sample items:")
    for name in namelist[:25]:
        print(" -", name)
    print("Extracting...")
    zip_ref.extractall(extract_dir)
    print("Extraction complete!")
