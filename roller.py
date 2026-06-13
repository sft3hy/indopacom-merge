#!/usr/bin/env python3
import os
import json
import base64
import fnmatch

# Directories and files to always ignore
DEFAULT_IGNORE_DIRS = {'.git', '.venv', 'venv', 'env', '__pycache__'}
DEFAULT_IGNORE_FILES = {
    'roller.py',
    'unroller.py',
    'unroller.py.txt',
    'repo_bundle.txt',
    '.DS_Store',
}

def load_gitignore(root_dir):
    """Loads .gitignore patterns if the file exists."""
    patterns = []
    gitignore_path = os.path.join(root_dir, '.gitignore')
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
        except Exception as e:
            print(f"Warning: Could not read .gitignore: {e}")
    return patterns

def should_ignore(rel_path, gitignore_patterns):
    """Determines whether a relative path should be ignored."""
    # Split the path using forward slash since we normalized it
    parts = rel_path.split('/')
    
    # Check default ignored directories
    for part in parts:
        if part in DEFAULT_IGNORE_DIRS:
            return True
            
    # Check default ignored files
    filename = parts[-1]
    if filename in DEFAULT_IGNORE_FILES:
        return True
        
    # Check gitignore patterns
    for pattern in gitignore_patterns:
        pat = pattern.rstrip('/')
        # Match direct file/folder, contents inside, or patterns relative to directories
        if fnmatch.fnmatch(rel_path, pat) or \
           fnmatch.fnmatch(filename, pat) or \
           any(fnmatch.fnmatch(part, pat) for part in parts) or \
           fnmatch.fnmatch(rel_path, pat + '/*') or \
           fnmatch.fnmatch(rel_path, '*/' + pat):
            return True
            
    return False

def main():
    root_dir = os.path.abspath(os.getcwd())
    print(f"Rolling up repository at: {root_dir}")
    
    gitignore_patterns = load_gitignore(root_dir)
    bundled_files = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            abs_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(abs_path, root_dir)
            
            # Normalize to forward slashes to be OS-independent in the bundle
            rel_path_normalized = rel_path.replace(os.sep, '/')
            
            if should_ignore(rel_path_normalized, gitignore_patterns):
                continue
                
            print(f"Adding: {rel_path_normalized}")
            
            try:
                # Get file permissions
                stat = os.stat(abs_path)
                mode = stat.st_mode
                
                # Try reading as UTF-8 text
                is_base64 = False
                try:
                    with open(abs_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    # Fallback to base64 for binary files
                    is_base64 = True
                    with open(abs_path, 'rb') as f:
                        content_bytes = f.read()
                        content = base64.b64encode(content_bytes).decode('utf-8')
                
                bundled_files.append({
                    "path": rel_path_normalized,
                    "mode": mode,
                    "is_base64": is_base64,
                    "content": content
                })
            except Exception as e:
                print(f"Error reading {rel_path_normalized}: {e}")
                
    output_file = 'repo_bundle.txt'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(bundled_files, f, indent=2, ensure_ascii=False)
        print(f"\nSuccessfully rolled up {len(bundled_files)} files into '{output_file}'!")
    except Exception as e:
        print(f"Error writing bundle: {e}")

if __name__ == '__main__':
    main()
