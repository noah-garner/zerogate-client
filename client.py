import asyncio
import json
import logging
import os
import random
import sys
import urllib.request
import urllib.error

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)

log = logging.getLogger("ZEROGATE")

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "")

HEADERS = {
    "X-ZeroGate-Key": "zerogate-beta-key",
    "X-Runpod-Key": RUNPOD_API_KEY,
    "Content-Type": "application/json",
    "User-Agent": "ZeroGate-Client/1.0",
}

PROMPTS = [
    "Analyze the economic drain of unmanaged bare-metal GPU idle time for AI start-ups, and contrast it with the operational cost-arbitrage of a self-hosted, scale-to-zero multi-tenant control plane running on wholesale spot instances in one dense sentence.",
    "Write a high-performance concurrent python worker loop strategy.",
    "Why is unmanaged GPU idle time an enterprise financial drain?",
    "Synthesize the trade-offs between Kafka streams and RabbitMQ configurations.",
]

BASE_URL = os.getenv("ZEROGATE_BASE_URL", "https://api.zerogate.cloud").rstrip("/")

def send_sync_request(url, data_bytes, headers_dict):
    """Executes a synchronous HTTP POST request to bypass third-party library dependencies."""
    req = urllib.request.Request(
        url, data=data_bytes, headers=headers_dict, method="POST"
    )
    with urllib.request.urlopen(req, timeout=60.0) as response:
        return response.status, response.read(), response.info()


async def fire_simulated_inference(task_id):
    arg_model = sys.argv[1].lower().strip() if len(sys.argv) > 1 else "mixed"

    if "llama" in arg_model:
        chosen_model = "unsloth/Meta-Llama-3.1-8B-Instruct"
    elif "phi" in arg_model:
        chosen_model = "microsoft/Phi-3.5-mini-instruct"
    else:
        chosen_model = random.choice(
            ["unsloth/Meta-Llama-3.1-8B-Instruct", "microsoft/Phi-3.5-mini-instruct"]
        )

    payload = {"model": chosen_model, "prompt": random.choice(PROMPTS)}
    data_bytes = json.dumps(payload).encode("utf-8")
    url = f"{BASE_URL}/v1/compute"

    try:
        status, body, response_info = await asyncio.to_thread(
            send_sync_request, url, data_bytes, HEADERS
        )

        content_type = response_info.get("Content-Type", "")
        if "application/json" in content_type:
            res_json = json.loads(body.decode("utf-8"))
            req_id = res_json.get("request_id", "unknown_id")
            log.info(f"[Task {task_id}] Gateway Response: {status} | {req_id}")
        else:
            log.info(
                f"[Task {task_id}] Error: Expected JSON response, got text/html. Check your BASE_URL."
            )

    except urllib.error.HTTPError as e:
        log.info(f"[Task {task_id}] Gateway HTTP Error: {e.code}")
    except urllib.error.URLError as e:
        log.info(f"[Task {task_id}] Gateway Network/Timeout Error: {e.reason}")
    except Exception as e:
        log.info(f"[Task {task_id}] Unexpected Error: {e}")

async def run_stress_test_engine(total_requests, batch_size):
    for i in range(1, total_requests + 1, batch_size):
        current_batch = min(batch_size, total_requests - i + 1)
        tasks = [fire_simulated_inference(i + j) for j in range(current_batch)]
        await asyncio.gather(*tasks)
        await asyncio.sleep(0.2)

if __name__ == "__main__":

    total_reqs = int(os.getenv("SIM_TOTAL_REQUESTS", 10))
    batch_sz = int(os.getenv("SIM_BATCH_SIZE", 5))

    user_url = os.getenv("ZEROGATE_BASE_URL", "https://api.zerogate.cloud")
    if "zerogate-gateway" in user_url:
        user_url = "http://localhost:8000"

    print("─" * 93)
    print("TASKS:")
    print("─" * 93)
    asyncio.run(run_stress_test_engine(total_reqs, batch_sz))
    print("─" * 93)
    print("\n")
    print("─" * 93)
    print("ENDPOINTS (Copy & Run to Verify Telemetry):")
    print("─" * 93)
    print(f"curl -X GET {user_url}/v1/status/<task_id>")
    print(f'curl -X GET {user_url}/v1/analytics -H "X-ZeroGate-Key: zerogate-beta-key"')
    print("─" * 93)
    print("\n")