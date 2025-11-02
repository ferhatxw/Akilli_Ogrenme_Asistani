# database.py (RENDER İÇİN GÜNCELLENDİ)

import sqlite3
import os

# Veritabanı yolunu belirle. Render'da persistent disk için RENDER_DISK_PATH
# kullanılır, lokal test için '.' (mevcut dizin) kullanılır.
DB_DIR = os.environ.get("RENDER_DISK_PATH", ".")
DB_NAME = "ders_takip.db"
DB_PATH = os.path.join(DB_DIR, DB_NAME)

def init_db():
    print(f"Veritabanı yolu: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, first_name TEXT, username TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS sinav_turleri (sinav_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, sinav_adi TEXT NOT NULL, tamamlandi INTEGER DEFAULT 0, FOREIGN KEY (user_id) REFERENCES users (user_id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS dersler (ders_id INTEGER PRIMARY KEY AUTOINCREMENT, sinav_id INTEGER NOT NULL, ders_adi TEXT NOT NULL, tamamlandi INTEGER DEFAULT 0, FOREIGN KEY (sinav_id) REFERENCES sinav_turleri (sinav_id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS konular (konu_id INTEGER PRIMARY KEY AUTOINCREMENT, ders_id INTEGER NOT NULL, konu_adi TEXT NOT NULL, tamamlandi INTEGER DEFAULT 0, FOREIGN KEY (ders_id) REFERENCES dersler (ders_id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS soru_takip (takip_id INTEGER PRIMARY KEY AUTOINCREMENT, konu_id INTEGER NOT NULL UNIQUE, hedef_soru INTEGER DEFAULT 0, cozulen_dogru INTEGER DEFAULT 0, cozulen_yanlis INTEGER DEFAULT 0, cozulen_bos INTEGER DEFAULT 0, FOREIGN KEY (konu_id) REFERENCES konular (konu_id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS notlar (not_id INTEGER PRIMARY KEY AUTOINCREMENT, konu_id INTEGER NOT NULL, not_icerik TEXT NOT NULL, FOREIGN KEY (konu_id) REFERENCES konular (konu_id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS haftalik_program (program_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, gun INTEGER NOT NULL, ders_id INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users (user_id), FOREIGN KEY (ders_id) REFERENCES dersler(ders_id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS gunluk_rituel (rituel_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, rituel_icerik TEXT NOT NULL, FOREIGN KEY (user_id) REFERENCES users (user_id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS gunluk_notlar (gunluk_not_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, gun INTEGER NOT NULL, not_icerik TEXT NOT NULL, FOREIGN KEY (user_id) REFERENCES users (user_id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY NOT NULL UNIQUE, FOREIGN KEY (user_id) REFERENCES users (user_id))')
    conn.commit(); conn.close()

# --- ADMIN FONKSİYONLARI ---
def add_admin(user_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, first_name, username) VALUES (?, ?, ?)", (user_id, f"Kullanıcı {user_id}", None))
    cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
    conn.commit(); rowcount = cursor.rowcount; conn.close()
    return rowcount > 0
def remove_admin(user_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("DELETE FROM admins WHERE user_id = ?", (user_id,)); conn.commit(); rowcount = cursor.rowcount; conn.close()
    return rowcount > 0
def list_admins(super_admin_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT u.user_id, u.first_name FROM admins a JOIN users u ON a.user_id = u.user_id WHERE a.user_id != ?", (super_admin_id,)); admins = cursor.fetchall(); conn.close()
    return admins
def is_admin(user_id: int, super_admin_id: int) -> bool:
    if user_id == super_admin_id: return True
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,)); result = cursor.fetchone(); conn.close()
    return result is not None
def get_user_info_by_id(user_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT first_name FROM users WHERE user_id = ?", (user_id,)); result = cursor.fetchone(); conn.close()
    return result[0] if result else None
def get_user_by_username(username: str):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    if username.startswith('@'): username = username[1:]
    cursor.execute("SELECT user_id, first_name FROM users WHERE username = ?", (username,)); result = cursor.fetchone(); conn.close()
    return result
def get_all_users():
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT user_id, first_name, username FROM users"); users = cursor.fetchall(); conn.close()
    return users

# --- PROGRAM VE RİTÜEL FONKSİYONLARI ---
def get_program_for_gun(user_id: int, gun: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    query = "SELECT p.program_id, d.ders_adi, s.sinav_adi FROM haftalik_program p JOIN dersler d ON p.ders_id = d.ders_id JOIN sinav_turleri s ON d.sinav_id = s.sinav_id WHERE p.user_id = ? AND p.gun = ?"
    cursor.execute(query, (user_id, gun)); result = cursor.fetchall(); conn.close(); return result
def add_ders_to_program(user_id: int, gun: int, ders_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("INSERT INTO haftalik_program (user_id, gun, ders_id) VALUES (?, ?, ?)", (user_id, gun, ders_id)); conn.commit(); conn.close()
def remove_ders_from_program(program_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("DELETE FROM haftalik_program WHERE program_id = ?", (program_id,)); conn.commit(); conn.close()
def get_all_user_dersler(user_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    query = "SELECT d.ders_id, d.ders_adi, s.sinav_adi FROM dersler d JOIN sinav_turleri s ON d.sinav_id = s.sinav_id WHERE s.user_id = ?"
    cursor.execute(query, (user_id,)); result = cursor.fetchall(); conn.close(); return result
def get_rituels(user_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT rituel_id, rituel_icerik FROM gunluk_rituel WHERE user_id = ?", (user_id,)); result = cursor.fetchall(); conn.close(); return result
def add_rituel(user_id: int, icerik: str):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("INSERT INTO gunluk_rituel (user_id, rituel_icerik) VALUES (?, ?)", (user_id, icerik)); conn.commit(); conn.close()
def delete_rituel(rituel_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("DELETE FROM gunluk_rituel WHERE rituel_id = ?", (rituel_id,)); conn.commit(); conn.close()

# YENİ EKLENEN FONKSİYONLAR
def get_gunluk_notlar(user_id: int, gun: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT gunluk_not_id, not_icerik FROM gunluk_notlar WHERE user_id = ? AND gun = ?", (user_id, gun)); result = cursor.fetchall(); conn.close(); return result

def add_gunluk_not(user_id: int, gun: int, icerik: str):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("INSERT INTO gunluk_notlar (user_id, gun, not_icerik) VALUES (?, ?, ?)", (user_id, gun, icerik)); conn.commit(); conn.close()

def delete_gunluk_not(gunluk_not_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("DELETE FROM gunluk_notlar WHERE gunluk_not_id = ?", (gunluk_not_id,)); conn.commit(); conn.close()

# --- TEMEL VERİ FONKSİYONLARI ---
def add_user_if_not_exists(user_id: int, first_name: str, username: str):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (user_id, first_name, username) VALUES (?, ?, ?)", (user_id, first_name, username))
    else:
        cursor.execute("UPDATE users SET first_name = ?, username = ? WHERE user_id = ?", (first_name, username, user_id))
    conn.commit(); conn.close()
def get_sinavlar(user_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT sinav_id, sinav_adi, tamamlandi FROM sinav_turleri WHERE user_id = ?", (user_id,)); sinavlar = cursor.fetchall(); conn.close()
    return sinavlar
def get_dersler(sinav_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT ders_id, ders_adi, tamamlandi FROM dersler WHERE sinav_id = ?", (sinav_id,)); dersler = cursor.fetchall(); conn.close()
    return dersler
def get_konular(ders_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT konu_id, konu_adi, tamamlandi FROM konular WHERE ders_id = ?", (ders_id,)); konular = cursor.fetchall(); conn.close()
    return konular
def get_soru_istatistik(konu_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT hedef_soru, cozulen_dogru, cozulen_yanlis, cozulen_bos FROM soru_takip WHERE konu_id = ?", (konu_id,)); stats = cursor.fetchone()
    if stats is None: return (0, 0, 0, 0)
    conn.close(); return stats
def get_sinav_adi(sinav_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT sinav_adi FROM sinav_turleri WHERE sinav_id = ?", (sinav_id,)); result = cursor.fetchone(); conn.close()
    return result[0] if result else "Bilinmeyen Sınav"
def get_ders_adi(ders_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT ders_adi FROM dersler WHERE ders_id = ?", (ders_id,)); result = cursor.fetchone(); conn.close()
    return result[0] if result else "Bilinmeyen Ders"
def get_konu_adi(konu_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT konu_adi FROM konular WHERE konu_id = ?", (konu_id,)); result = cursor.fetchone(); conn.close()
    return result[0] if result else "Bilinmeyen Konu"
def get_konu_id_by_name(ders_adi: str, konu_adi: str, user_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    query = "SELECT k.konu_id FROM konular k JOIN dersler d ON k.ders_id = d.ders_id JOIN sinav_turleri s ON d.sinav_id = s.sinav_id WHERE d.ders_adi = ? AND k.konu_adi = ? AND s.user_id = ?"
    cursor.execute(query, (ders_adi, konu_adi, user_id)); result = cursor.fetchone(); conn.close()
    return result[0] if result else None
def get_parent_ids(konu_id: int = None, ders_id: int = None):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    if konu_id: cursor.execute("SELECT d.ders_id, d.sinav_id FROM konular k JOIN dersler d ON k.ders_id = d.ders_id WHERE k.konu_id = ?", (konu_id,))
    elif ders_id: cursor.execute("SELECT sinav_id FROM dersler WHERE ders_id = ?", (ders_id,))
    result = cursor.fetchone(); conn.close()
    return result
def get_notes(konu_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT not_id, not_icerik FROM notlar WHERE konu_id = ?", (konu_id,)); notlar = cursor.fetchall(); conn.close()
    return notlar
def get_konu_id_from_not_id(not_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT konu_id FROM notlar WHERE not_id = ?", (not_id,)); result = cursor.fetchone(); conn.close()
    return result[0] if result else None

def add_sinav(user_id: int, sinav_adi: str):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("INSERT INTO sinav_turleri (user_id, sinav_adi) VALUES (?, ?)", (user_id, sinav_adi)); conn.commit(); conn.close()
def add_ders(sinav_id: int, ders_adi: str):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("INSERT INTO dersler (sinav_id, ders_adi) VALUES (?, ?)", (sinav_id, ders_adi)); conn.commit(); conn.close()
def add_konu(ders_id: int, konu_adi: str):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("INSERT INTO konular (ders_id, konu_adi) VALUES (?, ?)", (ders_id, konu_adi)); conn.commit(); conn.close()
def add_soru_stats(konu_id: int, dogru: int, yanlis: int, bos: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    query = "INSERT INTO soru_takip (konu_id, cozulen_dogru, cozulen_yanlis, cozulen_bos) VALUES (?, ?, ?, ?) ON CONFLICT(konu_id) DO UPDATE SET cozulen_dogru = cozulen_dogru + excluded.cozulen_dogru, cozulen_yanlis = cozulen_yanlis + excluded.cozulen_yanlis, cozulen_bos = cozulen_bos + excluded.cozulen_bos;"
    cursor.execute(query, (konu_id, dogru, yanlis, bos)); conn.commit(); conn.close()
def set_hedef_soru(konu_id: int, hedef: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    query = "INSERT INTO soru_takip (konu_id, hedef_soru) VALUES (?, ?) ON CONFLICT(konu_id) DO UPDATE SET hedef_soru = excluded.hedef_soru;"
    cursor.execute(query, (konu_id, hedef)); conn.commit(); conn.close()
def add_note(konu_id: int, icerik: str):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("INSERT INTO notlar (konu_id, not_icerik) VALUES (?, ?)", (konu_id, icerik)); conn.commit(); conn.close()

def update_sinav_adi(sinav_id: int, yeni_ad: str):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("UPDATE sinav_turleri SET sinav_adi = ? WHERE sinav_id = ?", (yeni_ad, sinav_id)); conn.commit(); conn.close()
def update_ders_adi(ders_id: int, yeni_ad: str):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("UPDATE dersler SET ders_adi = ? WHERE ders_id = ?", (yeni_ad, ders_id)); conn.commit(); conn.close()
def update_konu_adi(konu_id: int, yeni_ad: str):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("UPDATE konular SET konu_adi = ? WHERE konu_id = ?", (yeni_ad, konu_id)); conn.commit(); conn.close()
def update_soru_stats(konu_id: int, dogru: int, yanlis: int, bos: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    query = "INSERT INTO soru_takip (konu_id, cozulen_dogru, cozulen_yanlis, cozulen_bos) VALUES (?, ?, ?, ?) ON CONFLICT(konu_id) DO UPDATE SET cozulen_dogru = ?, cozulen_yanlis = ?, cozulen_bos = ?;"
    cursor.execute(query, (konu_id, dogru, yanlis, bos, dogru, yanlis, bos)); conn.commit(); conn.close()
def update_status(item_type: str, item_id: int, status: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    table_map = {"sinav": "sinav_turleri", "ders": "dersler", "konu": "konular"}; id_map = {"sinav": "sinav_id", "ders": "ders_id", "konu": "konu_id"}
    if item_type in table_map: cursor.execute(f"UPDATE {table_map[item_type]} SET tamamlandi = ? WHERE {id_map[item_type]} = ?", (status, item_id))
    conn.commit(); conn.close()

def delete_konu(konu_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("DELETE FROM soru_takip WHERE konu_id = ?", (konu_id,)); cursor.execute("DELETE FROM notlar WHERE konu_id = ?", (konu_id,)); cursor.execute("DELETE FROM konular WHERE konu_id = ?", (konu_id,)); conn.commit(); conn.close()
def delete_ders(ders_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT konu_id FROM konular WHERE ders_id = ?", (ders_id,)); konular_to_delete = cursor.fetchall()
    for konu_id_tuple in konular_to_delete: delete_konu(konu_id_tuple[0])
    cursor.execute("DELETE FROM dersler WHERE ders_id = ?", (ders_id,)); conn.commit(); conn.close()
def delete_sinav(sinav_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT ders_id FROM dersler WHERE sinav_id = ?", (sinav_id,)); dersler_to_delete = cursor.fetchall()
    for ders_id_tuple in dersler_to_delete: delete_ders(ders_id_tuple[0])
    cursor.execute("DELETE FROM sinav_turleri WHERE sinav_id = ?", (sinav_id,)); conn.commit(); conn.close()
def delete_note(not_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("DELETE FROM notlar WHERE not_id = ?", (not_id,)); conn.commit(); conn.close()
