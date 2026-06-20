import urllib.request, json

# 直接打 Vite 代理端口 (5173)，模拟浏览器请求
s = json.load(urllib.request.urlopen("http://localhost:5173/api/sample"))
body = {"rider": s["rider"], "orders": s["orders"], "strategy": s["strategy"], "max_step": 2.0}
req = urllib.request.Request("http://localhost:5173/api/simulate",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req, timeout=60)
sim = json.load(resp)
with open("/tmp/proxy_final.txt", "w") as f:
    f.write(f"status={resp.status}\n")
    f.write(f"frames={len(sim['frames'])}\n")
    f.write(f"total_time={sim['total_time']:.3f}\n")
    f.write(f"total_distance={sim['total_distance']:.2f}\n")
    f.write(f"route_stops={len(sim['route'])}\n")
    f.write(f"risk_count={sim['risk']['risk_count']}\n")
    f.write("sequence=" + "->".join(f"{x['kind'][:1]}{x['order_id']}" for x in sim['route']) + "\n")
    f.write("frames[0] keys: " + ",".join(sim['frames'][0].keys()) + "\n")
    f.write("final order_states: " + str(sim['frames'][-1]['order_states']) + "\n")
print("OK")
