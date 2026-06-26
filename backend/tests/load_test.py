import requests
import random
import time

# 测试的示例问题（你可以随时扩展）未来增加功能后要进一步修改load_test.
questions = [
    "Can I refund my ticket?",
    "Can I transfer my ticket to a friend?",
    "Can I bring food or drinks?",
    "Any EDM shows in Hong Kong?",
    "Any indie concerts in Taipei?",
    "Rock concerts in Tokyo?",
    "Any jazz events in East Asia?",
    "What time does the venue open?",
    "How much is the service fee?",
    "Is electronic ticket supported?",
]

context_template = {
    "city": "Hong Kong",
    "liked_tags": ["edm", "indie", "jazz"],
}

N = 200   # 请求总次数，可调整（100 / 200 / 500）

success = 0
fail = 0

latencies = []

print(f"Starting load test: {N} requests...")
print("--------------------------------------")

for i in range(N):
    q = random.choice(questions)
    t0 = time.time()

    try:
        r = requests.post(
            "http://127.0.0.1:8000/ask",
            json={
                "question": q,
                "context": context_template,
            },
            timeout=5,
        )
        latency = time.time() - t0
        latencies.append(latency)

        if r.status_code == 200:
            success += 1
        else:
            fail += 1

    except Exception as e:
        fail += 1
        print(f"[{i}] Error:", e)

print("--------------------------------------")
print("Load test completed!")
print(f"Total requests: {N}")
print(f"Success: {success}")
print(f"Failed: {fail}")
print(f"Success rate: {success/N*100:.2f}%")

if latencies:
    print(f"Average latency: {sum(latencies)/len(latencies):.3f}s")
    print(f"Max latency: {max(latencies):.3f}s")
    print(f"Min latency: {min(latencies):.3f}s")
