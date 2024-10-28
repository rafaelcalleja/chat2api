import json
import os
import requests
import logging
import base64

from utils.Logger import logger

DATA_FOLDER = "data"
TOKENS_FILE = os.path.join(DATA_FOLDER, "token.txt")
REFRESH_MAP_FILE = os.path.join(DATA_FOLDER, "refresh_map.json")
ERROR_TOKENS_FILE = os.path.join(DATA_FOLDER, "error_token.txt")
WSS_MAP_FILE = os.path.join(DATA_FOLDER, "wss_map.json")
REFRESH_MAP_URL = os.environ.get('REFRESH_MAP_URL')
REFRESH_MAP_URL_AUTH = os.environ.get('REFRESH_MAP_URL_AUTH', "")

count = 0
token_list = []
error_token_list = []
refresh_map = {}
wss_map = {}


if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

if os.path.exists(REFRESH_MAP_FILE):
    with open(REFRESH_MAP_FILE, "r") as file:
        refresh_map = json.load(file)
elif REFRESH_MAP_URL:
    headers = {
        'accept': 'application/json',
        'authorization': f'Bearer {REFRESH_MAP_URL_AUTH}'
    }

    response = requests.get(f"{REFRESH_MAP_URL}", headers=headers)

    logger.info(f"Refresh Map with status: {response.status_code}")
    response_json = response.json()
    response_item = response_json['items'][0] if len(response_json['items']) > 0 else None
    refresh_map = {}
    if response_item:
        refresh_map = json.loads(base64.b64decode(response_item).decode('utf-8'))
        with open(TOKENS_FILE, "a", encoding="utf-8") as file:
            for key in refresh_map:
                file.write(refresh_map[key]["token"] + "\n")
else:
    refresh_map = {}

if os.path.exists(WSS_MAP_FILE):
    with open(WSS_MAP_FILE, "r") as file:
        wss_map = json.load(file)
else:
    wss_map = {}
    
    
if os.path.exists(TOKENS_FILE):
    with open(TOKENS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                token_list.append(line.strip())
else:
    with open(TOKENS_FILE, "w", encoding="utf-8") as f:
        pass

if os.path.exists(ERROR_TOKENS_FILE):
    with open(ERROR_TOKENS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                error_token_list.append(line.strip())
else:
    with open(ERROR_TOKENS_FILE, "w", encoding="utf-8") as f:
        pass

if token_list:
    logger.info(f"Token list count: {len(token_list)}, Error token list count: {len(error_token_list)}")