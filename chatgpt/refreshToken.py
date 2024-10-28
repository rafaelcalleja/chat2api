import json
import random
import time
import base64
import requests

from fastapi import HTTPException

from utils.Client import Client
from utils.Logger import logger
from utils.config import proxy_url_list
import chatgpt.globals as globals


def save_refresh_map(refresh_map):
    with open(globals.REFRESH_MAP_FILE, "w") as file:
        json.dump(refresh_map, file)


async def rt2ac(refresh_token, force_refresh=False):
    if not force_refresh and (refresh_token in globals.refresh_map and int(time.time()) - globals.refresh_map.get(refresh_token, {}).get("timestamp", 0) < 5 * 24 * 60 * 60):
        access_token = globals.refresh_map[refresh_token]["token"]
        logger.info(f"refresh_token -> access_token from cache")
        return access_token
    else:
        try:
            access_token, new_refresh_token = await chat_refresh(refresh_token)

            if refresh_token in globals.refresh_map:
                old_access_token = globals.refresh_map[refresh_token]['token']
                if old_access_token in globals.token_list:
                    for i, token in enumerate(globals.token_list):
                        if token == old_access_token:
                            del globals.token_list[i]
                            break
                del globals.refresh_map[refresh_token]

            refresh_token = new_refresh_token
            globals.refresh_map[refresh_token] = {"token": access_token, "timestamp": int(time.time())}
            save_refresh_map(globals.refresh_map)
            logger.info(f"refresh_token -> access_token with openai: {access_token}")

            globals.token_list.append(access_token)
            with open("data/token.txt", "a", encoding="utf-8") as f:
                f.write(access_token + "\n")

            if globals.REFRESH_MAP_URL:
                headers = {
                    'accept': 'application/json',
                    'authorization': f'Bearer {globals.REFRESH_MAP_URL_AUTH}'
                }

                params = {'value': base64.b64encode(json.dumps(globals.refresh_map).encode('utf-8')).decode('utf-8')}
                requests.post(f"{globals.REFRESH_MAP_URL}/pop", headers=headers)
                response = requests.post(f"{globals.REFRESH_MAP_URL}/push", headers=headers, params=params)

                logger.info(f"Refresh Map saved status: {response.status_code}")

            return access_token
        except HTTPException as e:
            raise HTTPException(status_code=e.status_code, detail=e.detail)

async def ac2rt2ac(access_token, force_refresh=False):
    for refresh_token in globals.refresh_map:
        if globals.refresh_map[refresh_token]["token"] == access_token:
            return await rt2ac(refresh_token, force_refresh=force_refresh)

    raise HTTPException(status_code=404, detail="AccessToken not found")

async def chat_refresh(refresh_token):
    data = {
        "client_id": "DRivsnm2Mu42T3KOpqdtwB3NYviHYzwD",
        "grant_type": "refresh_token",
        "redirect_uri": "com.openai.chat://auth0.openai.com/ios/com.openai.chat/callback",
        "refresh_token": refresh_token
    }
    client = Client(proxy=random.choice(proxy_url_list) if proxy_url_list else None)
    try:
        r = await client.post("https://auth0.openai.com/oauth/token", json=data, timeout=5)
        if r.status_code == 200:
            json = r.json()
            access_token = json['access_token']
            refresh_token = json['refresh_token']
            return access_token, refresh_token
        else:
            with open(globals.ERROR_TOKENS_FILE, "a", encoding="utf-8") as f:
                f.write(refresh_token + "\n")
            if refresh_token not in globals.error_token_list:
                globals.error_token_list.append(refresh_token)
            raise Exception(r.text[:100])
    except Exception as e:
        logger.error(f"Failed to refresh access_token `{refresh_token}`: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh access_token.")
    finally:
        await client.close()
        del client

def main():
    import asyncio
    refresh_token = 'v1.OadEUCpFvxGkYSMJgJuw6wFF_yEJSbApWXyiLNP3Lk_s6ljBEapi0iWrm7B5HrkrP71F_PrvKf3wElpryE8xzKQ'
    asyncio.run(rt2ac(refresh_token, True))

if __name__ == "__main__":
    main()