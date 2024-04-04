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

## Setup
After you've finished setup your MCCL Workers, it's time to setup the client for it!

- Clone this repo.
- Create a **server** folder.
- Put your paper server in it.
- Rename `config.template.json` to `config.json`.
- Edit the command to whatever you want, but you must put the executable file at the 3rd index of the `cmd` array (`cmd[2]`).
- Change `service` to the URL of your MCCL workers.
- After this step, you can pack everything up and send to other people to be able to host.
- And on each host, replace `name` and `token` accordingly to the accepted user in MCCL workers.
- Launch `main.py` and start a session.
- **DO NOT** quit by closing the terminal, call `stop` command in console and wait for MCCL to handle changes.