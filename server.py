"""
Production-grade, zero-dependency Python HTTP Server for Bitqik QR Tracker.
Handles:
- Web App UI serving
- RESTful JSON API (/api/qrs, /api/analytics, /api/logs, etc.)
- Real-time QR Code Tracking & Dynamic 302 Redirect (/r/<short_code>)
- CSV Export for analytics reporting
- LAN IP auto-detection for real smartphone camera testing over local Wi-Fi
"""

import http.server
import socketserver
import urllib.parse
import json
import os
import socket
import csv
import io
import sys
import datetime
import database

PORT = int(os.environ.get("PORT", 8000))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_lan_ips():
    """Find all local network IP addresses for phone testing."""
    ips = []
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if not ip.startswith("127.") and ip not in ips:
                ips.append(ip)
    except Exception:
        pass
        
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(('8.8.8.8', 80))
        primary = s.getsockname()[0]
        if primary and primary not in ips and not primary.startswith("127."):
            ips.insert(0, primary)
        s.close()
    except Exception:
        pass
        
    return ips if ips else ["127.0.0.1"]

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

class BitqikQRHandler(http.server.BaseHTTPRequestHandler):
    server_version = "BitqikQR/2.0"
    
    def log_message(self, format, *args):
        # Keep logs clean and informative
        sys.stderr.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {self.command} {self.path} -> {args[0]}\n")
        
    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()
        
    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status=400):
        self.send_json({"error": True, "message": message}, status=status)

    def read_json_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length <= 0:
            return {}
        body = self.rfile.read(content_length)
        return json.loads(body.decode('utf-8'))

    def get_client_ip(self):
        forwarded = self.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return self.client_address[0] if self.client_address else "127.0.0.1"

    # ==========================================
    # GET REQUEST ROUTER
    # ==========================================
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. TRACKING REDIRECT: /r/<short_code>
        if path.startswith("/r/"):
            short_code = path[3:].strip()
            self.handle_tracking_redirect(short_code)
            return

        # 2. REST API ENDPOINTS
        if path == "/api/status":
            self.send_json({
                "status": "online",
                "version": "2.0.0",
                "app": "Bitqik QR Studio Tracker",
                "lan_ips": get_lan_ips(),
                "port": PORT,
                "server_time": datetime.datetime.now(datetime.timezone.utc).isoformat()
            })
            return

        if path == "/api/qrs":
            search = query.get("search", [None])[0]
            qrs = database.list_qrs(search=search)
            self.send_json({"qrs": qrs, "count": len(qrs)})
            return

        if path.startswith("/api/qrs/"):
            qr_id = path[len("/api/qrs/"):].strip()
            qr = database.get_qr_by_id(qr_id)
            if qr:
                self.send_json(qr)
            else:
                self.send_error_json("QR code not found", 404)
            return

        if path == "/api/analytics":
            qr_id = query.get("qr_id", [None])[0]
            days = int(query.get("days", [30])[0])
            data = database.get_analytics(days=days, qr_id=qr_id)
            self.send_json(data)
            return

        if path == "/api/logs":
            limit = int(query.get("limit", [50])[0])
            qr_id = query.get("qr_id", [None])[0]
            logs = database.get_recent_logs(limit=limit, qr_id=qr_id)
            self.send_json({"logs": logs, "count": len(logs)})
            return

        if path == "/api/export":
            qr_id = query.get("qr_id", [None])[0]
            self.handle_csv_export(qr_id=qr_id)
            return

        if path == "/api/export-json":
            qr_id = query.get("qr_id", [None])[0]
            logs = database.get_recent_logs(limit=5000, qr_id=qr_id)
            analytics = database.get_analytics(qr_id=qr_id)
            self.send_json({"qr_id": qr_id, "analytics": analytics, "logs": logs})
            return

        # 3. STATIC FILES
        self.serve_static_file(path)

    # ==========================================
    # POST REQUEST ROUTER
    # ==========================================
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/qrs":
            try:
                data = self.read_json_body()
                label = data.get("label", "").strip()
                url = data.get("destination_url", "").strip()
                qr_type = data.get("qr_type", "dynamic")
                short_code = data.get("short_code", "").strip()
                has_logo = bool(data.get("has_logo", True))
                logo_data = data.get("logo_data", None)

                if not label:
                    return self.send_error_json("Label is required")
                if not url:
                    return self.send_error_json("Destination URL is required")

                created = database.create_qr(
                    label=label,
                    destination_url=url,
                    qr_type=qr_type,
                    short_code=short_code,
                    has_logo=has_logo,
                    logo_data=logo_data
                )
                self.send_json({"success": True, "qr": created}, status=201)
            except Exception as e:
                self.send_error_json(str(e), 500)
            return

        if path.startswith("/api/test-scan/"):
            short_code = path[len("/api/test-scan/"):].strip()
            qr = database.get_qr_by_code(short_code)
            if not qr:
                return self.send_error_json("QR code not found", 404)

            ip = self.get_client_ip()
            ua = self.headers.get("User-Agent", "Web Test Simulator")
            ref = self.headers.get("Referer", "Bitqik In-App Scanner")

            scan_info = database.record_scan(qr['id'], ip, ua, ref)
            self.send_json({
                "success": True,
                "message": "Scan recorded successfully",
                "destination_url": qr['destination_url'],
                "scan": scan_info
            })
            return

        self.send_error_json("Endpoint not found", 404)

    # ==========================================
    # PUT REQUEST ROUTER
    # ==========================================
    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/qrs/"):
            qr_id = path[len("/api/qrs/"):].strip()
            try:
                data = self.read_json_body()
                label = data.get("label")
                destination_url = data.get("destination_url")
                is_active = data.get("is_active")

                updated = database.update_qr(qr_id, label=label, destination_url=destination_url, is_active=is_active)
                if updated:
                    self.send_json({"success": True, "qr": updated})
                else:
                    self.send_error_json("QR code not found", 404)
            except Exception as e:
                self.send_error_json(str(e), 500)
            return

        self.send_error_json("Endpoint not found", 404)

    # ==========================================
    # DELETE REQUEST ROUTER
    # ==========================================
    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/qrs/"):
            qr_id = path[len("/api/qrs/"):].strip()
            deleted = database.delete_qr(qr_id)
            if deleted:
                self.send_json({"success": True, "message": "QR code deleted"})
            else:
                self.send_error_json("QR code not found", 404)
            return

        self.send_error_json("Endpoint not found", 404)

    # ==========================================
    # TRACKING REDIRECT HANDLER
    # ==========================================
    def handle_tracking_redirect(self, short_code):
        qr = database.get_qr_by_code(short_code)
        if not qr:
            # Render a 404 page styled with Bitqik brand
            body = self.render_redirect_error(
                title="QR Code Not Found",
                desc=f"No active campaign matches code: {short_code}"
            )
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body.encode('utf-8'))
            return

        if not qr.get('is_active', 1):
            body = self.render_redirect_error(
                title="Campaign Inactive",
                desc=f"This QR code campaign '{qr.get('label')}' is currently paused."
            )
            self.send_response(403)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body.encode('utf-8'))
            return

        # Record scan log
        ip = self.get_client_ip()
        ua = self.headers.get("User-Agent", "")
        ref = self.headers.get("Referer", "Camera Scan")

        database.record_scan(qr['id'], ip, ua, ref)

        dest = qr['destination_url']
        if not dest.startswith(("http://", "https://")):
            dest = "https://" + dest

        # Instant 302 Redirect with modern fallback HTML
        self.send_response(302)
        self.send_cors_headers()
        self.send_header("Location", dest)
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Content-Type", "text/html; charset=utf-8")
        
        fallback_html = f"""<!DOCTYPE html>
<html lang="lo">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="0;url={dest}">
    <title>Redirecting to Bitqik...</title>
    <style>
        body {{
            background: #f7e4d1;
            color: #392719;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Saysettha OT", sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            text-align: center;
            padding: 20px;
        }}
        .card {{
            background: #fff8ef;
            padding: 30px;
            border-radius: 24px;
            box-shadow: 9px 9px 19px #d9bba1, -9px -9px 19px #fff8ef;
            max-width: 380px;
            width: 100%;
        }}
        .spinner {{
            width: 48px;
            height: 48px;
            border: 4px solid #f8d3b4;
            border-top: 4px solid #f68a32;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 20px;
        }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
        h2 {{ margin: 0 0 10px; color: #392719; font-size: 1.3rem; }}
        p {{ margin: 0 0 20px; color: #765f50; font-size: 0.9rem; line-height: 1.5; }}
        a {{
            display: inline-block;
            background: #f68a32;
            color: #fff;
            padding: 10px 24px;
            border-radius: 14px;
            text-decoration: none;
            font-weight: bold;
            box-shadow: 4px 4px 9px #d9bba1;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="spinner"></div>
        <h2>ກຳລັງເປີດລິ້ງ Bitqik...</h2>
        <p>Redirecting to <strong>{qr.get('label', 'Bitqik')}</strong></p>
        <a href="{dest}">ກົດບ່ອນນີ້ ຖ້າລະບົບບໍ່ປ່ຽນໜ້າອັດຕະໂນມັດ</a>
    </div>
    <script>
        setTimeout(function() {{ window.location.replace("{dest}"); }}, 50);
    </script>
</body>
</html>"""
        encoded = fallback_html.encode('utf-8')
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def render_redirect_error(self, title, desc):
        return f"""<!DOCTYPE html>
<html lang="lo">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title} · Bitqik QR</title>
    <style>
        body {{
            background: #f7e4d1;
            color: #392719;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Saysettha OT", sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            padding: 20px;
        }}
        .card {{
            background: #fff8ef;
            padding: 36px;
            border-radius: 24px;
            box-shadow: 9px 9px 19px #d9bba1, -9px -9px 19px #fff8ef;
            max-width: 420px;
            text-align: center;
        }}
        h2 {{ color: #bf531b; margin-top: 0; }}
        p {{ color: #765f50; line-height: 1.6; }}
        a {{
            display: inline-block;
            margin-top: 15px;
            background: #392719;
            color: #fff;
            padding: 10px 20px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h2>⚠️ {title}</h2>
        <p>{desc}</p>
        <a href="/">ໄປທີ່ໜ້າຫຼັກ Bitqik QR Studio</a>
    </div>
</body>
</html>"""

    # ==========================================
    # CSV EXPORT HANDLER
    # ==========================================
    def handle_csv_export(self, qr_id=None):
        logs = database.get_recent_logs(limit=10000, qr_id=qr_id)
        qr_obj = database.get_qr_by_id(qr_id) if qr_id else None
        tag = qr_obj['short_code'] if qr_obj else 'all_campaigns'
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Scan ID", "Scanned At (UTC)", "QR Shortcode", "Campaign Label", "Destination URL", "Device", "OS", "Browser", "IP Address", "Referrer"])
        
        for l in logs:
            writer.writerow([
                l['id'],
                l['scanned_at'],
                l['short_code'],
                l['qr_label'],
                l['destination_url'],
                l['device'],
                l['os'],
                l['browser'],
                l['ip_address'],
                l['referrer']
            ])
            
        csv_bytes = output.getvalue().encode('utf-8-sig') # with BOM for Excel UTF-8 Lao/English support
        self.send_response(200)
        self.send_cors_headers()
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", f"attachment; filename=bitqik_scans_{tag}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        self.send_header("Content-Length", str(len(csv_bytes)))
        self.end_headers()
        self.wfile.write(csv_bytes)

    # ==========================================
    # STATIC FILE HANDLER
    # ==========================================
    def serve_static_file(self, req_path):
        if req_path in ("/", ""):
            file_name = "index.html"
        else:
            file_name = req_path.lstrip("/")
            
        # URL decode
        file_name = urllib.parse.unquote(file_name)
        target_path = os.path.join(BASE_DIR, file_name)
        
        # Security check: prevent directory traversal
        target_path = os.path.abspath(target_path)
        if not target_path.startswith(BASE_DIR):
            self.send_error_json("Access denied", 403)
            return

        if not os.path.isfile(target_path):
            self.send_error_json(f"File not found: {file_name}", 404)
            return

        content_types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon"
        }
        _, ext = os.path.splitext(target_path)
        mime = content_types.get(ext.lower(), "application/octet-stream")

        try:
            with open(target_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error_json(str(e), 500)

def run_server(port=PORT):
    database.init_db()
    database.seed_sample_data()
    
    server = ThreadedHTTPServer(("0.0.0.0", port), BitqikQRHandler)
    lan_ips = get_lan_ips()
    print("=" * 64)
    print("🚀 BITQIK QR STUDIO TRACKER RUNNING")
    print(f"👉 Local Access:   http://localhost:{port}")
    for ip in lan_ips:
        print(f"📱 Smartphone LAN: http://{ip}:{port}")
    print("=" * 64)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()

if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PORT", PORT))
    run_server(p)
