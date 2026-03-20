import hashlib
import os
from natsort import natsorted


def get_code(folder_path, output_file):

    def get_file_hash(path):
        sha256_hash = hashlib.sha256()
        with open(path, 'rb') as file:
            for chunk in iter(lambda: file.read(4096), b''):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    xml_files = natsorted(os.listdir(folder_path))
    file_hashes = []

    for file_name in xml_files:
        if file_name.endswith('.xml'):
            file_path = os.path.join(folder_path, file_name)
            file_hash = get_file_hash(file_path)
            file_hashes.append(f"{file_name}: {file_hash}")

    with open(output_file, 'w') as f:
        f.write('\n'.join(file_hashes))

