"""
Rename pytest-summary.json file according to its purpose and, for cibuildwheel,
move it to the location from which it can be retrieved with the corresponding
wheel.

cibuildwheel doesn't provide any reasonable variables for naming pytest results
files, neither any tools to supply these files with the built wheels, so all
this work is done by this script.

It must be called after running pytest, in the same directory, with the
{package} and {wheel} cibuildwheel placeholders as its arguments.

If only renaming is needed, call with a single name argument (without .json).
"""
import os
import platform
import sys
import shutil

if len(sys.argv) < 3:
    out = sys.argv[1]
else:
    package = sys.argv[1]  # full path to package directory
    wheel = os.path.basename(sys.argv[2])  # wheel file name
    if platform.system() == 'Linux':
        out = f'/output/{wheel}'  # in container
    else:
        out = f'{package}/wheels/{wheel}'  # assuming "--output-dir wheels"
out += '.json'

print('Saving results to', out)
# destination directory might not exist yet
os.makedirs(os.path.normpath(os.path.dirname(out)), exist_ok=True)
shutil.move('pytest-summary.json', out)
