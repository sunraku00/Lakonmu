import pymupdf
import io
import os
from typing import Dict, Any, List

def draw_check(page, x: float, y: float, color=(0.05, 0.15, 0.5)):
    """Draw a clean checkmark at (x, y)"""
    page.draw_line(pymupdf.Point(x, y - 1), pymupdf.Point(x + 2.5, y + 2.5), color=color, width=1.4)
    page.draw_line(pymupdf.Point(x + 2.5, y + 2.5), pymupdf.Point(x + 6.5, y - 4), color=color, width=1.4)

def fill_f201a_pdf(template_path: str, data: Dict[str, Any], single_page: bool = True) -> bytes:
    # Use the specified template
    doc = pymupdf.open(template_path)
    
    jenis_pelaporan = str(data.get("jenis_pelaporan", "Kelahiran")).strip().lower()

    # Route to the dedicated page in this official A4 template:
    # Page 0 = Kelahiran
    # Page 1 = Lahir Mati
    # Page 2 = Kematian
    if "mati" in jenis_pelaporan and "lahir" in jenis_pelaporan:
        target_page_idx = 1
    elif "mati" in jenis_pelaporan or "kematian" in jenis_pelaporan:
        target_page_idx = 2
    else:
        target_page_idx = 0

    page = doc[target_page_idx]

    font_name = "helv"
    font_size = 7.8
    font_size_sm = 6.8
    text_color = (0.05, 0.15, 0.5) # Dark navy blue for filled text

    wilayah = data.get("wilayah", {})
    pelapor = data.get("pelapor", {})
    subjek = data.get("subjek_akta", {})
    ayah = data.get("ayah", {})
    ibu = data.get("ibu", {})
    saksi1 = data.get("saksi_1", {})
    saksi2 = data.get("saksi_2", {})
    kelahiran = data.get("kelahiran", {})
    kematian = data.get("kematian", {})

    # 1. DATA WILAYAH (KOP Atas)
    if wilayah.get("provinsi"):
        page.insert_text((140, 43.0), str(wilayah["provinsi"]).upper(), fontsize=font_size, fontname=font_name, color=text_color)
    if wilayah.get("kabupaten_kota"):
        page.insert_text((140, 55.0), str(wilayah["kabupaten_kota"]).upper(), fontsize=font_size, fontname=font_name, color=text_color)
    if wilayah.get("kecamatan"):
        page.insert_text((140, 66.0), str(wilayah["kecamatan"]).upper(), fontsize=font_size, fontname=font_name, color=text_color)
    if wilayah.get("desa_kelurahan"):
        page.insert_text((140, 78.0), str(wilayah["desa_kelurahan"]).upper(), fontsize=font_size, fontname=font_name, color=text_color)
    if wilayah.get("kode_wilayah"):
        page.insert_text((140, 89.0), str(wilayah["kode_wilayah"]), fontsize=font_size, fontname=font_name, color=text_color)

    # 2. DATA PELAPOR
    if pelapor.get("nama"):
        page.insert_text((198, 145.5), str(pelapor["nama"]).upper(), fontsize=font_size, fontname=font_name, color=text_color)
    if pelapor.get("nik"):
        page.insert_text((198, 157.5), str(pelapor["nik"]), fontsize=font_size, fontname=font_name, color=text_color)
    if pelapor.get("nomor_paspor"):
        page.insert_text((198, 169.0), str(pelapor["nomor_paspor"]), fontsize=font_size, fontname=font_name, color=text_color)
    if pelapor.get("nomor_kk"):
        page.insert_text((198, 180.5), str(pelapor["nomor_kk"]), fontsize=font_size, fontname=font_name, color=text_color)
    if pelapor.get("kewarganegaraan"):
        page.insert_text((198, 192.0), str(pelapor["kewarganegaraan"]).upper(), fontsize=font_size, fontname=font_name, color=text_color)

    # 3. DATA SUBJEK AKTA
    nama_subjek = subjek.get("nama") or (kelahiran.get("nama_bayi") if target_page_idx == 0 else kematian.get("nama_lengkap"))
    if nama_subjek:
        page.insert_text((198, 218.0), str(nama_subjek).upper(), fontsize=font_size, fontname=font_name, color=text_color)
    
    nik_subjek = subjek.get("nik") or (kematian.get("nik") if target_page_idx == 2 else "")
    if nik_subjek:
        page.insert_text((198, 230.0), str(nik_subjek), fontsize=font_size, fontname=font_name, color=text_color)
    if subjek.get("nomor_paspor"):
        page.insert_text((198, 241.5), str(subjek["nomor_paspor"]), fontsize=font_size, fontname=font_name, color=text_color)
    
    kk_subjek = subjek.get("nomor_kk") or pelapor.get("nomor_kk")
    if kk_subjek:
        page.insert_text((198, 253.5), str(kk_subjek), fontsize=font_size, fontname=font_name, color=text_color)
    if subjek.get("kewarganegaraan"):
        page.insert_text((198, 265.5), str(subjek["kewarganegaraan"]).upper(), fontsize=font_size, fontname=font_name, color=text_color)

    # 4. DATA ORANG TUA
    # Ayah
    if ayah.get("nama"):
        page.insert_text((198, 291.0), str(ayah["nama"]).upper(), fontsize=font_size, fontname=font_name, color=text_color)
    if ayah.get("nik"):
        page.insert_text((198, 303.0), str(ayah["nik"]), fontsize=font_size, fontname=font_name, color=text_color)
    if ayah.get("tempat_lahir"):
        page.insert_text((198, 315.0), str(ayah["tempat_lahir"]).upper(), fontsize=font_size, fontname=font_name, color=text_color)
    
    tgl_ayah = ayah.get("tanggal_lahir")
    if not tgl_ayah and ayah.get("tgl"):
        tgl_ayah = f"{ayah.get('tgl', '')}-{ayah.get('bln', '')}-{ayah.get('thn', '')}".strip("-")
    if tgl_ayah:
        page.insert_text((198, 326.5), str(tgl_ayah), fontsize=font_size, fontname=font_name, color=text_color)
    if ayah.get("kewarganegaraan"):
        page.insert_text((198, 338.5), str(ayah["kewarganegaraan"]).upper(), fontsize=font_size, fontname=font_name, color=text_color)

    # Ibu
    if ibu.get("nama"):
        page.insert_text((198, 350.5), str(ibu["nama"]).upper(), fontsize=font_size, fontname=font_name, color=text_color)
    if ibu.get("nik"):
        page.insert_text((198, 361.5), str(ibu["nik"]), fontsize=font_size, fontname=font_name, color=text_color)
    if ibu.get("tempat_lahir"):
        page.insert_text((198, 373.5), str(ibu["tempat_lahir"]).upper(), fontsize=font_size, fontname=font_name, color=text_color)
    
    tgl_ibu = ibu.get("tanggal_lahir")
    if not tgl_ibu and ibu.get("tgl"):
        tgl_ibu = f"{ibu.get('tgl', '')}-{ibu.get('bln', '')}-{ibu.get('thn', '')}".strip("-")
    if tgl_ibu:
        page.insert_text((198, 385.5), str(tgl_ibu), fontsize=font_size, fontname=font_name, color=text_color)
    if ibu.get("kewarganegaraan"):
        page.insert_text((198, 397.0), str(ibu["kewarganegaraan"]).upper(), fontsize=font_size, fontname=font_name, color=text_color)

    # 5. DATA SAKSI I
    if saksi1.get("nama"):
        page.insert_text((198, 423.0), str(saksi1["nama"]).upper(), fontsize=font_size, fontname=font_name, color=text_color)
    if saksi1.get("nik"):
        page.insert_text((198, 435.0), str(saksi1["nik"]), fontsize=font_size, fontname=font_name, color=text_color)
    if saksi1.get("nomor_kk"):
        page.insert_text((198, 446.5), str(saksi1["nomor_kk"]), fontsize=font_size, fontname=font_name, color=text_color)
    if saksi1.get("kewarganegaraan"):
        page.insert_text((198, 458.5), str(saksi1["kewarganegaraan"]).upper(), fontsize=font_size, fontname=font_name, color=text_color)

    # 6. DATA SAKSI II
    if saksi2.get("nama"):
        page.insert_text((198, 484.5), str(saksi2["nama"]).upper(), fontsize=font_size, fontname=font_name, color=text_color)
    if saksi2.get("nik"):
        page.insert_text((198, 496.0), str(saksi2["nik"]), fontsize=font_size, fontname=font_name, color=text_color)
    if saksi2.get("nomor_kk"):
        page.insert_text((198, 508.0), str(saksi2["nomor_kk"]), fontsize=font_size, fontname=font_name, color=text_color)
    if saksi2.get("kewarganegaraan"):
        page.insert_text((198, 520.0), str(saksi2["kewarganegaraan"]).upper(), fontsize=font_size, fontname=font_name, color=text_color)

    # 7. PERISTIWA KHUSUS
    # A. KELAHIRAN (Page Index 0)
    if target_page_idx == 0:
        if kelahiran.get("nama_bayi"):
            page.insert_text((198, 545.5), str(kelahiran["nama_bayi"]).upper(), fontsize=font_size, fontname=font_name, color=text_color)

        # 2. Jenis Kelamin: 1. Laki-Laki (200), 2. Perempuan (282)
        jk = str(kelahiran.get("jenis_kelamin", "")).lower()
        if "perempuan" in jk or jk == "2" or jk.startswith("p"):
            draw_check(page, 282, 555, text_color)
        else: # Default 1. Laki-Laki
            draw_check(page, 200, 555, text_color)

        # 3. Tempat Dilahirkan: 1. RS/RB (200), 2. Puskesmas (256), 3. Polindes (331), 4. Rumah (397), 5. Lainnya (441)
        td = str(kelahiran.get("tempat_dilahirkan", "")).lower()
        faskes = kelahiran.get("nama_faskes", "")
        if "puskesmas" in td or td == "2":
            draw_check(page, 256, 566, text_color)
        elif "polindes" in td or "pustu" in td or td == "3":
            draw_check(page, 331, 566, text_color)
        elif "rumah" in td or td == "4":
            draw_check(page, 397, 566, text_color)
        elif "lain" in td or td == "5":
            draw_check(page, 441, 566, text_color)
        else:
            draw_check(page, 200, 566, text_color)
        if faskes:
            page.insert_text((450, 568.5), f"{faskes}"[:25], fontsize=6.5, fontname=font_name, color=text_color)

        # 4. Tempat Kelahiran
        tmpt_lahir = kelahiran.get("tempat_kelahiran") or wilayah.get("kabupaten_kota", "")
        if tmpt_lahir:
            page.insert_text((198, 580.5), str(tmpt_lahir).upper(), fontsize=font_size, fontname=font_name, color=text_color)

        # 5. Hari & Tanggal Lahir
        hari = kelahiran.get("hari_lahir", "")
        if hari:
            page.insert_text((220, 592.5), str(hari).capitalize(), fontsize=font_size, fontname=font_name, color=text_color)
        
        tgl_lahir_str = kelahiran.get("tanggal_lengkap")
        if not tgl_lahir_str and (kelahiran.get("tgl_lahir") or kelahiran.get("bln_lahir")):
            tgl_lahir_str = f"{kelahiran.get('tgl_lahir', '')} {kelahiran.get('bln_lahir', '')} {kelahiran.get('thn_lahir', '')}".strip()
        if tgl_lahir_str:
            page.insert_text((305, 592.5), str(tgl_lahir_str), fontsize=font_size, fontname=font_name, color=text_color)

        # 6. Pukul
        jam = kelahiran.get("pukul_jam", "")
        menit = kelahiran.get("pukul_menit", "")
        if jam or menit:
            page.insert_text((198, 604.0), f"{jam or '00'} : {menit or '00'} WIB", fontsize=font_size, fontname=font_name, color=text_color)

        # 7. Jenis Kelahiran: 1. Tunggal (200), 2. Kembar 2 (262), 3. Kembar 3 (327), 4. Kembar 4 (392), 5. Lainnya (458)
        jk_lahir = str(kelahiran.get("jenis_kelahiran", "")).lower()
        if "kembar 2" in jk_lahir or jk_lahir == "2":
            draw_check(page, 262, 614, text_color)
        elif "kembar 3" in jk_lahir or jk_lahir == "3":
            draw_check(page, 327, 614, text_color)
        elif "kembar 4" in jk_lahir or jk_lahir == "4":
            draw_check(page, 392, 614, text_color)
        elif "lain" in jk_lahir or jk_lahir == "5":
            draw_check(page, 458, 614, text_color)
        else:
            draw_check(page, 200, 614, text_color)

        # 8. Kelahiran ke
        k_ke = str(kelahiran.get("kelahiran_ke", "1")).strip()
        page.insert_text((198, 627.0), k_ke, fontsize=font_size, fontname=font_name, color=text_color)

        # 9. Penolong: 1. Dokter (200), 2. Bidan/Perawat (256), 3. Dukun (344), 4. Lainnya (400)
        penolong = str(kelahiran.get("penolong_kelahiran", "")).lower()
        if "bidan" in penolong or "perawat" in penolong or penolong == "2":
            draw_check(page, 256, 637, text_color)
        elif "dukun" in penolong or penolong == "3":
            draw_check(page, 344, 637, text_color)
        elif "lain" in penolong or penolong == "4":
            draw_check(page, 400, 637, text_color)
        else:
            draw_check(page, 200, 637, text_color)

        # 10. Berat & 11. Panjang Bayi
        if kelahiran.get("berat_bayi_kg"):
            page.insert_text((198, 651.0), str(kelahiran["berat_bayi_kg"]), fontsize=font_size, fontname=font_name, color=text_color)
        if kelahiran.get("panjang_bayi_cm"):
            page.insert_text((198, 662.5), str(kelahiran["panjang_bayi_cm"]), fontsize=font_size, fontname=font_name, color=text_color)

        # Tanggal & Pelapor Footer
        tempat = wilayah.get("kabupaten_kota", "Kota").replace("KABUPATEN ", "").replace("KOTA ", "").title()
        tgl_footer = data.get("tanggal_lapor_tempat") or f"{tempat}, {data.get('tanggal_lapor_tgl', '')}".strip(", ")
        page.insert_text((370, 679.5), tgl_footer, fontsize=font_size, fontname=font_name, color=text_color)

        nama_pelapor = pelapor.get("nama") or ayah.get("nama") or ibu.get("nama") or "........................"
        page.insert_text((365, 726.5), str(nama_pelapor).upper(), fontsize=font_size, fontname=font_name, color=text_color)

    # B. KEMATIAN (Page Index 2)
    elif target_page_idx == 2:
        if kematian.get("nik"):
            page.insert_text((198, 545.5), str(kematian["nik"]), fontsize=font_size, fontname=font_name, color=text_color)
        if kematian.get("nama_lengkap"):
            page.insert_text((198, 557.5), str(kematian["nama_lengkap"]).upper(), fontsize=font_size, fontname=font_name, color=text_color)
        
        tgl_mati = kematian.get("tanggal_kematian")
        if not tgl_mati and (kematian.get("tgl_kematian") or kematian.get("bln_kematian")):
            tgl_mati = f"{kematian.get('tgl_kematian', '')} {kematian.get('bln_kematian', '')} {kematian.get('thn_kematian', '')}".strip()
        if tgl_mati:
            page.insert_text((220, 569.5), str(tgl_mati), fontsize=font_size, fontname=font_name, color=text_color)
            
        jam_m = kematian.get("pukul_jam", "")
        menit_m = kematian.get("pukul_menit", "")
        if jam_m or menit_m:
            page.insert_text((198, 581.0), f"{jam_m or '00'} : {menit_m or '00'} WIB", fontsize=font_size, fontname=font_name, color=text_color)

        # Sebab Kematian: 1. Sakit (200), 2. Wabah (288), 3. Kecelakaan (388), 4. Kriminal (458), 5. Bunuh Diri (200, 604), 6. Lainnya (264, 604)
        sebab = str(kematian.get("sebab_kematian", "")).lower()
        if "wabah" in sebab or sebab == "2":
            draw_check(page, 288, 592, text_color)
        elif "kecelakaan" in sebab or sebab == "3":
            draw_check(page, 388, 592, text_color)
        elif "kriminal" in sebab or sebab == "4":
            draw_check(page, 458, 592, text_color)
        elif "bunuh diri" in sebab or sebab == "5":
            draw_check(page, 200, 604, text_color)
        elif "lain" in sebab or sebab == "6":
            draw_check(page, 264, 604, text_color)
        else:
            draw_check(page, 200, 592, text_color)

        if kematian.get("tempat_kematian"):
            page.insert_text((198, 616.0), str(kematian["tempat_kematian"]).upper(), fontsize=font_size, fontname=font_name, color=text_color)

        # Yang Menerangkan: 1. Dokter (200), 2. Nakes (256), 3. Kepolisian (358), 4. Lainnya (428)
        ym = str(kematian.get("yang_menerangkan", "")).lower()
        if "nakes" in ym or "tenaga kesehatan" in ym or ym == "2":
            draw_check(page, 256, 627, text_color)
        elif "polisi" in ym or "kepolisian" in ym or ym == "3":
            draw_check(page, 358, 627, text_color)
        elif "lain" in ym or ym == "4":
            draw_check(page, 428, 627, text_color)
        else:
            draw_check(page, 200, 627, text_color)

        # Tanggal & Pelapor Footer
        tempat = wilayah.get("kabupaten_kota", "Kota").replace("KABUPATEN ", "").replace("KOTA ", "").title()
        tgl_footer = data.get("tanggal_lapor_tempat") or f"{tempat}, {data.get('tanggal_lapor_tgl', '')}".strip(", ")
        page.insert_text((370, 644.5), tgl_footer, fontsize=font_size, fontname=font_name, color=text_color)

        nama_pelapor = pelapor.get("nama") or "........................"
        page.insert_text((365, 691.5), str(nama_pelapor).upper(), fontsize=font_size, fontname=font_name, color=text_color)

    # C. LAHIR MATI (Page Index 1)
    elif target_page_idx == 1:
        lahir_mati = data.get("lahir_mati", {})
        
        # 1. Lamanya dalam kandungan (Bulan)
        kandungan = str(lahir_mati.get("lama_kandungan_bulan") or kelahiran.get("lama_kandungan_bulan") or "8").strip()
        page.insert_text((198, 545.5), f"{kandungan}", fontsize=font_size, fontname=font_name, color=text_color)

        # 2. Jenis Kelamin: 1. Laki-laki (200), 2. Perempuan (282)
        jk = str(lahir_mati.get("jenis_kelamin") or kelahiran.get("jenis_kelamin", "")).lower()
        if "perempuan" in jk or jk == "2" or jk.startswith("p"):
            draw_check(page, 282, 555, text_color)
        else:
            draw_check(page, 200, 555, text_color)

        # 3. Tanggal lahir mati
        tgl_lm = lahir_mati.get("tanggal") or kelahiran.get("tanggal_lengkap")
        if not tgl_lm:
            t_val = kelahiran.get("tgl_lahir") or kematian.get("tgl_kematian", "")
            b_val = kelahiran.get("bln_lahir") or kematian.get("bln_kematian", "")
            y_val = kelahiran.get("thn_lahir") or kematian.get("thn_kematian", "")
            tgl_lm = f"{t_val} {b_val} {y_val}".strip()
        if tgl_lm:
            page.insert_text((220, 568.5), str(tgl_lm), fontsize=font_size, fontname=font_name, color=text_color)

        # 4. Jenis Kelahiran: 1. Tunggal (200), 2. Kembar 2 (262)
        jk_l = str(lahir_mati.get("jenis_kelahiran") or kelahiran.get("jenis_kelahiran", "")).lower()
        if "kembar 2" in jk_l:
            draw_check(page, 262, 579, text_color)
        else:
            draw_check(page, 200, 579, text_color)

        # 5. Anak Ke-
        anak_ke = str(lahir_mati.get("anak_ke") or kelahiran.get("kelahiran_ke", "1")).strip()
        page.insert_text((198, 591.5), anak_ke, fontsize=font_size, fontname=font_name, color=text_color)

        # 6. Tempat dilahirkan: 1. RS/RB (200), 2. Puskesmas (256), 3. Polindes (331), 4. Rumah (397), 5. Lainnya (441)
        td = str(lahir_mati.get("tempat_dilahirkan") or kelahiran.get("tempat_dilahirkan", "")).lower()
        if "puskesmas" in td:
            draw_check(page, 256, 603, text_color)
        elif "polindes" in td:
            draw_check(page, 331, 603, text_color)
        elif "rumah" in td:
            draw_check(page, 397, 603, text_color)
        elif "lain" in td:
            draw_check(page, 441, 603, text_color)
        else:
            draw_check(page, 200, 603, text_color)

        # 7. Penolong: 1. Dokter (200), 2. Bidan/Perawat (256), 3. Dukun (344), 4. Lainnya (400)
        pn = str(lahir_mati.get("penolong") or kelahiran.get("penolong_kelahiran", "")).lower()
        if "bidan" in pn or "perawat" in pn:
            draw_check(page, 256, 614, text_color)
        elif "dukun" in pn:
            draw_check(page, 344, 614, text_color)
        elif "lain" in pn:
            draw_check(page, 400, 614, text_color)
        else:
            draw_check(page, 200, 614, text_color)

        # 8. Sebab Lahir Mati
        sebab_lm = str(lahir_mati.get("sebab") or kematian.get("sebab_kematian") or "Asfiksia / Medis").strip()
        page.insert_text((198, 626.5), sebab_lm.upper()[:35], fontsize=font_size, fontname=font_name, color=text_color)

        # 9. Yang Menentukan: 1. Dokter (200), 2. Bidan/Perawat (256), 3. Nakes (340), 4. Kepolisian (438)
        ym = str(lahir_mati.get("yang_menentukan") or kematian.get("yang_menerangkan", "")).lower()
        if "bidan" in ym or "perawat" in ym:
            draw_check(page, 256, 638, text_color)
        elif "nakes" in ym:
            draw_check(page, 340, 638, text_color)
        elif "polisi" in ym:
            draw_check(page, 438, 638, text_color)
        else:
            draw_check(page, 200, 638, text_color)

        # 10. Tempat Kelahiran
        tmpt_lm = lahir_mati.get("tempat_kelahiran") or kelahiran.get("nama_faskes") or wilayah.get("kabupaten_kota", "")
        if tmpt_lm:
            page.insert_text((198, 661.5), str(tmpt_lm).upper()[:35], fontsize=font_size, fontname=font_name, color=text_color)

        # Footer Tanggal & Pelapor
        tempat = wilayah.get("kabupaten_kota", "Kota").replace("KABUPATEN ", "").replace("KOTA ", "").title()
        tgl_footer = data.get("tanggal_lapor_tempat") or f"{tempat}, {data.get('tanggal_lapor_tgl', '')}".strip(", ")
        page.insert_text((370, 679.5), tgl_footer, fontsize=font_size, fontname=font_name, color=text_color)
        nama_pelapor = pelapor.get("nama") or ayah.get("nama") or "........................"
        page.insert_text((365, 726.5), str(nama_pelapor).upper(), fontsize=font_size, fontname=font_name, color=text_color)

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
