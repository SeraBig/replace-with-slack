#!/usr/bin/env python

# Python 2.7 and 3

from __future__ import print_function


# Load modules

import argparse
import json
import os
import shutil
import struct
import sys

try:
    # Python 3
    import urllib.request as urllib_request
except:
    # Python 2
    import urllib as urllib_request

import tarfile
import tempfile


rws_version = '0.1.0.1000'


# Parse command line options

parser = argparse.ArgumentParser(prog='slack-replace', description='Inject Replace within Slack.')
parser.add_argument('-a', '--app-file', help='Path to Slack\'s \'app.asar\' file.')
parser.add_argument('-d', '--destination-dir', help='Path to write unpacked contents', default=".")
parser.add_argument('--version', action='version', version='%(prog)s ' + rws_version)
args = parser.parse_args()


# Misc functions

def exprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
    sys.exit(1)

if args.app_file is not None:
    app_path = args.app_file
elif sys.platform == 'darwin':
    app_path = '/Applications/Slack.app/Contents/Resources/app.asar'
elif sys.platform.startswith('linux'):
    for test_app_file in [
        '/usr/lib/slack/resources/app.asar',
        '/usr/local/lib/slack/resources/app.asar',
        '/opt/slack/resources/app.asar'
    ]:
        if os.path.isfile(test_app_file):
            app_path = test_app_file
            break
elif sys.platform == 'win32':
   exprint('Not implemented')


# Check so app.asar file exists

try:
    if not os.path.isfile(app_path):
        exprint('Cannot find Slack at: ' + app_path)
except NameError:
    exprint('Could not find Slack\'s app.asar file. Please provide path.')



# Print info

print('Using Slack installation at: ' + app_path)


def unpack_recursive(target_path, json_directory, packed_file, contents_offset):
    os.makedirs(target_path, exist_ok=True)
    for entry_name, entry in json_directory.items():
        entry_name_with_path = os.path.join(target_path, entry_name)
        json_sub_dir = entry.get("files")
        if isinstance(json_sub_dir, dict):
            print(f"Directory {entry_name_with_path}")
            unpack_recursive(entry_name_with_path, json_sub_dir, packed_file, contents_offset)
        else:
            size = entry["size"]
            already_unpacked = entry.get("unpacked")
            if already_unpacked:
                continue
            offset = int(entry["offset"]) + contents_offset
            print(f"Writing {entry_name_with_path} from {offset} with {size} bytes")
            packed_file.seek(offset)
            file_data = packed_file.read(size)
            with open(entry_name_with_path, mode='wb') as new_file:
                new_file.write(file_data)
                new_file.truncate()

# Get file info

with open(app_path + '.rwsbak', mode='rb') as ori_app_fp:
    (header_data_size, json_binary_size) = struct.unpack('<II', ori_app_fp.read(8))
    assert header_data_size == 4
    json_binary = ori_app_fp.read(json_binary_size)
    ori_data_offset = 8 + json_binary_size
    ori_app_fp.seek(0, 2)
    ori_data_size = ori_app_fp.tell() - ori_data_offset

    (json_data_size, json_string_size) = struct.unpack('<II', json_binary[:8])
    assert json_binary_size == json_data_size + 4
    json_header = json.loads(json_binary[8:(json_string_size + 8)].decode('utf-8'))

    unpack_recursive(args.destination_dir, json_header["files"], ori_app_fp, ori_data_offset)