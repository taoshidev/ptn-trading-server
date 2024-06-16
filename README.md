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
PAIR_MAP={"BTCUSD": {"converted": "BTCUSDT", "muid": "5something"}, "ETHUSD": {"converted": "ETHUSDT", "muid": "5somethingelse"}}
MINER_POSITIONS_ENDPOINT_URL=https://path.to/positions-endpoint
```

# Start sn8-ptn-bybit-relay
```bash
cd ~/ptn-trading-server
pm2 start ./run_at_bybit_relay.py --name sn8-ptn-bybit-relay --interpreter python3 && pm2 save
```

## Copyright © 2024 Taoshi Inc (edits by sirouk)

```
Source code produced by Taoshi Inc may not be reproduced, modified, or 
distributed without the express permission of Taoshi Inc.