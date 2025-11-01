import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path
import glob
import pandas as pd
from .utils.charts import charts
class Renderer:
    def __init__(self, render_logs_dir: str):
        self.render_logs_dir = Path(render_logs_dir)
        self.df: pd.DataFrame = None
        self.metrics = [{'name': 'Market Return', 'function': lambda df:
            f"{(df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100:0.2f}%"
            }, {'name': 'Portfolio Return', 'function': lambda df:
            f"{(df['portfolio_valuation'].iloc[-1] / df['portfolio_valuation'].iloc[0] - 1) * 100:0.2f}%"
            }]
        self.lines = []
    def add_metric(self, name: str, function: callable) ->None:
        self.metrics.append({'name': name, 'function': function})
    def add_line(self, name: str, function: callable, line_options: dict=None
        ) ->None:
        line = {'name': name, 'function': function}
        if line_options is not None:
            line['line_options'] = line_options
        self.lines.append(line)
    def compute_metrics(self, df: pd.DataFrame) ->list:
        return [{'name': metric['name'], 'value': metric['function'](df)} for
            metric in self.metrics]
    def _serve_file(self, path: Path, content_type: str, handler:
        BaseHTTPRequestHandler) ->bool:
        if path.exists():
            handler.send_response(200)
            handler.send_header('Content-type', content_type)
            handler.end_headers()
            with open(path, 'rb') as f:
                handler.wfile.write(f.read())
            return True
        return False
    def _serve_html(self, handler: BaseHTTPRequestHandler) ->None:
        handler.send_response(200)
        handler.send_header('Content-type', 'text/html')
        handler.end_headers()
        render_paths = glob.glob(f'{self.render_logs_dir}/*.pkl')
        render_names = sorted([Path(p).name for p in render_paths], reverse
            =True)
        with open('templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read().replace('{{ render_names }}', json.dumps(
                render_names))
        handler.wfile.write(html.encode('utf-8'))
    def _handle_request(self, handler: BaseHTTPRequestHandler) ->None:
        parsed = urlparse(handler.path)
        if parsed.path == '/':
            self._serve_html(handler)
        elif parsed.path == '/update_data':
            name = parsed.query.strip()
            if not name:
                render_paths = glob.glob(f'{self.render_logs_dir}/*.pkl')
                if not render_paths:
                    handler.send_error(404, 'No render logs found')
                    return
                name = Path(render_paths[-1]).name
            else:
                name = name.split('=')[-1]
            file_path = self.render_logs_dir / name
            if not file_path.exists():
                handler.send_error(404, f'File not found: {name}')
                return
            try:
                self.df = pd.read_pickle(file_path)
                chart = charts(self.df, self.lines)
                data = chart.dump_options_with_quotes()
                handler.send_response(200)
                handler.send_header('Content-type', 'application/json')
                handler.end_headers()
                handler.wfile.write(data.encode('utf-8'))
            except Exception as e:
                handler.send_error(500, f'Error processing file: {str(e)}')
        elif parsed.path == '/metrics':
            if self.df is None:
                handler.send_error(400,
                    'No data loaded. Call /update_data first.')
                return
            try:
                metrics = self.compute_metrics(self.df)
                handler.send_response(200)
                handler.send_header('Content-type', 'application/json')
                handler.end_headers()
                handler.wfile.write(json.dumps(metrics).encode('utf-8'))
            except Exception as e:
                handler.send_error(500, f'Error computing metrics: {str(e)}')
        elif parsed.path.startswith('/static/'):
            static_path = Path('templates') / parsed.path[len('/static/'):]
            if not self._serve_file(static_path, 'text/css' if static_path.
                suffix == '.css' else 'application/javascript', handler):
                handler.send_error(404, 'Static file not found')
        else:
            handler.send_error(404, 'Not Found')
    def run(self, host: str='127.0.0.1', port: int=5000) ->None:
        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.server.renderer._handle_request(self)
            def log_message(self, format, *args):
                pass
        server = HTTPServer((host, port), RequestHandler)
        server.renderer = self
        print(f'Renderer running at http://{host}:{port}')
        print(f'Serving render logs from: {self.render_logs_dir}')
        print('Press Ctrl+C to stop.')
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('\nShutting down server...')
            server.shutdown()