import chainlit as cl
import httpx

@cl.on_message
async def main(message: cl.Message):
    msg = cl.Message(content="")
    await msg.send()
    
    headers = {}
    request_body = {"question": message.content}

    with httpx.stream(
        "POST",
        "http://127.0.0.1:5555/chat",
        json=request_body,
        headers=headers,
        timeout=600,
    ) as r:
        for chunk in r.iter_text():
            print(chunk, flush=True, end="")
            if token := chunk or "":
                await msg.stream_token(token)

    await msg.update()