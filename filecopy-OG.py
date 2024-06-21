import os
import shutil


def copy_files_with_extension(source, destination, extension, log_file):
    # Ensure the destination directory exists
    if not os.path.exists(destination):
        os.makedirs(destination)

    # Initialize counters for tracking
    copied_files_count = 0
    failed_files_count = 0

    # Open the log file for writing
    with open(log_file, 'w') as log:
        # Iterate through the files in the source directory
        for root, _, files in os.walk(source):
            for file in files:
                if file.endswith(extension):
                    try:
                        # Construct the full file paths
                        src_file = os.path.join(root, file)
                        dst_file = os.path.join(destination, os.path.relpath(src_file, source))

                        # Ensure the subdirectories in destination exist
                        os.makedirs(os.path.dirname(dst_file), exist_ok=True)

                        # Copy the file
                        shutil.copy2(src_file, dst_file)
                        copied_files_count += 1
                        print(f'Copied: {src_file} to {dst_file}')
                    except Exception as e:
                        failed_files_count += 1
                        error_message = f'Error copying {src_file} to {dst_file} - {e}'
                        print(error_message)
                        log.write(error_message + '\n')

    print(f'Finished copying process')
    print(f'Total files copied: {copied_files_count}')
    print(f'Total files failed to copy: {failed_files_count}')


# Example usage
source_directory = r'C:\Shadow'
destination_directory = r'C:\Temp\_FileCopy\PS'
file_extension = '.ps1'
log_file_path = r'C:\Temp\_FileCopy\copyLOG.log'

copy_files_with_extension(source_directory, destination_directory, file_extension, log_file_path)
input('Press Enter to exit')
