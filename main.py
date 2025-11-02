# main.py (RENDER İÇİN GÜNCELLENMİŞ NİHAİ HAL)

from telegram.ext import (
    Application, CommandHandler, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
)
import database as db
import handlers as hd
import os  # Eklendi
from flask import Flask  # Eklendi
import threading  # Eklendi

# --- Flask Web Sunucusu (Uyanık Tutma) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Aktif. Uyanık kalmak için pingleme alındı."

def run_flask():
    # Render, PORT'u çevre değişkeni olarak otomatik ayarlar
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# --- Telegram Bot Kodları ---

# Token ve ID'ler koddan kaldırıldı, Render'dan okunacak
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPER_ADMIN_ID = int(os.environ.get("SUPER_ADMIN_ID", 1981726869)) # 1981726869 varsayılan olarak ayarlandı

def main_bot() -> None:
    # Token kontrolü
    if not BOT_TOKEN:
        print("HATA: BOT_TOKEN çevre değişkeni ayarlanmamış. Lütfen Render ayarlarını kontrol edin.")
        return

    print("Veritabanı başlatılıyor..."); db.init_db(); print("Veritabanı hazır.")
    application = Application.builder().token(BOT_TOKEN).build()
    application.bot_data["SUPER_ADMIN_ID"] = SUPER_ADMIN_ID

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
        fallbacks=[CommandHandler('cancel', hd.cancel_handler)]
    )

    # --- Tüm Yöneticileri Bota Ekleme ---
    
    # Kullanıcı Komutları
    application.add_handler(CommandHandler("start", hd.start))
    application.add_handler(CommandHandler("panelim", hd.start))
    application.add_handler(CommandHandler("programim", hd.programim))
    application.add_handler(CommandHandler("gizlilik", hd.gizlilik))
    application.add_handler(CommandHandler("geribildirim", hd.geribildirim))
    application.add_handler(CommandHandler("hedefbelirle", hd.hedefbelirle))
    application.add_handler(CommandHandler("soruekle", hd.soruekle))
    application.add_handler(CommandHandler("istatistik", hd.istatistik))
    application.add_handler(CommandHandler("rutinolustur", hd.rutinolustur))
    application.add_handler(CommandHandler("myid", hd.my_id))
    
    # Admin Komutları
    application.add_handler(CommandHandler("admin", hd.admin_panel_help))
    application.add_handler(CommandHandler("addadmin", hd.add_admin_command))
    application.add_handler(CommandHandler("removeadmin", hd.remove_admin_command))
    application.add_handler(CommandHandler("listadmins", hd.list_admins_command))
    application.add_handler(CommandHandler("getuserdata", hd.get_user_data_command))
    application.add_handler(CommandHandler("listusers", hd.list_users_command))
    application.add_handler(CommandHandler("backup", hd.backup_database_command))
    
    # Sohbet ve Buton Yöneticileri
    application.add_handler(master_conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, hd.greet_and_start))
    application.add_handler(CallbackQueryHandler(hd.navigation_button_handler))

    print("Bot çalışmaya başlıyor..."); application.run_polling()

if __name__ == '__main__':
    # Flask'ı ayrı bir thread'de (iş parçacığı) çalıştır
    print("Web sunucusu başlatılıyor...")
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    # Botu ana ana thread'de çalıştır
    main_bot()
