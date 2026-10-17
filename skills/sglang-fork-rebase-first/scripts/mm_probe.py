"""Send one image chat request through the PE->D path, playing the router's role.

The same bootstrap_room goes to prefill and decode; the decode reply is the answer.
"""
import base64, io, json, random, sys, threading, urllib.request
from PIL import Image, ImageDraw

P_HOST, D_HOST = sys.argv[1], sys.argv[2]
img = Image.new("RGB", (448, 448), (255, 255, 255))
d = ImageDraw.Draw(img)
d.rectangle([40, 40, 240, 240], fill=(220, 20, 20))      # big red square, top-left
d.ellipse([260, 260, 420, 420], fill=(20, 20, 220))      # blue circle, bottom-right
buf = io.BytesIO(); img.save(buf, "PNG")
url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

def models(host):
    return json.load(urllib.request.urlopen(f"http://{host}:8000/v1/models", timeout=30))["data"][0]["id"]

room = random.randint(0, 2**62)
def body(host):
    return {"model": models(host), "max_tokens": 200, "temperature": 0,
            "chat_template_kwargs": {"thinking": False},
            "messages": [{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": url}},
                {"type": "text", "text": "图里有哪些形状，各是什么颜色？一句话回答。"}]}],
            "bootstrap_host": P_HOST, "bootstrap_port": 8200, "bootstrap_room": room}

def post(host, out, key):
    req = urllib.request.Request(f"http://{host}:8000/v1/chat/completions", json.dumps(body(host)).encode(),
                                 {"Content-Type": "application/json"})
    try:
        out[key] = json.load(urllib.request.urlopen(req, timeout=300))
    except Exception as e:  # keep the HTTP error body for the report
        out[key] = {"error": repr(e), "body": getattr(e, "read", lambda: b"")().decode("utf-8", "replace")[:500]}

out = {}
ts = [threading.Thread(target=post, args=(P_HOST, out, "prefill")), threading.Thread(target=post, args=(D_HOST, out, "decode"))]
[t.start() for t in ts]; [t.join() for t in ts]
for k, v in out.items():
    if "choices" in v:
        m = v["choices"][0]["message"]
        print(k, "OK", "prompt_tokens=", v["usage"]["prompt_tokens"], "|", (m.get("content") or "")[:200], "| reasoning:", (m.get("reasoning_content") or "")[:80])
    else:
        print(k, "ERR", json.dumps(v, ensure_ascii=False)[:600])
