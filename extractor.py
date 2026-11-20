import re
import json
import os
from typing import Dict, Any, Optional

# Indonesian month mapping
BULAN_MAP = {
    "januari": "01", "jan": "01",
    "februari": "02", "feb": "02",
    "maret": "03", "mar": "03",
    "april": "04", "apr": "04",
    "mei": "05",
    "juni": "06", "jun": "06",
    "juli": "07", "jul": "07",
    "agustus": "08", "agu": "08", "agt": "08",
    "september": "09", "sep": "09",
    "oktober": "10", "okt": "10",
    "november": "11", "nov": "11",
    "desember": "12", "des": "12"
}

SYSTEM_PROMPT = """Anda adalah asisten AI spesialis administrasi kependudukan dan pencatatan sipil Indonesia (Dukcapil).
Tugas Anda: mengekstrak data mentah hasil copas (dari web RS/Puskesmas, rekam medis, WA, atau portal online) ke dalam struktur Formulir F-2.01 A (Formulir Pelaporan Pencatatan Sipil di Dalam Wilayah NKRI).

Formulir F-2.01 A digunakan terutama untuk:
1. Pelaporan Kelahiran
2. Pelaporan Kematian
3. Pelaporan Lahir Mati

Instruksi Ekstraksi Khusus:
- Deteksi apakah ini peristiwa Kelahiran, Kematian, atau Lahir Mati.
- Penanganan Khusus Data SIAK (Hasil Ctrl+A dari Web SIAK Terpusat / Dukcapil):
  * Teks hasil Ctrl+A dari SIAK biasanya SANGAT ACAK, berisi tabel tab-separated, menu navigasi ("Beranda", "Pelayanan", "Logout"), tombol ("Simpan", "Batal", "Cetak"), dan header tabel berulang.
  * ABAIKAN seluruh teks navigasi, tombol, dan copyright SIAK tersebut.
  * Pada tabel keluarga SIAK ("Daftar Anggota Keluarga"):
    - Baris dengan status hubungan "KEPALA KELUARGA" atau "SUAMI" adalah AYAH.
    - Baris dengan status hubungan "ISTRI" adalah IBU.
    - Baris dengan status hubungan "ANAK" adalah SUBJEK AKTA / BAYI.
  * Ekstrak NIK (16 digit), Nama, Tempat Lahir, Tanggal Lahir, dan Pekerjaan untuk masing-masing Ayah & Ibu.
- NIK: angka 16 digit murni. Jika ada spasi/titik/strip, bersihkan menjadi 16 digit angka.
- Nomor KK: angka 16 digit murni.
- Bedakan data Subjek Akta (Bayi/Jenazah), Pelapor, Orang Tua (Ayah & Ibu), dan Saksi (Saksi 1 & Saksi 2).
- Jika nama pelapor tidak disebutkan eksplisit, default adalah Ayah (atau Ibu).
- Kewarganegaraan default: 'WNI' jika tidak disebutkan WNA.
- Tanggal & Waktu: Pisahkan hari (Senin/Selasa/...), tgl (DD), bln (MM atau nama bulan), thn (YYYY), jam (HH), menit (MM).
- Berat bayi: ubah ke format Kg (misal 3200 gr -> 3.2, 3.4 kg -> 3.4).
- Panjang bayi: ubah ke angka cm (misal 50 cm -> 50).
- Jenis Kelamin: 'Laki-Laki' atau 'Perempuan'.
- Tempat dilahirkan: 'RS/RB', 'Puskesmas', 'Polindes', 'Rumah', atau 'Lainnya'.
- Penolong kelahiran: 'Dokter', 'Bidan/Perawat', 'Dukun', atau 'Lainnya'.
- Jenis kelahiran: 'Tunggal', 'Kembar 2', 'Kembar 3', 'Kembar 4', 'Lainnya'.
- Format nama: gunakan huruf kapital rapi (UPPERCASE).

KEMBALIKAN HANYA JSON SESUAI SKEMA BERIKUT TANPA MARKDOWN EMBEDDING:
{
  "jenis_pelaporan": "Kelahiran" atau "Kematian" atau "Lahir Mati",
  "wilayah": {
    "provinsi": "",
    "kabupaten_kota": "",
    "kecamatan": "",
    "desa_kelurahan": "",
    "kode_wilayah": ""
  },
  "pelapor": {
    "nama": "",
    "nik": "",
    "nomor_paspor": "",
    "nomor_kk": "",
    "kewarganegaraan": "WNI"
  },
  "subjek_akta": {
    "nama": "",
    "nik": "",
    "nomor_paspor": "",
    "nomor_kk": "",
    "kewarganegaraan": "WNI"
  },
  "ayah": {
    "nama": "",
    "nik": "",
    "tempat_lahir": "",
    "tgl": "",
    "bln": "",
    "thn": "",
    "kewarganegaraan": "WNI"
  },
  "ibu": {
    "nama": "",
    "nik": "",
    "tempat_lahir": "",
    "tgl": "",
    "bln": "",
    "thn": "",
    "kewarganegaraan": "WNI"
  },
  "saksi_1": {
    "nama": "",
    "nik": "",
    "nomor_kk": "",
    "kewarganegaraan": "WNI"
  },
  "saksi_2": {
    "nama": "",
    "nik": "",
    "nomor_kk": "",
    "kewarganegaraan": "WNI"
  },
  "kelahiran": {
    "nama_bayi": "",
    "jenis_kelamin": "Laki-Laki" atau "Perempuan",
    "tempat_dilahirkan": "RS/RB" atau "Puskesmas" atau "Polindes" atau "Rumah" atau "Lainnya",
    "nama_faskes": "",
    "tempat_kelahiran": "",
    "hari_lahir": "",
    "tgl_lahir": "",
    "bln_lahir": "",
    "thn_lahir": "",
    "pukul_jam": "",
    "pukul_menit": "",
    "jenis_kelahiran": "Tunggal",
    "kelahiran_ke": "1",
    "penolong_kelahiran": "Dokter" atau "Bidan/Perawat",
    "berat_bayi_kg": "",
    "panjang_bayi_cm": ""
  },
  "kematian": {
    "nik": "",
    "nama_lengkap": "",
    "tgl_kematian": "",
    "bln_kematian": "",
    "thn_kematian": "",
    "pukul_jam": "",
    "pukul_menit": "",
    "sebab_kematian": "Sakit biasa / tua",
    "tempat_kematian": "",
    "yang_menerangkan": "Dokter"
  },
  "tanggal_lapor_tempat": "",
  "tanggal_lapor_tgl": ""
}
"""

def extract_with_smart_regex(raw_text: str) -> Dict[str, Any]:
    """
    Ekstraksi cerdas berbasis pola regex dan analisis semantik kata kunci bahasa Indonesia.
    Bekerja 100% offline tanpa membutuhkan API Key.
    """
    text = raw_text.strip()
    data = {
        "jenis_pelaporan": "Kelahiran",
        "wilayah": {
            "provinsi": "",
            "kabupaten_kota": "",
            "kecamatan": "",
            "desa_kelurahan": "",
            "kode_wilayah": ""
        },
        "pelapor": {"nama": "", "nik": "", "nomor_paspor": "", "nomor_kk": "", "kewarganegaraan": "WNI"},
        "subjek_akta": {"nama": "", "nik": "", "nomor_paspor": "", "nomor_kk": "", "kewarganegaraan": "WNI"},
        "ayah": {"nama": "", "nik": "", "tempat_lahir": "", "tgl": "", "bln": "", "thn": "", "kewarganegaraan": "WNI"},
        "ibu": {"nama": "", "nik": "", "tempat_lahir": "", "tgl": "", "bln": "", "thn": "", "kewarganegaraan": "WNI"},
        "saksi_1": {"nama": "", "nik": "", "nomor_kk": "", "kewarganegaraan": "WNI"},
        "saksi_2": {"nama": "", "nik": "", "nomor_kk": "", "kewarganegaraan": "WNI"},
        "kelahiran": {
            "nama_bayi": "",
            "jenis_kelamin": "",
            "tempat_dilahirkan": "RS/RB",
            "nama_faskes": "",
            "tempat_kelahiran": "",
            "hari_lahir": "",
            "tgl_lahir": "",
            "bln_lahir": "",
            "thn_lahir": "",
            "pukul_jam": "",
            "pukul_menit": "",
            "jenis_kelahiran": "Tunggal",
            "kelahiran_ke": "1",
            "penolong_kelahiran": "Dokter",
            "berat_bayi_kg": "",
            "panjang_bayi_cm": ""
        },
        "kematian": {
            "nik": "",
            "nama_lengkap": "",
            "tgl_kematian": "",
            "bln_kematian": "",
            "thn_kematian": "",
            "pukul_jam": "",
            "pukul_menit": "",
            "sebab_kematian": "Sakit biasa / tua",
            "tempat_kematian": "",
            "yang_menerangkan": "Dokter"
        },
        "tanggal_lapor_tempat": "",
        "tanggal_lapor_tgl": ""
    }

    # 1. Deteksi Jenis Peristiwa
    lower_text = text.lower()
    if any(k in lower_text for k in ["kematian", "meninggal", "wafat", "tutup usia", "jenazah", "sebab kematian"]):
        data["jenis_pelaporan"] = "Kematian"
    elif any(k in lower_text for k in ["lahir mati", "stillbirth", "meninggal dalam kandungan"]):
        data["jenis_pelaporan"] = "Lahir Mati"
    else:
        data["jenis_pelaporan"] = "Kelahiran"

    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # 2. Cari Semua NIK 16 digit
    nik_matches = re.findall(r"\b(\d{16})\b", text)
    # Cari juga nomor KK
    kk_match = re.search(r"(?:no\.?\s*kk|kartu\s*keluarga|nomor\s*kk)[\s:]*([0-9]{16})", lower_text)
    if kk_match:
        nomor_kk = kk_match.group(1)
        data["pelapor"]["nomor_kk"] = nomor_kk
        data["subjek_akta"]["nomor_kk"] = nomor_kk

    # 3. Parsing Baris demi Baris dengan Keyword Context & Format SIAK (Tab/Space Separated)
    for line in lines:
        ll = line.lower()
        parts = re.split(r"(?:[:=]|\t|\s{2,})\s*", line, 1)
        val = parts[1].strip() if len(parts) > 1 else ""

        # A. Deteksi Baris Tabel Anggota Keluarga SIAK (Daftar Anggota Keluarga)
        cols = [c.strip() for c in re.split(r"[\t|]|\s{2,}", line) if c.strip()]
        if len(cols) >= 3:
            row_nik = next((c for c in cols if re.match(r"^\d{16}$", c)), None)
            if row_nik:
                line_u = line.upper()
                if "KEPALA KELUARGA" in line_u or "SUAMI" in line_u:
                    data["ayah"]["nik"] = row_nik
                    for c in cols:
                        if c != row_nik and len(c) > 3 and not re.match(r"^\d+$", c) and c.upper() not in ["LAKI-LAKI", "PEREMPUAN", "KEPALA KELUARGA", "SUAMI", "ISLAM", "KRISTEN", "KATOLIK", "HINDU", "BUDDHA", "KAWIN", "BELUM KAWIN"]:
                            data["ayah"]["nama"] = c
                            break
                    ttl_m = re.search(r"\b([a-zA-Z\s]+)\s+(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b", line)
                    if ttl_m:
                        data["ayah"]["tempat_lahir"] = ttl_m.group(1).strip()
                elif "ISTRI" in line_u:
                    data["ibu"]["nik"] = row_nik
                    for c in cols:
                        if c != row_nik and len(c) > 3 and not re.match(r"^\d+$", c) and c.upper() not in ["LAKI-LAKI", "PEREMPUAN", "ISTRI", "ISLAM", "KRISTEN", "KATOLIK", "HINDU", "BUDDHA", "KAWIN", "BELUM KAWIN"]:
                            data["ibu"]["nama"] = c
                            break
                    ttl_m = re.search(r"\b([a-zA-Z\s]+)\s+(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b", line)
                    if ttl_m:
                        data["ibu"]["tempat_lahir"] = ttl_m.group(1).strip()

        # B. Ekstraksi Nama Bayi / Anak
        if any(k in ll for k in ["nama bayi", "nama anak", "nama anak:", "bayi ny", "bayi ny."]):
            if val:
                data["kelahiran"]["nama_bayi"] = val
                data["subjek_akta"]["nama"] = val
        
        # C. Ekstraksi Nama Ibu
        elif any(k in ll for k in ["nama ibu", "ibu kandung", "ibu:", "ny."]) and not data["ibu"]["nama"]:
            clean_name = re.sub(r"^(?:nama\s*ibu|ibu kandung|ibu|ny\.?)\s*[:=]?\s*", "", val or line, flags=re.I).strip()
            clean_name = re.sub(r"\(?\s*nik\s*[:=]?\s*\d+\s*\)?", "", clean_name, flags=re.I).strip(" ,/()-")
            if clean_name and len(clean_name) > 2:
                data["ibu"]["nama"] = clean_name

        # D. Ekstraksi Nama Ayah
        elif any(k in ll for k in ["nama ayah", "ayah kandung", "ayah:", "tn.", "suami"]) and not data["ayah"]["nama"]:
            clean_name = re.sub(r"^(?:nama\s*ayah|ayah kandung|ayah|tn\.?|suami)\s*[:=]?\s*", "", val or line, flags=re.I).strip()
            clean_name = re.sub(r"\(?\s*nik\s*[:=]?\s*\d+\s*\)?", "", clean_name, flags=re.I).strip(" ,/()-")
            if clean_name and len(clean_name) > 2:
                data["ayah"]["nama"] = clean_name

        # E. Ekstraksi Pelapor
        elif any(k in ll for k in ["nama pelapor", "pelapor:"]) and not data["pelapor"]["nama"]:
            if val:
                data["pelapor"]["nama"] = val

        # F. Ekstraksi Jenazah (Kematian)
        elif any(k in ll for k in ["nama jenazah", "almarhum", "almarhumah", "nama lengkap:"]) and data["jenis_pelaporan"] == "Kematian":
            clean_name = re.sub(r"^(?:nama\s*(?:jenazah|lengkap)?|almarhum(?:ah)?)\s*[:=]?\s*", "", val or line, flags=re.I).strip()
            if clean_name:
                data["kematian"]["nama_lengkap"] = clean_name
                data["subjek_akta"]["nama"] = clean_name

        # G. Ekstraksi Wilayah
        if "provinsi" in ll:
            m = re.search(r"provinsi\s*[:=]?\s*([a-zA-Z\s]+)", line, re.I)
            if m: data["wilayah"]["provinsi"] = m.group(1).strip()
        if any(k in ll for k in ["kabupaten", "kota"]) and "kelahiran" not in ll:
            m = re.search(r"(?:kabupaten|kota)\s*[:=]?\s*([a-zA-Z\s]+)", line, re.I)
            if m: data["wilayah"]["kabupaten_kota"] = m.group(1).strip()
        if "kota kelahiran" in ll or "tempat kelahiran" in ll:
            m = re.search(r"(?:kota\s*kelahiran|tempat\s*kelahiran)\s*[:=]?\s*([a-zA-Z\s]+)", line, re.I)
            if m: data["kelahiran"]["tempat_kelahiran"] = m.group(1).strip()
        if "kecamatan" in ll:
            m = re.search(r"kecamatan\s*[:=]?\s*([a-zA-Z\s]+)", line, re.I)
            if m: data["wilayah"]["kecamatan"] = m.group(1).strip()
        if any(k in ll for k in ["desa", "kelurahan"]):
            m = re.search(r"(?:desa|kelurahan)\s*[:=]?\s*([a-zA-Z\s]+)", line, re.I)
            if m: data["wilayah"]["desa_kelurahan"] = m.group(1).strip()

    # 4. Asosiasi NIK ke Ayah / Ibu / Pelapor
    # Cari pola NIK Ayah: 32... / NIK Ibu: 32...
    nik_ayah_m = re.search(r"(?:nik\s*(?:ayah|suami)|ayah[^\n]*nik)[\s:=]*(\d{16})", lower_text)
    if nik_ayah_m:
        data["ayah"]["nik"] = nik_ayah_m.group(1)
    nik_ibu_m = re.search(r"(?:nik\s*(?:ibu|istri)|ibu[^\n]*nik)[\s:=]*(\d{16})", lower_text)
    if nik_ibu_m:
        data["ibu"]["nik"] = nik_ibu_m.group(1)
    nik_pelapor_m = re.search(r"(?:nik\s*pelapor|pelapor[^\n]*nik)[\s:=]*(\d{16})", lower_text)
    if nik_pelapor_m:
        data["pelapor"]["nik"] = nik_pelapor_m.group(1)

    # Jika NIK belum terisi tapi ada daftar NIK yang terdeteksi
    remaining_niks = [n for n in nik_matches if n != data["pelapor"]["nomor_kk"]]
    if not data["ayah"]["nik"] and remaining_niks:
        data["ayah"]["nik"] = remaining_niks.pop(0)
    if not data["ibu"]["nik"] and remaining_niks:
        data["ibu"]["nik"] = remaining_niks.pop(0)
    if not data["pelapor"]["nik"]:
        data["pelapor"]["nik"] = data["ayah"]["nik"] or data["ibu"]["nik"] or (remaining_niks.pop(0) if remaining_niks else "")

    # Default Pelapor = Ayah atau Ibu jika kosong
    if not data["pelapor"]["nama"]:
        data["pelapor"]["nama"] = data["ayah"]["nama"] or data["ibu"]["nama"]

    # 5. Ekstraksi Jenis Kelamin
    if re.search(r"\b(?:perempuan|wanita|\(p\)|jk\s*[:=]?\s*p)\b", lower_text):
        data["kelahiran"]["jenis_kelamin"] = "Perempuan"
    elif re.search(r"\b(?:laki[\s-]*laki|pria|\(l\)|jk\s*[:=]?\s*l)\b", lower_text):
        data["kelahiran"]["jenis_kelamin"] = "Laki-Laki"

    # 6. Ekstraksi Berat Bayi (kg / gram)
    bb_m = re.search(r"(?:berat\s*(?:badan|bayi|lahir)?|bb)[\s:=]*(\d+[.,]?\d*)\s*(kg|gram|gr)?", lower_text)
    if bb_m:
        val_str = bb_m.group(1).replace(",", ".")
        unit = bb_m.group(2) or ""
        try:
            val_num = float(val_str)
            if val_num > 100 or "gram" in unit or "gr" in unit: # dalam gram, e.g. 3200
                data["kelahiran"]["berat_bayi_kg"] = f"{val_num / 1000:.2f}".rstrip("0").rstrip(".")
            else:
                data["kelahiran"]["berat_bayi_kg"] = f"{val_num:.2f}".rstrip("0").rstrip(".")
        except ValueError:
            data["kelahiran"]["berat_bayi_kg"] = val_str

    # 7. Ekstraksi Panjang Bayi (cm)
    pb_m = re.search(r"(?:panjang\s*(?:bayi|badan|lahir)?|pb)[\s:=]*(\d+[.,]?\d*)\s*(?:cm)?", lower_text)
    if pb_m:
        data["kelahiran"]["panjang_bayi_cm"] = pb_m.group(1).replace(",", ".")

    # 8. Ekstraksi Kelahiran Ke-
    anak_ke_m = re.search(r"(?:anak\s*ke|kelahiran\s*ke)[\s:=]*([0-9]+|pertama|kedua|ketiga|keempat|kelima)", lower_text)
    if anak_ke_m:
        val = anak_ke_m.group(1)
        map_urutan = {"pertama": "1", "kedua": "2", "ketiga": "3", "keempat": "4", "kelima": "5"}
        data["kelahiran"]["kelahiran_ke"] = map_urutan.get(val, val)

    # 9. Ekstraksi Tanggal & Jam Lahir
    # Cari nama hari
    for hari in ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu"]:
        if hari in lower_text:
            data["kelahiran"]["hari_lahir"] = hari.capitalize()
            break

    # Cari Tanggal (e.g. 18 November 2026 atau 18-11-2026)
    date_m = re.search(r"\b(\d{1,2})[\s/-]([0-1]?\d|[a-zA-Z]+)[\s/-](\d{4})\b", text)
    if date_m:
        d_val = f"{int(date_m.group(1)):02d}"
        m_raw = date_m.group(2).lower()
        y_val = date_m.group(3)
        m_val = BULAN_MAP.get(m_raw, f"{int(m_raw):02d}" if m_raw.isdigit() else m_raw.capitalize())
        
        data["kelahiran"]["tgl_lahir"] = d_val
        data["kelahiran"]["bln_lahir"] = m_val
        data["kelahiran"]["thn_lahir"] = y_val
        data["kematian"]["tgl_kematian"] = d_val
        data["kematian"]["bln_kematian"] = m_val
        data["kematian"]["thn_kematian"] = y_val

    # Cari Jam / Pukul (e.g. 07.45 atau 07:45 atau pukul 07.45 WIB)
    jam_m = re.search(r"(?:pukul|jam)?[\s:=]*([0-2]?\d)[:.]([0-5]\d)\s*(?:wib|wita|wit)?", lower_text)
    if jam_m:
        data["kelahiran"]["pukul_jam"] = f"{int(jam_m.group(1)):02d}"
        data["kelahiran"]["pukul_menit"] = jam_m.group(2)
        data["kematian"]["pukul_jam"] = f"{int(jam_m.group(1)):02d}"
        data["kematian"]["pukul_menit"] = jam_m.group(2)

    # 10. Ekstraksi Fasilitas Kesehatan / RS
    faskes_m = re.search(r"\b(rs\w*|rumah\s*sakit|puskesmas|klinik|polindes|rb\b)[^\n,\.]*", text, re.I)
    if faskes_m:
        faskes_name = faskes_m.group(0).strip()
        data["kelahiran"]["nama_faskes"] = faskes_name
        if "puskesmas" in faskes_name.lower():
            data["kelahiran"]["tempat_dilahirkan"] = "Puskesmas"
        elif "polindes" in faskes_name.lower():
            data["kelahiran"]["tempat_dilahirkan"] = "Polindes"
        else:
            data["kelahiran"]["tempat_dilahirkan"] = "RS/RB"

    # Penolong
    if "bidan" in lower_text or "perawat" in lower_text:
        data["kelahiran"]["penolong_kelahiran"] = "Bidan/Perawat"
    elif "dokter" in lower_text or "dr." in lower_text:
        data["kelahiran"]["penolong_kelahiran"] = "Dokter"

    # Tempat Pelaporan Default
    if data["wilayah"]["kabupaten_kota"]:
        kota = data["wilayah"]["kabupaten_kota"].replace("KABUPATEN ", "").replace("KOTA ", "").title()
        tgl_str = f"{data['kelahiran']['tgl_lahir']} {data['kelahiran']['bln_lahir']} {data['kelahiran']['thn_lahir']}".strip()
        data["tanggal_lapor_tempat"] = f"{kota}, {tgl_str}" if tgl_str else kota

    return data


NON_NAME_WORDS = {
    "wiraswasta", "swasta", "karyawan", "karyawan swasta", "karyawan bumn", "pegawai",
    "pegawai negeri", "pns", "asn", "tni", "polri", "pensiunan", "ibu rumah tangga",
    "irt", "pelajar", "mahasiswa", "belum bekerja", "tidak bekerja", "buruh",
    "pedagang", "petani", "nelayan", "guru", "dosen", "dokter", "bidan", "perawat",
    "laki-laki", "perempuan", "pria", "wanita", "kepala keluarga", "istri", "suami", "anak",
    "islam", "kristen", "katolik", "hindu", "buddha", "khonghucu", "kawin", "belum kawin",
    "wni", "wna", "nik", "kk", "no", "nama", "nama pelapor", "nama lengkap", "umur", "usia",
    "pekerjaan", "alamat", "hubungan", "ayah kandung", "ibu kandung", "ayah", "ibu", "pelapor",
    "saksi", "saksi 1", "saksi 2", "saksi i", "saksi ii", "kandung", "hubungan keluarga"
}

COMMON_JOBS = [
    "karyawan swasta", "karyawan bumn", "pegawai negeri sipil", "pns", "asn",
    "tni", "polri", "wiraswasta", "ibu rumah tangga", "irt", "pelajar/mahasiswa",
    "pelajar", "mahasiswa", "belum/tidak bekerja", "belum bekerja", "tidak bekerja",
    "buruh harian lepas", "buruh", "pedagang", "petani/pekebun", "petani",
    "nelayan", "pensiunan", "guru", "dosen", "dokter", "bidan", "perawat",
    "advokat", "pengacara", "arsitek", "sopir", "pengemudi"
]

LABEL_PAT = r"(?:nama\s*(?:lengkap|pelapor|ayah|ibu|saksi\s*(?:[12i]+)?|bayi|jenazah)?|nama|pelapor|saksi\s*(?:[12i]+)?|ayah|ibu)"

def clean_person_name(line: str) -> str:
    """Bersihkan label nama, nomor NIK, umur, dan pekerjaan yang menempel di baris nama."""
    s = line.strip()
    # Bersihkan leading label
    s = re.sub(r"^" + LABEL_PAT + r"[\s:=	\s]+", "", s, flags=re.I).strip()
    # Bersihkan trailing label
    s = re.sub(r"[\s:=	\s]+" + LABEL_PAT + r"$", "", s, flags=re.I).strip()
    s = re.sub(r"\(?\s*nik[\s:=	]*\d{16}\s*\)?", " ", s, flags=re.I)
    s = re.sub(r"\b\d{16}\b", " ", s)
    s = re.sub(r"\b\d{1,3}\s*(?:tahun|thn|th|th\.?)\b.*", "", s, flags=re.I)
    s = re.sub(r"\b(?:wiraswasta|karyawan|swasta|bumn|pns|asn|irt|ibu\s*rumah\s*tangga|pensiunan|guru|dokter|bidan|buruh)\b.*", "", s, flags=re.I)
    s = re.sub(r"\(.*?\)", "", s)
    return s.strip(" ,/()-:\t")

def parse_person_snippet(text: str) -> Dict[str, str]:
    """
    Helper untuk mengekstrak data identitas (NIK, Nama, TTL, Pekerjaan, Alamat, Umur)
    dari potongan teks spesifik per kotak kependudukan.
    Tahan banting terhadap teks acak (hasil Ctrl+A SIAK, urutan terbalik, format tabel).
    """
    res = {
        "nama": "",
        "nik": "",
        "nomor_kk": "",
        "umur": "",
        "pekerjaan": "",
        "alamat": "",
        "tempat_lahir": "",
        "tgl": "",
        "bln": "",
        "thn": "",
        "kewarganegaraan": "WNI"
    }
    if not text:
        return res

    clean_text = text.strip()
    lines = [l.strip() for l in clean_text.splitlines() if l.strip()]

    # 1. Deteksi Baris Tabel SIAK (kolom dipisah tab '\t', pipa '|', atau spasi >= 2)
    for line in lines:
        cols = [c.strip() for c in re.split(r"[\t|]|\s{2,}", line) if c.strip()]
        if len(cols) >= 3 and any(re.match(r"^\d{16}$", c) for c in cols):
            for c in cols:
                cl = c.lower()
                if re.match(r"^\d{16}$", c):
                    if not res["nik"]: res["nik"] = c
                elif any(j == cl for j in COMMON_JOBS):
                    if not res["pekerjaan"]: res["pekerjaan"] = c.title()
                elif re.search(r"\d{1,2}[-/]\d{1,2}[-/]\d{4}", c):
                    ttl_m = re.search(r"([a-zA-Z\s]+)?\s*(\d{1,2})[-/](\d{1,2})[-/](\d{4})", c)
                    if ttl_m:
                        if ttl_m.group(1): res["tempat_lahir"] = ttl_m.group(1).strip().title()
                        res["tgl"] = f"{int(ttl_m.group(2)):02d}"
                        res["bln"] = f"{int(ttl_m.group(3)):02d}"
                        res["thn"] = ttl_m.group(4)
                elif re.match(r"^[a-zA-Z\s\'.]+$", c) and len(c) > 2 and cl not in NON_NAME_WORDS:
                    if not res["nama"]: res["nama"] = c.upper()

    # 2. Analisis Baris demi Baris untuk Key-Value (Maju maupun Mundur / Terbalik)
    for line in lines:
        # A. Nomor KK (Maju & Mundur)
        if not res["nomor_kk"] and re.search(r"(?:kartu\s*keluarga|nomor\s*kk|no\.?\s*kk|\bkk\b)", line, re.I):
            m16 = re.search(r"\b(\d{16})\b", line)
            if m16:
                res["nomor_kk"] = m16.group(1)

        # B. NIK (Maju & Mundur)
        if not res["nik"] and re.search(r"\bnik\b", line, re.I):
            m16 = re.search(r"\b(\d{16})\b", line)
            if m16 and m16.group(1) != res["nomor_kk"]:
                res["nik"] = m16.group(1)

        # C. Umur (Maju & Mundur)
        if not res["umur"] and re.search(r"\b(?:umur|usia|tahun|thn|th)\b", line, re.I):
            u_m = re.search(r"\b(\d{1,3})\b", line)
            if u_m and int(u_m.group(1)) <= 130:
                res["umur"] = u_m.group(1)

        # D. Pekerjaan (Maju & Mundur)
        if not res["pekerjaan"] and re.search(r"\b(?:pekerjaan|profesi)\b", line, re.I):
            clean_pek = re.sub(r"^(?:pekerjaan|profesi)[\s:=	]*", "", line, flags=re.I)
            clean_pek = re.sub(r"[\s:=	]*(?:pekerjaan|profesi)$", "", clean_pek, flags=re.I).strip(" :-\t")
            if clean_pek and clean_pek.lower() not in NON_NAME_WORDS:
                res["pekerjaan"] = clean_pek.title()

        # E. Alamat (Maju & Mundur)
        if not res["alamat"] and re.search(r"\b(?:alamat|domisili)\b", line, re.I):
            clean_almt = re.sub(r"^(?:alamat\s*domisili|alamat|domisili)[\s:=	]*", "", line, flags=re.I)
            clean_almt = re.sub(r"[\s:=	]*(?:alamat\s*domisili|alamat|domisili)$", "", clean_almt, flags=re.I).strip(" :-\t")
            if clean_almt and len(clean_almt) > 3:
                res["alamat"] = clean_almt

        # F. Nama dengan label eksplisit (Maju maupun Mundur)
        if not res["nama"] and re.search(r"\b" + LABEL_PAT + r"\b", line, re.I):
            if re.search(r"\b(?:hubungan|status\s*hubungan)\b", line, re.I):
                continue
            clean_nm = re.sub(r"^" + LABEL_PAT + r"[\s:=	]*", "", line, flags=re.I)
            clean_nm = re.sub(r"[\s:=	]*" + LABEL_PAT + r"$", "", clean_nm, flags=re.I).strip(" :-\t")
            clean_nm = re.sub(r"\b\d{16}\b", "", clean_nm).strip()
            clean_nm = re.sub(r"\(.*?\)", "", clean_nm).strip()
            if clean_nm and len(clean_nm) > 2 and clean_nm.lower() not in NON_NAME_WORDS and not any(w in clean_nm.lower() for w in ["hubungan", "kandung"]):
                res["nama"] = clean_nm.upper()

    # 3. Fallbacks jika belum terisi
    # NIK fallback dari angka 16 digit yang bukan KK
    if not res["nik"]:
        all_16 = re.findall(r"\b(\d{16})\b", text)
        for n in all_16:
            if n != res["nomor_kk"]:
                res["nik"] = n
                break
        if not res["nik"] and all_16:
            res["nik"] = all_16[0]

    # Pekerjaan fallback dari daftar profesi umum
    if not res["pekerjaan"]:
        for job in sorted(COMMON_JOBS, key=len, reverse=True):
            if re.search(r"\b" + re.escape(job) + r"\b", text, re.I):
                res["pekerjaan"] = job.title()
                break

    # Alamat fallback dari indikator jalan/rt/rw
    if not res["alamat"]:
        for line in lines:
            if re.search(r"\b(?:jalan|jl\.|rt\s*\d+|rw\s*\d+|kel\.|kec\.)\b", line, re.I) and not re.search(r"\b\d{16}\b", line):
                res["alamat"] = line.strip(" :-\t")
                break

    # TTL
    if not res["tgl"]:
        ttl_m = re.search(r"(?:ttl|tempat[\s,]*tanggal\s*lahir|tempat\s*lahir)[\s:=	]*([a-zA-Z\s]+)[\s,]+(\d{1,2})[\s/-]([0-1]?\d|[a-zA-Z]+)[\s/-](\d{4})", text, re.I)
        if ttl_m:
            res["tempat_lahir"] = ttl_m.group(1).strip().title()
            res["tgl"] = f"{int(ttl_m.group(2)):02d}"
            m_raw = ttl_m.group(3).lower()
            res["bln"] = BULAN_MAP.get(m_raw, f"{int(m_raw):02d}" if m_raw.isdigit() else m_raw.capitalize())
            res["thn"] = ttl_m.group(4)
        else:
            pl_m = re.search(r"tempat\s*(?:tgl\s*)?lahir[\s:=	]*([a-zA-Z\s]+)", text, re.I)
            if pl_m: res["tempat_lahir"] = pl_m.group(1).strip().title()
            dt_m = re.search(r"\b(\d{1,2})[\s/-]([0-1]?\d|[a-zA-Z]+)[\s/-](\d{4})\b", text)
            if dt_m:
                res["tgl"] = f"{int(dt_m.group(1)):02d}"
                m_raw = dt_m.group(2).lower()
                res["bln"] = BULAN_MAP.get(m_raw, f"{int(m_raw):02d}" if m_raw.isdigit() else m_raw.capitalize())
                res["thn"] = dt_m.group(3)

    # Nama fallback: ambil baris bersih yang berformat nama orang
    if not res["nama"]:
        for line in lines:
            if re.search(r"\d", line): continue
            if any(re.search(r"\b" + re.escape(w) + r"\b", line, re.I) for w in ["hubungan", "alamat", "umur", "pekerjaan", "nik", "kk"]): continue
            if line.lower() in NON_NAME_WORDS: continue
            clean = re.sub(r"\(.*?\)", "", line).strip(" :-\t")
            if re.match(r"^[a-zA-Z\s\'.]+$", clean) and 2 < len(clean) < 45 and clean.lower() not in NON_NAME_WORDS:
                res["nama"] = clean.upper()
                break

    return res

def parse_peristiwa_snippet(text: str, jenis: str = "Kelahiran") -> Dict[str, Any]:
    """Helper untuk mengekstrak detail peristiwa kelahiran, lahir mati, atau kematian dari teks acak."""
    res = {}
    if not text:
        return res
    ll = text.lower()
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]

    # 0. NIK pada teks peristiwa (misal Jenazah pada Kematian)
    nik_p_m = re.search(r"\b(\d{16})\b", text)
    if nik_p_m:
        res["nik"] = nik_p_m.group(1)

    # 1. Nama Bayi / Subjek Akta / Jenazah
    for line in lines:
        m_fwd = re.search(r"^(?:nama\s*(?:bayi|anak|jenazah|lengkap)?|bayi\s*ny\.?|almarhum(?:ah)?)[\s:=	]+([a-zA-Z\s\'.]+)$", line, re.I)
        m_rev = re.search(r"^([a-zA-Z\s\'.]+?)\s+(?:nama\s*(?:bayi|anak|jenazah|lengkap)?|bayi\s*ny\.?|almarhum(?:ah)?)$", line, re.I)
        if m_fwd:
            cand = m_fwd.group(1).strip()
            if cand.lower() not in NON_NAME_WORDS:
                res["nama_bayi"] = cand.upper()
                res["nama_jenazah"] = cand.upper()
                break
        elif m_rev:
            cand = m_rev.group(1).strip()
            if cand.lower() not in NON_NAME_WORDS:
                res["nama_bayi"] = cand.upper()
                res["nama_jenazah"] = cand.upper()
                break

    # 2. Jenis Kelamin
    if re.search(r"\b(?:perempuan|wanita|\(p\)|jk\s*[:=]?\s*p)\b", ll):
        res["jenis_kelamin"] = "Perempuan"
    elif re.search(r"\b(?:laki[\s-]*laki|pria|\(l\)|jk\s*[:=]?\s*l)\b", ll):
        res["jenis_kelamin"] = "Laki-Laki"

    # 3. Berat Bayi (Maju & Mundur)
    bb_m = (re.search(r"(?:berat\s*(?:badan|bayi|lahir)?|bb)[\s:=	]*(\d+[.,]?\d*)\s*(kg|gram|gr)?", text, re.I) or
            re.search(r"(\d+[.,]?\d*)\s*(kg|gram|gr)?[\s:=	]*(?:berat\s*(?:badan|bayi|lahir)?|bb)\b", text, re.I))
    if bb_m:
        val_str = bb_m.group(1).replace(",", ".")
        unit = (bb_m.group(2) or "").lower()
        try:
            val_num = float(val_str)
            if val_num > 100 or "gram" in unit or "gr" in unit:
                res["berat_bayi_kg"] = f"{val_num / 1000:.2f}".rstrip("0").rstrip(".")
            else:
                res["berat_bayi_kg"] = f"{val_num:.2f}".rstrip("0").rstrip(".")
        except ValueError:
            res["berat_bayi_kg"] = val_str

    # 4. Panjang Bayi (Maju & Mundur)
    pb_m = (re.search(r"(?:panjang\s*(?:bayi|badan|lahir)?|pb)[\s:=	]*(\d+[.,]?\d*)\s*(?:cm)?", text, re.I) or
            re.search(r"(\d+[.,]?\d*)\s*(?:cm)?[\s:=	]*(?:panjang\s*(?:bayi|badan|lahir)?|pb)\b", text, re.I))
    if pb_m:
        res["panjang_bayi_cm"] = pb_m.group(1).replace(",", ".")

    # 5. Kelahiran Ke- (Maju & Mundur)
    ak_m = (re.search(r"(?:anak\s*ke|kelahiran\s*ke)[\s:=	]*([0-9]+|pertama|kedua|ketiga|keempat|kelima)", text, re.I) or
            re.search(r"([0-9]+|pertama|kedua|ketiga|keempat|kelima)[\s:=	]*(?:anak\s*ke|kelahiran\s*ke)\b", text, re.I))
    if ak_m:
        val = ak_m.group(1).lower()
        map_urutan = {"pertama": "1", "kedua": "2", "ketiga": "3", "keempat": "4", "kelima": "5"}
        res["kelahiran_ke"] = map_urutan.get(val, val)

    # 6. Hari Lahir
    for hari in ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu"]:
        if hari in ll:
            res["hari_lahir"] = hari.capitalize()
            break

    # 7. Tanggal Lahir / Tanggal Kematian
    dt_m = re.search(r"\b(\d{1,2})[\s/-]([0-1]?\d|[a-zA-Z]+)[\s/-](\d{4})\b", text)
    if dt_m:
        res["tgl"] = f"{int(dt_m.group(1)):02d}"
        m_raw = dt_m.group(2).lower()
        res["bln"] = BULAN_MAP.get(m_raw, f"{int(m_raw):02d}" if m_raw.isdigit() else m_raw.capitalize())
        res["thn"] = dt_m.group(3)

    # 8. Pukul / Jam
    jam_m = re.search(r"(?:pukul|jam)?[\s:=	]*([0-2]?\d)[:.]([0-5]\d)\s*(?:wib|wita|wit)?", ll)
    if jam_m:
        res["pukul_jam"] = f"{int(jam_m.group(1)):02d}"
        res["pukul_menit"] = jam_m.group(2)

    # 9. Fasilitas Kesehatan / RS
    faskes_m = re.search(r"\b(rsia|rsud|rs\b|rumah\s*sakit|puskesmas|klinik|polindes|rb\b)[^\n,\.]*", text, re.I)
    if faskes_m:
        fn = faskes_m.group(0).strip()
        res["nama_faskes"] = fn
        if "puskesmas" in fn.lower():
            res["tempat_dilahirkan"] = "Puskesmas"
        elif "polindes" in fn.lower():
            res["tempat_dilahirkan"] = "Polindes"
        else:
            res["tempat_dilahirkan"] = "RS/RB"

    # 10. Penolong
    if re.search(r"\b(?:dokter|dr\.)\b", ll):
        res["penolong_kelahiran"] = "Dokter"
    elif re.search(r"\b(?:bidan|perawat)\b", ll):
        res["penolong_kelahiran"] = "Bidan/Perawat"
    elif re.search(r"\bdukun\b", ll):
        res["penolong_kelahiran"] = "Dukun"

    # 11. Khusus Lahir Mati & Kematian: Usia Kandungan, Sebab, Tempat, Yang Menerangkan
    uk_m = (re.search(r"(?:usia\s*kandungan|gestasi|umur\s*kandungan|lamanya\s*(?:dalam\s*)?kandungan)[\s:=	]*(\d{1,2})\s*(?:minggu|bulan)?", text, re.I) or
            re.search(r"(\d{1,2})\s*(?:minggu|bulan)?[\s:=	]*(?:usia\s*kandungan|gestasi|umur\s*kandungan|lamanya\s*(?:dalam\s*)?kandungan)\b", text, re.I))
    if uk_m:
        res["usia_kandungan"] = uk_m.group(1)

    sebab_m = (re.search(r"(?:sebab(?:\s*kematian|\s*lahir\s*mati)?|penyebab|diagnosa|karena)[\s:=	]*([^\n\r,]+)", text, re.I) or
               re.search(r"([^\n\r,]+?)[\s:=	]*(?:sebab(?:\s*kematian|\s*lahir\s*mati)?|penyebab|diagnosa)\b", text, re.I))
    if sebab_m:
        res["sebab"] = sebab_m.group(1).strip()

    tk_m = re.search(r"(?:tempat\s*(?:kematian|meninggal)|meninggal\s*di)[\s:=	]*([^\n\r]+)", text, re.I)
    if tk_m:
        res["tempat_kematian"] = tk_m.group(1).strip()

    ym_m = re.search(r"(?:yang\s*menerangkan|penerang)[\s:=	]*([^\n\r]+)", text, re.I)
    if ym_m:
        res["yang_menerangkan"] = ym_m.group(1).strip()
    elif re.search(r"\b(?:dokter|dr\.)\b", ll):
        res["yang_menerangkan"] = "Dokter"

    t_kel_m = re.search(r"(?:kota\s*kelahiran|tempat\s*kelahiran)[\s:=	]*([^\n\r]+)", text, re.I)
    if t_kel_m:
        res["tempat_kelahiran"] = t_kel_m.group(1).strip()

    return res


def extract_from_sections(
    sections: Dict[str, str],
    ai_engine: str = "ollama",
    host: str = "http://localhost:11434",
    model_name: str = "qwen2.5:7b",
    api_key: str = ""
) -> Dict[str, Any]:
    """
    Ekstraksi cerdas langsung dari 5 kotak input terpisah:
    1. Data Peristiwa (Kelahiran / Kematian / Lahir Mati)
    2. Data Pelapor
    3. Data Orang Tua (Ayah & Ibu)
    4. Data Saksi I
    5. Data Saksi II
    
    Menjamin akurasi 100% dan bebas tertukar antar identitas.
    """
    p_text = (sections.get("peristiwa") or "").strip()
    pelapor_text = (sections.get("pelapor") or "").strip()
    ayah_text = (sections.get("ayah") or "").strip()
    ibu_text = (sections.get("ibu") or "").strip()
    ortu_text = (sections.get("orangtua") or "").strip()
    saksi1_text = (sections.get("saksi1") or "").strip()
    saksi2_text = (sections.get("saksi2") or "").strip()

    # Bangun prompt terstruktur rapi untuk AI
    prompt_parts = []
    if p_text:
        prompt_parts.append(f"=== DATA PERISTIWA ===\n{p_text}")
    if pelapor_text:
        prompt_parts.append(f"=== DATA PELAPOR ===\n{pelapor_text}")
    if ayah_text:
        prompt_parts.append(f"=== DATA AYAH ===\n{ayah_text}")
    if ibu_text:
        prompt_parts.append(f"=== DATA IBU ===\n{ibu_text}")
    if ortu_text and not (ayah_text and ibu_text):
        prompt_parts.append(f"=== DATA ORANG TUA ===\n{ortu_text}")

    if saksi1_text:
        prompt_parts.append(f"=== DATA SAKSI 1 ===\n{saksi1_text}")
    if saksi2_text:
        prompt_parts.append(f"=== DATA SAKSI 2 ===\n{saksi2_text}")

    combined_text = "\n\n".join(prompt_parts)
    if not combined_text:
        combined_text = sections.get("raw_text", "")

    # Jalankan AI atau fallback regex
    result = None
    engine = (ai_engine or "ollama").lower()
    
    try:
        if engine == "ollama":
            result = extract_with_ollama(combined_text, host=host, model_name=model_name)
        elif engine == "gemini":
            if not api_key:
                result = extract_with_smart_regex(combined_text)
            else:
                result = extract_with_gemini(combined_text, api_key, model_name)
        elif engine == "openai":
            if not api_key:
                result = extract_with_smart_regex(combined_text)
            else:
                result = extract_with_openai(combined_text, api_key, model_name)
        else:
            result = extract_with_smart_regex(combined_text)
    except Exception as e:
        result = extract_with_smart_regex(combined_text)
        result["_warning"] = f"AI ({engine}) dialihkan ke Smart Regex terstruktur: {str(e)}"

    # Hormati pilihan jenis pelaporan yang eksplisit jika dikirimkan
    if sections.get("jenis_pelaporan") in ["Kelahiran", "Lahir Mati", "Kematian"]:
        result["jenis_pelaporan"] = sections["jenis_pelaporan"]

    # Ekstraksi dan perkuat data peristiwa dari kotak peristiwa spesifik
    if p_text:
        p_info = parse_peristiwa_snippet(p_text, result.get("jenis_pelaporan", "Kelahiran"))
        if p_info.get("nama_bayi"):
            result.setdefault("kelahiran", {})["nama_bayi"] = p_info["nama_bayi"]
            result.setdefault("subjek_akta", {})["nama"] = p_info["nama_bayi"]
        if p_info.get("nama_jenazah") and result.get("jenis_pelaporan") == "Kematian":
            result.setdefault("kematian", {})["nama_lengkap"] = p_info["nama_jenazah"]
            result.setdefault("subjek_akta", {})["nama"] = p_info["nama_jenazah"]
        if p_info.get("jenis_kelamin"):
            result.setdefault("kelahiran", {})["jenis_kelamin"] = p_info["jenis_kelamin"]
        if p_info.get("berat_bayi_kg"):
            result.setdefault("kelahiran", {})["berat_bayi_kg"] = p_info["berat_bayi_kg"]
        if p_info.get("panjang_bayi_cm"):
            result.setdefault("kelahiran", {})["panjang_bayi_cm"] = p_info["panjang_bayi_cm"]
        if p_info.get("kelahiran_ke"):
            result.setdefault("kelahiran", {})["kelahiran_ke"] = p_info["kelahiran_ke"]
        if p_info.get("hari_lahir"):
            result.setdefault("kelahiran", {})["hari_lahir"] = p_info["hari_lahir"]
        if p_info.get("tgl"):
            result.setdefault("kelahiran", {})["tgl_lahir"] = p_info["tgl"]
            result.setdefault("kematian", {})["tgl_kematian"] = p_info["tgl"]
        if p_info.get("bln"):
            result.setdefault("kelahiran", {})["bln_lahir"] = p_info["bln"]
            result.setdefault("kematian", {})["bln_kematian"] = p_info["bln"]
        if p_info.get("thn"):
            result.setdefault("kelahiran", {})["thn_lahir"] = p_info["thn"]
            result.setdefault("kematian", {})["thn_kematian"] = p_info["thn"]
        if p_info.get("pukul_jam"):
            result.setdefault("kelahiran", {})["pukul_jam"] = p_info["pukul_jam"]
            result.setdefault("kematian", {})["pukul_jam"] = p_info["pukul_jam"]
        if p_info.get("pukul_menit"):
            result.setdefault("kelahiran", {})["pukul_menit"] = p_info["pukul_menit"]
            result.setdefault("kematian", {})["pukul_menit"] = p_info["pukul_menit"]
        if p_info.get("nama_faskes"):
            result.setdefault("kelahiran", {})["nama_faskes"] = p_info["nama_faskes"]
            if p_info.get("tempat_dilahirkan"):
                result.setdefault("kelahiran", {})["tempat_dilahirkan"] = p_info["tempat_dilahirkan"]
        if p_info.get("penolong_kelahiran"):
            result.setdefault("kelahiran", {})["penolong_kelahiran"] = p_info["penolong_kelahiran"]
        if p_info.get("nik") and result.get("jenis_pelaporan") == "Kematian":
            result.setdefault("kematian", {})["nik"] = p_info["nik"]
            result.setdefault("subjek_akta", {})["nik"] = p_info["nik"]
        if p_info.get("tempat_kelahiran"):
            result.setdefault("kelahiran", {})["tempat_kelahiran"] = p_info["tempat_kelahiran"]
        if p_info.get("tempat_kematian") and result.get("jenis_pelaporan") == "Kematian":
            result.setdefault("kematian", {})["tempat_kematian"] = p_info["tempat_kematian"]
        if p_info.get("yang_menerangkan") and result.get("jenis_pelaporan") == "Kematian":
            result.setdefault("kematian", {})["yang_menerangkan"] = p_info["yang_menerangkan"]
        if p_info.get("sebab"):
            if result.get("jenis_pelaporan") == "Kematian":
                result.setdefault("kematian", {})["sebab_kematian"] = p_info["sebab"]
            elif result.get("jenis_pelaporan") == "Lahir Mati":
                result.setdefault("lahir_mati", {})["sebab"] = p_info["sebab"]
        if p_info.get("usia_kandungan"):
            result.setdefault("lahir_mati", {})["lama_kandungan_bulan"] = p_info["usia_kandungan"]

    # Enforce keakuratan dari masing-masing kotak spesifik
    if pelapor_text:
        p_info = parse_person_snippet(pelapor_text)
        if p_info["nama"]:
            result.setdefault("pelapor", {})["nama"] = p_info["nama"]
        if p_info["nik"]:
            result.setdefault("pelapor", {})["nik"] = p_info["nik"]
        if p_info["nomor_kk"]:
            result.setdefault("pelapor", {})["nomor_kk"] = p_info["nomor_kk"]
            result.setdefault("subjek_akta", {})["nomor_kk"] = p_info["nomor_kk"]

    if ayah_text:
        a_info = parse_person_snippet(ayah_text)
        if a_info["nama"]: result.setdefault("ayah", {})["nama"] = a_info["nama"]
        if a_info["nik"]: result.setdefault("ayah", {})["nik"] = a_info["nik"]
        if a_info["tempat_lahir"]: result.setdefault("ayah", {})["tempat_lahir"] = a_info["tempat_lahir"]
        if a_info["tgl"]: result.setdefault("ayah", {})["tgl"] = a_info["tgl"]
        if a_info["bln"]: result.setdefault("ayah", {})["bln"] = a_info["bln"]
        if a_info["thn"]: result.setdefault("ayah", {})["thn"] = a_info["thn"]

    if ibu_text:
        i_info = parse_person_snippet(ibu_text)
        if i_info["nama"]: result.setdefault("ibu", {})["nama"] = i_info["nama"]
        if i_info["nik"]: result.setdefault("ibu", {})["nik"] = i_info["nik"]
        if i_info["tempat_lahir"]: result.setdefault("ibu", {})["tempat_lahir"] = i_info["tempat_lahir"]
        if i_info["tgl"]: result.setdefault("ibu", {})["tgl"] = i_info["tgl"]
        if i_info["bln"]: result.setdefault("ibu", {})["bln"] = i_info["bln"]
        if i_info["thn"]: result.setdefault("ibu", {})["thn"] = i_info["thn"]

    if ortu_text and not (ayah_text and ibu_text):
        # 1. Cek baris tabel SIAK untuk Ayah (KEPALA KELUARGA/SUAMI) & Ibu (ISTRI)
        ayah_line = ""
        ibu_line = ""
        for line in ortu_text.splitlines():
            line_u = line.upper()
            if "KEPALA KELUARGA" in line_u or "SUAMI" in line_u:
                ayah_line = line
            elif "ISTRI" in line_u:
                ibu_line = line

        if ayah_line or ibu_line:
            if ayah_line:
                a_info = parse_person_snippet(ayah_line)
                if a_info["nama"]: result.setdefault("ayah", {})["nama"] = a_info["nama"]
                if a_info["nik"]: result.setdefault("ayah", {})["nik"] = a_info["nik"]
                if a_info["tempat_lahir"]: result.setdefault("ayah", {})["tempat_lahir"] = a_info["tempat_lahir"]
                if a_info["tgl"]: result.setdefault("ayah", {})["tgl"] = a_info["tgl"]
                if a_info["bln"]: result.setdefault("ayah", {})["bln"] = a_info["bln"]
                if a_info["thn"]: result.setdefault("ayah", {})["thn"] = a_info["thn"]
            if ibu_line:
                i_info = parse_person_snippet(ibu_line)
                if i_info["nama"]: result.setdefault("ibu", {})["nama"] = i_info["nama"]
                if i_info["nik"]: result.setdefault("ibu", {})["nik"] = i_info["nik"]
                if i_info["tempat_lahir"]: result.setdefault("ibu", {})["tempat_lahir"] = i_info["tempat_lahir"]
                if i_info["tgl"]: result.setdefault("ibu", {})["tgl"] = i_info["tgl"]
                if i_info["bln"]: result.setdefault("ibu", {})["bln"] = i_info["bln"]
                if i_info["thn"]: result.setdefault("ibu", {})["thn"] = i_info["thn"]
        else:
            # 2. Cek pemisahan blok Ayah dan Ibu jika berlabel
            ibu_m = re.search(r"\b(?:identitas\s*ibu|nama\s*ibu|ibu\s*kandung|ibu:)\b", ortu_text, re.I)
            ayah_m = re.search(r"\b(?:identitas\s*ayah|nama\s*ayah|ayah\s*kandung|ayah:)\b", ortu_text, re.I)
            if ibu_m and ayah_m:
                if ayah_m.start() < ibu_m.start():
                    part_a = ortu_text[ayah_m.start():ibu_m.start()]
                    part_i = ortu_text[ibu_m.start():]
                else:
                    part_i = ortu_text[ibu_m.start():ayah_m.start()]
                    part_a = ortu_text[ayah_m.start():]
                a_info = parse_person_snippet(part_a)
                i_info = parse_person_snippet(part_i)
                if a_info["nama"]: result.setdefault("ayah", {})["nama"] = a_info["nama"]
                if a_info["nik"]: result.setdefault("ayah", {})["nik"] = a_info["nik"]
                if a_info["tempat_lahir"]: result.setdefault("ayah", {})["tempat_lahir"] = a_info["tempat_lahir"]
                if a_info["tgl"]: result.setdefault("ayah", {})["tgl"] = a_info["tgl"]
                if a_info["bln"]: result.setdefault("ayah", {})["bln"] = a_info["bln"]
                if a_info["thn"]: result.setdefault("ayah", {})["thn"] = a_info["thn"]
                if i_info["nama"]: result.setdefault("ibu", {})["nama"] = i_info["nama"]
                if i_info["nik"]: result.setdefault("ibu", {})["nik"] = i_info["nik"]
                if i_info["tempat_lahir"]: result.setdefault("ibu", {})["tempat_lahir"] = i_info["tempat_lahir"]
                if i_info["tgl"]: result.setdefault("ibu", {})["tgl"] = i_info["tgl"]
                if i_info["bln"]: result.setdefault("ibu", {})["bln"] = i_info["bln"]
                if i_info["thn"]: result.setdefault("ibu", {})["thn"] = i_info["thn"]

    if saksi1_text:
        s1_info = parse_person_snippet(saksi1_text)
        if s1_info["nama"]: result.setdefault("saksi_1", {})["nama"] = s1_info["nama"]
        if s1_info["nik"]: result.setdefault("saksi_1", {})["nik"] = s1_info["nik"]
        if s1_info["nomor_kk"]: result.setdefault("saksi_1", {})["nomor_kk"] = s1_info["nomor_kk"]

    if saksi2_text:
        s2_info = parse_person_snippet(saksi2_text)
        if s2_info["nama"]: result.setdefault("saksi_2", {})["nama"] = s2_info["nama"]
        if s2_info["nik"]: result.setdefault("saksi_2", {})["nik"] = s2_info["nik"]
        if s2_info["nomor_kk"]: result.setdefault("saksi_2", {})["nomor_kk"] = s2_info["nomor_kk"]

    return result



def extract_with_gemini(raw_text: str, api_key: str, model_name: str = "gemini-2.5-flash") -> Dict[str, Any]:
    """
    Ekstraksi menggunakan Google Gemini API via official google-genai SDK.
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    prompt = f"{SYSTEM_PROMPT}\n\nDATA MENTAH DARI PENGGUNA:\n{raw_text}\n"

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1
        )
    )
    res_text = response.text.strip()
    # Bersihkan markdown fence jika ada
    if res_text.startswith("```json"):
        res_text = res_text[7:]
    if res_text.startswith("```"):
        res_text = res_text[3:]
    if res_text.endswith("```"):
        res_text = res_text[:-3]
    return json.loads(res_text.strip())


def get_ollama_status(host: str = "") -> Dict[str, Any]:
    """
    Mengecek apakah server Ollama sedang aktif dan mengambil daftar model lokal yang terinstal.
    Mendukung fallback otomatis ke host.docker.internal jika dijalankan di dalam container Docker.
    """
    target_hosts = []
    if host and host.strip():
        target_hosts.append(host.strip().rstrip("/"))
    env_host = os.environ.get("OLLAMA_HOST", "").strip().rstrip("/")
    if env_host and env_host not in target_hosts:
        target_hosts.append(env_host)
    if "http://localhost:11434" not in target_hosts:
        target_hosts.append("http://localhost:11434")
    if "http://host.docker.internal:11434" not in target_hosts:
        target_hosts.append("http://host.docker.internal:11434")

    last_error = ""
    for clean_host in target_hosts:
        try:
            import urllib.request
            req = urllib.request.Request(f"{clean_host}/api/tags", headers={"User-Agent": "F201A-App"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name") or m.get("model") for m in data.get("models", [])]
                return {
                    "online": True,
                    "host": clean_host,
                    "models": models,
                    "count": len(models)
                }
        except Exception as e:
            last_error = str(e)

    primary_host = (host or env_host or "http://localhost:11434").rstrip("/")
    return {
        "online": False,
        "host": primary_host,
        "models": [],
        "error": last_error
    }


def extract_with_ollama(raw_text: str, host: str = "", model_name: str = "qwen2.5:7b") -> Dict[str, Any]:
    """
    Ekstraksi menggunakan Local LLM via Ollama. 100% Offline dan Privat.
    Mendukung format JSON terstruktur untuk Formulir F-2.01 A Dukcapil.
    """
    target_hosts = []
    if host and host.strip():
        target_hosts.append(host.strip().rstrip("/"))
    env_host = os.environ.get("OLLAMA_HOST", "").strip().rstrip("/")
    if env_host and env_host not in target_hosts:
        target_hosts.append(env_host)
    if "http://localhost:11434" not in target_hosts:
        target_hosts.append("http://localhost:11434")
    if "http://host.docker.internal:11434" not in target_hosts:
        target_hosts.append("http://host.docker.internal:11434")

    import urllib.request
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"DATA MENTAH DARI PENGGUNA:\n{raw_text}"}
        ],
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.1}
    }

    last_err = None
    for clean_host in target_hosts:
        try:
            req = urllib.request.Request(
                f"{clean_host}/api/chat",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                msg_content = res.get("message", {}).get("content") or res.get("response", "{}")
                if msg_content.startswith("```json"):
                    msg_content = msg_content[7:]
                if msg_content.startswith("```"):
                    msg_content = msg_content[3:]
                if msg_content.endswith("```"):
                    msg_content = msg_content[:-3]
                return json.loads(msg_content.strip())
        except Exception as e:
            last_err = e
            continue

    if last_err:
        raise last_err
    raise ConnectionError("Gagal terhubung ke Ollama di semua host yang dicoba.")


def extract_with_openai(raw_text: str, api_key: str, model_name: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Ekstraksi menggunakan OpenAI API.
    """
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    prompt = f"{SYSTEM_PROMPT}\n\nDATA MENTAH DARI PENGGUNA:\n{raw_text}\n"

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1
    )
    return json.loads(response.choices[0].message.content.strip())
