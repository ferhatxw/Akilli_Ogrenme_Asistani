# main.py (HANDLER ÇAKIŞMASI DÜZELTİLMİŞ NİHAİ HAL)

from telegram.ext import (
    Application, CommandHandler, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
)
import database as db
import handlers as hd
import os
from flask import Flask
import threading

# --- Flask Web Sunucusu (Uyanık Tutma) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Aktif. Uyanık kalmak için pingleme alındı."

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# --- Telegram Bot Kodları ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPER_ADMIN_ID = int(os.environ.get("SUPER_ADMIN_ID", 1981726869))
DATABASE_URL = os.environ.get("DATABASE_URL") # Bu satırı (eğer yoksa) ekleyin

def main_bot() -> None:
    if not BOT_TOKEN:
        print("HATA: BOT_TOKEN çevre değişkeni ayarlanmamış.")
        return
    if not DATABASE_URL:
        print("HATA: DATABASE_URL çevre değişkeni ayarlanmamış.")
        return

    print("Veritabanı başlatılıyor..."); db.init_db(); print("Veritabanı hazır.")
    application = Application.builder().token(BOT_TOKEN).build()
    application.bot_data["SUPER_ADMIN_ID"] = SUPER_ADMIN_ID

    # --- GÜNCELLENMİŞ MASTER CONVERSATION HANDLER ---
    # Artık 'fallbacks' (kaçış yolları) içeriyor.
    # Bu sayede kullanıcı bir sınav adı girerken "Panelim" tuşuna basarsa
    # bot kilitlenmek yerine ana menüye döner.
    master_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(hd.conversation_entry_handler, pattern='^add_'),
            CallbackQueryHandler(hd.conversation_entry_handler, pattern='^edit_'),
            CallbackQueryHandler(hd.conversation_entry_handler, pattern='^set_hedef_'),
            CallbackQueryHandler(hd.conversation_entry_handler, pattern='^program_add_rituel$'),
            CallbackQueryHandler(hd.conversation_entry_handler, pattern='^program_add_gunnot_')
        ],
        states={
            hd.GET_SINAV_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, hd.get_sinav_name_handler)],
            hd.GET_DERS_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, hd.get_ders_name_handler)],
            hd.GET_KONU_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, hd.get_konu_name_handler)],
            hd.EDIT_SINAV_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, hd.get_new_sinav_name_handler)],
            hd.EDIT_DERS_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, hd.get_new_ders_name_handler)],
            hd.EDIT_KONU_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, hd.get_new_konu_name_handler)],
            hd.GET_NOTE_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, hd.get_note_content_handler)],
            hd.GET_ADD_DOGRU: [MessageHandler(filters.TEXT & ~filters.COMMAND, hd.get_add_dogru_handler)],
            hd.GET_ADD_YANLIS: [MessageHandler(filters.TEXT & ~filters.COMMAND, hd.get_add_yanlis_handler)],
            hd.GET_ADD_BOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, hd.get_add_bos_handler)],
            hd.GET_EDIT_DOGRU: [MessageHandler(filters.TEXT & ~filters.COMMAND, hd.get_edit_dogru_handler)],
            hd.GET_EDIT_YANLIS: [MessageHandler(filters.TEXT & ~filters.COMMAND, hd.get_edit_yanlis_handler)],
            hd.GET_EDIT_BOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, hd.get_edit_bos_handler)],
            hd.GET_HEDEF: [MessageHandler(filters.TEXT & ~filters.COMMAND, hd.get_hedef_handler)],
            hd.GET_RITUEL_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, hd.get_rituel_content_handler)],
            hd.GET_GUN_NOT_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, hd.get_gun_not_content_handler)],
        },
        fallbacks=[
            CommandHandler('cancel', hd.cancel_handler),
            CommandHandler('start', hd.cancel_handler), # /start komutu da sohbeti iptal eder
            CommandHandler('panelim', hd.cancel_handler), # /panelim komutu da iptal eder
            MessageHandler(filters.Regex('^(📚 Panelim)$'), hd.cancel_handler), # 'Panelim' tuşu da iptal eder
            CommandHandler('programim', hd.cancel_and_programim), # /programim komutu programı açar
            MessageHandler(filters.Regex('^(🗓️ Programım)$'), hd.cancel_and_programim) # 'Programım' tuşu da programı açar
        ]
    )

    # --- HANDLER GRUPLARI (ÇAKIŞMAYI ÖNLEYEN ANA DÜZELTME) ---
    
    # GRUP 0: Sohbet Yöneticisi (En Yüksek Öncelik)
    # Bot önce bir sohbetin içinde mi diye bakar
    application.add_handler(master_conv_handler, group=0)

    # GRUP 1: Diğer Tüm Komutlar (İkinci Öncelik)
    # Bot bir sohbetin içinde değilse bunlara bakar
    
    # Kullanıcı Komutları
    application.add_handler(CommandHandler("start", hd.start), group=1)
    application.add_handler(CommandHandler("panelim", hd.start), group=1)
    application.add_handler(CommandHandler("programim", hd.programim), group=1)
    application.add_handler(CommandHandler("gizlilik", hd.gizlilik), group=1)
    application.add_handler(CommandHandler("geribildirim", hd.geribildirim), group=1)
    application.add_handler(CommandHandler("hedefbelirle", hd.hedefbelirle), group=1)
    application.add_handler(CommandHandler("soruekle", hd.soruekle), group=1)
    application.add_handler(CommandHandler("istatistik", hd.istatistik), group=1)
    application.add_handler(CommandHandler("rutinolustur", hd.rutinolustur), group=1)
    application.add_handler(CommandHandler("myid", hd.my_id), group=1)
    
    # Admin Komutları
    application.add_handler(CommandHandler("admin", hd.admin_panel_help), group=1)
    application.add_handler(CommandHandler("addadmin", hd.add_admin_command), group=1)
    application.add_handler(CommandHandler("removeadmin", hd.remove_admin_command), group=1)
    application.add_handler(CommandHandler("listadmins", hd.list_admins_command), group=1)
    application.add_handler(CommandHandler("getuserdata", hd.get_user_data_command), group=1)
    application.add_handler(CommandHandler("listusers", hd.list_users_command), group=1)
    application.add_handler(CommandHandler("backup", hd.backup_database_command), group=1)
    
    # Kalan Sohbet ve Buton Yöneticileri
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, hd.greet_and_start), group=1)
    application.add_handler(CallbackQueryHandler(hd.navigation_button_handler), group=1)

    print("Bot çalışmaya başlıyor..."); application.run_polling()

if __name__ == '__main__':
    print("Web sunucusu başlatılıyor...")
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    main_bot()
