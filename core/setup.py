import requests
import sys
import os
from core.utils import Utils

class Setup:
    def __init__(self, session: requests.Session, config: dict):
        self.session = session
        self.config = config

    def withService(self, url: str):
        return f"{self.config["service"]}{url}"
    
    def authorized(self, response: requests.Response):
        if response.status_code == 401:
            return False
        return True

    def check(self):
        sessionCheck = self.session.get(self.withService("/session/check"))

        if not self.authorized(sessionCheck):
            return 401

        sessionCheckJson = sessionCheck.json()

        if sessionCheckJson["status"] == "running":
            return sessionCheckJson["host"]
        
        # Save server"s reported last run.
        self.lastRun: int = sessionCheckJson["lastRun"]
        
        return True
    
    def start(self):
        sessionStart = self.session.get(self.withService("/session/start"))

        # 401 check already passed. No need to repeat.
        
        sessionStartJson = sessionStart.json()

        if sessionStartJson["status"] == "running":
            return sessionStartJson["host"]
        
        try:
            self.session.post(
                self.config["discordWebhook"],
                json={
                    "content": None,
                    "embeds": [{
                        "title": "Server opened",
                        "description": f"The server is being hosted by {self.config["name"]}!",
                        "color": 39423
                        }],
                    "attachments":[],
                }
            )
        except:
            pass
        
        return True
    
    def updateAvailability(self):
        if self.config["localLastRun"] < self.lastRun:
            return True
        if self.config["localLastRun"] > self.lastRun:
            print("[MCCL] Conflict detected! Canceling this session...\n")
            Utils.closeSession(self.session, self.config)
            sys.exit(0)
        return False
    
    def compareLocks(self):
        latestMapping = self.session.get(f"{self.config["service"]}/session/getMapping")
        if latestMapping.status_code == 404:
            print("[MCCL] Can't find mapping structure file on the cloud. Exiting...")
            return None, None
        
        print("[MCCL] Reading mapping...")
        latestMappingJson: dict[str, list[int]] = latestMapping.json()

        localServerFolder: dict[str, list[int]] = Utils.scanServerFolder(self.config, ".\\server\\")
        localServerFolder = dict(sorted(localServerFolder.items(), key=lambda item: item[1][0], reverse=True))
        
        print("[MCCL] Checking for conflicts in world files...")

        difference = set(localServerFolder.keys()) - set(latestMappingJson.keys())
        worldConflicts = []

        for conflicted in difference:
            if any([conflicted.startswith(worldFolder) for worldFolder in [".\\server\\world", ".\\server\\world_nether", ".\\server\\world_the_end"]]):
                print(conflicted)
                worldConflicts.append(conflicted)
        
        if len(worldConflicts) > 0:
            while True:
                askForDeletion = input("[MCCL] These file have conflicted with the server version. Would you like to delete and continue? [Y/N]").upper()
                if askForDeletion[0] == "Y":
                    break
                if askForDeletion[0] == "N":
                    print("[MCCL] Releasing session from main service...")
                    Utils.closeSession(self.session, self.config)
                    sys.exit(0)
            
            print("[MCCL] Removing conflicted world files...")
            for entry in worldConflicts:
                os.remove(entry)
                del localServerFolder[entry]

        print("[MCCL] Comparing with your local structure...")

        # Since both has been sorted in reverse and removed all conflicted entries,
        # I have to get the smallest timestamp that is differrent and download from that.
        # Cloudflare R2 doesn't support get multiple ranges at once.

        getChunkTo = -1

        for index, (file, info) in enumerate(latestMappingJson.items()):
            if file not in localServerFolder:
                getChunkTo = index
                continue

            # The number is very specific, so I have to strip the float part.
            localTime = int(localServerFolder[file][0])
            latestTime = int(info[0])
            
            if localTime != latestTime:
                getChunkTo = index
        
        # Get size offset relative to the previous one to get the total number of size for download.
        totalBytes = sum([size[1] for _, size in latestMappingJson.items()])
        print(f"[MCCL] Compare mapping complete, a total of {getChunkTo + 1} files needed to be updated.")

        self.latestMapping = latestMappingJson

        return totalBytes, getChunkTo