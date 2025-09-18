from flask import Flask, render_template, request
app = Flask(__name__)

SINAVLAR_VE_KATSAYILARI = [
    ("wr1_not", 5), ("re1_not", 9), ("ls1_not", 9), ("lu1_not", 8),
    ("wr2_not", 5), ("sp1_not", 7), ("on_not", 4), ("st_not", 6), ("re2_not", 9), ("ls2_not", 9),
    ("lu2_not", 8), ("wr3_not", 9), ("sp2_not", 12)
]

HEDEF_ORTALAMA = 70.0  # Geçmek için gereken hedef ortalama

@app.route('/')
def index():
    return render_template('index.html', hedef_ortalama=HEDEF_ORTALAMA, girilen_notlar={})

@app.route('/reset', methods=['POST'])
def reset():
    # Temizle butonuna basıldığında formu sıfırlar.
    return render_template('index.html', hedef_ortalama=HEDEF_ORTALAMA, girilen_notlar={}, hatalar=[], sonuc_mesaji="", kalan_ders_bilgisi="")

@app.route('/hesapla', methods=['POST'])
def hesapla():
    mevcut_toplam_puan_carpi_katsayi = 0
    mevcut_toplam_katsayi = 0
    kalan_derslerin_toplam_katsayisi = 0
    kalan_ders_sayisi = 0
    kalan_ders_isimleri = []

    hatalar = []
    girilen_notlar_form_icin = {}

    toplam_tum_katsayilar = sum(k for _, k in SINAVLAR_VE_KATSAYILARI)

    for sinav_adi_key, katsayi in SINAVLAR_VE_KATSAYILARI:
        not_str = request.form.get(sinav_adi_key)
        girilen_notlar_form_icin[sinav_adi_key] = not_str if not_str is not None else ""
        okunabilir_sinav_adi = sinav_adi_key.replace("_not", "").upper()

        if not_str and not_str.strip():
            try:
                not_value = float(not_str)
                if 0 <= not_value <= 100:
                    mevcut_toplam_puan_carpi_katsayi += not_value * katsayi
                    mevcut_toplam_katsayi += katsayi
                else:
                    hatalar.append(f"{okunabilir_sinav_adi} için girilen not ({not_value}) 0-100 arasında olmalıdır.")
            except ValueError:
                hatalar.append(f"{okunabilir_sinav_adi} için girilen değer ('{not_str}') geçerli bir sayı değil.")
        else:
            kalan_derslerin_toplam_katsayisi += katsayi
            kalan_ders_sayisi += 1
            kalan_ders_isimleri.append(okunabilir_sinav_adi)

    if hatalar:
        # Hatalar varsa, diğer mesajları boş gönderelim ki HTML'de görünmesinler
        return render_template('index.html',
                               hatalar=hatalar,
                               girilen_notlar=girilen_notlar_form_icin,
                               hedef_ortalama=HEDEF_ORTALAMA,
                               sonuc_mesaji="",
                               kalan_ders_bilgisi="")

    # --- Hesaplama İşlemi ---
    sonuc_mesaji = ""
    kalan_ders_bilgisi = ""

    if kalan_ders_sayisi == 0: # Tüm derslerin notu girilmişse
        if mevcut_toplam_katsayi > 0:
            ortalama = mevcut_toplam_puan_carpi_katsayi / mevcut_toplam_katsayi
            sonuc_mesaji = f"Mevcut ortalamanız: {ortalama:.2f}. "
            if ortalama >= HEDEF_ORTALAMA:
                sonuc_mesaji += "Tebrikler, kuru geçtiniz!"
            else:
                sonuc_mesaji += f"Maalesef, kuru geçmek için {HEDEF_ORTALAMA:.2f} ortalama gerekiyordu."
        # Eğer mevcut_toplam_katsayi == 0 ise (yani tüm notlar girilmiş ama hepsi geçersizse veya katsayıları 0 ise - ki bu olmaz)
        # bu durum yukarıdaki 'if hatalar:' bloğunda zaten yakalanmış olur.
        # Ya da hiç not girilmemişse, o da aşağıdaki 'Lütfen en az bir not giriniz' ile yakalanır.

    else: # Eğer girilmemiş dersler varsa
        hedeflenen_toplam_puan_carpi_katsayi = HEDEF_ORTALAMA * toplam_tum_katsayilar
        kalan_derslerden_gereken_puan_carpi_katsayi = hedeflenen_toplam_puan_carpi_katsayi - mevcut_toplam_puan_carpi_katsayi

        if kalan_derslerin_toplam_katsayisi > 0:
            kalan_derslerden_gereken_ortalama_not = kalan_derslerden_gereken_puan_carpi_katsayi / kalan_derslerin_toplam_katsayisi
            kalan_ders_listesi_str = ", ".join(kalan_ders_isimleri)
            kalan_ders_bilgisi = f"Kalan {kalan_ders_sayisi} dersiniz ({kalan_ders_listesi_str}) için; "

            if kalan_derslerden_gereken_ortalama_not > 100:
                kalan_ders_bilgisi += f"maalesef {HEDEF_ORTALAMA:.2f} ortalamasına ulaşmanız artık mümkün değil (kalan derslerden ortalama {kalan_derslerden_gereken_ortalama_not:.2f} almanız gerekiyor)."
            elif kalan_derslerden_gereken_ortalama_not < 0:
                kalan_ders_bilgisi += f"{HEDEF_ORTALAMA:.2f} ortalamasına ulaşmak için ek puana ihtiyacınız yok, hatta 0 alsanız bile geçiyorsunuz. Mevcut durumunuz iyi!"
                if mevcut_toplam_katsayi > 0:
                     mevcut_ortalama_sadece_girilenler = mevcut_toplam_puan_carpi_katsayi / mevcut_toplam_katsayi
                     kalan_ders_bilgisi += f" (Sadece girilen derslerinizin ortalaması: {mevcut_ortalama_sadece_girilenler:.2f})"
            else: # 0 <= gereken_not <= 100 durumu
                kalan_ders_bilgisi += f"{HEDEF_ORTALAMA:.2f} ortalamasına ulaşmak için her birinden ortalama en az {kalan_derslerden_gereken_ortalama_not:.2f} almanız gerekmektedir."
        else:
            kalan_ders_bilgisi = "Hesaplama için kalan ders katsayısı bulunamadı."

    # Eğer hiç not girilmemişse (tüm inputlar boşsa) özel bir hata mesajı verelim.
    # `kalan_ders_sayisi == len(SINAVLAR_VE_KATSAYILARI)` tüm derslerin boş bırakıldığını gösterir.
    
    all_inputs_empty_or_whitespace = True
    for value in girilen_notlar_form_icin.values():
        if value and value.strip(): # Eğer değer var ve sadece boşluk değilse
            all_inputs_empty_or_whitespace = False
            break
            
    if all_inputs_empty_or_whitespace and not hatalar: # Eğer başka hata yoksa ve tüm alanlar boşsa
        hatalar.append("Lütfen en az bir not giriniz.")
        return render_template('index.html',
                               hatalar=hatalar,
                               girilen_notlar=girilen_notlar_form_icin,
                               hedef_ortalama=HEDEF_ORTALAMA,
                               sonuc_mesaji="",
                               kalan_ders_bilgisi="")

    return render_template('index.html',
                           sonuc_mesaji=sonuc_mesaji,
                           kalan_ders_bilgisi=kalan_ders_bilgisi,
                           girilen_notlar=girilen_notlar_form_icin,
                           hedef_ortalama=HEDEF_ORTALAMA,
                           hatalar=hatalar) 

if __name__ == '__main__':
    app.run(debug=True)