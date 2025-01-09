<h1 align=center>
    Minecraft Cloudflared Client
</h1>
<h2 align=center>
    An implementation of MCCL CLient ⛈️
</h2>

> [!WARNING]
> This is an Alpha release. Tested on Windows 10/11.
> 
> Some errors is not handled, but if you do it correctly, I **THINK** it'll work.

> [!CAUTION]
> In any situation, **DO NOT** quit by closing the terminal, run `stop` command in console and wait for MCCL to handle the rest, closing your terminal while the server is open could results in conflicts between MCCL instances and potentially corrupt the server.

> [!TIP]
> Cloudflare R2 have a free limit of 10 GB.
> 
> Try not to go over it. Use [MCA Selector](https://github.com/Querz/mcaselector) to clear unused chunks to reduce world size.
> 
> Smaller world size also makes updates and server uploads faster.

## Setup
After you've finished setup your [MCCL Workers](https://github.com/neursh/MCCL-workers), it's time to setup the client for it!

- Download the latest build.
- Create a `server` folder in the same folder that you've extracted the build.
- Put your server executable in it.
- Take a look at `config.template.json`:
    - `name`: Username must be differrent for every instance.
    - `token`: Token must be differrent for every instance.
    - `service`: The Workers url from deployed MCCL Workers.
    - `discordWebhook`: A webhook in case you want to announce server open / close (optional).
    - `localLastRun`: MCCL client's internal variable, do not change unless you know what you're doing.
    - `cmd`: Command to run the server.
    - `excludeLockStructure`: Exclude folders/files in `server` folder when uploading the server to MCCL Workers. By default, executable is also excluded.
- After this step, rename `config.template.json` to `config.json`, you can pack everything up and send to other people to be able to host.

For example `config.json`:
```json
{
    "name": "name",
    "token": "sdkKlai...",
    "service": "https://...workers.dev",
    "discordWebhook": "https://discord.com/api/webhooks/...",
    "localLastRun": 0,
    "cmd": ["java", "-jar", "paper-1.20.4-464.jar", "-nogui"],
    "excludeLockStructure": ["cache", "libraries", "versions", "logs", "crash-report"]
}
```

- And on each host, replace `name` and `token` accordingly to the accepted user in MCCL workers.
- Launch `mccl_client.exe` and start a session.
- **DO NOT** quit by closing the terminal, call `stop` command in console and wait for MCCL to handle the rest, closing your terminal while the server is open could results in your world getting corrupted.

## What's next?
Well, do what you want with it.

- You can group everyone's devices together on Zero Tier or use Ngrok to expose TCP over the internet.
- Or for the sake of simplicity, go for Radmin VPN, though I'm not a fan of it.
- If you have a domain on Cloudflare however, I recommend using [Cloudflare Tunnel](https://www.cloudflare.com/products/tunnel/).
