import requests, json, os, tarfile
from io import BytesIO
from tqdm.utils import CallbackIOWrapper
from tqdm import tqdm

def savewrap(path, name, executable):
    with tarfile.open(name, "w") as tarhandle:
        for root, _, files in os.walk(path):
            for f in files:
                cPath = os.path.join(root, f)
                if cPath.startswith("./cache") or cPath.startswith("./libraries") or cPath.startswith("./versions") or cPath.startswith(f"./{executable}"):
                    continue
                print(f"-> {cPath}")
                tarhandle.add(cPath)

def main():
    config = None
    with open("config.json", "r") as rawConfig:
        config = json.load(rawConfig)

    headers = { "Authorization": f"{config['name']} {config['token']}" }

    input("Fool proof, press Enter to continue...")

    print(f"[MCCL] Checking for session...")

    sessionCheck = requests.get(f"{config['service']}/session/check", headers=headers).json()

    if sessionCheck["status"] == "running":
        input(f"[MCCL] {sessionCheck['host']} is running the session!\n\nPress Enter to close...")
        return

    print(f"[MCCL] Starting a session on behalf of {config['name']}...")

    sessionStart = requests.get(f"{config['service']}/session/start",
                                headers=headers)
    if sessionStart.status_code == 200:
        print("[MCCL] Session started! Checking for latest update...")
    else:
        input(f"[MCCL] {sessionStart['host']} is running the session!\n\nPress Enter to close...")
        return
    
    if config["localLastRun"] < sessionCheck["lastRun"]:
        print("[MCCL] Update available. Downloading the latest patch...")
        with open("server.tar", "wb+") as serverFile:
            for part in range(sessionCheck["partsCount"]):
                resp = requests.get(f"{config['service']}/session/update/part{part}", headers=headers, timeout=None, stream=True)
                total = int(resp.headers.get('content-length', 0))
                bar = tqdm(
                    desc=f"Part {part}",
                    total=total,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
                )
                for data in resp.iter_content(chunk_size=1024):
                    size = serverFile.write(data)
                    bar.update(size)
                
                bar.close()
        
        print(f"[MCCL] Cleaning up files...")
        for root, dirs, files in os.walk("./server"):
            for f in files:
                cPath = os.path.join(root, f)
                if cPath.startswith("./server\\cache") or cPath.startswith("./server\\libraries") or cPath.startswith("./server\\versions") or cPath.startswith(f"./server\\{config['executable']}"):
                    continue
                os.remove(cPath)
        
        print(f"[MCCL] Applying patch...")
        with tarfile.open("server.tar", "r") as serverFile:
            serverFile.extractall(path="./server")
        os.remove("server.tar")
        
    elif config["localLastRun"] > sessionCheck["lastRun"]:
        print("[MCCL] Conflict detected! Canceling this session...\n")
        requests.get(f"{config['service']}/session/stop", headers=headers)

        input("Press Enter to close...")
        return
    else:
        print("[MCCL] No updates found!")
    
    print("[MCCL] Starting server...")

    owd = os.getcwd()
    os.chdir("./server")
    os.system(" ".join(config["cmd"]))

    print("[MCCL] Server closed! Wrapping things up...")
    savewrap("./", "server.tar", config["executable"])

    print("[MCCL] Uploading & stopping the session...")
    stopRes = None
    part = 0
    with open("server.tar", 'rb') as sv:
        des = BytesIO(sv.read(90000000))
        total = des.getbuffer().nbytes
        while total > 0:
            bar = tqdm(
                desc=f"[MCCL] Uploading part {part}",
                total=total,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            )
            read_wrapper = CallbackIOWrapper(bar.update, des, "read")
            stopRes = requests.post(
                f"{config['service']}/session/upload/part{part}",
                headers=headers,
                data=read_wrapper,
                timeout=None)
            if stopRes.status_code == 200:
                des = BytesIO(sv.read(90000000))
                total = des.getbuffer().nbytes
                if total > 0:
                    part += 1
            elif stopRes.status_code != 501:
                requests.get(f"{config['service']}/session/stop", headers=headers)
                input("Something went wrong.\n\nPress Enter to close...")
                return
            bar.close()
    os.remove("server.tar")

    config["localLastRun"] = int(requests.post(f"{config['service']}/session/stop", headers=headers, json={ "partsCount": part }).json()["time"])
    os.chdir(owd)
    with open("config.json", "w") as rawConfig:
        json.dump(config, rawConfig)
    
    input("[MCCL] Session ended successfully!\n\nPress Enter to close...")

if __name__ == "__main__":
    main()