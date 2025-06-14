import os
import shutil

print("Listing files in repository root before cleanup:")
# Filter out .git directory if present and other common hidden items for cleaner listing
# For this environment, os.listdir('.') should be fine as is.
# items_in_root = [item for item in os.listdir('.') if not item.startswith('.')]
# for item in sorted(items_in_root):
#    print(f"- {item}")
# Simplification for now, raw output is fine.
for item in os.listdir('.'):
    print(f"- {item}")


stray_files_to_remove = [
    'parsed_json_data.py',
    'id_mapping.py',
    # The following two are inside temp_data, so rmtree on temp_data handles them.
    # 'temp_data/current_game_data.py',
    # 'temp_data/id_map_for_descriptions.py'
]
# temp_data was already removed in the previous subtask, but we include it for completeness
# of the user's request.
stray_dirs_to_remove = ['temp_data']

print("\nAttempting to remove specified stray files and directories...")

for f_path in stray_files_to_remove:
    if os.path.exists(f_path):
        try:
            os.remove(f_path)
            print(f"Successfully removed stray file: {f_path}")
        except OSError as e: # Catch more specific OS errors if needed
            print(f"Error removing file {f_path}: {e}")
    else:
        print(f"Stray file not found (already removed or never created): {f_path}")

for d_path in stray_dirs_to_remove:
    if os.path.exists(d_path):
        try:
            shutil.rmtree(d_path)
            print(f"Successfully removed stray directory: {d_path}")
        except OSError as e:
            print(f"Error removing directory {d_path}: {e}")
    else:
        print(f"Stray directory not found (already removed or never created): {d_path}")

print("\nFinal check for specified stray items:")
if os.path.exists('temp_data'):
    print("- temp_data directory STILL EXISTS.")
else:
    print("- temp_data directory successfully removed or was not present at check time.")

if os.path.exists('parsed_json_data.py'):
    print("- parsed_json_data.py STILL EXISTS.")
else:
    print("- parsed_json_data.py successfully removed or was not present at check time.")

if os.path.exists('id_mapping.py'):
    print("- id_mapping.py STILL EXISTS.")
else:
    print("- id_mapping.py successfully removed or was not present at check time.")

print("\nListing files in repository root after cleanup attempt:")
# items_in_root_after = [item for item in os.listdir('.') if not item.startswith('.')]
# for item in sorted(items_in_root_after):
#    print(f"- {item}")
for item in os.listdir('.'):
    print(f"- {item}")

# Using os.system for git commands as requested.
# Note: Direct shell commands in Python can be risky if paths are dynamic; here they are static.
# In a real application, subprocess module would be preferred for better control.
print("\nRunning git rm --cached for specified stray files (output suppressed, errors ignored):")
# We run these regardless of prior existence checks, as git tracking is separate from filesystem.
# If the file is not tracked, git rm --cached will error, but output is suppressed.
# If it was tracked and deleted from disk, this will unstage it.
# If it was tracked and NOT deleted from disk, this would unstage it and leave it as an untracked file.

commands = [
    "git rm --cached parsed_json_data.py > /dev/null 2>&1",
    "git rm --cached id_mapping.py > /dev/null 2>&1",
    "git rm --cached -r temp_data > /dev/null 2>&1" # -r for directory
]

for cmd in commands:
    exit_code = os.system(cmd)
    # print(f"Command '{cmd}' executed with exit code: {exit_code}") # for debugging

print("Attempted git rm --cached for specified stray files.")

# Final git status to see the effect of git rm --cached
print("\nFinal git status:")
os.system("git status")
