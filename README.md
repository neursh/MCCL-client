<h1 align=center>
    Minecraft Cloudflared Client
</h1>
<h2 align=center>
    A rough implementation of MCCL CLient ⛈️
</h2>

> [!WARNING]
> Currently this only supports Paper server.
> 
> This is not even a "Work in progress", I'll call it a "Far from progress". But I think it will get the idea across.
> 
> Some errors is not handled, bugs here and there, but if you do it correctly, I **THINK** it'll work.

> [!CAUTION]
> **DO NOT** quit by closing the terminal, call `stop` command in console and wait for MCCL to handle the rest, closing your terminal while the server is open could results in your world getting corrupted.

## Setup
After you've finished setup your MCCL Workers, it's time to setup the client for it!

- Download the latest build.
- Create a **server** folder in the same folder that you've extracted the build.
- Put your server executable in it.
- Take a look at `config.template.json` and make it yourself, put it in the same place as MCCL.
- Provide `executable` and `cmd` for MCCL to work with.
- Change `service` to the URL of your MCCL workers.
- Change `discord-webhook` if you want to announce when you're opening the server.
- After this step, you can pack everything up and send to other people to be able to host.
- And on each host, replace `name` and `token` accordingly to the accepted user in MCCL workers.
- Launch `mccl.exe` and start a session.
- **DO NOT** quit by closing the terminal, call `stop` command in console and wait for MCCL to handle the rest, closing your terminal while the server is open could results in your world getting corrupted.
