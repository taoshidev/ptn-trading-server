# pn-tg-server


# install bittensor 
```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv nvtop gcc jq npm
```

# install pm2
```bash
sudo npm install pm2 -g && pm2 update
```

# make pm2 and processes survive reboot
```bash
npm install pm2@latest -g && pm2 update && pm2 save --force && pm2 startup && pm2 save
```

# run Bybit copy trading bridge for Dale
```bash
cd ~
git clone https://github.com/taoshidev/ptn-trading-server
```

## Edit your .env file
```bash
nano ~/ptn-trading-server/.env

# contents
API_KEY=
TOP_MINER_UID=
MINER_POSITIONS_ENDPOINT_URL=
```

# Start sn8-ptn-bybit-relay
```bash
cd ~/ptn-trading-server
pm2 start ./run_at_bybit.py --name sn8-ptn-bybit-relay --interpreter python3 && pm2 save
```

## Copyright © 2024 Taoshi Inc (edits by sirouk)

```
Source code produced by Taoshi Inc may not be reproduced, modified, or 
distributed without the express permission of Taoshi Inc.
