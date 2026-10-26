import argparse
import statistics
import time

import httpx


def main():
    parser = argparse.ArgumentParser(description="Evaluate the Qwen Agent API.")
    parser.add_argument("--url", default="http://127.0.0.1:8001/api/chat")
    parser.add_argument("--requests", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=180)
    args = parser.parse_args()

    if args.requests < 1:
        parser.error("--requests must be at least 1")

    results = []

    with httpx.Client(timeout=args.timeout) as client:
        for number in range(1, args.requests + 1):
            payload = {
                "message": "Reply with exactly: EVAL_OK",
                "session_id": f"repeatable-evaluation-{number}",
            }

            started = time.perf_counter()
            success = False
            error = None

            try:
                response = client.post(args.url, json=payload)
                response.raise_for_status()
                data = response.json()
                success = bool(data.get("answer"))
                if not success:
                    error = "Response did not contain a non-empty answer"
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"

            elapsed = time.perf_counter() - started
            results.append((elapsed, success))

            status = "PASS" if success else "FAIL"
            print(f"Request {number:02d}: {status} | {elapsed:.3f}s")
            if error:
                print(f"  Error: {error}")

    latencies = [elapsed for elapsed, _ in results]
    successes = sum(success for _, success in results)

    print("\n=== Evaluation Summary ===")
    print(f"Endpoint: {args.url}")
    print(f"Requests: {args.requests}")
    print(f"Successful: {successes}")
    print(f"Failed: {args.requests - successes}")
    print(f"Success rate: {100 * successes / args.requests:.1f}%")
    print(f"Mean latency: {statistics.mean(latencies):.3f}s")
    print(f"Minimum latency: {min(latencies):.3f}s")
    print(f"Maximum latency: {max(latencies):.3f}s")


if __name__ == "__main__":
    main()
