from datetime import datetime
from colorama import Fore, Back, Style, init
import os

def LogInfo(text:str):
    dt = datetime.now()
    print(f"[{dt.hour}:{dt.minute}:{dt.second}] {Fore.BLUE}INFO{Style.RESET_ALL}: {text}")

def LogWarning(text:str):
    dt = datetime.now()
    print(f"[{dt.hour}:{dt.minute}:{dt.second}] {Fore.YELLOW}WARNING{Style.RESET_ALL}: {text}")

def LogError(text:str):
    dt = datetime.now()
    print(f"[{dt.hour}:{dt.minute}:{dt.second}] {Fore.RED}ERROR{Style.RESET_ALL}: {text}")

def Take(target_list:list, count:int):
    return target_list[:count]

def TakeLast(target_list:list, count:int):
    return target_list[-count:]

def ClearConsole():
    if os.name == "nt": os.system("cls")
    if os.name == "posix": os.system("clear")