import os
import requests
import json

class Utils:
    @classmethod
    def scanServerFolder(cls, config: dict, path: str, withRelativeBytesOffset: bool | None = None) -> dict[str, list[int]]:
        scanResult = {}
        for root, _, files in os.walk(path):
            for file in files:
                cPath: str = os.path.join(root, file)
                if any([cPath.startswith(f"{path}{excluded}") for excluded in config["excludeLockStructure"] + [config["executable"]]]):
                    continue

                modifiedDate = os.path.getmtime(cPath)

                if withRelativeBytesOffset:
                    scanResult.update({
                        cPath: [modifiedDate, os.path.getsize(cPath)],
                    })
                else:
                    scanResult.update({
                        cPath: [modifiedDate],
                    })

        return scanResult

    @classmethod
    def combineValues(cls, through: list):
        if not through:
            return []

        combinedList = [through[0]]

        for value in through[1:]:
            if value != combinedList[-1]:
                combinedList.append(value)

        return combinedList
    
    @classmethod
    def closeSession(cls, session: requests.Session, config: dict):
        config["localLastRun"] = int(session.get(f"{config["service"]}/session/stop").json()["time"])

        with open("config.json", "w") as rawConfig:
            json.dump(config, rawConfig)

        try:
            session.post(
                config["discordWebhook"],
                json={
                    "content":None,
                    "embeds":[{
                        "title": "Server closed",
                        "description": f"{config["name"]} has closed the server.",
                        "color": 39423
                        }],
                    "attachments":[]}
                )
        except:
            pass