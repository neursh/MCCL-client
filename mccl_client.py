import requests
import subprocess
from core.utils import Utils
from core.config_loader import ConfigLoader
from core.setup import Setup
from core.content_service import ContentService

def checkUnauthorized(response):
    if response == 401:
        return True
    return False

def main(session: requests.Session):
    print("[MCCL] Loading config.json...")

    loader = ConfigLoader()

    if not loader.get():
        print("[MCCL] Cannot load config.json, press Enter to exit...")
        return

    session.headers = { "Authorization": f"{loader.config["name"]} {loader.config["token"]}" }

    input("[MCCL] Fool proof, press Enter to start MCCL...")

    setup = Setup(session, loader.config)
    setupCheck = setup.check()

    if checkUnauthorized(setupCheck):
        print("[MCCL] Unauthorized, press Enter to exit...")
        return
    
    if setupCheck is not True:
        input(f"[MCCL] {setupCheck} is running the session!\n\nPress Enter to close...")
        return
    
    print(f"[MCCL] Starting a session on behalf of {loader.config["name"]}...")

    setupStart = setup.start()

    if setupStart is not True:
        print(f"[MCCL] {setupStart} is running the session!\n\nPress Enter to close...")
        return
    
    print("[MCCL] Session started! Checking for update...")

    contentService = ContentService(session, loader.config)

    if setup.updateAvailability():
        print("[MCCL] Performing lock checking...")
        totalBytes, getChunkTo = setup.compareLocks()
        
        if not totalBytes:
            Utils.closeSession(session, loader.config)
            input("[MCCL] Cannot perform update without mapping on the cloud...\n\nPress Enter to close...")
            return
        
        if getChunkTo != -1:
            print("[MCCL] Downloading server resources...")
            contentService.downloadServer(totalBytes)

            print("[MCCL] Extracting files...")
            if not contentService.extractServerLock(setup.latestMapping):
                Utils.closeSession(session, loader.config)
                input("[MCCL] Cannot perform extracting the server...\n\nPress Enter to close...")
                return
        else:
            print("[MCCL] No action needed to update.")
    
    filum_instance = None
    if loader.config["filum"]:
        print("[MCCL] Filum found! Running host...")
        filum_instance = subprocess.Popen(["filum", "host", "tcp", f"127.0.0.1:{loader.config["filum"][1]}"], executable=loader.config["filum"][0])

    print("[MCCL] Staring server...")

    subprocess.Popen(loader.config["cmd"], cwd=".\\server\\").wait()

    print("\n\n[MCCL] Server closed! Wrapping things up...")

    if filum_instance:
        filum_instance.kill()

    if not contentService.archiveServerLock():
        Utils.closeSession(session, loader.config)
        input("[MCCL] Cannot perform the action...\n\nPress Enter to close...")
        return
    
    print("[MCCL] NLock file generated. Creating multipart upload task...")

    contentService.createMultipart()

    print("[MCCL] Uploading the session...")

    if contentService.uploadMultipart():
        print("[MCCL] Signed multipart successfully. File uploaded!")
    else:
        print("[MCCL] Can't sign multipart task. Upload failed. Please contact admin! The program will continue to exit normally...")

    contentService.clearLockFiles()

    print('[MCCL] Releasing session from main service...')

    Utils.closeSession(session, loader.config)
    input('[MCCL] Session ended!\n\nPress Enter to close...')

if __name__ == "__main__":
    with requests.Session() as session:
        main(session)