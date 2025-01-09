import requests
from tqdm.utils import CallbackIOWrapper
from tqdm import tqdm
import os
import json
import sys
from io import BytesIO
from core.utils import Utils
import traceback

class ContentService:
    def __init__(self, session: requests.Session, config: dict):
        self.session = session
        self.config = config
    
    def withService(self, url: str):
        return f"{self.config["service"]}{url}"

    def downloadServer(self, endRange: int | None = None):
        try:
            with open("server.nlock", "wb+") as serverFile:
                resp = self.session.get(self.withService(f"/session/getServer?getTo={endRange}"), timeout=None, stream=True)
                total = int(resp.headers.get("content-length", 0))

                bar = tqdm(
                    desc="Server build",
                    total=total,
                    unit="iB",
                    unit_scale=True,
                    unit_divisor=1024,
                )
                for data in resp.iter_content(chunk_size=1024):
                    size = serverFile.write(data)
                    bar.update(size)
                    
                bar.close()
        except:
            traceback.print_exc()
            Utils.closeSession(self.session, self.config)
            input("Press Enter to close...")
            sys.exit(0)
    
    def extractServerLock(self, mapping: dict[str, list[int]]):
        if os.path.exists("server.nlock") and os.path.isfile("server.nlock"):
            try:
                with open("server.nlock", "rb") as serverLock:
                    for file, info in mapping.items():
                        os.makedirs(os.path.dirname(file), exist_ok=True)
                        with open(file, "wb") as extractedFile:
                            extractedFile.write(serverLock.read(info[1]))
                        os.utime(file, (info[0], info[0]))
                os.remove("server.nlock")
            except:
                traceback.print_exc()
                return False
            return True
        else:
            return False
    
    def archiveServerLock(self):
        try:
            files = dict(sorted(Utils.scanServerFolder(self.config, ".\\server\\", withRelativeBytesOffset=True).items(), key=lambda item: item[1][0], reverse=True))

            with open("server.nlock", "wb") as serverLockHandle:
                for file in files.keys():
                    with open(file, "rb") as rf:
                        while chunk := rf.read(2048):
                            serverLockHandle.write(chunk)
            
            with open("server.nlock.map.json", "w", encoding="utf-8") as mapping:
                mapping.write(json.dumps(files))
        except:
            traceback.print_exc()
            return False
        
        return True
    
    def createMultipart(self):
        try:
            self.multipartId = self.session.get(self.withService("/session/createMultipartUpload")).json()["uploadId"]
        except:
            traceback.print_exc()
            Utils.closeSession(self.session, self.config)
            input("Press Enter to close...")
            sys.exit(0)

    
    def abortMultipart(self):
        try:
            self.session.get(self.withService(f"/session/uploadAbort?uploadId={self.multipartId}"))
        except:
            traceback.print_exc()
            Utils.closeSession(self.session, self.config)
            input("Press Enter to close...")
            sys.exit(0)
    
    def uploadMultipart(self):
        try:
            uploadedMultipart = []
            stopRes = None
            part = 1
            cancel = False
            with open("server.nlock", "rb") as sv:
                des = BytesIO(sv.read(100000000))
                total = des.getbuffer().nbytes
                while total > 0 and not cancel:
                    while True:
                        bar = tqdm(
                            desc=f"[MCCL] Uploading part {part}",
                            total=total,
                            unit="iB",
                            unit_scale=True,
                            unit_divisor=1024,
                        )
                        readWrapper = CallbackIOWrapper(bar.update, des, "read")
                        stopRes = self.session.post(
                            self.withService(f"/session/uploadPart?uploadId={self.multipartId}&part={part}"),
                            data=readWrapper, # type: ignore
                            timeout=None)
                        if stopRes.status_code == 200:
                            des = BytesIO(sv.read(100000000))
                            total = des.getbuffer().nbytes
                            if total > 0:
                                part += 1
                            uploadedMultipart.append(stopRes.json())
                            break
                        elif stopRes.status_code != 501:
                            if input("Something went wrong.\n\nPress Enter to retry, type \"Cancel\" to abort upload: ") == "Cancel":
                                print("[MCCL] Aborting...")
                                self.abortMultipart()
                                cancel = True
                                break
                        bar.close()
            
            if not cancel:
                print("[MCCL] Signing multipart task...")
                result = self.session.post(self.withService(f"/session/uploadComplete?uploadId={self.multipartId}"), json=uploadedMultipart)

                if result.status_code != 200:
                    self.abortMultipart()
                    return False
                else:
                    with open("server.nlock.map.json", "r", encoding="utf-8") as mapping:
                        self.session.post(self.withService("/session/uploadMapping"), data=mapping.read())
                    return True
        except:
            traceback.print_exc()
            return False
        
        return False
    
    def clearLockFiles(self):
        try:
            os.remove("server.nlock")
            os.remove("server.nlock.map.json")
        except:
            pass