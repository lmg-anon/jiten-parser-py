import zipfile
import pathlib
import sys
import tempfile
import glob

def main():
    try:
        package_path = pathlib.Path(__file__).parent.resolve()
    except NameError:
        print("Error: Could not determine the package installation path.")
        sys.exit(1)

    files_to_extract = [
        (
            package_path / "jmdict" / "data" / "jmdict.zip.001",
            "jmdict.db",
            "JMDict Database"
        ),
        (
            package_path / "resources" / "system_full.zip",
            "system_full.dic",
            "Sudachi Dictionary"
        ),
    ]

    print("Starting Jiten-Parser data setup...")
    all_successful = True

    for zip_path, filename, description in files_to_extract:
        extract_dir = zip_path.parent
        target_file = extract_dir / filename
        is_multipart = zip_path.name.endswith(".001")
        temp_zip_handle = None
        files_to_delete = []

        print(f"Checking for {description}...")

        if target_file.exists():
            print(f"  [OK] Found existing file: {target_file}")
            continue

        try:
            zip_to_read_from = zip_path

            if is_multipart:
                # For multipart archives, find all parts and combine them into a temporary file
                base_name = zip_path.name.replace('.001', '')
                search_pattern = str(extract_dir / f"{base_name}.*")
                parts = sorted(glob.glob(search_pattern))

                if not parts:
                    raise FileNotFoundError(f"Could not find parts for '{base_name}'")
                
                files_to_delete = [pathlib.Path(p) for p in parts]

                print(f"  -> Reassembling {len(parts)} parts for '{base_name}'...")
                temp_zip_handle = tempfile.NamedTemporaryFile(delete=False)
                with open(temp_zip_handle.name, 'wb') as assembled_zip:
                    for part_path in parts:
                        with open(part_path, 'rb') as part_file:
                            assembled_zip.write(part_file.read())
                
                zip_to_read_from = temp_zip_handle.name

            elif not zip_path.exists():
                 raise FileNotFoundError(f"Zip file not found at: {zip_path}")
            else:
                files_to_delete.append(zip_path)

            print(f"  -> Extracting '{filename}'...")
            with zipfile.ZipFile(zip_to_read_from, 'r') as zf:
                zf.extract(filename, path=extract_dir)
            
            if target_file.exists():
                print(f"  [SUCCESS] Extracted '{filename}' successfully.")
                
                for file_path in files_to_delete:
                    try:
                        file_path.unlink()
                    except OSError as e:
                        print(f"     [WARNING] Could not delete {file_path.name}: {e}")

            else:
                print(f"  [ERROR] Extraction failed to create '{filename}'.")
                all_successful = False

        except Exception as e:
            print(f"  [ERROR] An unexpected error occurred: {e}")
            all_successful = False
        finally:
            if temp_zip_handle:
                temp_zip_handle.close()
                pathlib.Path(temp_zip_handle.name).unlink(missing_ok=True)

    if not all_successful:
        print("[FAILURE] Jiten-Parser data setup failed. Please review the errors above.")
    else:
        print("[SUCCESS] Jiten-Parser data setup completed successfully.")


if __name__ == "__main__":
    main()