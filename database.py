"""
Database layer for Bitqik QR Tracked WebApp.
Uses SQLite for zero-dependency, reliable, persistent local storage.
"""

import sqlite3
import datetime
import random
import string
import os
import re

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bitqik_qr.db")

def get_connection(db_path=DB_FILE):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def generate_short_code(length=6):
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=length))

def parse_user_agent(ua_string):
    """
    Parse User-Agent string to extract device, OS, and browser.
    """
    if not ua_string:
        return ("Unknown", "Unknown", "Unknown")
    
    ua = ua_string.lower()
    
    # Device & OS
    device = "Desktop"
    os_name = "Other"
    
    if "iphone" in ua:
        device = "Mobile"
        os_name = "iOS"
    elif "ipad" in ua:
        device = "Tablet"
        os_name = "iPadOS"
    elif "android" in ua:
        if "tablet" in ua or "nexus 7" in ua or "nexus 9" in ua or "nexus 10" in ua:
            device = "Tablet"
        else:
            device = "Mobile"
        os_name = "Android"
    elif "macintosh" in ua or "mac os x" in ua:
        device = "Desktop"
        os_name = "macOS"
    elif "windows" in ua:
        device = "Desktop"
        os_name = "Windows"
    elif "linux" in ua:
        device = "Desktop"
        os_name = "Linux"
        
    # Browser
    browser = "Other"
    if "micromessenger" in ua:
        browser = "WeChat"
    elif "line/" in ua:
        browser = "Line"
    elif "fban" in ua or "fbav" in ua:
        browser = "Facebook"
    elif "instagram" in ua:
        browser = "Instagram"
    elif "tiktok" in ua:
        browser = "TikTok"
    elif "edg/" in ua or "edge/" in ua:
        browser = "Edge"
    elif "chrome" in ua or "crios" in ua:
        browser = "Chrome"
    elif "safari" in ua and "chrome" not in ua and "crios" not in ua:
        browser = "Safari"
    elif "firefox" in ua or "fxios" in ua:
        browser = "Firefox"
    elif "opera" in ua or "opr/" in ua:
        browser = "Opera"
        
    return (device, os_name, browser)

def init_db(db_path=DB_FILE):
    conn = get_connection(db_path)
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS qr_codes (
        id TEXT PRIMARY KEY,
        short_code TEXT UNIQUE NOT NULL,
        label TEXT NOT NULL,
        destination_url TEXT NOT NULL,
        qr_type TEXT NOT NULL DEFAULT 'dynamic',
        has_logo INTEGER NOT NULL DEFAULT 1,
        logo_data TEXT,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS scan_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        qr_id TEXT NOT NULL,
        scanned_at TEXT NOT NULL,
        ip_address TEXT,
        user_agent TEXT,
        device TEXT,
        os TEXT,
        browser TEXT,
        referrer TEXT,
        FOREIGN KEY (qr_id) REFERENCES qr_codes (id) ON DELETE CASCADE
    )
    """)
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_qr_short_code ON qr_codes(short_code)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_scan_qr_id ON scan_logs(qr_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_scan_scanned_at ON scan_logs(scanned_at)")
    
    conn.commit()
    conn.close()

def cleanup_sample_data(db_path=DB_FILE):
    """Purge test sample data so production/fresh database is clean."""
    try:
        conn = get_connection(db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM scan_logs WHERE qr_id IN ('bq-app-dl', 'bq-trade', 'bq-academy', 'bq-dca', 'bq-1', 'bq-2', 'bq-3')")
        cur.execute("DELETE FROM qr_codes WHERE id IN ('bq-app-dl', 'bq-trade', 'bq-academy', 'bq-dca', 'bq-1', 'bq-2', 'bq-3')")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Sample cleanup notice: {e}")

def clear_all_data(db_path=DB_FILE):
    """Reset all QR codes and scan logs completely."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM scan_logs")
    cur.execute("DELETE FROM qr_codes")
    conn.commit()
    conn.close()

def seed_sample_data(db_path=DB_FILE):
    # Only seed if explicitly enabled via environment variable SEED_SAMPLE_DATA=1
    if os.environ.get("SEED_SAMPLE_DATA", "").lower() not in ("1", "true"):
        return
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM qr_codes")
    row = cur.fetchone()
    
    if row and row['count'] == 0:
        now = datetime.datetime.now(datetime.timezone.utc)
        
        sample_qrs = [
            ("bq-app-dl", "bqapp", "Bitqik App Download (iOS/Android)", "https://bitqik.com/download", "dynamic", 1),
            ("bq-trade", "bqtrade", "Bitqik Trading Platform Launch", "https://trade.bitqik.com", "dynamic", 1),
            ("bq-academy", "bqedu", "Bitqik Academy Crypto Workshop", "https://bitqik.com/academy", "dynamic", 1),
            ("bq-dca", "bqdca", "Bitqik DCA Campaign 2026", "https://bitqik.com/campaign/dca", "dynamic", 1),
        ]
        
        for qid, code, label, dest, qtype, has_logo in sample_qrs:
            created = (now - datetime.timedelta(days=random.randint(1, 10))).isoformat()
            cur.execute("""
            INSERT INTO qr_codes (id, short_code, label, destination_url, qr_type, has_logo, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (qid, code, label, dest, qtype, has_logo, created, created))
            
            # Add sample realistic scan logs
            num_scans = random.randint(8, 35)
            devices = [
                ("Mobile", "iOS", "Safari", "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1"),
                ("Mobile", "Android", "Chrome", "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36"),
                ("Mobile", "iOS", "Facebook", "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) Mobile/15E148 [FBAN/FBIOS;FBAV/456.0.0]"),
                ("Desktop", "macOS", "Safari", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15"),
                ("Desktop", "Windows", "Chrome", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"),
                ("Tablet", "iPadOS", "Safari", "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1"),
            ]
            
            for _ in range(num_scans):
                scan_time = (now - datetime.timedelta(
                    days=random.randint(0, 6),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )).isoformat()
                
                dev, os_n, br, ua = random.choice(devices)
                ip = f"115.84.{random.randint(10, 250)}.{random.randint(2, 250)}"
                ref = random.choice(["Direct Camera Scan", "https://facebook.com", "https://bitqik.com", "Flyer Print QR"])
                
                cur.execute("""
                INSERT INTO scan_logs (qr_id, scanned_at, ip_address, user_agent, device, os, browser, referrer)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (qid, scan_time, ip, ua, dev, os_n, br, ref))
                
        conn.commit()
    conn.close()

def list_qrs(search=None, db_path=DB_FILE):
    conn = get_connection(db_path)
    cur = conn.cursor()
    
    query = """
    SELECT q.*, 
           COUNT(s.id) AS scan_count,
           MAX(s.scanned_at) AS last_scanned_at
    FROM qr_codes q
    LEFT JOIN scan_logs s ON q.id = s.qr_id
    """
    params = []
    
    if search:
        query += " WHERE (q.label LIKE ? OR q.destination_url LIKE ? OR q.short_code LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s])
        
    query += " GROUP BY q.id ORDER BY q.created_at DESC"
    
    cur.execute(query, params)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows

def get_qr_by_id(qr_id, db_path=DB_FILE):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
    SELECT q.*, 
           COUNT(s.id) AS scan_count,
           MAX(s.scanned_at) AS last_scanned_at
    FROM qr_codes q
    LEFT JOIN scan_logs s ON q.id = s.qr_id
    WHERE q.id = ?
    GROUP BY q.id
    """, (qr_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def get_qr_by_code(short_code, db_path=DB_FILE):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM qr_codes WHERE short_code = ?", (short_code,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def create_qr(label, destination_url, qr_type="dynamic", short_code=None, has_logo=True, logo_data=None, db_path=DB_FILE):
    conn = get_connection(db_path)
    cur = conn.cursor()
    
    qr_id = f"bq-{int(datetime.datetime.now().timestamp() * 1000)}"
    if not short_code or len(short_code.strip()) == 0:
        short_code = generate_short_code(6)
    else:
        short_code = re.sub(r'[^a-zA-Z0-9_-]', '', short_code.strip().lower())
        if not short_code:
            short_code = generate_short_code(6)
            
    # Ensure uniqueness of short_code
    cur.execute("SELECT id FROM qr_codes WHERE short_code = ?", (short_code,))
    if cur.fetchone():
        short_code = f"{short_code}-{generate_short_code(3)}"
        
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    cur.execute("""
    INSERT INTO qr_codes (id, short_code, label, destination_url, qr_type, has_logo, logo_data, is_active, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
    """, (qr_id, short_code, label, destination_url, qr_type, 1 if has_logo else 0, logo_data, now, now))
    
    conn.commit()
    conn.close()
    return get_qr_by_id(qr_id, db_path=db_path)

def update_qr(qr_id, label=None, destination_url=None, is_active=None, db_path=DB_FILE):
    conn = get_connection(db_path)
    cur = conn.cursor()
    
    fields = []
    params = []
    
    if label is not None:
        fields.append("label = ?")
        params.append(label)
    if destination_url is not None:
        fields.append("destination_url = ?")
        params.append(destination_url)
    if is_active is not None:
        fields.append("is_active = ?")
        params.append(1 if is_active else 0)
        
    if not fields:
        conn.close()
        return get_qr_by_id(qr_id, db_path=db_path)
        
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    fields.append("updated_at = ?")
    params.append(now)
    params.append(qr_id)
    
    query = f"UPDATE qr_codes SET {', '.join(fields)} WHERE id = ?"
    cur.execute(query, params)
    conn.commit()
    conn.close()
    return get_qr_by_id(qr_id, db_path=db_path)

def delete_qr(qr_id, db_path=DB_FILE):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM scan_logs WHERE qr_id = ?", (qr_id,))
    cur.execute("DELETE FROM qr_codes WHERE id = ?", (qr_id,))
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def record_scan(qr_id, ip_address, user_agent, referrer=None, db_path=DB_FILE):
    conn = get_connection(db_path)
    cur = conn.cursor()
    
    device, os_name, browser = parse_user_agent(user_agent)
    scanned_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    cur.execute("""
    INSERT INTO scan_logs (qr_id, scanned_at, ip_address, user_agent, device, os, browser, referrer)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (qr_id, scanned_at, ip_address, user_agent, device, os_name, browser, referrer or ""))
    
    log_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {
        "id": log_id,
        "qr_id": qr_id,
        "scanned_at": scanned_at,
        "device": device,
        "os": os_name,
        "browser": browser,
        "ip_address": ip_address
    }

def get_analytics(days=30, qr_id=None, db_path=DB_FILE):
    conn = get_connection(db_path)
    cur = conn.cursor()
    
    # Overview counts
    cur.execute("SELECT COUNT(*) AS total_codes FROM qr_codes")
    total_codes = cur.fetchone()['total_codes']
    
    cur.execute("SELECT COUNT(*) AS active_codes FROM qr_codes WHERE is_active = 1")
    active_codes = cur.fetchone()['active_codes']
    
    scan_filter = ""
    scan_params = []
    if qr_id:
        scan_filter = " WHERE qr_id = ?"
        scan_params.append(qr_id)
        
    cur.execute(f"SELECT COUNT(*) AS total_scans FROM scan_logs{scan_filter}", scan_params)
    total_scans = cur.fetchone()['total_scans']
    
    # Scans today
    today_start = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    if qr_id:
        cur.execute("SELECT COUNT(*) AS today_scans FROM scan_logs WHERE qr_id = ? AND scanned_at >= ?", (qr_id, today_start))
    else:
        cur.execute("SELECT COUNT(*) AS today_scans FROM scan_logs WHERE scanned_at >= ?", (today_start,))
    today_scans = cur.fetchone()['today_scans']
    
    # Scans by date (last 7 days)
    date_query = """
    SELECT SUBSTR(scanned_at, 1, 10) AS scan_date, COUNT(*) AS count
    FROM scan_logs
    """
    if qr_id:
        date_query += " WHERE qr_id = ?"
    date_query += " GROUP BY scan_date ORDER BY scan_date DESC LIMIT 14"
    cur.execute(date_query, [qr_id] if qr_id else [])
    scans_by_date = [dict(row) for row in cur.fetchall()]
    scans_by_date.reverse()
    
    # Device breakdown
    dev_query = "SELECT device, COUNT(*) AS count FROM scan_logs"
    if qr_id:
        dev_query += " WHERE qr_id = ?"
    dev_query += " GROUP BY device ORDER BY count DESC"
    cur.execute(dev_query, [qr_id] if qr_id else [])
    device_breakdown = [dict(row) for row in cur.fetchall()]
    
    # OS breakdown
    os_query = "SELECT os, COUNT(*) AS count FROM scan_logs"
    if qr_id:
        os_query += " WHERE qr_id = ?"
    os_query += " GROUP BY os ORDER BY count DESC LIMIT 5"
    cur.execute(os_query, [qr_id] if qr_id else [])
    os_breakdown = [dict(row) for row in cur.fetchall()]
    
    # Browser breakdown
    br_query = "SELECT browser, COUNT(*) AS count FROM scan_logs"
    if qr_id:
        br_query += " WHERE qr_id = ?"
    br_query += " GROUP BY browser ORDER BY count DESC LIMIT 5"
    cur.execute(br_query, [qr_id] if qr_id else [])
    browser_breakdown = [dict(row) for row in cur.fetchall()]
    
    # Hourly breakdown
    hour_query = """
    SELECT CAST(SUBSTR(scanned_at, 12, 2) AS INTEGER) AS hour, COUNT(*) AS count
    FROM scan_logs
    """
    if qr_id:
        hour_query += " WHERE qr_id = ?"
    hour_query += " GROUP BY hour ORDER BY hour ASC"
    cur.execute(hour_query, [qr_id] if qr_id else [])
    scans_by_hour = [dict(row) for row in cur.fetchall()]

    # Top QRs by scan (if viewing all) or single QR scan details
    top_qrs = []
    qr_info = None
    if qr_id:
        cur.execute("SELECT * FROM qr_codes WHERE id = ?", (qr_id,))
        row = cur.fetchone()
        if row:
            qr_info = dict(row)
    else:
        cur.execute("""
        SELECT q.id, q.label, q.short_code, COUNT(s.id) AS scan_count
        FROM qr_codes q
        LEFT JOIN scan_logs s ON q.id = s.qr_id
        GROUP BY q.id
        ORDER BY scan_count DESC
        LIMIT 8
        """)
        top_qrs = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    
    avg_scans = round(total_scans / total_codes, 1) if (total_codes > 0 and not qr_id) else (total_scans if qr_id else 0)
    
    return {
        "qr_id": qr_id,
        "qr_info": qr_info,
        "total_codes": total_codes,
        "active_codes": active_codes,
        "total_scans": total_scans,
        "today_scans": today_scans,
        "average_scans": avg_scans,
        "scans_by_date": scans_by_date,
        "scans_by_hour": scans_by_hour,
        "device_breakdown": device_breakdown,
        "os_breakdown": os_breakdown,
        "browser_breakdown": browser_breakdown,
        "top_qrs": top_qrs
    }

def get_recent_logs(limit=30, qr_id=None, db_path=DB_FILE):
    conn = get_connection(db_path)
    cur = conn.cursor()
    
    query = """
    SELECT s.*, q.label AS qr_label, q.short_code, q.destination_url
    FROM scan_logs s
    JOIN qr_codes q ON s.qr_id = q.id
    """
    params = []
    if qr_id:
        query += " WHERE s.qr_id = ?"
        params.append(qr_id)
        
    query += " ORDER BY s.scanned_at DESC LIMIT ?"
    params.append(limit)
    
    cur.execute(query, params)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows
