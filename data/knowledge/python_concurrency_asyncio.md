topic: python

# Python Concurrency: Threading, Multiprocessing, and AsyncIO

Python provides multiple concurrency models tailored for different execution bottlenecks.

## 1. The Global Interpreter Lock (GIL)
CPython enforces a mutex lock preventing multiple native threads from executing Python bytecodes simultaneously. Consequently:
- **I/O-Bound Workloads:** Benefited by multi-threading or cooperative asynchronous I/O (`asyncio`).
- **CPU-Bound Workloads:** Require multi-processing (`multiprocessing` module) to spawn separate OS processes with independent memory heaps and bypass the GIL across CPU cores.

## 2. Asynchronous Event Loops with AsyncIO
`asyncio` uses cooperative multitasking driven by an event loop on a single OS thread. Coroutines yield control to the loop using `await` during non-blocking socket operations.

```python
import asyncio
import httpx

async def fetch_status(client: httpx.AsyncClient, url: str) -> int:
    response = await client.get(url, timeout=5.0)
    return response.status_code

async def main():
    urls = ["https://httpbin.org/status/200", "https://httpbin.org/status/201"]
    async with httpx.AsyncClient() as client:
        # Concurrent asynchronous fan-out
        results = await asyncio.gather(*(fetch_status(client, u) for u in urls))
        print("Completed status codes:", results)

if __name__ == "__main__":
    asyncio.run(main())
```
In NEXUS, FastAPI and LangGraph use `asyncio` to service hundreds of concurrent SSE connections without blocking the main event thread.
