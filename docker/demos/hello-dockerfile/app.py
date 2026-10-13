"""最小 HTTP 服务：用 Redis 计数，练习 Compose 服务名互通。"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import os

import redis


def redis_client() -> redis.Redis:
    return redis.Redis(
        host=os.environ.get("REDIS_HOST", "127.0.0.1"),
        port=int(os.environ.get("REDIS_PORT", "6379")),
        decode_responses=True,
        socket_connect_timeout=2,
    )


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        host = os.uname().nodename
        try:
            count = redis_client().incr("hello:hits")
            body = (
                f"hello from docker | hostname={host} | hits={count} | redis=ok\n"
            ).encode()
            status = 200
        except redis.RedisError as exc:
            body = (
                f"hello from docker | hostname={host} | redis=error | {exc}\n"
            ).encode()
            status = 503

        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} - {fmt % args}")


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(
        f"listening on 0.0.0.0:{port} redis={os.environ.get('REDIS_HOST', '127.0.0.1')}",
        flush=True,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
