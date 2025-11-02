# database.py (PostgreSQL - NEON İÇİN TAMAMEN YENİDEN YAZILDI)

import psycopg
import os
from psycopg.rows import tuple_row
from contextlib import contextmanager

# Neon'dan aldığımız DATABASE_URL'i Render'daki Environment Variable'dan çek
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("HATA: DATABASE_URL çevre değişkeni bulunamadı.")
    # Lokal test için bir varsayılan belirleyebilirsiniz, ancak Render için bu gereklidir.
    # raise ValueError("DATABASE_URL bulunamadı!")

@contextmanager
def get_db_connection():
    """Veritabanı bağlantısını ve cursor'ı yöneten bir context manager."""
    try:
        # DATABASE_URL'i kullanarak doğrudan bağlan
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor(row_factory=tuple_row) as cursor:
                yield cursor
                conn.commit()
    except (psycopg.OperationalError, psycopg.DatabaseError) as e:
        print(f"Veritabanı bağlantı hatası: {e}")
        # Hata durumunda rollback yap (gerçi context manager bunu kendi halleder)
        # conn.rollback() # Gerekli değil, 'with' bloğu halleder
        raise

def init_db():
    """
    Veritabanı tablolarını PostgreSQL sözdizimi (SERIAL, TEXT, INTEGER) 
    kullanarak oluşturur.
    """
    print(f"Veritabanı {DATABASE_URL} üzerinde başlatılıyor...")
    create_tables_sql = [
        'CREATE TABLE IF NOT EXISTS users (user_id BIGINT PRIMARY KEY, first_name TEXT, username TEXT)',
        
        'CREATE TABLE IF NOT EXISTS sinav_turleri (sinav_id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, sinav_adi TEXT NOT NULL, tamamlandi INTEGER DEFAULT 0, FOREIGN KEY (user_id) REFERENCES users (user_id))',
        
        'CREATE TABLE IF NOT EXISTS dersler (ders_id SERIAL PRIMARY KEY, sinav_id INTEGER NOT NULL, ders_adi TEXT NOT NULL, tamamlandi INTEGER DEFAULT 0, FOREIGN KEY (sinav_id) REFERENCES sinav_turleri (sinav_id) ON DELETE CASCADE)',
        
        'CREATE TABLE IF NOT EXISTS konular (konu_id SERIAL PRIMARY KEY, ders_id INTEGER NOT NULL, konu_adi TEXT NOT NULL, tamamlandi INTEGER DEFAULT 0, FOREIGN KEY (ders_id) REFERENCES dersler (ders_id) ON DELETE CASCADE)',
        
        'CREATE TABLE IF NOT EXISTS soru_takip (takip_id SERIAL PRIMARY KEY, konu_id INTEGER NOT NULL UNIQUE, hedef_soru INTEGER DEFAULT 0, cozulen_dogru INTEGER DEFAULT 0, cozulen_yanlis INTEGER DEFAULT 0, cozulen_bos INTEGER DEFAULT 0, FOREIGN KEY (konu_id) REFERENCES konular (konu_id) ON DELETE CASCADE)',
        
        'CREATE TABLE IF NOT EXISTS notlar (not_id SERIAL PRIMARY KEY, konu_id INTEGER NOT NULL, not_icerik TEXT NOT NULL, FOREIGN KEY (konu_id) REFERENCES konular (konu_id) ON DELETE CASCADE)',
        
        'CREATE TABLE IF NOT EXISTS haftalik_program (program_id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, gun INTEGER NOT NULL, ders_id INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users (user_id), FOREIGN KEY (ders_id) REFERENCES dersler(ders_id) ON DELETE CASCADE)',
        
        'CREATE TABLE IF NOT EXISTS gunluk_rituel (rituel_id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, rituel_icerik TEXT NOT NULL, FOREIGN KEY (user_id) REFERENCES users (user_id))',
        
        'CREATE TABLE IF NOT EXISTS gunluk_notlar (gunluk_not_id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, gun INTEGER NOT NULL, not_icerik TEXT NOT NULL, FOREIGN KEY (user_id) REFERENCES users (user_id))',
        
        'CREATE TABLE IF NOT EXISTS admins (user_id BIGINT PRIMARY KEY NOT NULL UNIQUE, FOREIGN KEY (user_id) REFERENCES users (user_id))'
    ]
    
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                for sql in create_tables_sql:
                    cursor.execute(sql)
            conn.commit()
        print("Tüm tablolar başarıyla oluşturuldu veya zaten mevcut.")
    except (psycopg.OperationalError, psycopg.DatabaseError) as e:
        print(f"Tablo oluşturma hatası: {e}")
        raise

# --- ADMIN FONKSİYONLARI ---
# Not: placeholder '?' yerine '%s' oldu.
def add_admin(user_id: int):
    with get_db_connection() as cursor:
        cursor.execute("INSERT INTO users (user_id, first_name, username) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO NOTHING", (user_id, f"Kullanıcı {user_id}", None))
        cursor.execute("INSERT INTO admins (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING", (user_id,))
        return cursor.rowcount > 0

def remove_admin(user_id: int):
    with get_db_connection() as cursor:
        cursor.execute("DELETE FROM admins WHERE user_id = %s", (user_id,))
        return cursor.rowcount > 0

def list_admins(super_admin_id: int):
    with get_db_connection() as cursor:
        cursor.execute("SELECT u.user_id, u.first_name FROM admins a JOIN users u ON a.user_id = u.user_id WHERE a.user_id != %s", (super_admin_id,))
        return cursor.fetchall()

def is_admin(user_id: int, super_admin_id: int) -> bool:
    if user_id == super_admin_id: return True
    with get_db_connection() as cursor:
        cursor.execute("SELECT user_id FROM admins WHERE user_id = %s", (user_id,))
        return cursor.fetchone() is not None

def get_user_info_by_id(user_id: int):
    with get_db_connection() as cursor:
        cursor.execute("SELECT first_name FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None

def get_user_by_username(username: str):
    if username.startswith('@'): username = username[1:]
    with get_db_connection() as cursor:
        cursor.execute("SELECT user_id, first_name FROM users WHERE username = %s", (username,))
        return cursor.fetchone()

def get_all_users():
    with get_db_connection() as cursor:
        cursor.execute("SELECT user_id, first_name, username FROM users")
        return cursor.fetchall()

# --- PROGRAM VE RİTÜEL FONKSİYONLARI ---
def get_program_for_gun(user_id: int, gun: int):
    query = "SELECT p.program_id, d.ders_adi, s.sinav_adi FROM haftalik_program p JOIN dersler d ON p.ders_id = d.ders_id JOIN sinav_turleri s ON d.sinav_id = s.sinav_id WHERE p.user_id = %s AND p.gun = %s"
    with get_db_connection() as cursor:
        cursor.execute(query, (user_id, gun))
        return cursor.fetchall()

def add_ders_to_program(user_id: int, gun: int, ders_id: int):
    with get_db_connection() as cursor:
        cursor.execute("INSERT INTO haftalik_program (user_id, gun, ders_id) VALUES (%s, %s, %s)", (user_id, gun, ders_id))

def remove_ders_from_program(program_id: int):
    with get_db_connection() as cursor:
        cursor.execute("DELETE FROM haftalik_program WHERE program_id = %s", (program_id,))

def get_all_user_dersler(user_id: int):
    query = "SELECT d.ders_id, d.ders_adi, s.sinav_adi FROM dersler d JOIN sinav_turleri s ON d.sinav_id = s.sinav_id WHERE s.user_id = %s"
    with get_db_connection() as cursor:
        cursor.execute(query, (user_id,))
        return cursor.fetchall()

def get_rituels(user_id: int):
    with get_db_connection() as cursor:
        cursor.execute("SELECT rituel_id, rituel_icerik FROM gunluk_rituel WHERE user_id = %s", (user_id,))
        return cursor.fetchall()

def add_rituel(user_id: int, icerik: str):
    with get_db_connection() as cursor:
        cursor.execute("INSERT INTO gunluk_rituel (user_id, rituel_icerik) VALUES (%s, %s)", (user_id, icerik))

def delete_rituel(rituel_id: int):
    with get_db_connection() as cursor:
        cursor.execute("DELETE FROM gunluk_rituel WHERE rituel_id = %s", (rituel_id,))

def get_gunluk_notlar(user_id: int, gun: int):
    with get_db_connection() as cursor:
        cursor.execute("SELECT gunluk_not_id, not_icerik FROM gunluk_notlar WHERE user_id = %s AND gun = %s", (user_id, gun))
        return cursor.fetchall()

def add_gunluk_not(user_id: int, gun: int, icerik: str):
    with get_db_connection() as cursor:
        cursor.execute("INSERT INTO gunluk_notlar (user_id, gun, not_icerik) VALUES (%s, %s, %s)", (user_id, gun, icerik))

def delete_gunluk_not(gunluk_not_id: int):
    with get_db_connection() as cursor:
        cursor.execute("DELETE FROM gunluk_notlar WHERE gunluk_not_id = %s", (gunluk_not_id,))

# --- TEMEL VERİ FONKSİYONLARI ---
def add_user_if_not_exists(user_id: int, first_name: str, username: str):
    sql_insert = "INSERT INTO users (user_id, first_name, username) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO NOTHING"
    sql_update = "UPDATE users SET first_name = %s, username = %s WHERE user_id = %s"
    with get_db_connection() as cursor:
        cursor.execute(sql_insert, (user_id, first_name, username))
        # Eğer insert olmadıysa (kullanıcı zaten varsa), update et
        if cursor.rowcount == 0:
            cursor.execute(sql_update, (first_name, username, user_id))

def get_sinavlar(user_id: int):
    with get_db_connection() as cursor:
        cursor.execute("SELECT sinav_id, sinav_adi, tamamlandi FROM sinav_turleri WHERE user_id = %s", (user_id,))
        return cursor.fetchall()

def get_dersler(sinav_id: int):
    with get_db_connection() as cursor:
        cursor.execute("SELECT ders_id, ders_adi, tamamlandi FROM dersler WHERE sinav_id = %s", (sinav_id,))
        return cursor.fetchall()

def get_konular(ders_id: int):
    with get_db_connection() as cursor:
        cursor.execute("SELECT konu_id, konu_adi, tamamlandi FROM konular WHERE ders_id = %s", (ders_id,))
        return cursor.fetchall()

def get_soru_istatistik(konu_id: int):
    with get_db_connection() as cursor:
        cursor.execute("SELECT hedef_soru, cozulen_dogru, cozulen_yanlis, cozulen_bos FROM soru_takip WHERE konu_id = %s", (konu_id,))
        stats = cursor.fetchone()
        return stats if stats else (0, 0, 0, 0)

def get_sinav_adi(sinav_id: int):
    with get_db_connection() as cursor:
        cursor.execute("SELECT sinav_adi FROM sinav_turleri WHERE sinav_id = %s", (sinav_id,))
        result = cursor.fetchone()
        return result[0] if result else "Bilinmeyen Sınav"

def get_ders_adi(ders_id: int):
    with get_db_connection() as cursor:
        cursor.execute("SELECT ders_adi FROM dersler WHERE ders_id = %s", (ders_id,))
        result = cursor.fetchone()
        return result[0] if result else "Bilinmeyen Ders"

def get_konu_adi(konu_id: int):
    with get_db_connection() as cursor:
        cursor.execute("SELECT konu_adi FROM konular WHERE konu_id = %s", (konu_id,))
        result = cursor.fetchone()
        return result[0] if result else "Bilinmeyen Konu"

def get_konu_id_by_name(ders_adi: str, konu_adi: str, user_id: int):
    query = "SELECT k.konu_id FROM konular k JOIN dersler d ON k.ders_id = d.ders_id JOIN sinav_turleri s ON d.sinav_id = s.sinav_id WHERE d.ders_adi = %s AND k.konu_adi = %s AND s.user_id = %s"
    with get_db_connection() as cursor:
        cursor.execute(query, (ders_adi, konu_adi, user_id))
        result = cursor.fetchone()
        return result[0] if result else None

def get_parent_ids(konu_id: int = None, ders_id: int = None):
    with get_db_connection() as cursor:
        if konu_id:
            cursor.execute("SELECT d.ders_id, d.sinav_id FROM konular k JOIN dersler d ON k.ders_id = d.ders_id WHERE k.konu_id = %s", (konu_id,))
        elif ders_id:
            cursor.execute("SELECT sinav_id FROM dersler WHERE ders_id = %s", (ders_id,))
        return cursor.fetchone()

def get_notes(konu_id: int):
    with get_db_connection() as cursor:
        cursor.execute("SELECT not_id, not_icerik FROM notlar WHERE konu_id = %s", (konu_id,))
        return cursor.fetchall()

def get_konu_id_from_not_id(not_id: int):
    with get_db_connection() as cursor:
        cursor.execute("SELECT konu_id FROM notlar WHERE not_id = %s", (not_id,))
        result = cursor.fetchone()
        return result[0] if result else None

def add_sinav(user_id: int, sinav_adi: str):
    with get_db_connection() as cursor:
        cursor.execute("INSERT INTO sinav_turleri (user_id, sinav_adi) VALUES (%s, %s)", (user_id, sinav_adi))

def add_ders(sinav_id: int, ders_adi: str):
    with get_db_connection() as cursor:
        cursor.execute("INSERT INTO dersler (sinav_id, ders_adi) VALUES (%s, %s)", (sinav_id, ders_adi))

def add_konu(ders_id: int, konu_adi: str):
    with get_db_connection() as cursor:
        cursor.execute("INSERT INTO konular (ders_id, konu_adi) VALUES (%s, %s)", (ders_id, konu_adi))

def add_soru_stats(konu_id: int, dogru: int, yanlis: int, bos: int):
    query = """
    INSERT INTO soru_takip (konu_id, cozulen_dogru, cozulen_yanlis, cozulen_bos) 
    VALUES (%s, %s, %s, %s) 
    ON CONFLICT(konu_id) 
    DO UPDATE SET 
        cozulen_dogru = soru_takip.cozulen_dogru + EXCLUDED.cozulen_dogru, 
        cozulen_yanlis = soru_takip.cozulen_yanlis + EXCLUDED.cozulen_yanlis, 
        cozulen_bos = soru_takip.cozulen_bos + EXCLUDED.cozulen_bos;
    """
    with get_db_connection() as cursor:
        cursor.execute(query, (konu_id, dogru, yanlis, bos))

def set_hedef_soru(konu_id: int, hedef: int):
    query = """
    INSERT INTO soru_takip (konu_id, hedef_soru) 
    VALUES (%s, %s) 
    ON CONFLICT(konu_id) 
    DO UPDATE SET hedef_soru = EXCLUDED.hedef_soru;
    """
    with get_db_connection() as cursor:
        cursor.execute(query, (konu_id, hedef))

def add_note(konu_id: int, icerik: str):
    with get_db_connection() as cursor:
        cursor.execute("INSERT INTO notlar (konu_id, not_icerik) VALUES (%s, %s)", (konu_id, icerik))

def update_sinav_adi(sinav_id: int, yeni_ad: str):
    with get_db_connection() as cursor:
        cursor.execute("UPDATE sinav_turleri SET sinav_adi = %s WHERE sinav_id = %s", (yeni_ad, sinav_id))

def update_ders_adi(ders_id: int, yeni_ad: str):
    with get_db_connection() as cursor:
        cursor.execute("UPDATE dersler SET ders_adi = %s WHERE ders_id = %s", (yeni_ad, ders_id))

def update_konu_adi(konu_id: int, yeni_ad: str):
    with get_db_connection() as cursor:
        cursor.execute("UPDATE konular SET konu_adi = %s WHERE konu_id = %s", (yeni_ad, konu_id))

def update_soru_stats(konu_id: int, dogru: int, yanlis: int, bos: int):
    query = """
    INSERT INTO soru_takip (konu_id, cozulen_dogru, cozulen_yanlis, cozulen_bos) 
    VALUES (%s, %s, %s, %s) 
    ON CONFLICT(konu_id) 
    DO UPDATE SET 
        cozulen_dogru = EXCLUDED.cozulen_dogru, 
        cozulen_yanlis = EXCLUDED.cozulen_yanlis, 
        cozulen_bos = EXCLUDED.cozulen_bos;
    """
    with get_db_connection() as cursor:
        cursor.execute(query, (konu_id, dogru, yanlis, bos))

def update_status(item_type: str, item_id: int, status: int):
    table_map = {"sinav": "sinav_turleri", "ders": "dersler", "konu": "konular"}
    id_map = {"sinav": "sinav_id", "ders": "ders_id", "konu": "konu_id"}
    if item_type in table_map:
        with get_db_connection() as cursor:
            # PostgreSQL için f-string'ler güvenlidir, çünkü parametreler ayrı veriliyor
            sql = f"UPDATE {table_map[item_type]} SET tamamlandi = %s WHERE {id_map[item_type]} = %s"
            cursor.execute(sql, (status, item_id))

def delete_konu(konu_id: int):
    # Foreign key'lerde ON DELETE CASCADE ayarlandığı için
    # sadece ana konuyu silmek, ilişkili notları ve istatistikleri de siler.
    with get_db_connection() as cursor:
        cursor.execute("DELETE FROM konular WHERE konu_id = %s", (konu_id,))

def delete_ders(ders_id: int):
    # ON DELETE CASCADE, bu derse bağlı konuları ve onlara bağlı her şeyi siler.
    with get_db_connection() as cursor:
        cursor.execute("DELETE FROM dersler WHERE ders_id = %s", (ders_id,))

def delete_sinav(sinav_id: int):
    # ON DELETE CASCADE, bu sınava bağlı dersleri ve onlara bağlı her şeyi siler.
    with get_db_connection() as cursor:
        cursor.execute("DELETE FROM sinav_turleri WHERE sinav_id = %s", (sinav_id,))

def delete_note(not_id: int):
    with get_db_connection() as cursor:
        cursor.execute("DELETE FROM notlar WHERE not_id = %s", (not_id,))
