# analysis.py (PROJENİN BİTMİŞ NİHAİ HALİ)

import database as db

def calculate_konu_stats(konu_id: int):
    stats = db.get_soru_istatistik(konu_id); hedef, dogru, yanlis, bos = stats
    toplam_cozulen = dogru + yanlis + bos
    hakimiyet = (dogru / toplam_cozulen * 100) if toplam_cozulen > 0 else 0.0
    hedefe_ulasma = (toplam_cozulen / hedef * 100) if hedef > 0 else 0.0
    score = (hakimiyet * 0.6) + (min(hedefe_ulasma, 100) * 0.4)
    return {"hakimiyet": hakimiyet, "hedefe_ulasma": hedefe_ulasma, "toplam_cozulen": toplam_cozulen, "score": score}

def get_ders_overall_stats(ders_id: int):
    konular = db.get_konular(ders_id)
    if not konular: return {"ortalama_hakimiyet": 0.0, "konu_sayisi": 0}
    
    total_hakimiyet = 0
    konu_sayisi_with_data = 0
    
    for konu_id, konu_adi, _ in konular:
        konu_stats = calculate_konu_stats(konu_id)
        if konu_stats['toplam_cozulen'] > 0:
            total_hakimiyet += konu_stats['hakimiyet']
            konu_sayisi_with_data += 1
            
    ortalama_hakimiyet = total_hakimiyet / konu_sayisi_with_data if konu_sayisi_with_data > 0 else 0.0
    
    return {"ortalama_hakimiyet": ortalama_hakimiyet, "konu_sayisi": len(konular)}

def get_sinav_overall_stats(sinav_id: int):
    dersler = db.get_dersler(sinav_id)
    if not dersler: return {"ortalama_hakimiyet": 0.0, "ders_sayisi": 0, "konu_sayisi": 0}
    
    total_hakimiyet_sum = 0
    total_konu_sayisi_with_data = 0
    toplam_ders_konu_sayisi = 0

    for ders_id, ders_adi, _ in dersler:
        ders_stats = get_ders_overall_stats(ders_id)
        konular = db.get_konular(ders_id)
        ders_konu_sayisi_with_data = 0
        for konu_id, _, _ in konular:
            if calculate_konu_stats(konu_id)['toplam_cozulen'] > 0:
                ders_konu_sayisi_with_data += 1
                
        if ders_konu_sayisi_with_data > 0:
            total_hakimiyet_sum += ders_stats['ortalama_hakimiyet'] * ders_konu_sayisi_with_data
            total_konu_sayisi_with_data += ders_konu_sayisi_with_data

        toplam_ders_konu_sayisi += ders_stats['konu_sayisi']
            
    ortalama_hakimiyet = total_hakimiyet_sum / total_konu_sayisi_with_data if total_konu_sayisi_with_data > 0 else 0.0
    
    return {"ortalama_hakimiyet": ortalama_hakimiyet, "ders_sayisi": len(dersler), "konu_sayisi": toplam_ders_konu_sayisi}

def generate_routine(user_id: int):
    sinavlar = db.get_sinavlar(user_id); all_konular = []
    for sinav_id, sinav_adi, _ in sinavlar:
        dersler = db.get_dersler(sinav_id)
        for ders_id, ders_adi, tamamlandi in dersler:
            if not tamamlandi:
                konular = db.get_konular(ders_id)
                for konu_id, konu_adi, konu_tamamlandi in konular:
                    if not konu_tamamlandi:
                        stats = calculate_konu_stats(konu_id)
                        if stats['score'] < 99: all_konular.append({"ders_id": ders_id, "ders_adi": ders_adi, "sinav_adi": sinav_adi, "score": stats['score']})
    
    if not all_konular: return "Tebrikler! Tamamlanmamış ve zayıf olduğun bir konu bulunamadı.", []
    
    sorted_konular = sorted(all_konular, key=lambda k: k['score'])
    
    ders_listesi = []
    for konu in sorted_konular:
        ders_temsili = (konu['sinav_adi'], konu['ders_adi'])
        if ders_temsili not in ders_listesi:
            ders_listesi.append(ders_temsili)

    message = "🧠 **Akıllı Program Tavsiyesi** 🧠\n\nAnalizlerine göre en zayıf olduğun konuların ait olduğu dersler şunlar:\n\n"
    for i, (sinav_adi, ders_adi) in enumerate(ders_listesi[:3]):
        message += f"**{i+1}. Öncelik:** {sinav_adi} - {ders_adi}\n"

    return message, ders_listesi
