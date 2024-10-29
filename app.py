import os
import hashlib
import json

CHUNK_SIZE = 500 * 1024  # 500 KB chunks

def hash_file(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()
 
def list_files(folder):
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    if not files:
        print("No files found in the source folder.")
        return None
    print("\nFiles in source folder:")
    for index, file in enumerate(files):
        print(f"[{index}] {file}")
    return files

def select_file(folder):
    files = list_files(folder)
    if files is None:
        return None
    while True:
        try:
            file_index = int(input("\nEnter the index of the file to split: "))
            if 0 <= file_index < len(files):
                return os.path.join(folder, files[file_index])
            else:
                print("Invalid index. Please select a valid file index.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def split_file(filepath, chunk_folder, tracker_file):
    if not os.path.exists(chunk_folder):
        os.makedirs(chunk_folder)

    file_hash = hash_file(filepath)
    metadata = {
        "filename": os.path.basename(filepath),
        "file_hash": file_hash,
        "chunks": [],
    }
    chunk_index = 0
    
    with open(filepath, 'rb') as f:
        while chunk := f.read(CHUNK_SIZE):
            chunk_hash = hashlib.sha256(chunk).hexdigest()
            chunk_filename = f"{chunk_folder}/chunk_{chunk_index}.part"
            with open(chunk_filename, 'wb') as chunk_file:
                chunk_file.write(chunk)
            
            metadata["chunks"].append({
                "index": chunk_index,
                "filename": chunk_filename,
                "chunk_size": len(chunk),
                "chunk_hash": chunk_hash,
            })
            chunk_index += 1

    metadata["total_chunks"] = chunk_index
    with open(tracker_file, 'w') as tracker_file:
        json.dump(metadata, tracker_file, indent=4)
    
    print(f"File split complete. Tracker saved to: {tracker_file.name}")

def reassemble_file(tracker_path, output_folder):
    with open(tracker_path, 'r') as tracker_file:
        metadata = json.load(tracker_file)
    
    output_filepath = os.path.join(output_folder, metadata["filename"])
    with open(output_filepath, 'wb') as output_file:
        for chunk_meta in metadata["chunks"]:
            with open(chunk_meta["filename"], 'rb') as chunk_file:
                chunk_data = chunk_file.read()
                # Validate chunk hash
                if hashlib.sha256(chunk_data).hexdigest() != chunk_meta["chunk_hash"]:
                    raise ValueError(f"Chunk {chunk_meta['index']} is corrupted.")
                output_file.write(chunk_data)

    print("File reassembly complete:", output_filepath)

def main():
    action = input("Enter 'split' to split a file or 'assemble' to reassemble a file: ").strip().lower()

    if action == "split":
        src_folder = input("Enter the source folder name: ").strip()
        src_filepath = select_file(src_folder)
        if not src_filepath:
            print("No file selected. Exiting.")
            return
        chunk_folder = input("Enter the folder name to save chunks: ").strip()
        tracker_file = input("Enter the tracker file name (e.g., 'tracker.json'): ").strip()

        split_file(src_filepath, chunk_folder, tracker_file)

    elif action == "assemble":
        tracker_folder = input("Enter the folder containing the tracker file: ").strip()
        tracker_file = input("Enter the tracker file name (e.g., 'tracker.json'): ").strip()
        output_folder = input("Enter the folder to save the reassembled file: ").strip()

        tracker_filepath = os.path.join(tracker_folder, tracker_file)
        reassemble_file(tracker_filepath, output_folder)

    else:
        print("Invalid option. Please enter 'split' or 'assemble'.")

if __name__ == "__main__":
    main()
