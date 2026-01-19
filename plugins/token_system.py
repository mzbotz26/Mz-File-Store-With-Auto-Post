import time, secrets

TOKEN_DB = {}

TOKEN_EXPIRY = 3600  # 1 hour

def generate_token(msg_id, user_id):
    token = secrets.token_hex(8)
    TOKEN_DB[token] = {
        "msg_id": msg_id,
        "user_id": user_id,
        "time": time.time()
    }
    return token

def verify_token(token, user_id):
    data = TOKEN_DB.get(token)
    if not data:
        return None

    if data["user_id"] != user_id:
        return None

    if time.time() - data["time"] > TOKEN_EXPIRY:
        del TOKEN_DB[token]
        return None

    msg_id = data["msg_id"]
    del TOKEN_DB[token]   # one time use
    return msg_id
