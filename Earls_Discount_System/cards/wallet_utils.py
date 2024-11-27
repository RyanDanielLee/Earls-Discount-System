import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import pkcs12
import os
import json
import zipfile
from dotenv import load_dotenv

load_dotenv()

p12_file_path = './certificate.p12'
password = os.getenv('CERT_PASSWORD')
team_id = os.getenv('TEAM_ID')
bundle_id = os.getenv('BUNDLE_ID')

pass_directory = './pass_directory'

# Files to include in the manifest
files = ['pass.json']

manifest = {}

# Compute SHA1 hash for each file
for file in files:
    file_path = os.path.join(pass_directory, file)
    with open(file_path, 'rb') as f:
        file_data = f.read()
        file_hash = hashlib.sha1(file_data).hexdigest()
        manifest[file] = file_hash

# Save the manifest
with open(os.path.join(pass_directory, 'manifest.json'), 'w') as manifest_file:
    json.dump(manifest, manifest_file, indent=4)

# Extract private key from .p12 file
def extract_private_key_from_p12(p12_file_path, password):
    with open(p12_file_path, 'rb') as p12_file:
        p12_data = p12_file.read()

    private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(p12_data, password.encode())
    return private_key

private_key = extract_private_key_from_p12(p12_file_path, password)

# Create the hash of the manifest file
with open('./pass_directory/manifest.json', 'rb') as f:
    manifest_data = f.read()

manifest_hash = hashlib.sha1(manifest_data).digest()

# Sign the manifest hash with the private key
signed_data = private_key.sign(
    manifest_hash,
    padding.PKCS1v15(),
    hashes.SHA256()
)

# Save the signature to a file
with open('./pass_directory/signature', 'wb') as signature_file:
    signature_file.write(signed_data)

# Create the .pkpass file
with zipfile.ZipFile('./pass.pkpass', 'w') as zipf:
    for root, dirs, files in os.walk(pass_directory):
        for file in files:
            file_path = os.path.join(root, file)
            zipf.write(file_path, os.path.relpath(file_path, pass_directory))
