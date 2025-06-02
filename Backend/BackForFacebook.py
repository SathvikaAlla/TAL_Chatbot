from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
import httpx

app = FastAPI()

VERIFY_TOKEN = "secret_token1233"
PAGE_ACCESS_TOKEN = "EAAOcjMbynsMBO6yPEiIrIGE40FxILBIOg5WRSwyCZAbvTJaZBS7nQYJ3pBUqyNv5Nwgl4VrazV7BC3A4KELoBeWxbvODadJrxMvr5bKPbusyu1HIrqZAf0SFFr7iMYNowZC7Mt2jic8I4gNnS5JwJaLRvFu20enZCxwUCvDdsoxxnMWwXudwTfhV7sHBiZBoUPADIyiMOZANpTTD9rZAoQH3yZAnBLUO8SoAZBkJUZD"  # Your Facebook Page Access Token


from fastapi import Query

@app.get("/webhook")
async def verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    verify_token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge")
):
    if mode == "subscribe" and verify_token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200)
    else:
        raise HTTPException(status_code=403, detail="Verification token mismatch")



@app.post("/webhook")
async def handle_messages(request: Request):
    body = await request.json()

    # Facebook sends different event types - filter message events
    if body.get("object") == "page":
        for entry in body.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event.get("sender", {}).get("id")
                message = messaging_event.get("message", {}).get("text")

                if sender_id and message:
                    # TODO: Replace this with call to your Azure AI model (once ready)
                    reply_text = f"You said: {message}"

                    await send_message(sender_id, reply_text)

        return JSONResponse({"status": "ok"}, status_code=200)
    else:
        raise HTTPException(status_code=404, detail="Not Found")


async def send_message(recipient_id: str, message_text: str):
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
