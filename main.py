import os, re, requests, traceback, time
from util import *
from pathlib import Path
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from tqdm import tqdm

import config

def GetFilename(url:str):
    return url.rsplit("#", 1)[1]

def ExtractLink(target_url):
    with sync_playwright() as playwright_instance:
        user_agent_string = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        browser_type = playwright_instance.chromium
        browser = browser_type.launch(headless=config.HEADLESS, args=["--disable-blink-features=AutomationControlled"])
        
        context = browser.new_context(user_agent=user_agent_string)
        page = context.new_page()
        
        page.goto(target_url)
        script = page.locator("script").nth(3).text_content()
        
        context.close()
        browser.close()

        match = re.search(r'window\.open\(\s*["\'](https?://[^"\']+)["\']\s*\)', script)
        if match:
            return match.group(1)
        
    return None

def GetFFastLinks(url):
    page = requests.get(url)
    
    if page.status_code != 200:
        LogError(f"HTTP ERROR {page.status_code}")
        print(page.text)
        return False
    
    soup = BeautifulSoup(page.text, "html.parser")

    return [
        a["href"]
        for dlinks_div in soup.find_all("div", class_="dlinks")
        for a in dlinks_div.find_all("a", href=True)
        if a["href"].startswith("https://fuckingfast.co/")
    ]

def SubstringInList(target_string:str, string_list, remove_ext = True):
    if remove_ext: target_string = target_string.rsplit(".", 1)[0]
    return any(target_string in s for s in string_list)

def DownloadFile(url, destination_path):
    # Send a header request to get the file size first without downloading
    response = requests.get(url, stream=True)
    
    # Total size in bytes. Default to 0 if Content-Length header is missing
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 # 1 Kibibyte

    # Initialize the progress bar
    progress_bar = tqdm(
        total=total_size, 
        unit='iB', 
        unit_scale=True, 
        desc="Downloading",
        ncols=100
    )
    
    try:
        with open(destination_path, 'wb') as file:
            for data in response.iter_content(block_size):
                file.write(data)
                progress_bar.update(len(data))
    finally:
        progress_bar.close()

    if total_size != 0 and progress_bar.n != total_size:
        LogError("Something went wrong. Download incomplete.")
        return False
    else:
        LogInfo(f"Download completed successfully! File saved to: {destination_path}")
        return True

def VerifyFiles(paths):
    not_found = []
    for p in paths:
        if not os.path.exists(p): not_found.append(p)

if __name__ == "__main__":
    links = []
    failed = []
    current = None

    def MainMenu():
        print(f"1) Links from .txt file\n2) From FitGirl page\n3) Cancel")
        selection = input("Select: ").replace(" ","")

        if selection == "1":
            if not FromTxtFile():
                ClearConsole()
                MainMenu()
                return
            else:
                Main()
            
        if selection == "2":
            if not FromPage():
                ClearConsole()
                MainMenu()
                return
            else:
                Main()
                
        if selection == "3":
            quit(0)

        else:
            ClearConsole()
            MainMenu()

    def FromTxtFile():
        global links

        fname = input("Input filename (# to cancel): ")

        if fname == "#":
            return False

        if not os.path.exists(fname):
            ClearConsole()
            LogError("File not found!")
            FromTxtFile()
            return
        
        with open(fname, "r") as f:
            for l in f.read().split("\n"):
                if len(l) <= 3: continue
                if l[0] == "#": continue
                links.append(l)

        return True

    def FromPage():
        global links
        url = input("Input FitGirl page URL ('x' to cancel): ").lower()

        if url == "x":
            ClearConsole()
            MainMenu()
            return False
        
        links = GetFFastLinks(url)

        if links == False:
            LogError("Error fetching links from FitGirl page!")
            return False
        
        return True

    def FilterLinks():
        global links

        pre_total = len(links)
        filtered = [l for l in links if "optional" in l or "selective" in l]
        for _ in filtered:
            links.remove(_)

        for i in range(len(filtered)):
            print(f"{i+1}) {filtered[i]}")
                
        selection = input("Select which links to include (',' as separator. 'x' to cancel): ").lower()

        if selection == "x": 
            links.extend(filtered)
            return
        selection = selection.replace(" ","").split(",")
        for i in selection:
            links.append(filtered[int(i)-1])

        LogInfo(f"{len(links)} out of {pre_total} selected")

    def Main():
        global failed

        LogInfo(f"Found {len(links)} link(s)")
        
        selection = input("Would you like to filter optional/selective links? (y/n): ").lower().replace(" ","")
        if selection == "y":
            FilterLinks()
        if selection == "n":
            pass
        else:
            ClearConsole()
            Main()

        try:
            input("Press any key to continue to downloading... (Ctrl + C to cancel)")
            start_time = time.time()

            if config.CREATE_GAME_FOLDER_INSIDE_DOWNLOAD: 
                game_name = input("Input game name: ")
            else:
                game_name = ""

            for l in links:
                current = l

                fname = GetFilename(l)
                LogInfo(f"{links.index(l)}/{len(links)} Downloading {fname}")
                dl_path = Path(config.DOWNLOAD_OUTPUT)
                if config.CREATE_GAME_FOLDER_INSIDE_DOWNLOAD:
                    dl_path = dl_path / game_name
                    if not os.path.exists(dl_path):
                        os.mkdir(dl_path)
                dl_path = dl_path / fname
                
                download = DownloadFile(ExtractLink(l), dl_path)
                if download == False:
                    LogError(f"Error downloading {fname}, added to failed list")
                    failed.append(l)

            LogInfo("All downloads attempted")
                

        except KeyboardInterrupt:
            LogInfo("Cancelled by user")
            quit(0)
        except Exception:
            traceback.print_exc()
            LogError(f"Unknown error failed {current}")
            failed.append(current)

        finally:
            if len(failed) > 0:
                LogWarning(f"There's {len(failed)} link(s) failed out of {len(links)}")
                with open("failed.txt", "w") as f:
                    for l in failed:
                        f.write(f"{l}\n")
                LogInfo("Failed links written to failed.txt, you can retry with this file")
            
            LogInfo(f"Execution time: {str(time.time() - start_time).split('.')[0]}")
            quit(0)

    MainMenu()
        