import requests, json, os, tarfile
from io import BytesIO
from tqdm.utils import CallbackIOWrapper
from tqdm import tqdm

def savewrap(path, name, executable):
    with tarfile.open(name, 'w') as tarhandle:
        for root, _, files in os.walk(path):
            for f in files:
                cPath = os.path.join(root, f)
                if cPath.startswith('./cache') or cPath.startswith('./libraries') or cPath.startswith('./versions') or cPath.startswith(f'./{executable}'):
                    continue
                print(f'[MCCL] Archive <- {cPath}')
                tarhandle.add(cPath)

def main(session: requests.Session):
    config = None
    with open('config.json', 'r') as rawConfig:
        config = json.load(rawConfig)

    session.headers = { 'Authorization': f'{config['name']} {config['token']}' }

    input('Fool proof, press Enter to continue...')

    print(f'[MCCL] Checking for session...')

    sessionCheck = session.get(f'{config['service']}/session/check').json()

    if sessionCheck['status'] == 'running':
        input(f'[MCCL] {sessionCheck['host']} is running the session!\n\nPress Enter to close...')
        return

    print(f'[MCCL] Starting a session on behalf of {config['name']}...')

    sessionStart = session.get(f'{config['service']}/session/start')
    if sessionStart.status_code == 200:
        print('[MCCL] Session started! Checking for latest update...')
        try:
            requests.post(
                config['discord-webhook'],
                json={
                    'content':None,
                    'embeds':[{
                        'title': 'Server opened',
                        'description': f'The server is being hosted by {config['name']}!',
                        'color': 39423
                        }],
                    'attachments':[]}
            )
        except:
            pass
    else:
        input(f'[MCCL] {sessionStart['host']} is running the session!\n\nPress Enter to close...')
        return
    
    if config['localLastRun'] < sessionCheck['lastRun']:
        print('[MCCL] Update available. Downloading the latest patch...')
        with open('server.tar', 'wb+') as serverFile:
            resp = session.get(f'{config['service']}/session/getServer', timeout=None, stream=True)
            total = int(resp.headers.get('content-length', 0))

            bar = tqdm(
                desc=f'Server build {sessionCheck['lastRun']}',
                total=total,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            )
            for data in resp.iter_content(chunk_size=1024):
                size = serverFile.write(data)
                bar.update(size)
                
            bar.close()
        
        print(f'[MCCL] Cleaning up files...')
        for root, dirs, files in os.walk('./server'):
            for f in files:
                cPath = os.path.join(root, f)
                if cPath.startswith('./server\\cache') or cPath.startswith('./server\\libraries') or cPath.startswith('./server\\versions') or cPath.startswith(f'./server\\{config['executable']}'):
                    continue
                os.remove(cPath)
        
        print(f'[MCCL] Applying patch...')
        with tarfile.open('server.tar', 'r') as serverFile:
            serverFile.extractall(path='./server')
        os.remove('server.tar')
        
    elif config['localLastRun'] > sessionCheck['lastRun']:
        print('[MCCL] Conflict detected! Canceling this session...\n')
        session.get(f'{config['service']}/session/stop')

        input('Press Enter to close...')
        return
    else:
        print('[MCCL] No updates found!')
    
    print('[MCCL] Starting server...')

    owd = os.getcwd()
    os.chdir('./server')
    os.system(' '.join(config['cmd']))

    print('[MCCL] Server closed! Wrapping things up...')
    savewrap('./', 'server.tar', config['executable'])

    print('[MCCL] Creating multipart upload task...')
    multipartInfo = session.get(f'{config['service']}/session/createMultipartUpload').json()

    print('[MCCL] Uploading the session...')
    uploadedMultipart = []
    stopRes = None
    part = 1
    cancel = False
    with open('server.tar', 'rb') as sv:
        des = BytesIO(sv.read(90000000))
        total = des.getbuffer().nbytes
        while total > 0 and not cancel:
            while True:
                bar = tqdm(
                    desc=f'[MCCL] Uploading part {part}',
                    total=total,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
                )
                read_wrapper = CallbackIOWrapper(bar.update, des, 'read')
                stopRes = session.post(
                    f'{config['service']}/session/uploadPart?uploadId={multipartInfo['uploadId']}&part={part}',
                    data=read_wrapper,
                    timeout=None)
                if stopRes.status_code == 200:
                    des = BytesIO(sv.read(90000000))
                    total = des.getbuffer().nbytes
                    if total > 0:
                        part += 1
                    uploadedMultipart.append(stopRes.json())
                    break
                elif stopRes.status_code != 501:
                    if input('Something went wrong.\n\nPress Enter to retry, type "Cancel" to abort upload: ') == "Cancel":
                        print("[MCCL] Aborting...")
                        session.get(f'{config['service']}/session/uploadAbort?uploadId={multipartInfo['uploadId']}')
                        cancel = True
                        break
                bar.close()
    
    if not cancel:
        print("[MCCL] Signing multipart task...")
        result = session.post(f'{config['service']}/session/uploadComplete?uploadId={multipartInfo['uploadId']}', json=uploadedMultipart)

        if result.status_code != 200:
            session.get(f'{config['service']}/session/uploadAbort?uploadId={multipartInfo['uploadId']}')
            print("[MCCL] Can't sign multipart task. Upload failed. Please contact admin! The program will continue to exit normally...")
        else:
            print("[MCCL] Signed multipart successfully. File uploaded!")

    os.remove('server.tar')

    print('[MCCL] Releasing session lock from main server...')

    config['localLastRun'] = int(session.get(f'{config['service']}/session/stop').json()['time'])
    os.chdir(owd)
    with open('config.json', 'w') as rawConfig:
        json.dump(config, rawConfig)

    try:
        session.post(
            config['discord-webhook'],
            json={
                'content':None,
                'embeds':[{
                    'title': 'Server closed',
                    'description': f'{config['name']} has closed the server.',
                    'color': 39423
                    }],
                'attachments':[]}
            )
    except:
        pass
    
    input('[MCCL] Session ended!\n\nPress Enter to close...')

if __name__ == '__main__':
    with requests.Session() as session:
        main(session)
