import glob
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import List
from urllib.parse import urlparse

import pandas as pd

from .utils.charts import charts


class Renderer:

    def __init__(self, render_logs_dir: str):
        self.render_logs_dir = Path(render_logs_dir)
        self.df: pd.DataFrame = None
        self.metrics = [
            {
                "name": "Market Return",
                "function": lambda df: f"{(df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100:0.2f}%",
            },
            {
                "name": "Portfolio Return",
                "function": lambda df: f"{(df['portfolio_valuation'].iloc[-1] / df['portfolio_valuation'].iloc[0] - 1) * 100:0.2f}%",
            },
        ]
        self.lines = []

    def add_metric(self, name: str, function: callable) -> None:
        self.metrics.append({"name": name, "function": function})

    def add_line(self, name: str, function: callable, line_options: dict = None) -> None:
        line = {"name": name, "function": function}
        if line_options is not None:
            line["line_options"] = line_options
        self.lines.append(line)

    def compute_metrics(self, df: pd.DataFrame) -> List[dict]:
        return [
            {"name": metric["name"], "value": metric["function"](df)}
            for metric in self.metrics
        ]

    def _serve_file(self, path: Path, content_type: str, handler: BaseHTTPRequestHandler):
        if not path.exists():
            return
        handler.send_response(200)
        handler.send_header("Content-type", content_type)
        handler.end_headers()
        with open(path, "rb") as f:
            handler.wfile.write(f.read())

    def _serve_html(self, handler: BaseHTTPRequestHandler):
        handler.send_response(200)
        handler.send_header("Content-type", "text/html")
        handler.end_headers()
        render_paths = glob.glob(f"{self.render_logs_dir}/*.pkl")
        render_names = sorted([Path(p).name for p in render_paths], reverse=True)
        with open("templates/index.html", "r", encoding="utf-8") as f:
            html = f.read().replace("{{ render_names }}", json.dumps(render_names))
        handler.wfile.write(html.encode("utf-8"))

    def _handle_request(self, handler: BaseHTTPRequestHandler):
        parsed = urlparse(handler.path)
        if parsed.path == "/":
            self._serve_html(handler)
        elif parsed.path == "/update_data":
            self._handle_update_data(handler, parsed.query)
        elif parsed.path == "/metrics":
            self._handle_metrics(handler)
        elif parsed.path.startswith("/static/"):
            self._handle_static(handler, parsed.path)
        else:
            handler.send_error(404, "Not Found")

    def _handle_update_data(self, handler: BaseHTTPRequestHandler, query: str):
        name = self._get_name_from_query(query)
        if not name:
            handler.send_error(404, "No render logs found")
            return

        file_path = self.render_logs_dir / name
        if not file_path.exists():
            handler.send_error(404, f"File not found: {name}")
            return

        try:
            self.df = pd.read_pickle(file_path)
            chart = charts(self.df, self.lines)
            data = chart.dump_options_with_quotes()
            handler.send_response(200)
            handler.send_header("Content-type", "application/json")
            handler.end_headers()
            handler.wfile.write(data.encode("utf-8"))
        except Exception as e:
            handler.send_error(500, f"Error processing file: {e}")

    def _get_name_from_query(self, query: str) -> str:
        if not query:
            render_paths = glob.glob(f"{self.render_logs_dir}/*.pkl")
            return Path(render_paths[-1]).name if render_paths else None
        return query.split("=")[-1]

    def _handle_metrics(self, handler: BaseHTTPRequestHandler):
        if self.df is None:
            handler.send_error(400, "No data loaded. Call /update_data first.")
            return

        try:
            metrics = self.compute_metrics(self.df)
            handler.send_response(200)
            handler.send_header("Content-type", "application/json")
            handler.end_headers()
            handler.wfile.write(json.dumps(metrics).encode("utf-8"))
        except Exception as e:
            handler.send_error(500, f"Error computing metrics: {e}")

    def _handle_static(self, handler: BaseHTTPRequestHandler, path: str):
        static_path = Path("templates") / path[len("/static/"):]
        content_type = (
            "text/css" if static_path.suffix == ".css" else "application/javascript"
        )
        self._serve_file(static_path, content_type, handler)

    def run(self, host: str = "127.0.0.1", port: int = 5000):
        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.server.renderer._handle_request(self)

            def log_message(self, format, *args):
                pass

        server = HTTPServer((host, port), RequestHandler)
        server.renderer = self
        print(f"Renderer running at http://{host}:{port}")
        print(f"Serving render logs from: {self.render_logs_dir}")
        print("Press Ctrl+C to stop.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            server.shutdown()


if __name__ == "__main__":
    renderer = Renderer(render_logs_dir="render_logs")
    renderer.run()
