# keyboards.py (GÜNE ÖZEL NOT ÖZELLİĞİ EKLENDİ)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
import database as db

def get_persistent_menu_keyboard():
    keyboard = [['📚 Panelim', '🗓️ Programım']]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_program_main_menu():
    gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    keyboard = [[InlineKeyboardButton(gun, callback_data=f"program_gun_{i}")] for i, gun in enumerate(gunler)]
    keyboard.append([InlineKeyboardButton("🧘 Günlük Ritüeller", callback_data="program_rituel")])
    keyboard.append([InlineKeyboardButton("🤖 Akıllı Program Tavsiyesi", callback_data="program_smart_fill")])
    keyboard.append([InlineKeyboardButton("📊 Genel İstatistik Raporu", callback_data="program_stats")]) # YENİ EKLENDİ
    return InlineKeyboardMarkup(keyboard)

def get_gun_program_menu(user_id: int, gun: int, gun_adi: str):
    program = db.get_program_for_gun(user_id, gun); keyboard = []
    text = f"🗓️ **{gun_adi} Programı**\n\n"
    if not program: text += "Bu gün için henüz bir ders planlanmamış.\n"
    else:
        for program_id, ders_adi, sinav_adi in program: text += f" - {sinav_adi} / {ders_adi}\n"
    
    text += "\n🧘 **Günlük Ritüeller**\n"
    rituels = db.get_rituels(user_id)
    if not rituels: text += "Günlük ritüel eklenmemiş."
    else:
        for _, rituel_icerik in rituels: text += f" - {rituel_icerik}\n"

    # YENİ EKLENDİ
    text += "\n\n📝 **Güne Özel Notlar**\n"
    gunluk_notlar = db.get_gunluk_notlar(user_id, gun)
    if not gunluk_notlar: text += "Bu güne özel bir not eklenmemiş."
    else:
        for _, not_icerik in gunluk_notlar: text += f" - {not_icerik}\n"
    
    keyboard.append([InlineKeyboardButton("➕ Dersekle", callback_data=f"program_add_{gun}"), InlineKeyboardButton("➖ Ders Sil", callback_data=f"program_delete_menu_{gun}")])
    
    # YENİ EKLENDİ
    keyboard.append([InlineKeyboardButton("📝 O Güne Not Ekle/Sil", callback_data=f"program_not_menu_{gun}")])
    
    keyboard.append([InlineKeyboardButton("« Haftalık Programa Dön", callback_data="program_main")])
    return text, InlineKeyboardMarkup(keyboard)

def get_ders_secim_menu(user_id: int, gun: int):
    dersler = db.get_all_user_dersler(user_id); keyboard = []
    for ders_id, ders_adi, sinav_adi in dersler:
        keyboard.append([InlineKeyboardButton(f"{sinav_adi} - {ders_adi}", callback_data=f"program_select_{gun}_{ders_id}")])
    keyboard.append([InlineKeyboardButton("« Geri", callback_data=f"program_gun_{gun}")])
    return InlineKeyboardMarkup(keyboard)

def get_ders_silme_menu(user_id: int, gun: int, gun_adi: str):
    program = db.get_program_for_gun(user_id, gun); keyboard = []
    text = f"🗓️ **{gun_adi} Programından Ders Sil**\n\nHangi dersi silmek istersin?\n\n"
    for program_id, ders_adi, sinav_adi in program:
        keyboard.append([InlineKeyboardButton(f"🗑️ {sinav_adi} / {ders_adi}", callback_data=f"program_delete_{program_id}")])
    keyboard.append([InlineKeyboardButton("« Geri", callback_data=f"program_gun_{gun}")])
    return text, InlineKeyboardMarkup(keyboard)
    
def get_rituel_menu(user_id: int):
    rituels = db.get_rituels(user_id); keyboard = []; text = "🧘 **Günlük Ritüeller Yönetimi**\n\n"
    if not rituels: text += "Henüz bir günlük ritüel eklenmemiş."
    else:
        for rituel_id, rituel_icerik in rituels:
            text += f" - {rituel_icerik}\n"; keyboard.append([InlineKeyboardButton(f"🗑️ {rituel_icerik[:20]}..", callback_data=f"program_del_rituel_{rituel_id}")])
    keyboard.append([InlineKeyboardButton("➕ Yeni Ritüel Ekle", callback_data="program_add_rituel")])
    keyboard.append([InlineKeyboardButton("« Haftalık Programa Dön", callback_data="program_main")])
    return text, InlineKeyboardMarkup(keyboard)

# YENİ EKLENEN FONKSİYON
def get_gun_not_menu(user_id: int, gun: int, gun_adi: str):
    notlar = db.get_gunluk_notlar(user_id, gun); keyboard = []; text = f"📝 **{gun_adi} - Güne Özel Notlar**\n\n"
    if not notlar: text += "Henüz bir not eklenmemiş."
    else:
        for not_id, not_icerik in notlar:
            kisa_icerik = (not_icerik[:20] + '..') if len(not_icerik) > 20 else not_icerik
            text += f" - {not_icerik}\n"; keyboard.append([InlineKeyboardButton(f"🗑️ {kisa_icerik}", callback_data=f"program_del_gunnot_{not_id}_{gun}")])
    keyboard.append([InlineKeyboardButton("➕ Yeni Not Ekle", callback_data=f"program_add_gunnot_{gun}")])
    keyboard.append([InlineKeyboardButton("« Geri", callback_data=f"program_gun_{gun}")])
    return text, InlineKeyboardMarkup(keyboard)

def get_main_menu_keyboard(user_id: int):
    sinavlar = db.get_sinavlar(user_id); keyboard = []
    for sinav_id, sinav_adi, tamamlandi in sinavlar:
        icon = "✅" if tamamlandi else "❌"; keyboard.append([InlineKeyboardButton(f"{icon} {sinav_adi}", callback_data=f"sinav_{sinav_id}")])
    keyboard.append([InlineKeyboardButton("➕ Yeni Sınav Ekle", callback_data="add_sinav")]); return InlineKeyboardMarkup(keyboard)
def get_dersler_menu_keyboard(sinav_id: int):
    dersler = db.get_dersler(sinav_id); keyboard = []
    for ders_id, ders_adi, tamamlandi in dersler:
        icon = "✅" if tamamlandi else "❌"; keyboard.append([InlineKeyboardButton(f"{icon} {ders_adi}", callback_data=f"ders_{ders_id}")])
    keyboard.append([InlineKeyboardButton("➕ Yeni Ders Ekle", callback_data=f"add_ders_{sinav_id}")])
    keyboard.append([InlineKeyboardButton(f"⚙️ Sınavı Yönet", callback_data=f"manage_sinav_{sinav_id}")])
    keyboard.append([InlineKeyboardButton("« Ana Menüye Dön", callback_data="back_to_main")]); return InlineKeyboardMarkup(keyboard)
def get_konular_menu_keyboard(ders_id: int):
    konular = db.get_konular(ders_id); keyboard = []
    for konu_id, konu_adi, tamamlandi in konular:
        icon = "✅" if tamamlandi else "❌"; keyboard.append([InlineKeyboardButton(f"{icon} {konu_adi}", callback_data=f"konu_{konu_id}")])
    keyboard.append([InlineKeyboardButton("➕ Yeni Konu Ekle", callback_data=f"add_konu_{ders_id}")])
    keyboard.append([InlineKeyboardButton(f"⚙️ Dersi Yönet", callback_data=f"manage_ders_{ders_id}")])
    parent_ids = db.get_parent_ids(ders_id=ders_id)
    if parent_ids: keyboard.append([InlineKeyboardButton("« Derslere Dön", callback_data=f"sinav_{parent_ids[0]}")])
    return InlineKeyboardMarkup(keyboard)
def get_konu_detay_menu_keyboard(konu_id: int):
    keyboard = [[InlineKeyboardButton("📊 Soru Bilgisi", callback_data=f"show_stats_{konu_id}")], [InlineKeyboardButton("📝 Notlar", callback_data=f"show_notes_{konu_id}")], [InlineKeyboardButton(f"⚙️ Konuyu Yönet", callback_data=f"manage_konu_{konu_id}")],]
    parent_ids = db.get_parent_ids(konu_id=konu_id)
    if parent_ids: keyboard.append([InlineKeyboardButton("« Konulara Dön", callback_data=f"ders_{parent_ids[0]}")])
    return InlineKeyboardMarkup(keyboard)
def get_sinav_management_keyboard(sinav_id: int):
    keyboard = [[InlineKeyboardButton("✍️ Adını Değiştir", callback_data=f"edit_sinav_{sinav_id}")], [InlineKeyboardButton("🗑️ SINAVI SİL", callback_data=f"delete_sinav_confirm_{sinav_id}")], [InlineKeyboardButton("✅ Tamamlandı İşaretle", callback_data=f"toggle_sinav_{sinav_id}_1")], [InlineKeyboardButton("❌ Tamamlanmadı İşaretle", callback_data=f"toggle_sinav_{sinav_id}_0")], [InlineKeyboardButton("« Derslere Dön", callback_data=f"sinav_{sinav_id}")],]
    return InlineKeyboardMarkup(keyboard)
def get_ders_management_keyboard(ders_id: int):
    keyboard = [[InlineKeyboardButton("✍️ Adını Değiştir", callback_data=f"edit_ders_{ders_id}")], [InlineKeyboardButton("🗑️ DERSİ SİL", callback_data=f"delete_ders_confirm_{ders_id}")], [InlineKeyboardButton("✅ Tamamlandı İşaretle", callback_data=f"toggle_ders_{ders_id}_1")], [InlineKeyboardButton("❌ Tamamlanmadı İşaretle", callback_data=f"toggle_ders_{ders_id}_0")], [InlineKeyboardButton("« Konulara Dön", callback_data=f"ders_{ders_id}")],]
    return InlineKeyboardMarkup(keyboard)
def get_konu_management_keyboard(konu_id: int):
    keyboard = [[InlineKeyboardButton("✍️ Adını Değiştir", callback_data=f"edit_konu_{konu_id}")], [InlineKeyboardButton("🗑️ KONUYU SİL", callback_data=f"delete_konu_confirm_{konu_id}")], [InlineKeyboardButton("✅ Tamamlandı İşaretle", callback_data=f"toggle_konu_{konu_id}_1")], [InlineKeyboardButton("❌ Tamamlanmadı İşaretle", callback_data=f"toggle_konu_{konu_id}_0")], [InlineKeyboardButton("« Konu Detayına Dön", callback_data=f"konu_{konu_id}")],]
    return InlineKeyboardMarkup(keyboard)
def get_confirmation_keyboard(item_type: str, item_id: int):
    keyboard = [[InlineKeyboardButton("✅ EVET, SİL", callback_data=f"delete_{item_type}_yes_{item_id}")], [InlineKeyboardButton("❌ HAYIR, VAZGEÇ", callback_data=f"manage_{item_type}_{item_id}")],]
    return InlineKeyboardMarkup(keyboard)
def get_notes_menu_keyboard(konu_id: int):
    notlar = db.get_notes(konu_id); keyboard = []
    for not_id, not_icerik in notlar: kisa_icerik = (not_icerik[:30] + '..') if len(not_icerik) > 30 else not_icerik; keyboard.append([InlineKeyboardButton(f"🗑️ {kisa_icerik}", callback_data=f"delete_note_{not_id}")])
    keyboard.append([InlineKeyboardButton("➕ Yeni Not Ekle", callback_data=f"add_note_{konu_id}")]); keyboard.append([InlineKeyboardButton("« Konu Detayına Dön", callback_data=f"konu_{konu_id}")])
    return InlineKeyboardMarkup(keyboard)
def get_stats_management_keyboard(konu_id: int):
    keyboard = [[InlineKeyboardButton("➕ Soru Ekle", callback_data=f"add_stats_{konu_id}"), InlineKeyboardButton("✍️ Bilgiyi Düzenle", callback_data=f"edit_stats_{konu_id}")], [InlineKeyboardButton("🎯 Hedef Belirle", callback_data=f"set_hedef_{konu_id}")], [InlineKeyboardButton("« Konu Detayına Dön", callback_data=f"konu_{konu_id}")]]
    return InlineKeyboardMarkup(keyboard)
