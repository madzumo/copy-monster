import os
import shutil
import subprocess
from enum import Enum
from tqdm import tqdm
from colorama import Fore, Back, Style
import re


class ConsoleColors(Enum):
    title = Back.CYAN + Fore.BLACK
    menu = Back.LIGHTGREEN_EX + Fore.BLACK
    info = Back.LIGHTYELLOW_EX + Fore.BLACK
    info_bright = Back.LIGHTYELLOW_EX + Fore.BLACK + Style.BRIGHT
    error = Back.RED + Fore.WHITE
    special = Back.MAGENTA + Fore.WHITE
    basic = Back.BLACK + Fore.WHITE
    commands = Back.BLACK + Fore.LIGHTBLUE_EX
    warning = Back.MAGENTA + Fore.LIGHTWHITE_EX


shadow_copy_id = ""
shadow_copy_volume_name = ""
header_art = r"""
    ___________________ 
    |# :           : #| 
    |  :    Copy   :  | 
    |  :   Monster :  | 
    |  :___________:  | 
    |     _________   | 
    |    | __      |  | 
    |    ||  |     |  | 
    \____||__|_____|__| 
                        """


def copy_files_plus(source, destination, log_file, copy_message, specific_extensions=None):
    if not os.path.exists(destination):
        os.makedirs(destination)

    copied_files_count = 0
    failed_files_count = 0

    print(ConsoleColors.info.value + 'Searching Files.....' + Style.RESET_ALL)
    print(ConsoleColors.info.value + f'{copy_message}' + Style.RESET_ALL)
    files_to_copy = []
    if specific_extensions is None:
        for root, _, files in os.walk(source):
            for file in files:
                files_to_copy.append((root, file))
    else:
        for root, _, files in os.walk(source):
            for file in files:
                for extension in specific_extensions:
                    if file.endswith(extension):
                        files_to_copy.append((root, file))

    print(ConsoleColors.info.value + f'Found: {len(files_to_copy)} files' + Style.RESET_ALL)
    with open(log_file, 'w') as log:
        for root, file in tqdm(files_to_copy, desc="Copying files", unit="file"):
            src_file = os.path.join(root, file)
            dst_file = os.path.join(destination, os.path.relpath(src_file, source))
            src_file_long = r"\\?\{}".format(src_file)
            dst_file_long = r"\\?\{}".format(dst_file)
            try:
                os.makedirs(os.path.dirname(dst_file_long), exist_ok=True)
                shutil.copy2(src_file_long, dst_file_long)
                copied_files_count += 1
                # tqdm.write(f'Copying: {file}')
            except Exception as e:
                failed_files_count += 1
                error_message = f'Error copying {src_file} to {dst_file} - {e}'
                # tqdm.write(error_message)
                log.write(error_message + '\n')

    print(ConsoleColors.special.value + f'Total files copied: {copied_files_count}' + Style.RESET_ALL)
    if failed_files_count <= 0:
        print(ConsoleColors.special.value + f'Total files failed: {failed_files_count}' + Style.RESET_ALL)
    else:
        print(ConsoleColors.error.value + f'Total files failed: {failed_files_count}' + Style.RESET_ALL)


def open_shadow_copy(shadow_path):
    global shadow_copy_id
    global shadow_copy_volume_name
    print(ConsoleColors.title.value + 'Creating Shadow Copy' + Style.RESET_ALL)
    try:
        result = subprocess.run(['vssadmin', 'create', 'shadow', '/for=C:'], capture_output=True, text=True)
        vss_admin_output = result.stdout
        print(vss_admin_output)
        shadow_copy_id_match = re.search(r'Shadow Copy ID: ({[0-9a-fA-F-]+})', vss_admin_output)
        shadow_copy_volume_name_match = re.search(r'Shadow Copy Volume Name: (.+)', vss_admin_output)

        if shadow_copy_id_match and shadow_copy_volume_name_match:
            shadow_copy_id = shadow_copy_id_match.group(1)
            shadow_copy_volume_name = shadow_copy_volume_name_match.group(1)
            shadow_copy = f"{shadow_copy_volume_name}\\"

            cmd = f'cmd /c mklink /d "{shadow_path}" "{shadow_copy}"'
            subprocess.run(cmd, shell=True)
        else:
            print("ERROR - Failed to parse shadow copy information")
    except Exception as e:
        print(ConsoleColors.error.value + f"ERROR - {e}" + Style.RESET_ALL)


def close_shadow_copy(shadow_path):
    print(ConsoleColors.title.value + 'Removing Shadow Copy' + Style.RESET_ALL)
    try:
        cmd = f'cmd /c rmdir /S /Q "{shadow_path}"'
        subprocess.run(cmd, shell=True, check=True)

        subprocess.run(['vssadmin', 'delete', 'shadows', f'/Shadow={shadow_copy_id}', '/quiet'], check=True)
    except Exception as e:
        print(ConsoleColors.error.value + f"ERROR - {e}" + Style.RESET_ALL)


def main():
    root_destination = r'C:\Temp\_CopyMonster'
    shadow_path = r'C:\Shadow'
    shadow_path2 = r'C:\Shadow\WINDOWS\System32\winevt\Logs'
    destination1 = r'\PS'
    destination2 = r'\LOG'
    file_extensions = (".ps1", ".psm1", ".psc1", ".psd1", ".ps1xml", ".pssc", ".psrc", ".cdxml")
    log_file_path = r'C:\Temp\_CopyMonster\copy_errors.log'
    try:
        print(ConsoleColors.menu.value + header_art + Style.RESET_ALL)
        print(ConsoleColors.title.value + f'Working Directory: {root_destination}' + Style.RESET_ALL)
        open_shadow_copy(shadow_path)
        print(ConsoleColors.title.value + f'**********************************' + Style.RESET_ALL)
        copy_files_plus(shadow_path2, f'{root_destination}{destination2}', log_file_path, 'Looking for LOG files')
        print(ConsoleColors.title.value + f'**********************************' + Style.RESET_ALL)
        copy_files_plus(shadow_path, f'{root_destination}{destination1}', log_file_path, f'Looking for:{file_extensions}',
                        file_extensions)
        print(ConsoleColors.title.value + f'**********************************' + Style.RESET_ALL)
        close_shadow_copy(shadow_path)
        print(ConsoleColors.menu.value + f'!Great Success! View output here -> {root_destination}' + Style.RESET_ALL)
        input('Press Enter to exit')
    except Exception as e:
        print(ConsoleColors.error.value + f'Error: {e}' + Style.RESET_ALL)
        input('Press Enter to exit')


if __name__ == "__main__":
    main()
