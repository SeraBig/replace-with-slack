#!/usr/bin/env python

################################################################################
# MIT License
# Copyright 2017-2020 Fredrik Savje
################################################################################

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
parser.add_argument('-u', '--uninstall', action='store_true', help='Removes injected Replace within Slack code.')
parser.add_argument('--version', action='version', version='%(prog)s ' + rws_version)
args = parser.parse_args()


# Misc functions

def exprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
    sys.exit(1)


# Find path to app.asar

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


# Remove previously injected code if it exists

with open(app_path, mode='rb') as check_app_fp:
    (header_data_size, json_binary_size) = struct.unpack('<II', check_app_fp.read(8))
    assert header_data_size == 4
    json_binary = check_app_fp.read(json_binary_size)

(json_data_size, json_string_size) = struct.unpack('<II', json_binary[:8])
assert json_binary_size == json_data_size + 4
json_check = json.loads(json_binary[8:(json_string_size + 8)].decode('utf-8'))

if 'RWSINJECT' in json_check['files']:
    if not os.path.isfile(app_path + '.rwsbak'):
        exprint('Found injected code without backup. Please re-install Slack.')
    try:
        os.remove(app_path)
        shutil.move(app_path + '.rwsbak', app_path)
    except Exception as e:
        print(e)
        exprint('Cannot remove previously injected code. Make sure the script has write permissions.')


# Remove old backup if it exists

if os.path.isfile(app_path + '.rwsbak'):
    try:
        os.remove(app_path + '.rwsbak')
    except Exception as e:
        print(e)
        exprint('Cannot remove old backup. Make sure the script has write permissions.')


# Are we uninstalling?

if args.uninstall:
    print('Uninstall successful. Please restart Slack.')
    sys.exit(0)


# These replacements are to remove the name of an abusive sexual harasser
# who caused trauma to the extent that this program would be made.
default_replacements = {
    'ChrisTower': 'AvoidThisAbuser',
    'Chris Tower': 'Avoid This Abuser',
    'Chris.Tower': 'avoid.this.abuser',
    'Chris': 'Abuser',
    'Tower': 'ToAvoid',
    'CT': 'Abuser'
}

### Inject code

# Code to be injected
# Css names were discovered by doing 
# export SLACK_DEVELOPER_MENU=true; open -a /Applications/Slack.app
# which allows a "View->Developer Tools" menu that has inspectors and a console

inject_code = ('\n\n// replace-within-slack ' + rws_version + '''
// Inject Replace within slack
document.addEventListener('DOMContentLoaded', function() {

    function replaceMessage(element) {
        var elementArray;
        if(!(element instanceof Array)) {
            elementArray = new Array(element);
        } else {
	        elementArray = element;
        }
        const replaceMap =
''' + json.dumps(default_replacements) + ''';

        for(var i = 0; i < elementArray.length; i++) {
            oneElement = elementArray[i];
            for(var searchKey in replaceMap) {
                oneElement.textContent = oneElement.textContent.replace(searchKey, replaceMap[searchKey]);
            }
        }
    }
    var entry_observer = new IntersectionObserver(
        (entries, observer) => {
            var appearedEntries = entries.filter((entry) => entry.intersectionRatio > 0);
            replaceMessage(appearedEntries.map((entry) => entry.target));
        }, 
        { root: document.body }
    );
    document.body.addEventListener("DOMNodeInserted", 
        function(event) {
            var target = event.relatedNode;
            if(target) { // && typeof target.getElementsByClassName === 'function') {
                // span.c-message_kit__text for messages in the Threads View
                // span.c-message__body for messages in the chats (i.e. direct messages)
                //.c-mrkdwn__member--link .c-message_attachment__author_name 
                var messages = target.querySelectorAll('span.c-message__sender_link span.c-message_kit__sender span.c-message__sender span.c-message__body, span.c-message_kit__text, div.p-rich_text_block');
                for (var i = 0; i < messages.length; i++) {
                    msg = messages[i];
                    entry_observer.observe(msg);
                }
            }
        }
    );

    function rewriteAllSenders() {
        // replace all the sender names
        var messages = document.querySelectorAll('span.c-message__sender');
        for (var i = 0; i < messages.length; i++) {
            replaceMessage(messages[i]);
        }
    }
    function rewriteAllSendersDelayed(event) {
        // Slack fills out the sender after the node is inserted
        // thus it's not available immediately but can be fetched a moment later
        setTimeout(rewriteAllSenders, 100);
    }
    document.body.addEventListener("DOMNodeInserted", rewriteAllSendersDelayed);

});
''').encode('utf-8')


# Make backup

try:
    shutil.move(app_path, app_path + '.rwsbak')
except Exception as e:
    print(e)
    exprint('Cannot make backup. Make sure the script has write permissions.')


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
assert 'RWSINJECT' not in json_header['files']


injected_file_name = 'main-preload-entry-point.bundle.js'
ori_injected_file_size = json_header['files']['dist']['files'][injected_file_name]['size']
ori_injected_file_offset = int(json_header['files']['dist']['files'][injected_file_name]['offset'])


# Modify JSON data

json_header['files']['RWSINJECT'] = json_header['files']['LICENSE']
json_header['files']['dist']['files'][injected_file_name]['size'] = ori_injected_file_size + len(inject_code)
json_header['files']['dist']['files'][injected_file_name]['offset'] = str(ori_data_size)

def split_path_to_components(path):
    dirs = []
    while True:
        path, dir = os.path.split(path)
        if dir != "":
            dirs.append(dir)
        else:
            if path != "":
                dirs.append(dir)
            break
    dirs.reverse()
    if dirs == ['.']:
        return dirs
    else:
        return ['.'] + dirs

def dir_to_json_header(root_dir, initial_offset):
    """Returns the json header for `root_dir`.
    
    Args:
        - root_dir: the root_dir 
        - initial_offset: a number that is added to all offset of files

    Returns:
        a tuple of (result, file_paths), where result is a dict containing
        the json header, and file_paths is a list of file paths in order 
        that should be appended to the end of the .asar file. 
    """
    file_paths = []
    result = {"files": {}}
    offset = initial_offset
    for parent_abs, dirs, files in os.walk(root_dir):
        parent = os.path.relpath(parent_abs, root_dir)
        parent_components = split_path_to_components(parent)
        rdict = result
        for dir_component in parent_components[:-1]:
            rdict = rdict["files"][dir_component]
        rdict["files"][parent_components[-1]] = {"files": {}}
        for file in files:
            file_path = os.path.join(parent_abs, file)
            file_paths.append(file_path)
            size = os.path.getsize(file_path)
            rdict["files"][parent_components[-1]]["files"][file] = {'size': size, 'offset': str(offset)}
            offset += size
    return result, file_paths

# Write new app.asar file

new_json_header = json.dumps(json_header, separators=(',', ':')).encode('utf-8')
new_json_header_padding = (4 - len(new_json_header) % 4) % 4

with open(app_path + '.rwsbak', mode='rb') as ori_app_fp, \
     open(app_path, mode='wb') as new_app_fp:
    # Header
    new_app_fp.write(struct.pack('<I', 4))
    new_app_fp.write(struct.pack('<I', 8 + len(new_json_header) + new_json_header_padding))
    new_app_fp.write(struct.pack('<I', 4 + len(new_json_header) + new_json_header_padding))
    new_app_fp.write(struct.pack('<I', len(new_json_header)))
    new_app_fp.write(new_json_header)
    new_app_fp.write(b'\0' * new_json_header_padding)
    # Old data
    ori_app_fp.seek(ori_data_offset)
    shutil.copyfileobj(ori_app_fp, new_app_fp)
    # Modified injected_file
    ori_app_fp.seek(ori_data_offset + ori_injected_file_offset)
    copy_until = ori_app_fp.tell() + ori_injected_file_size
    while ori_app_fp.tell() < copy_until:
        new_app_fp.write(ori_app_fp.read(min(65536, copy_until - ori_app_fp.tell())))
    new_app_fp.write(inject_code)

# We are done

print('Install successful. Please restart Slack.')
sys.exit(0)


# References

# https://github.com/electron/node-chromium-pickle-js
# https://chromium.googlesource.com/chromium/src/+/master/base/pickle.h
# https://github.com/electron/asar
# https://github.com/electron-archive/node-chromium-pickle
# https://github.com/leovoel/BeautifulDiscord/tree/master/beautifuldiscord
# https://github.com/fsavje/math-with-slack
# https://github.com/thisiscam/math-with-slack
