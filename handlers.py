# handlers.py (GÜNE ÖZEL NOT ÖZELLİĞİ EKLENDİ)

from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler, filters
)
from telegram.error import BadRequest
import database as db
import keyboards as kb
import analysis as an
import random

# Sohbet durumları
GET_SINAV_NAME, GET_DERS_NAME, GET_KONU_NAME, EDIT_DERS_NAME, EDIT_KONU_NAME, EDIT_SINAV_NAME, GET_NOTE_CONTENT, \
GET_ADD_DOGRU, GET_ADD_YANLIS, GET_ADD_BOS, \
GET_EDIT_DOGRU, GET_EDIT_YANLIS, GET_EDIT_BOS, \
GET_HEDEF, GET_RITUEL_CONTENT, GET_GUN_NOT_CONTENT = range(16) # GÜNCELLENDİ

# --- YARDIMCI FONKSİYON ---
async def send_updated_stats(update_or_query_or_message, context: ContextTypes.DEFAULT_TYPE, konu_id: int, prefix_text: str):
    stats = an.calculate_konu_stats(konu_id)
    db_stats = db.get_soru_istatistik(konu_id)
    stats_text = (
        f"📊 **Konu İstatistikleri**\n\n"
        f"🎯 **Hedeflenen Soru: {db_stats[0]}**\n"
        f"✍️ **Toplam Çözülen: {stats['toplam_cozulen']}**\n\n"
        f"✔️ Doğru: {db_stats[1]}\n"
        f"❌ Yanlış: {db_stats[2]}\n"
        f"➖ Boş: {db_stats[3]}\n\n"
        f"🧠 **Konu Hakimiyeti: %{stats['hakimiyet']:.1f}**\n"
        f"🏁 **Hedefe Ulaşma: %{stats['hedefe_ulasma']:.1f}**"
    )
    reply_markup = kb.get_stats_management_keyboard(konu_id)
    
    if isinstance(update_or_query_or_message, CallbackQuery):
        await update_or_query_or_message.edit_message_text(text=stats_text, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await context.bot.send_message(
            chat_id=update_or_query_or_message.effective_chat.id, 
            text=f"{prefix_text}\n\n{stats_text}", 
            parse_mode='Markdown', 
            reply_markup=reply_markup
        )

# --- YETKİ KONTROL ---
def is_super_admin(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    return user_id == context.bot_data.get("SUPER_ADMIN_ID")

def is_admin_user(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    super_admin_id = context.bot_data.get("SUPER_ADMIN_ID")
    return db.is_admin(user_id, super_admin_id)

# --- ANA KULLANICI FONKSİYONLARI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user; db.add_user_if_not_exists(user.id, user.first_name, user.username)
    inline_keyboard = kb.get_main_menu_keyboard(user.id)
    persistent_keyboard = kb.get_persistent_menu_keyboard()
    message_text = f"👤 {user.first_name} | Ana Panel"
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text(text=message_text, reply_markup=inline_keyboard)
        else:
            # DÜZELTME: 'if' kontrolü kaldırıldı. Artık /start komutu her zaman
            # sabit klavyeyi de göndererek kaybolmasını engeller.
            await update.message.reply_text("Kontrol paneli:", reply_markup=persistent_keyboard)
            context.user_data['persistent_keyboard_sent'] = True # Hafızada tutmaya devam edebiliriz, sorun değil.
            await update.message.reply_text(text=message_text, reply_markup=inline_keyboard)
    except BadRequest as e:
        if "Message is not modified" in str(e): pass
        else: raise e

async def programim(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reply_markup = kb.get_program_main_menu()
    message_text = "🗓️ **Haftalık Program Yönetimi**\n\nAşağıdan bir gün seçerek programını düzenleyebilir veya 'Akıllı Tavsiye' alabilirsin."
    try:
        if update.callback_query: await update.callback_query.edit_message_text(text=message_text, parse_mode='Markdown', reply_markup=reply_markup)
        else: await update.message.reply_text(text=message_text, parse_mode='Markdown', reply_markup=reply_markup)
    except BadRequest as e:
        if "Message is not modified" in str(e): pass
        else: raise e

async def greet_and_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text
    if message_text in ['📚 Panelim', 'Merhaba', 'Hi', 'Hello', 'Başla', '.']:
        await start(update, context)
    elif message_text == '🗓️ Programım':
        await programim(update, context)

async def gizlilik(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("Gizlilik Politikası: Bu bot, çalışma ilerlemenizi takip etmek amacıyla girdiğiniz verileri saklar. Bu veriler tamamen size özeldir ve sizin onayınız olmadan başka kimseyle paylaşılmaz.")

async def geribildirim(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    SUPER_ADMIN_ID = context.bot_data.get("SUPER_ADMIN_ID")
    if not SUPER_ADMIN_ID:
        await update.effective_message.reply_text("Hata: Geri bildirim sistemi şu anda aktif değil.")
        return
    user_feedback = " ".join(context.args)
    if not user_feedback:
        await update.effective_message.reply_text("Lütfen geri bildiriminizi komuttan sonra yazın.\nÖrnek: /geribildirim Bu harika bir bot!")
        return
    user = update.effective_user
    feedback_message = (f"📣 YENİ GERİ BİLDİRİM!\n\nGönderen: {user.first_name} (@{user.username} - ID: {user.id})\n\nMesaj: {user_feedback}")
    try:
        await context.bot.send_message(chat_id=SUPER_ADMIN_ID, text=feedback_message)
        await update.effective_message.reply_text("Geri bildiriminiz için teşekkürler! Mesajınız yöneticiye iletildi.")
    except Exception as e:
        await update.effective_message.reply_text(f"Geri bildirim gönderilemedi. Hata: {e}")

async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(f"Kullanıcı ID'niz: `{update.effective_user.id}`", parse_mode='Markdown')

async def istatistik(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id; sinavlar = db.get_sinavlar(user_id)
    if not sinavlar: await update.effective_message.reply_text("Henüz hiç sınav eklememişsiniz."); return
    message = "📊 **Genel Performans Raporu** 📊\n\n"
    for sinav_id, sinav_adi, _ in sinavlar:
        stats = an.get_sinav_overall_stats(sinav_id)
        message += f"📘 **Sınav: {sinav_adi}**\n   - Toplam Ders: {stats['ders_sayisi']}\n   - Toplam Konu: {stats['konu_sayisi']}\n   - **Genel Hakimiyet Ortalaması: %{stats['ortalama_hakimiyet']:.1f}**\n\n"
    
    if update.callback_query:
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("« Haftalık Programa Dön", callback_data="program_main")]])
        await update.callback_query.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await update.effective_message.reply_text(message, parse_mode='Markdown')

async def rutinolustur(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id; await update.effective_message.reply_text("Analiz yapılıyor, lütfen bekleyin...")
    routine_message, _ = an.generate_routine(user_id)
    await update.effective_message.reply_text(routine_message, parse_mode='Markdown')
    
async def hedefbelirle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        args = " ".join(context.args).split('|'); ders_adi, konu_adi, hedef_str = [a.strip() for a in args]; hedef = int(hedef_str)
        user_id = update.effective_user.id; konu_id = db.get_konu_id_by_name(ders_adi, konu_adi, user_id)
        if konu_id: db.set_hedef_soru(konu_id, hedef); await update.effective_message.reply_text(f"✅ Hedef ayarlandı: '{konu_adi}' için {hedef} soru.")
        else: await update.effective_message.reply_text(f"❌ Konu bulunamadı.")
    except (IndexError, ValueError): await update.effective_message.reply_text("Hatalı format!\nKullanım: /hedefbelirle Ders Adı | Konu Adı | Sayı")

async def soruekle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        args = context.args
        if len(args) < 3: raise ValueError
        dogru = 0; yanlis = 0; bos = 0
        if len(args) >= 5 and args[-1].isdigit() and args[-2].isdigit() and args[-3].isdigit():
             dogru, yanlis, bos = int(args[-3]), int(args[-2]), int(args[-1]); konu_adi_parts = args[:-3]
        elif len(args) >= 4 and args[-1].isdigit() and args[-2].isdigit():
             dogru, yanlis, bos = int(args[-2]), int(args[-1]), 0; konu_adi_parts = args[:-2]
        else: raise ValueError
        ders_adi = konu_adi_parts[0]; konu_adi = " ".join(konu_adi_parts[1:]) if len(konu_adi_parts) > 1 else konu_adi_parts[0]
        user_id = update.effective_user.id; konu_id = db.get_konu_id_by_name(ders_adi, konu_adi, user_id)
        if konu_id: db.add_soru_stats(konu_id, dogru, yanlis, bos); await update.effective_message.reply_text(f"✅ İstatistikler eklendi: '{konu_adi}' konusuna {dogru} D, {yanlis} Y, {bos} B.")
        else: await update.effective_message.reply_text(f"❌ Konu bulunamadı: '{ders_adi}' > '{konu_adi}'.")
    except (IndexError, ValueError): await update.effective_message.reply_text("Hatalı format!\nÖrnek: /soruekle Matematik Üslü Sayılar 40 8 2")

async def navigation_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query; await query.answer(); data = query.data
    user_id = query.from_user.id
    gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    try:
        if data == "program_stats":
            await istatistik(update, context)
            return
        elif data == "program_smart_fill":
            await query.edit_message_text("🤖 Akıllı program tavsiyen oluşturuluyor, lütfen bekleyin...")
            message, _ = an.generate_routine(user_id)
            reply_markup = kb.get_program_main_menu()
            await query.edit_message_text(text=f"{message}\n\n*Bu dersleri programına kendin eklemeyi unutma!*", parse_mode='Markdown', reply_markup=reply_markup)
            return
        elif data.startswith("program_gun_"):
            gun_index = int(data.split("_")[2]); context.user_data['current_gun'] = gun_index; gun_adi = gunler[gun_index]
            text, reply_markup = kb.get_gun_program_menu(user_id, gun_index, gun_adi)
            await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=reply_markup)
        elif data.startswith("program_add_"):
            gun_index = int(data.split("_")[2]); reply_markup = kb.get_ders_secim_menu(user_id, gun_index)
            await query.edit_message_text("Hangi dersi eklemek istersin?", reply_markup=reply_markup)
        elif data.startswith("program_select_"):
            parts = data.split('_'); gun_index, ders_id = int(parts[2]), int(parts[3]); db.add_ders_to_program(user_id, gun_index, ders_id)
            gun_adi = gunler[gun_index]; text, reply_markup = kb.get_gun_program_menu(user_id, gun_index, gun_adi)
            await query.edit_message_text(text=f"✅ Ders eklendi.\n\n{text}", parse_mode='Markdown', reply_markup=reply_markup)
        elif data.startswith("program_delete_menu_"):
            gun_index = int(data.split("_")[3]); gun_adi = gunler[gun_index]; context.user_data['current_gun'] = gun_index
            text, reply_markup = kb.get_ders_silme_menu(user_id, gun_index, gun_adi)
            await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=reply_markup)
        elif data.startswith("program_delete_"):
            program_id = int(data.split("_")[2]); db.remove_ders_from_program(program_id); gun_index = context.user_data.get('current_gun'); gun_adi = gunler[gun_index]
            text, reply_markup = kb.get_gun_program_menu(user_id, gun_index, gun_adi)
            await query.edit_message_text(text=f"🗑️ Ders silindi.\n\n{text}", parse_mode='Markdown', reply_markup=reply_markup)
        elif data == "program_rituel":
            text, reply_markup = kb.get_rituel_menu(user_id)
            await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=reply_markup)
        elif data.startswith("program_del_rituel_"):
            rituel_id = int(data.split("_")[3]); db.delete_rituel(rituel_id)
            text, reply_markup = kb.get_rituel_menu(user_id)
            await query.edit_message_text(text=f"🗑️ Ritüel silindi.\n\n{text}", parse_mode='Markdown', reply_markup=reply_markup)
        elif data == "program_main": await programim(update, context)
        
        # YENİ EKLENEN BLOKLAR
        elif data.startswith("program_not_menu_"):
            gun_index = int(data.split("_")[3])
            gun_adi = gunler[gun_index]
            text, reply_markup = kb.get_gun_not_menu(user_id, gun_index, gun_adi)
            await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=reply_markup)
        
        elif data.startswith("program_del_gunnot_"):
            parts = data.split("_")
            not_id, gun_index = int(parts[3]), int(parts[4])
            db.delete_gunluk_not(not_id)
            gun_adi = gunler[gun_index]
            text, reply_markup = kb.get_gun_not_menu(user_id, gun_index, gun_adi)
            await query.edit_message_text(text=f"🗑️ Not silindi.\n\n{text}", parse_mode='Markdown', reply_markup=reply_markup)
        
        elif data.startswith("toggle_"):
            parts = data.split('_'); item_type, item_id, status = parts[1], int(parts[2]), int(parts[3]); db.update_status(item_type, item_id, status)
            if item_type == "sinav": await start(update, context)
            elif item_type == "ders": 
                parent_ids = db.get_parent_ids(ders_id=item_id)
                if parent_ids: sinav_id = parent_ids[0]; sinav_adi = db.get_sinav_adi(sinav_id); reply_markup = kb.get_dersler_menu_keyboard(sinav_id); await query.edit_message_text(text=f"📚 Sınav: {sinav_adi}", reply_markup=reply_markup)
            elif item_type == "konu": 
                parent_ids = db.get_parent_ids(konu_id=item_id)
                if parent_ids: ders_id = parent_ids[0]; ders_adi = db.get_ders_adi(ders_id); reply_markup = kb.get_konular_menu_keyboard(ders_id); await query.edit_message_text(text=f"📖 Ders: {ders_adi}", reply_markup=reply_markup)
            return
        elif data.startswith("sinav_"):
            sinav_id = int(data.split("_")[1]); sinav_adi = db.get_sinav_adi(sinav_id); reply_markup = kb.get_dersler_menu_keyboard(sinav_id)
            await query.edit_message_text(text=f"📚 Sınav: {sinav_adi}", reply_markup=reply_markup)
        elif data.startswith("ders_"):
            ders_id = int(data.split("_")[1]); ders_adi = db.get_ders_adi(ders_id); reply_markup = kb.get_konular_menu_keyboard(ders_id)
            await query.edit_message_text(text=f"📖 Ders: {ders_adi}", reply_markup=reply_markup)
        elif data.startswith("konu_"):
            konu_id = int(data.split("_")[1]); konu_adi = db.get_konu_adi(konu_id); reply_markup = kb.get_konu_detay_menu_keyboard(konu_id)
            await query.edit_message_text(text=f"🎯 Konu: {konu_adi}", reply_markup=reply_markup)
        elif data == "back_to_main": await start(update, context)
        elif data.startswith("manage_sinav_"):
            sinav_id = int(data.split("_")[2]); reply_markup = kb.get_sinav_management_keyboard(sinav_id)
            await query.edit_message_text(text="Sınav Yönetim Paneli:", reply_markup=reply_markup)
        elif data.startswith("manage_ders_"):
            ders_id = int(data.split("_")[2]); reply_markup = kb.get_ders_management_keyboard(ders_id)
            await query.edit_message_text(text="Ders Yönetim Paneli:", reply_markup=reply_markup)
        elif data.startswith("manage_konu_"):
            konu_id = int(data.split("_")[2]); reply_markup = kb.get_konu_management_keyboard(konu_id)
            await query.edit_message_text(text="Konu Yönetim Paneli:", reply_markup=reply_markup)
        elif data.startswith("delete_sinav_confirm_"):
            sinav_id = int(data.split("_")[3]); sinav_adi = db.get_sinav_adi(sinav_id); reply_markup = kb.get_confirmation_keyboard("sinav", sinav_id)
            await query.edit_message_text(text=f"⚠️ EMİN MİSİNİZ? '{sinav_adi}' sınavını sileceksiniz.", reply_markup=reply_markup)
        elif data.startswith("delete_ders_confirm_"):
            ders_id = int(data.split("_")[3]); ders_adi = db.get_ders_adi(ders_id); reply_markup = kb.get_confirmation_keyboard("ders", ders_id)
            await query.edit_message_text(text=f"⚠️ EMİN MİSİNİZ? '{ders_adi}' dersini sileceksiniz.", reply_markup=reply_markup)
        elif data.startswith("delete_konu_confirm_"):
            konu_id = int(data.split("_")[3]); reply_markup = kb.get_confirmation_keyboard("konu", konu_id)
            await query.edit_message_text(text=f"⚠️ EMİN MİSİNİZ? Bu konuyu sileceksiniz.", reply_markup=reply_markup)
        elif data.startswith("delete_sinav_yes_"):
            sinav_id = int(data.split("_")[3]); db.delete_sinav(sinav_id); await query.edit_message_text(text="🗑️ Sınav silindi."); await start(update, context)
        elif data.startswith("delete_ders_yes_"):
            ders_id = int(data.split("_")[3]); parent_ids = db.get_parent_ids(ders_id=ders_id); sinav_id = parent_ids[0]; db.delete_ders(ders_id)
            await query.edit_message_text(text="🗑️ Ders silindi."); sinav_adi = db.get_sinav_adi(sinav_id); reply_markup = kb.get_dersler_menu_keyboard(sinav_id)
            await query.message.reply_text(text=f"📚 Sınav: {sinav_adi}", reply_markup=reply_markup)
        elif data.startswith("delete_konu_yes_"):
            konu_id = int(data.split("_")[3]); parent_ids = db.get_parent_ids(konu_id=konu_id); ders_id = parent_ids[0]; db.delete_konu(konu_id)
            await query.edit_message_text(text="🗑️ Konu silindi."); ders_adi = db.get_ders_adi(ders_id); reply_markup = kb.get_konular_menu_keyboard(ders_id)
            await query.message.reply_text(text=f"📖 Ders: {ders_adi}", reply_markup=reply_markup)
        elif data.startswith("show_stats_"):
            konu_id = int(data.split("_")[2]); context.user_data['current_konu_id'] = konu_id
            await send_updated_stats(query, context, konu_id, "")
        elif data.startswith("show_notes_"):
            konu_id = int(data.split("_")[2]); context.user_data['current_konu_id'] = konu_id; konu_adi = db.get_konu_adi(konu_id); reply_markup = kb.get_notes_menu_keyboard(konu_id)
            await query.edit_message_text(text=f"📝 Notlar: {konu_adi}", reply_markup=reply_markup)
        elif data.startswith("delete_note_"):
            not_id = int(data.split("_")[2]); konu_id = db.get_konu_id_from_not_id(not_id); db.delete_note(not_id)
            konu_adi = db.get_konu_adi(konu_id); reply_markup = kb.get_notes_menu_keyboard(konu_id)
            await query.edit_message_text(text=f"🗑️ Not silindi.\n\n📝 Notlar: {konu_adi}", reply_markup=reply_markup)
    except (BadRequest, TypeError) as e:
        if "Message is not modified" in str(e): pass
        else: await query.message.reply_text("Bir hata oluştu. Ana menüye yönlendiriliyorsunuz."); await start(update, context)

async def conversation_entry_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query; await query.answer(); data = query.data
    if data == 'add_sinav': await query.message.reply_text("Sınav adı:"); return GET_SINAV_NAME
    elif data.startswith('add_ders_'): sinav_id = int(data.split('_')[2]); context.user_data['current_sinav_id'] = sinav_id; await query.message.reply_text("Ders adı:"); return GET_DERS_NAME
    elif data.startswith('add_konu_'): ders_id = int(data.split('_')[2]); context.user_data['current_ders_id'] = ders_id; await query.message.reply_text("Konu adı:"); return GET_KONU_NAME
    elif data.startswith('edit_sinav_'): sinav_id = int(data.split('_')[2]); context.user_data['current_sinav_id'] = sinav_id; await query.message.reply_text("Yeni sınav adı:"); return EDIT_SINAV_NAME
    elif data.startswith('edit_ders_'): ders_id = int(data.split('_')[2]); context.user_data['current_ders_id'] = ders_id; await query.message.reply_text("Yeni ders adı:"); return EDIT_DERS_NAME
    elif data.startswith('edit_konu_'): konu_id = int(data.split('_')[2]); context.user_data['current_konu_id'] = konu_id; await query.message.reply_text("Yeni konu adı:"); return EDIT_KONU_NAME
    elif data.startswith('add_note_'): konu_id = int(data.split('_')[2]); context.user_data['current_konu_id'] = konu_id; await query.message.reply_text("Notunuz:"); return GET_NOTE_CONTENT
    elif data.startswith('add_stats_'): konu_id = int(data.split('_')[2]); context.user_data['current_konu_id'] = konu_id; await query.message.reply_text("✔️ Doğru sayısı:"); return GET_ADD_DOGRU
    elif data.startswith('edit_stats_'): konu_id = int(data.split('_')[2]); context.user_data['current_konu_id'] = konu_id; await query.message.reply_text("✍️ Yeni Doğru (toplam):"); return GET_EDIT_DOGRU
    elif data.startswith('set_hedef_'): konu_id = int(data.split('_')[2]); context.user_data['current_konu_id'] = konu_id; await query.message.reply_text("🎯 Yeni Hedef:"); return GET_HEDEF
    elif data == 'program_add_rituel': await query.message.reply_text("Eklemek istediğin ritüeli yaz:"); return GET_RITUEL_CONTENT
    
    # YENİ EKLENDİ
    elif data.startswith('program_add_gunnot_'):
        gun_index = int(data.split('_')[3])
        context.user_data['current_gun'] = gun_index
        gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        gun_adi = gunler[gun_index]
        await query.message.reply_text(f"📝 {gun_adi} için notunuz:"); 
        return GET_GUN_NOT_CONTENT
    
async def get_rituel_content_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id; icerik = update.message.text
    db.add_rituel(user_id, icerik); await update.message.reply_text("✅ Ritüel eklendi!")
    text, reply_markup = kb.get_rituel_menu(user_id)
    await update.message.reply_text(text=text, parse_mode='Markdown', reply_markup=reply_markup); return ConversationHandler.END

# YENİ EKLENEN FONKSİYON
async def get_gun_not_content_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    icerik = update.message.text
    gun_index = context.user_data.get('current_gun')
    
    if gun_index is None: # Güvenlik kontrolü
        await update.message.reply_text("Hata: Hangi gün olduğu anlaşılamadı. Lütfen tekrar deneyin.")
        return ConversationHandler.END
        
    db.add_gunluk_not(user_id, gun_index, icerik)
    await update.message.reply_text("✅ Not eklendi!")
    
    gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    gun_adi = gunler[gun_index]
    text, reply_markup = kb.get_gun_not_menu(user_id, gun_index, gun_adi)
    await update.message.reply_text(text=text, parse_mode='Markdown', reply_markup=reply_markup)
    return ConversationHandler.END

async def get_sinav_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db.add_sinav(update.message.from_user.id, update.message.text); await update.message.reply_text(f"✅ Eklendi!"); await start(update, context); return ConversationHandler.END
async def get_ders_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    sinav_id = context.user_data.get('current_sinav_id'); db.add_ders(sinav_id, update.message.text); await update.message.reply_text(f"✅ Eklendi!")
    sinav_adi = db.get_sinav_adi(sinav_id); reply_markup = kb.get_dersler_menu_keyboard(sinav_id); await update.message.reply_text(text=f"📚 Sınav: {sinav_adi}", reply_markup=reply_markup); return ConversationHandler.END
async def get_konu_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ders_id = context.user_data.get('current_ders_id'); db.add_konu(ders_id, update.message.text); await update.message.reply_text(f"✅ Eklendi!")
    ders_adi = db.get_ders_adi(ders_id); reply_markup = kb.get_konular_menu_keyboard(ders_id); await update.message.reply_text(text=f"📖 Ders: {ders_adi}", reply_markup=reply_markup); return ConversationHandler.END
async def get_new_sinav_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    sinav_id = context.user_data.get('current_sinav_id'); db.update_sinav_adi(sinav_id, update.message.text); await update.message.reply_text(f"✅ Güncellendi!")
    await start(update, context); return ConversationHandler.END
async def get_new_ders_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ders_id = context.user_data.get('current_ders_id'); db.update_ders_adi(ders_id, update.message.text); await update.message.reply_text(f"✅ Güncellendi!")
    parent_ids = db.get_parent_ids(ders_id=ders_id); sinav_id = parent_ids[0]; sinav_adi = db.get_sinav_adi(sinav_id); reply_markup = kb.get_dersler_menu_keyboard(sinav_id); await update.message.reply_text(text=f"📚 Sınav: {sinav_adi}", reply_markup=reply_markup); return ConversationHandler.END
async def get_new_konu_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    konu_id = context.user_data.get('current_konu_id'); db.update_konu_adi(konu_id, update.message.text); await update.message.reply_text(f"✅ Güncellendi!")
    parent_ids = db.get_parent_ids(konu_id=konu_id); ders_id = parent_ids[0]; ders_adi = db.get_ders_adi(ders_id); reply_markup = kb.get_konular_menu_keyboard(ders_id); await update.message.reply_text(text=f"📖 Ders: {ders_adi}", reply_markup=reply_markup); return ConversationHandler.END
async def get_note_content_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    konu_id = context.user_data.get('current_konu_id'); not_icerik = update.message.text
    db.add_note(konu_id, not_icerik); await update.message.reply_text("✅ Not eklendi!")
    konu_adi = db.get_konu_adi(konu_id); reply_markup = kb.get_notes_menu_keyboard(konu_id)
    await update.message.reply_text(text=f"📝 Notlar: {konu_adi}", reply_markup=reply_markup); return ConversationHandler.END

async def get_add_dogru_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['add_dogru'] = int(update.message.text); await update.message.reply_text("❌ Yanlış sayısı:"); return GET_ADD_YANLIS
async def get_add_yanlis_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['add_yanlis'] = int(update.message.text); await update.message.reply_text("➖ Boş sayısı (yoksa 0):"); return GET_ADD_BOS
async def get_add_bos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['add_bos'] = int(update.message.text); konu_id = context.user_data.get('current_konu_id')
    dogru, yanlis, bos = context.user_data.get('add_dogru', 0), context.user_data.get('add_yanlis', 0), context.user_data.get('add_bos', 0)
    db.add_soru_stats(konu_id, dogru, yanlis, bos); await update.message.reply_text(f"✅ Eklendi!")
    await send_updated_stats(update.message, context, konu_id, "📊 **GÜNCEL İstatistikler**"); return ConversationHandler.END

async def get_edit_dogru_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['edit_dogru'] = int(update.message.text); await update.message.reply_text("✍️ Yeni Yanlış (toplam):"); return GET_EDIT_YANLIS
async def get_edit_yanlis_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['edit_yanlis'] = int(update.message.text); await update.message.reply_text("✍️ Yeni Boş (toplam):"); return GET_EDIT_BOS
async def get_edit_bos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['edit_bos'] = int(update.message.text); konu_id = context.user_data.get('current_konu_id')
    dogru, yanlis, bos = context.user_data.get('edit_dogru', 0), context.user_data.get('edit_yanlis', 0), context.user_data.get('edit_bos', 0)
    db.update_soru_stats(konu_id, dogru, yanlis, bos); await update.message.reply_text(f"✅ Güncellendi!")
    await send_updated_stats(update.message, context, konu_id, "📊 **GÜNCEL İstatistikler**"); return ConversationHandler.END

async def get_hedef_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    konu_id = context.user_data.get('current_konu_id'); hedef = int(update.message.text)
    db.set_hedef_soru(konu_id, hedef); await update.message.reply_text(f"✅ Yeni hedef ayarlandı!")
    await send_updated_stats(update.message, context, konu_id, "📊 **GÜNCEL İstatistikler**"); return ConversationHandler.END

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('İşlem iptal edildi.'); await start(update, context); return ConversationHandler.END
    
async def cancel_and_programim(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Aktif bir sohbeti (Conversation) iptal eder ve kullanıcıyı 
    'Programım' menüsüne yönlendirir.
    """
    await programim(update, context) # 'programim' fonksiyonunu çağır
    return ConversationHandler.END
    
    # --- YENİ EKLENECEK ACİL ÇÖZÜM FONKSİYONU ---

async def unhandled_callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Bot bir sohbet durumundayken (örn: metin beklerken) 
    basılan ve beklenmeyen tüm butonları yakalar.
    Kilitlenmeyi önler.
    """
    query = update.callback_query
    await query.answer()
    
    # Kullanıcıyı uyar
    await query.message.reply_text(
        "⚠️ **İşlem Çakışması!**\n\n"
        "Görünüşe göre bir işlemi (örn. 'Sınav Adı' girme) tamamlamadan başka bir butona bastınız.\n\n"
        "Lütfen önce o işlemi tamamlayın veya /cancel yazarak mevcut işlemi iptal edin.",
        parse_mode='Markdown'
    )
    
    # Mevcut durumda kalmaya devam et (hiçbir şeyi bozma)
    # Hangi state'te olduğunu bilmediğimiz için 'None' veya 'PASS' güvenlidir.
    return None 
# --- YENİ FONKSİYON SONU ---

# --- ADMİN FONKSİYONLARI ---
async def admin_panel_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context):
        await update.effective_message.reply_text("Bu komutu kullanma yetkiniz yok."); return
    text = (
        "👑 **Admin Paneli Komutları** 👑\n\n"
        "`/myid` - Kendi Telegram ID'nizi gösterir.\n"
        "`/backup` - Veritabanı yedeğini gönderir (Sadece Süper Admin).\n"
        "`/listusers` - Tüm kullanıcıları listeler.\n"
        "`/getuserdata <user_id|@username>` - Kullanıcı verilerini özetler.\n\n"
        "**Sadece Süper Admin:**\n"
        "`/addadmin <user_id>` - Yeni bir admin ekler.\n"
        "`/removeadmin <user_id>` - Bir admini siler.\n"
        "`/listadmins` - Tüm adminleri listeler."
    )
    await update.effective_message.reply_text(text, parse_mode='Markdown')

async def backup_database_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not is_super_admin(user_id, context):
        await update.effective_message.reply_text("Bu komutu sadece Süper Admin kullanabilir."); return
    
    await update.effective_message.reply_text(
        "Veritabanı yedeği artık Neon (PostgreSQL) bulut sunucusunda tutulmaktadır.\n\n"
        "Yedek almak için [Neon Dashboard](httpsa://console.neon.tech/app/projects) adresine gidin, "
        "projenizi seçin ve 'Backup & Restore' (Yedekle & Geri Yükle) menüsünü kullanın.",
        parse_mode='Markdown'
    )

async def add_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not is_super_admin(user_id, context):
        await update.effective_message.reply_text("Bu komutu sadece Süper Admin kullanabilir."); return
    try:
        target_id = int(context.args[0])
        if db.add_admin(target_id):
            await update.effective_message.reply_text(f"✅ {target_id} ID'li kullanıcı başarıyla admin yapıldı.")
            name = db.get_user_info_by_id(target_id)
            try:
                if name: await context.bot.send_message(chat_id=target_id, text=f"Tebrikler, {name}! Artık bir adminsiniz.")
            except BadRequest:
                await update.effective_message.reply_text(f"ℹ️ {target_id} ID'li kullanıcıya tebrik mesajı gönderilemedi (Botu başlatmamış olabilir).")
        else:
            await update.effective_message.reply_text("Kullanıcı zaten admin veya bir hata oluştu.")
    except (IndexError, ValueError):
        await update.effective_message.reply_text("Hatalı kullanım. /addadmin <user_id>")

async def remove_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not is_super_admin(user_id, context):
        await update.effective_message.reply_text("Bu komutu sadece Süper Admin kullanabilir."); return
    try:
        target_id = int(context.args[0])
        if target_id == user_id:
            await update.effective_message.reply_text("Kendinizi adminlikten çıkaramazsınız."); return
        if db.remove_admin(target_id):
            await update.effective_message.reply_text(f"✅ {target_id} ID'li kullanıcının admin yetkisi kaldırıldı.")
        else:
            await update.effective_message.reply_text("Kullanıcı admin değil veya bir hata oluştu.")
    except (IndexError, ValueError):
        await update.effective_message.reply_text("Hatalı kullanım. /removeadmin <user_id>")

async def list_admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not is_super_admin(user_id, context):
        await update.effective_message.reply_text("Bu komutu sadece Süper Admin kullanabilir."); return
    admins = db.list_admins(user_id)
    if not admins:
        await update.effective_message.reply_text("Sizden başka admin bulunmamaktadır."); return
    message = "👑 **Admin Listesi** 👑\n\n"
    for admin_id, admin_name in admins:
        message += f"- {admin_name} (ID: `{admin_id}`)\n"
    await update.effective_message.reply_text(message, parse_mode='Markdown')

async def get_user_data_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context):
        await update.effective_message.reply_text("Bu komutu kullanma yetkiniz yok."); return
    try:
        arg = context.args[0]
        user_info = None # (user_id, user_name)
        if arg.isdigit():
            target_id = int(arg)
            user_name = db.get_user_info_by_id(target_id)
            if user_name: user_info = (target_id, user_name)
        else:
            username = arg.lstrip('@')
            user_info = db.get_user_by_username(username)
        
        if not user_info:
            await update.effective_message.reply_text("Bu ID veya kullanıcı adına sahip bir kullanıcı bulunamadı."); return
        
        target_id, user_name = user_info
        message = f"👤 **Kullanıcı Veri Özeti: {user_name} (ID: {target_id})**\n\n"
        sinavlar = db.get_sinavlar(target_id)
        if not sinavlar:
            message += "Bu kullanıcının henüz eklenmiş bir verisi yok."
            await update.effective_message.reply_text(message); return
        for sinav_id, sinav_adi, s_tamamlandi in sinavlar:
            sinav_stats = an.get_sinav_overall_stats(sinav_id)
            s_icon = "✅" if s_tamamlandi else "❌"
            message += f"📘 {s_icon} **{sinav_adi}** (Genel Hakimiyet: %{sinav_stats['ortalama_hakimiyet']:.1f})\n"
            dersler = db.get_dersler(sinav_id)
            if not dersler: message += "  (Bu sınavda ders yok)\n"; continue
            for ders_id, ders_adi, d_tamamlandi in dersler:
                ders_stats = an.get_ders_overall_stats(ders_id)
                d_icon = "✅" if d_tamamlandi else "❌"
                message += f"  📖 {d_icon} *{ders_adi}* (Hakimiyet: %{ders_stats['ortalama_hakimiyet']:.1f})\n"
                konular = db.get_konular(ders_id)
                if not konular: message += "    (Bu derste konu yok)\n"; continue
                for konu_id, konu_adi, k_tamamlandi in konular:
                    konu_stats = an.calculate_konu_stats(konu_id)
                    k_icon = "✅" if k_tamamlandi else "❌"
                    message += f"    🎯 {k_icon} {konu_adi} (Hedef: %{konu_stats['hedefe_ulasma']:.1f})\n"
        
        if len(message) > 4096:
            await update.effective_message.reply_text("Hata: Kullanıcı verisi 4096 karakter sınırını aşıyor.")
        else:
            await update.effective_message.reply_text(message, parse_mode='Markdown')
            
    except (IndexError, ValueError):
        await update.effective_message.reply_text("Hatalı kullanım. /getuserdata <user_id_veya_@kullaniciadi>")

async def list_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not is_admin_user(user_id, context):
        await update.effective_message.reply_text("Bu komutu kullanma yetkiniz yok."); return
    users = db.get_all_users()
    message = "👥 **Tüm Kullanıcılar Listesi** 👥\n\n"
    for user_id, user_name, username in users:
        username_str = f"(@{username})" if username else ""
        message += f"- {user_name} {username_str} (ID: `{user_id}`)\n"
    if len(message) > 4000:
        await update.effective_message.reply_text("Kullanıcı listesi 4096 karakter sınırını aşıyor.")
    else:
        await update.effective_message.reply_text(message, parse_mode='Markdown')



