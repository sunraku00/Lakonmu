import pymupdf
import os
import re
import datetime
from typing import Dict, Any, Optional

BULAN_MAP = {
    "januari": "01", "jan": "01", "februari": "02", "feb": "02",
    "maret": "03", "mar": "03", "april": "04", "apr": "04",
    "mei": "05", "juni": "06", "jun": "06", "juli": "07", "jul": "07",
    "agustus": "08", "agu": "08", "agt": "08", "september": "09", "sep": "09",
    "oktober": "10", "okt": "10", "november": "11", "nov": "11",
    "desember": "12", "des": "12"
}

def parse_date_digits(d_str: Any) -> Optional[str]:
    """Parse date string into DD-MM-YYYY using pure numeric digits."""
    if not d_str:
        return None
    m = re.search(r"\b(\d{1,2})[\s/-]([0-1]?\d|[a-zA-Z]+)[\s/-](\d{4})\b", str(d_str))
    if m:
        day = f"{int(m.group(1)):02d}"
        raw_m = m.group(2).lower()
        mon = BULAN_MAP.get(raw_m, f"{int(raw_m):02d}" if raw_m.isdigit() else raw_m)
        year = m.group(3)
        return f"{day}-{mon}-{year}"
    return None

def build_pdf_filename(data: Dict[str, Any]) -> str:
    """
    Format nama file PDF unduhan:
    [tgl-bulan-tahun (angka)] - [NAMA YANG DIAJUKAN].pdf
    - Kelahiran : Tanggal Lahir & Nama Bayi
    - Kematian  : Tanggal Kematian & Nama Jenazah
    - Lahir Mati: Tanggal Peristiwa & Nama Bayi / Subjek
    """
    jenis = str(data.get("jenis_pelaporan", "Kelahiran")).strip().lower()
    kel = data.get("kelahiran", {}) or {}
    kem = data.get("kematian", {}) or {}
    lm = data.get("lahir_mati", {}) or {}
    subjek = data.get("subjek_akta", {}) or {}
    ibu = data.get("ibu", {}) or {}
    pelapor = data.get("pelapor", {}) or {}

    date_str = None
    name_str = None

    if "mati" in jenis and "lahir" in jenis:
        # Lahir Mati: Nama Subjek / Bayi Ny Ibu
        name_str = subjek.get("nama") or kel.get("nama_bayi") or (f"BAYI NY {ibu.get('nama')}" if ibu.get('nama') else None) or pelapor.get("nama") or "BAYI LAHIR MATI"
        date_str = parse_date_digits(lm.get("tanggal")) or parse_date_digits(kel.get("tanggal_lengkap"))
        if not date_str and (lm.get("thn") or kel.get("thn_lahir")):
            d_val = lm.get("tgl") or kel.get("tgl_lahir", 1)
            d = f"{int(d_val):02d}"
            m_val = str(lm.get("bln") or kel.get("bln_lahir", "01")).lower()
            m = BULAN_MAP.get(m_val, f"{int(m_val):02d}" if m_val.isdigit() else "01")
            y = lm.get("thn") or kel.get("thn_lahir")
            date_str = f"{d}-{m}-{y}"
    elif "mati" in jenis or "kematian" in jenis:
        # Kematian: Nama Jenazah
        name_str = kem.get("nama_lengkap") or subjek.get("nama") or "ALMARHUM"
        date_str = parse_date_digits(kem.get("tanggal_kematian"))
        if not date_str and (kem.get("tgl_kematian") or kem.get("bln_kematian")):
            d_val = kem.get("tgl_kematian", 1)
            d = f"{int(d_val):02d}"
            raw_m = str(kem.get("bln_kematian", "")).lower()
            m = BULAN_MAP.get(raw_m, f"{int(raw_m):02d}" if raw_m.isdigit() else "01")
            y = kem.get("thn_kematian", datetime.datetime.now().year)
            date_str = f"{d}-{m}-{y}"
    else:
        # Kelahiran: Nama Bayi
        name_str = kel.get("nama_bayi") or subjek.get("nama") or "BAYI"
        date_str = parse_date_digits(kel.get("tanggal_lengkap"))
        if not date_str and (kel.get("tgl_lahir") or kel.get("bln_lahir")):
            d_val = kel.get("tgl_lahir", 1)
            d = f"{int(d_val):02d}"
            raw_m = str(kel.get("bln_lahir", "")).lower()
            m = BULAN_MAP.get(raw_m, f"{int(raw_m):02d}" if raw_m.isdigit() else "01")
            y = kel.get("thn_lahir", datetime.datetime.now().year)
            date_str = f"{d}-{m}-{y}"

    if not date_str:
        date_str = parse_date_digits(data.get("tanggal_lapor_tgl")) or parse_date_digits(data.get("tanggal_lapor_tempat"))
    if not date_str:
        now = datetime.datetime.now()
        date_str = now.strftime("%d-%m-%Y")

    clean_name = re.sub(r'[/\\:*?"<>|]+', '', str(name_str).strip()).strip()
    clean_name = re.sub(r'\s+', ' ', clean_name).upper()
    if not clean_name:
        clean_name = "SUBJEK"

    return f"{date_str} - {clean_name}.pdf"

def mark_choice(page, x0: float, y0: float, color=(0.05, 0.15, 0.5)):
    """
    Menggambar tanda centang (checkmark) presisi di atas angka pilihan (misal '1.', '2.', dll.)
    pada template formulir baru tanpa menabrak kata di sebelahnya.
    x0, y0 adalah koordinat bounding box kiri-atas digit angka pilihan.
    """
    y1 = y0 + 9.5
    page.draw_line(pymupdf.Point(x0 - 0.5, y1 - 4.5), pymupdf.Point(x0 + 2.5, y1 - 1.5), color=color, width=1.4)
    page.draw_line(pymupdf.Point(x0 + 2.5, y1 - 1.5), pymupdf.Point(x0 + 7.0, y1 - 8.5), color=color, width=1.4)

def write_text(page, x: float, y: float, val: Any, max_len: int = 40, upper: bool = False, color=(0.05, 0.15, 0.5)):
    """
    Memasukkan teks dengan auto-scaling ukuran font agar teks panjang tidak keluar batas atau menabrak garis.
    y adalah baseline teks.
    """
    if val is None or str(val).strip() == "":
        return
    text = str(val).splitlines()[0].strip()
    if upper:
        text = text.upper()
    
    font_size = 8.5
    if len(text) > 48:
        font_size = 6.8
    elif len(text) > 36:
        font_size = 7.5
    
    page.insert_text((x, y), text, fontsize=font_size, fontname="helv", color=color)

def write_footer(page, y_date: float, y_pelapor: float, data: Dict[str, Any], wilayah: Dict[str, Any], pelapor: Dict[str, Any], ayah: Dict[str, Any] = None, ibu: Dict[str, Any] = None, text_color=(0.05, 0.15, 0.5)):
    """
    Menuliskan Tempat, Tanggal dan Nama Pelapor di bagian tanda tangan bawah.
    Pada template baru, koma (',') sudah tercetak di x = 421.9, sehingga:
    - Nama Tempat ditulis di sebelah kiri koma (berakhir sebelum x=418.0)
    - Tanggal ditulis di sebelah kanan koma (mulai x=428.0)
    - Nama Pelapor diletakkan di tengah tanda kurung (x = 358.3 s/d 491.8)
    """
    font = pymupdf.Font("helv")
    
    tempat = ""
    tgl = ""
    if data.get("tanggal_lapor_tempat"):
        full = data["tanggal_lapor_tempat"]
        if "," in full:
            parts = full.split(",", 1)
            tempat = parts[0].strip()
            tgl = parts[1].strip()
        else:
            tempat = full.strip()
    
    if not tempat or tempat.lower() in ["kelahiran", "kematian", "lahir mati"]:
        raw_tempat = wilayah.get("kabupaten_kota", "") or wilayah.get("kecamatan", "") or "Kota"
        tempat = raw_tempat.replace("KABUPATEN ", "").replace("KOTA ", "").strip().title()
        if not tempat or tempat.lower() in ["kelahiran", "kematian", "lahir mati"]:
            tempat = "Kota"
    
    if not tgl:
        tgl = data.get("tanggal_lapor_tgl", "")
    
    if tempat:
        w_tempat = font.text_length(tempat, fontsize=8.0)
        x_tempat = 418.0 - w_tempat
        page.insert_text((x_tempat, y_date), tempat, fontsize=8.0, fontname="helv", color=text_color)
    
    if tgl:
        page.insert_text((428.0, y_date), tgl, fontsize=8.0, fontname="helv", color=text_color)

    nama_pelapor = pelapor.get("nama") or (ayah.get("nama") if ayah else None) or (ibu.get("nama") if ibu else None) or "........................"
    w_pel = font.text_length(nama_pelapor.upper(), fontsize=8.5)
    x_pel = max(358.0, 425.0 - (w_pel / 2.0))
    write_text(page, x_pel, y_pelapor, nama_pelapor, upper=True, color=text_color)

def fill_f201a_pdf(template_path: str, data: Dict[str, Any], single_page: bool = True) -> bytes:
    """
    Mengisi data terstruktur ke dalam template resmi Formulir F-2.01 A (Versi Bersih Tanpa Border Garis).
    Mendukung 3 Peristiwa:
    - Kelahiran   -> Halaman 0
    - Lahir Mati  -> Halaman 1
    - Kematian    -> Halaman 2
    """
    doc = pymupdf.open(template_path)
    
    jenis_pelaporan = str(data.get("jenis_pelaporan", "Kelahiran")).strip().lower()

    if "mati" in jenis_pelaporan and "lahir" in jenis_pelaporan:
        target_page_idx = 1
    elif "mati" in jenis_pelaporan or "kematian" in jenis_pelaporan:
        target_page_idx = 2
    else:
        target_page_idx = 0

    page = doc[target_page_idx]
    text_color = (0.05, 0.15, 0.5) # Dark navy blue

    wilayah = data.get("wilayah", {})
    pelapor = data.get("pelapor", {})
    subjek = data.get("subjek_akta", {})
    ayah = data.get("ayah", {})
    ibu = data.get("ibu", {})
    saksi1 = data.get("saksi_1", {})
    saksi2 = data.get("saksi_2", {})
    kelahiran = data.get("kelahiran", {})
    kematian = data.get("kematian", {})
    lahir_mati = data.get("lahir_mati", {})

    # =========================================================================
    # 1. KOP WILAYAH (Titik Dua pada x = 132.6, Teks Mulai x = 142.0)
    # =========================================================================
    write_text(page, 142.0, 42.0, wilayah.get("provinsi"), upper=True, color=text_color)
    write_text(page, 142.0, 54.8, wilayah.get("kabupaten_kota"), upper=True, color=text_color)
    write_text(page, 142.0, 67.5, wilayah.get("kecamatan"), upper=True, color=text_color)
    write_text(page, 142.0, 80.2, wilayah.get("desa_kelurahan"), upper=True, color=text_color)
    write_text(page, 142.0, 93.0, wilayah.get("kode_wilayah"), upper=True, color=text_color)

    # =========================================================================
    # 2. DATA PELAPOR (Titik Dua pada x = 189.3, Teks Mulai x = 198.0)
    # =========================================================================
    write_text(page, 198.0, 150.8, pelapor.get("nama"), upper=True, color=text_color)
    write_text(page, 198.0, 163.5, pelapor.get("nik"), color=text_color)
    write_text(page, 198.0, 176.2, pelapor.get("nomor_paspor") or "-", color=text_color)
    write_text(page, 198.0, 189.0, pelapor.get("nomor_kk"), color=text_color)
    write_text(page, 198.0, 201.8, pelapor.get("kewarganegaraan") or "WNI", upper=True, color=text_color)

    # =========================================================================
    # 3. DATA SUBJEK AKTA (Titik Dua pada x = 189.3, Teks Mulai x = 198.0)
    # =========================================================================
    if target_page_idx == 0:
        nama_subjek = subjek.get("nama") or kelahiran.get("nama_bayi")
        nik_subjek = subjek.get("nik") or "-"
    elif target_page_idx == 2:
        nama_subjek = subjek.get("nama") or kematian.get("nama_lengkap")
        nik_subjek = subjek.get("nik") or kematian.get("nik") or "-"
    else:
        nama_subjek = subjek.get("nama") or "-"
        nik_subjek = subjek.get("nik") or "-"

    write_text(page, 198.0, 230.2, nama_subjek, upper=True, color=text_color)
    write_text(page, 198.0, 243.0, nik_subjek, color=text_color)
    write_text(page, 198.0, 255.8, subjek.get("nomor_paspor") or "-", color=text_color)
    
    kk_subjek = subjek.get("nomor_kk") or pelapor.get("nomor_kk")
    write_text(page, 198.0, 268.5, kk_subjek, color=text_color)
    write_text(page, 198.0, 281.2, subjek.get("kewarganegaraan") or "WNI", upper=True, color=text_color)

    # =========================================================================
    # 4. DATA ORANG TUA (Titik Dua pada x = 189.3, Teks Mulai x = 198.0)
    # =========================================================================
    # Ayah
    write_text(page, 198.0, 309.0, ayah.get("nama"), upper=True, color=text_color)
    write_text(page, 198.0, 321.8, ayah.get("nik"), color=text_color)
    write_text(page, 198.0, 334.5, ayah.get("tempat_lahir"), upper=True, color=text_color)
    
    tgl_ayah = ayah.get("tanggal_lahir")
    if not tgl_ayah and ayah.get("tgl"):
        tgl_ayah = f"{ayah.get('tgl', '')}-{ayah.get('bln', '')}-{ayah.get('thn', '')}".strip("-")
    write_text(page, 198.0, 347.2, tgl_ayah, color=text_color)
    write_text(page, 198.0, 360.0, ayah.get("kewarganegaraan") or "WNI", upper=True, color=text_color)

    # Ibu
    write_text(page, 198.0, 372.8, ibu.get("nama"), upper=True, color=text_color)
    write_text(page, 198.0, 385.5, ibu.get("nik"), color=text_color)
    write_text(page, 198.0, 398.2, ibu.get("tempat_lahir"), upper=True, color=text_color)
    
    tgl_ibu = ibu.get("tanggal_lahir")
    if not tgl_ibu and ibu.get("tgl"):
        tgl_ibu = f"{ibu.get('tgl', '')}-{ibu.get('bln', '')}-{ibu.get('thn', '')}".strip("-")
    write_text(page, 198.0, 411.0, tgl_ibu, color=text_color)
    write_text(page, 198.0, 423.8, ibu.get("kewarganegaraan") or "WNI", upper=True, color=text_color)

    # =========================================================================
    # 5. DATA SAKSI I (Titik Dua pada x = 189.3, Teks Mulai x = 198.0)
    # =========================================================================
    write_text(page, 198.0, 452.2, saksi1.get("nama"), upper=True, color=text_color)
    write_text(page, 198.0, 465.0, saksi1.get("nik"), color=text_color)
    write_text(page, 198.0, 477.8, saksi1.get("nomor_kk"), color=text_color)
    write_text(page, 198.0, 490.5, saksi1.get("kewarganegaraan") or "WNI", upper=True, color=text_color)

    # =========================================================================
    # 6. DATA SAKSI II (Titik Dua pada x = 189.3, Teks Mulai x = 198.0)
    # =========================================================================
    write_text(page, 198.0, 518.2, saksi2.get("nama"), upper=True, color=text_color)
    write_text(page, 198.0, 531.0, saksi2.get("nik"), color=text_color)
    write_text(page, 198.0, 543.8, saksi2.get("nomor_kk"), color=text_color)
    write_text(page, 198.0, 556.5, saksi2.get("kewarganegaraan") or "WNI", upper=True, color=text_color)

    # =========================================================================
    # 7. PERISTIWA KHUSUS
    # =========================================================================

    # -------------------------------------------------------------------------
    # A. KELAHIRAN (Halaman 0)
    # -------------------------------------------------------------------------
    if target_page_idx == 0:
        # 1. Nama Bayi
        write_text(page, 198.0, 584.2, kelahiran.get("nama_bayi"), upper=True, color=text_color)

        # 2. Jenis Kelamin: 1. Laki-Laki (194.2), 2. Perempuan (247.7)
        jk = str(kelahiran.get("jenis_kelamin", "")).lower()
        if "perempuan" in jk or jk == "2" or jk.startswith("p"):
            mark_choice(page, 247.7, 589.0, color=text_color)
        else:
            mark_choice(page, 194.2, 589.0, color=text_color)

        # 3. Tempat Dilahirkan: 1. RS/RB (194.2), 2. Puskesmas (236.6), 3. Polindes (293.8), 4. Rumah (342.0), 5. Lainnya (384.9)
        td = str(kelahiran.get("tempat_dilahirkan", "")).lower()
        faskes = kelahiran.get("nama_faskes", "")
        if "puskesmas" in td or td == "2":
            mark_choice(page, 236.6, 601.8, color=text_color)
        elif "polindes" in td or "pustu" in td or td == "3":
            mark_choice(page, 293.8, 601.8, color=text_color)
        elif "rumah" in td or td == "4":
            mark_choice(page, 342.0, 601.8, color=text_color)
        elif "lain" in td or td == "5":
            mark_choice(page, 384.9, 601.8, color=text_color)
        else:
            mark_choice(page, 194.2, 601.8, color=text_color)
        
        if faskes:
            page.insert_text((435.0, 609.0), str(faskes)[:30], fontsize=7.2, fontname="helv", color=text_color)

        # 4. Tempat Kelahiran (Kabupaten/Kota)
        tmpt_lahir = kelahiran.get("tempat_kelahiran") or wilayah.get("kabupaten_kota", "")
        write_text(page, 198.0, 621.8, tmpt_lahir, upper=True, color=text_color)

        # 5. Hari dan Tanggal Lahir
        hari = kelahiran.get("hari_lahir", "")
        if hari:
            page.insert_text((218.0, 634.5), str(hari).capitalize() + ",", fontsize=8.5, fontname="helv", color=text_color)

        tgl_lahir_str = kelahiran.get("tanggal_lengkap")
        if not tgl_lahir_str and (kelahiran.get("tgl_lahir") or kelahiran.get("bln_lahir")):
            tgl_lahir_str = f"{kelahiran.get('tgl_lahir', '')} {kelahiran.get('bln_lahir', '')} {kelahiran.get('thn_lahir', '')}".strip()
        if tgl_lahir_str:
            page.insert_text((298.0, 634.5), str(tgl_lahir_str), fontsize=8.5, fontname="helv", color=text_color)

        # 6. Pukul (Jam : Menit)
        jam = kelahiran.get("pukul_jam", "")
        menit = kelahiran.get("pukul_menit", "")
        if jam or menit:
            page.insert_text((198.0, 647.2), str(jam or "00"), fontsize=8.5, fontname="helv", color=text_color)
            page.insert_text((228.0, 647.2), f"{menit or '00'} WIB", fontsize=8.5, fontname="helv", color=text_color)

        # 7. Jenis Kelahiran: 1. Tunggal (194.2), 2. Kembar 2 (240.9), 3. Kembar 3 (294.0), 4. Kembar 4 (347.2), 5. Lainnya (400.4)
        jk_lahir = str(kelahiran.get("jenis_kelahiran", "")).lower()
        if "kembar 2" in jk_lahir or jk_lahir == "2":
            mark_choice(page, 240.9, 652.8, color=text_color)
        elif "kembar 3" in jk_lahir or jk_lahir == "3":
            mark_choice(page, 294.0, 652.8, color=text_color)
        elif "kembar 4" in jk_lahir or jk_lahir == "4":
            mark_choice(page, 347.2, 652.8, color=text_color)
        elif "lain" in jk_lahir or jk_lahir == "5":
            mark_choice(page, 400.4, 652.8, color=text_color)
        else:
            mark_choice(page, 194.2, 652.8, color=text_color)

        # 8. Kelahiran ke
        k_ke = str(kelahiran.get("kelahiran_ke", "1")).strip()
        write_text(page, 198.0, 673.5, k_ke, color=text_color)

        # 9. Penolong Kelahiran: 1. Dokter (194.2), 2. Bidan/Perawat (236.1), 3. Dukun (307.5), 4. Lainnya (348.8)
        penolong = str(kelahiran.get("penolong_kelahiran", "")).lower()
        if "bidan" in penolong or "perawat" in penolong or penolong == "2":
            mark_choice(page, 236.1, 679.0, color=text_color)
        elif "dukun" in penolong or penolong == "3":
            mark_choice(page, 307.5, 679.0, color=text_color)
        elif "lain" in penolong or penolong == "4":
            mark_choice(page, 348.8, 679.0, color=text_color)
        else:
            mark_choice(page, 194.2, 679.0, color=text_color)

        # 10. Berat & 11. Panjang Bayi
        write_text(page, 198.0, 699.0, kelahiran.get("berat_bayi_kg"), color=text_color)
        write_text(page, 198.0, 711.8, kelahiran.get("panjang_bayi_cm"), color=text_color)

        # Footer Tanggal Lapor & Pelapor
        write_footer(page, 742.5, 794.2, data, wilayah, pelapor, ayah, ibu, text_color=text_color)

    # -------------------------------------------------------------------------
    # B. LAHIR MATI (Halaman 1)
    # -------------------------------------------------------------------------
    elif target_page_idx == 1:
        # 1. Lamanya dalam kandungan (Bulan)
        kandungan = str(lahir_mati.get("lama_kandungan_bulan") or kelahiran.get("lama_kandungan_bulan") or "8").strip()
        write_text(page, 198.0, 584.2, kandungan, color=text_color)

        # 2. Jenis Kelamin: 1. Laki-laki (194.2), 2. Perempuan (244.5)
        jk = str(lahir_mati.get("jenis_kelamin") or kelahiran.get("jenis_kelamin", "")).lower()
        if "perempuan" in jk or jk == "2" or jk.startswith("p"):
            mark_choice(page, 244.5, 589.0, color=text_color)
        else:
            mark_choice(page, 194.2, 589.0, color=text_color)

        # 3. Tanggal lahir mati
        tgl_lm = lahir_mati.get("tanggal") or kelahiran.get("tanggal_lengkap")
        if not tgl_lm:
            t_val = kelahiran.get("tgl_lahir") or kematian.get("tgl_kematian", "")
            b_val = kelahiran.get("bln_lahir") or kematian.get("bln_kematian", "")
            y_val = kelahiran.get("thn_lahir") or kematian.get("thn_kematian", "")
            tgl_lm = f"{t_val} {b_val} {y_val}".strip()
        write_text(page, 220.0, 609.0, tgl_lm, color=text_color)

        # 4. Jenis Kelahiran: 1. Tunggal (194.2), 2. Kembar 2 (240.9), 3. Kembar 3 (294.0), 4. Kembar 4 (347.2), 5. Lainnya (400.4)
        jk_l = str(lahir_mati.get("jenis_kelahiran") or kelahiran.get("jenis_kelahiran", "")).lower()
        if "kembar 2" in jk_l:
            mark_choice(page, 240.9, 614.5, color=text_color)
        elif "kembar 3" in jk_l:
            mark_choice(page, 294.0, 614.5, color=text_color)
        elif "kembar 4" in jk_l:
            mark_choice(page, 347.2, 614.5, color=text_color)
        elif "lain" in jk_l:
            mark_choice(page, 400.4, 614.5, color=text_color)
        else:
            mark_choice(page, 194.2, 614.5, color=text_color)

        # 5. Anak Ke-
        anak_ke = str(lahir_mati.get("anak_ke") or kelahiran.get("kelahiran_ke", "1")).strip()
        write_text(page, 198.0, 634.5, anak_ke, color=text_color)

        # 6. Tempat dilahirkan: 1. RS/RB (194.2), 2. Puskesmas (236.6), 3. Polindes (293.8), 4. Rumah (342.0), 5. Lainnya (384.9)
        td = str(lahir_mati.get("tempat_dilahirkan") or kelahiran.get("tempat_dilahirkan", "")).lower()
        if "puskesmas" in td:
            mark_choice(page, 236.6, 640.0, color=text_color)
        elif "polindes" in td:
            mark_choice(page, 293.8, 640.0, color=text_color)
        elif "rumah" in td:
            mark_choice(page, 342.0, 640.0, color=text_color)
        elif "lain" in td:
            mark_choice(page, 384.9, 640.0, color=text_color)
        else:
            mark_choice(page, 194.2, 640.0, color=text_color)

        # 7. Penolong Kelahiran: 1. Dokter (194.2), 2. Bidan/Perawat (236.1), 3. Dukun (307.5), 4. Lainnya (348.8)
        pn = str(lahir_mati.get("penolong") or kelahiran.get("penolong_kelahiran", "")).lower()
        if "bidan" in pn or "perawat" in pn:
            mark_choice(page, 236.1, 652.8, color=text_color)
        elif "dukun" in pn:
            mark_choice(page, 307.5, 652.8, color=text_color)
        elif "lain" in pn:
            mark_choice(page, 348.8, 652.8, color=text_color)
        else:
            mark_choice(page, 194.2, 652.8, color=text_color)

        # 8. Sebab Lahir Mati
        sebab_lm = str(lahir_mati.get("sebab") or kematian.get("sebab_kematian") or "Asfiksia / Medis").strip()
        write_text(page, 198.0, 673.5, sebab_lm, color=text_color)

        # 9. Yang Menentukan: 1. Dokter (194.2), 2. Bidan/Perawat (236.1), 3. Tenaga Kesehatan (307.5), 4. Kepolisian (392.0), 5. Lainnya (194.2, 691.0)
        ym = str(lahir_mati.get("yang_menentukan") or kematian.get("yang_menerangkan", "")).lower()
        if "bidan" in ym or "perawat" in ym:
            mark_choice(page, 236.1, 678.3, color=text_color)
        elif "tenaga kesehatan" in ym or "nakes" in ym:
            mark_choice(page, 307.5, 678.3, color=text_color)
        elif "polisi" in ym or "kepolisian" in ym:
            mark_choice(page, 392.0, 678.3, color=text_color)
        elif "lain" in ym:
            mark_choice(page, 194.2, 691.0, color=text_color)
        else:
            mark_choice(page, 194.2, 678.3, color=text_color)

        # 10. Tempat Kelahiran
        tmpt_lm = lahir_mati.get("tempat_kelahiran") or kelahiran.get("nama_faskes") or wilayah.get("kabupaten_kota", "")
        write_text(page, 198.0, 711.0, tmpt_lm, upper=True, color=text_color)

        # Footer Tanggal Lapor & Pelapor
        write_footer(page, 741.8, 793.5, data, wilayah, pelapor, ayah, ibu, text_color=text_color)

    # -------------------------------------------------------------------------
    # C. KEMATIAN (Halaman 2)
    # -------------------------------------------------------------------------
    elif target_page_idx == 2:
        # 1. NIK Jenazah
        write_text(page, 198.0, 584.2, kematian.get("nik") or subjek.get("nik"), color=text_color)

        # 2. Nama Lengkap Jenazah
        write_text(page, 198.0, 597.0, kematian.get("nama_lengkap") or subjek.get("nama"), upper=True, color=text_color)

        # 3. Tanggal Kematian
        tgl_mati = kematian.get("tanggal_kematian")
        if not tgl_mati and (kematian.get("tgl_kematian") or kematian.get("bln_kematian")):
            tgl_mati = f"{kematian.get('tgl_kematian', '')} {kematian.get('bln_kematian', '')} {kematian.get('thn_kematian', '')}".strip()
        write_text(page, 220.0, 609.8, tgl_mati, color=text_color)

        # 4. Pukul Kematian
        jam_m = kematian.get("pukul_jam", "")
        menit_m = kematian.get("pukul_menit", "")
        if jam_m or menit_m:
            page.insert_text((198.0, 622.5), str(jam_m or "00"), fontsize=8.5, fontname="helv", color=text_color)
            page.insert_text((228.0, 622.5), f"{menit_m or '00'} WIB", fontsize=8.5, fontname="helv", color=text_color)

        # 5. Sebab Kematian: 1. Sakit biasa / tua (194.2), 2. Wabah Penyakit (270.1), 3. Kecelakaan (347.1), 4. Kriminalitas (406.9), 5. Bunuh Diri (469.9), 6. Lainnya (194.2, 640.0)
        sebab = str(kematian.get("sebab_kematian", "")).lower()
        if "wabah" in sebab or sebab == "2":
            mark_choice(page, 270.1, 627.3, color=text_color)
        elif "kecelakaan" in sebab or sebab == "3":
            mark_choice(page, 347.1, 627.3, color=text_color)
        elif "kriminal" in sebab or sebab == "4":
            mark_choice(page, 406.9, 627.3, color=text_color)
        elif "bunuh diri" in sebab or sebab == "5":
            mark_choice(page, 469.9, 627.3, color=text_color)
        elif "lain" in sebab or sebab == "6":
            mark_choice(page, 194.2, 640.0, color=text_color)
        else:
            mark_choice(page, 194.2, 627.3, color=text_color)

        # 6. Tempat Kematian
        write_text(page, 198.0, 660.0, kematian.get("tempat_kematian"), upper=True, color=text_color)

        # 7. Yang Menerangkan: 1. Dokter (194.2), 2. Tenaga Kesehatan (236.1), 3. Kepolisian (320.6), 4. Lainnya (377.2)
        ym = str(kematian.get("yang_menerangkan", "")).lower()
        if "nakes" in ym or "tenaga kesehatan" in ym or ym == "2":
            mark_choice(page, 236.1, 666.3, color=text_color)
        elif "polisi" in ym or "kepolisian" in ym or ym == "3":
            mark_choice(page, 320.6, 666.3, color=text_color)
        elif "lain" in ym or ym == "4":
            mark_choice(page, 377.2, 666.3, color=text_color)
        else:
            mark_choice(page, 194.2, 666.3, color=text_color)

        # Footer Tanggal Lapor & Pelapor
        write_footer(page, 704.2, 755.2, data, wilayah, pelapor, ayah, ibu, text_color=text_color)

    # Output selection: extract the single completed form page or whole doc
    output_doc = pymupdf.open()
    if single_page:
        output_doc.insert_pdf(doc, from_page=target_page_idx, to_page=target_page_idx)
    else:
        output_doc.insert_pdf(doc)

    out_bytes = output_doc.tobytes()
    output_doc.close()
    doc.close()
    return out_bytes
