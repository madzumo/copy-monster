import pytz
import datetime
from colorama import Fore, Back, Style
from enum import Enum
import os


class ConsoleColors(Enum):
    title = Back.CYAN + Fore.BLACK
    menu = Back.LIGHTGREEN_EX + Fore.BLACK
    info = Back.LIGHTYELLOW_EX + Fore.BLACK
    info_bright = Back.LIGHTYELLOW_EX + Fore.BLACK + Style.BRIGHT
    error = Back.RED + Fore.WHITE
    basic = Back.BLACK + Fore.WHITE
    commands = Back.BLACK + Fore.LIGHTBLUE_EX
    warning = Back.MAGENTA + Fore.LIGHTWHITE_EX
    outro = Back.LIGHTBLUE_EX + Fore.BLACK


welcome_message = ["This utility creates a complete CI/CD pipeline to deploy a microservice app in your AWS "
                   "infrastructure",
                   "Tools Used: Git,Jenkins,Docker,Kubernetes,EKS,ECR,Prometheus,Grafana,Terraform,Ansible & Python",
                   "All you need is an AWS Access Key ID and Secret Key ID. Select option below to get started"]

menu_options = ["Menu Options:", "1 - Set AWS Credentials", "2 - Test AWS Connection",
                "3 - Install Full Pipeline",
                "4 - Remove Existing Pipeline & all resources",
                "5 - View Pipeline Status", "6 - Quit"]

total_line_chars = 100

header_art_welcome = r"""
    ___________________    
    |# :           : #|    
    |  :  DevOps   :  |    
    |  :   demo    :  |    
    |  :___________:  |    
    |     _________   |    
    |    | __      |  |    
    |    ||  |     |  |       by Jonathan M. 
    \____||__|_____|__|   github.com/madzumo 
                                             """

header_art_clean = r"""
 .----------------.  .----------------.  .----------------.  .----------------.  .-----------------.
| .--------------. || .--------------. || .--------------. || .--------------. || .--------------. |
| |     ______   | || |   _____      | || |  _________   | || |      __      | || | ____  _____  | |
| |   .' ___  |  | || |  |_   _|     | || | |_   ___  |  | || |     /  \     | || ||_   \|_   _| | |
| |  / .'   \_|  | || |    | |       | || |   | |_  \_|  | || |    / /\ \    | || |  |   \ | |   | |
| |  | |         | || |    | |   _   | || |   |  _|  _   | || |   / ____ \   | || |  | |\ \| |   | |
| |  \ `.___.'\  | || |   _| |__/ |  | || |  _| |___/ |  | || | _/ /    \ \_ | || | _| |_\   |_  | |
| |   `._____.'  | || |  |________|  | || | |_________|  | || ||____|  |____|| || ||_____|\____| | |
| |              | || |              | || |              | || |              | || |              | |
| '--------------' || '--------------' || '--------------' || '--------------' || '--------------' |
 '----------------'  '----------------'  '----------------'  '----------------'  '----------------' 
"""

header_art_status = r"""
.----------------.  .----------------.  .----------------.  .----------------.  .----------------.  .----------------. 
| .--------------. || .--------------. || .--------------. || .--------------. || .--------------. || .--------------. |
| |    _______   | || |  _________   | || |      __      | || |  _________   | || | _____  _____ | || |    _______   | |
| |   /  ___  |  | || | |  _   _  |  | || |     /  \     | || | |  _   _  |  | || ||_   _||_   _|| || |   /  ___  |  | |
| |  |  (__ \_|  | || | |_/ | | \_|  | || |    / /\ \    | || | |_/ | | \_|  | || |  | |    | |  | || |  |  (__ \_|  | |
| |   '.___`-.   | || |     | |      | || |   / ____ \   | || |     | |      | || |  | '    ' |  | || |   '.___`-.   | |
| |  |`\____) |  | || |    _| |_     | || | _/ /    \ \_ | || |    _| |_     | || |   \ `--' /   | || |  |`\____) |  | |
| |  |_______.'  | || |   |_____|    | || ||____|  |____|| || |   |_____|    | || |    `.__.'    | || |  |_______.'  | |
| |              | || |              | || |              | || |              | || |              | || |              | |
| '--------------' || '--------------' || '--------------' || '--------------' || '--------------' || '--------------' |
 '----------------'  '----------------'  '----------------'  '----------------'  '----------------'  '----------------' 
"""


def get_current_time():
    eastern = pytz.timezone('America/New_York')
    current_time = datetime.datetime.now(eastern)
    military_time = current_time.strftime('%H:%M:%S')
    return military_time


def console_message(message_words, message_color, total_chars=total_line_chars, no_formatting=False, force_pause=False):
    """Display console messages in color. Message_words must be in a LIST []. Each list item will be on its own line.
    Select from ConsoleColors enum for the Color scheme. To have Back color stop with the word instead of full line,
    total_chars = 0. For non-color regular console message, no_formatting = True. To have a pause after showing
    the message console, force_pause = True"""

    paragraph = ''
    multi_word = False
    for word in message_words:
        if multi_word:
            paragraph += '\n'
        if total_chars > 0:  # If 0 then do not make back color uni-form
            if len(word) > total_chars:
                remaining_word = word
                paragraph += remaining_word[:total_chars]
                paragraph += remaining_word[total_chars:]
            else:
                remaining_spaces = total_chars - len(word)
                paragraph += word
                paragraph += ' ' * remaining_spaces
        else:
            paragraph += word
        multi_word = True

    if no_formatting:
        print(paragraph + Style.RESET_ALL)
    else:
        print(message_color.value + paragraph + Style.RESET_ALL)

    if force_pause:
        pause_console()


def clear_console():
    # For Windows
    if os.name == 'nt':
        os.system('cls')
    # For Linux/Unix/MacOS
    else:
        os.system('clear')

    print(Style.RESET_ALL + ' ')


def pause_console():
    console_message(['hit enter to continue'], ConsoleColors.commands, total_chars=0)
    input('')
