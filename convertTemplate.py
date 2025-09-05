#! /usr/bin/env python3


'''
Convert a templated tree of files and directories, replacing files, directories and files content,
using a template rendering engine.
'''

import os
import sys
import argparse
import shutil

from string import Template

# File and directory templates
# Template variable format : __name__, e.g __name__.txt => myfile.txt, __dirname__/ => mydir/
FILE_DIR_TEMPLATE_DELIMITER = '__'

class FileDirTemplate(Template):
    delimiter_s = '__'
    delimiter_e = '__'
    idpattern = r'[a-zA-Z][a-zA-Z0-9]*' # Matches variable names like __name__
    pattern = rf"""
    {delimiter_s}(?:
        (?P<escaped>{delimiter_e})           |         # Escaped delimiter
        (?P<named>{idpattern}){delimiter_e}  |         # Named variable
        (?P<braced>{idpattern}){delimiter_e} |         # Braced variable (not used)
        (?P<invalid>)                                  # Invalid variable
    )
    """

class ContentTemplate(Template):
    delimiter_s = '{{'
    delimiter_e = '}}'
    idpattern = r'[a-zA-Z_][a-zA-Z0-9]*'  # Matches variable names like __name__ or __name_ext__
    pattern = rf"""
    {delimiter_s}(?:
        (?P<escaped>{delimiter_e})           |         # Escaped delimiter
        (?P<named>{idpattern}){delimiter_e}  |         # Named variable
        (?P<braced>{idpattern}){delimiter_e} |         # Braced variable (not used)
        (?P<invalid>)                                  # Invalid variable
    )
    """

def render_fs_template(template_str, context):
    """
    Render a template string with the given context.
    """
    template = FileDirTemplate(template_str)
    return template.safe_substitute(context)

def render_content_template(template_str, context):
    """
    Render a content template string with the given context.
    """
    template = ContentTemplate(template_str)
    return template.safe_substitute(context)

def walk_dir(src_dir, dst_dir, context):
    """
    Walk through the source directory and render templates in files and directories.
    """
    for root, dirs, files in os.walk(src_dir):
        # Render directory names
        rendered_root = render_fs_template(root, context)
        dst_root = os.path.join(dst_dir, rendered_root[len(src_dir):].lstrip(os.sep))
        os.makedirs(dst_root, exist_ok=True)

        # Render file names and contents
        for file in files:
            src_file_path = os.path.join(root, file)
            rendered_file_name = render_fs_template(file, context)
            dst_file_path = os.path.join(dst_root, rendered_file_name)

            with open(src_file_path, 'r') as src_file:
                content = src_file.read()
                rendered_content = render_content_template(content, context)

            with open(dst_file_path, 'w') as dst_file:
                dst_file.write(rendered_content)

A2C_BUILDER_GIT_URL_DEFAULT = 'https://github.com/arch2code/arch2code.git'

def parse_args():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description='Convert a templated tree of files and directories.')
    parser.add_argument('src_dir', help='Source directory containing the template files')
    parser.add_argument('dst_dir', help='Destination directory for rendered files')
    parser.add_argument('--context', type=str, nargs='+', help='Context variables in key=value format, comma separated  (e.g., key1=value1,key2=value2)')
    parser.add_argument('--builder-git-url', type=str, default=A2C_BUILDER_GIT_URL_DEFAULT, help='Git URL for the builder submodule')
    parser.add_argument('--force', action='store_true', help='Force overwrite of destination directory if exists')

    args = parser.parse_args()

    context = {}
    if args.context:
        for item in args.context[0].split(','):
            key, value = item.split('=')
            context[key] = value
            context[key.upper()] = value.upper() if value.isalpha() else value

    return args.src_dir, args.dst_dir, context, args.builder_git_url, args.force

if __name__ == "__main__":
    src_dir, dst_dir, context, builder_git_url, force = parse_args()

    # Remove the destination directory if it exists and force is set
    if force and os.path.exists(dst_dir):
        shutil.rmtree(dst_dir)

    walk_dir(src_dir, dst_dir, context)

    # change to directory /work/isp_awb
    os.chdir(dst_dir)

    # invoke git init /work/isp_awb
    os.system('git init -b main')

    # git builder submodule add
    os.system(f'git submodule add {builder_git_url} builder')

    # git submodules update
    os.system('git submodule update --init --recursive')
