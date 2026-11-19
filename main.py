import os
import io
import json
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import extractor
import pdf_engine

app = FastAPI(title="Generator Formulir F-2.01 A", description="Ekstraksi AI & PDF Generator F-2.01 A Dukcapil")

USER_TEMPLATE = os.path.join(os.path.dirname(__file__), "Formulir F-2.01 A (Kelahiran, Lahir Mati, Kematian) (1).pdf")
TEMPLATE_PDF = USER_TEMPLATE if os.path.exists(USER_TEMPLATE) else os.path.join(os.path.dirname(__file__), "F-2.01 A.pdf")

# Request Schemas
class ExtractRequest(BaseModel):
    raw_text: Optional[str] = ""
    jenis_pelaporan: Optional[str] = "Kelahiran" # "Kelahiran", "Lahir Mati", "Kematian"
    # 5 Box Specific Fields
    text_peristiwa: Optional[str] = ""
    text_pelapor: Optional[str] = ""
    text_orangtua: Optional[str] = ""
    text_ayah: Optional[str] = ""
    text_ibu: Optional[str] = ""
    text_saksi1: Optional[str] = ""
    text_saksi2: Optional[str] = ""
    
    ai_engine: Optional[str] = "ollama" # "ollama", "regex", "gemini", "openai"
    api_key: Optional[str] = ""
    model_name: Optional[str] = "qwen2.5:7b"
    ollama_host: Optional[str] = "http://localhost:11434"

class GeneratePdfRequest(BaseModel):
    data: Dict[str, Any]
    single_page: Optional[bool] = True

class ExtractAndGenerateRequest(BaseModel):
    raw_text: Optional[str] = ""
    jenis_pelaporan: Optional[str] = "Kelahiran"
    text_peristiwa: Optional[str] = ""
    text_pelapor: Optional[str] = ""
    text_orangtua: Optional[str] = ""
    text_ayah: Optional[str] = ""
    text_ibu: Optional[str] = ""
    text_saksi1: Optional[str] = ""
    text_saksi2: Optional[str] = ""
    
    ai_engine: Optional[str] = "ollama"
    api_key: Optional[str] = ""
    model_name: Optional[str] = "qwen2.5:7b"
    ollama_host: Optional[str] = "http://localhost:11434"
    single_page: Optional[bool] = True

# Helper to execute extraction
def do_extraction(req: ExtractRequest) -> Dict[str, Any]:
    sections = {
        "peristiwa": (req.text_peristiwa or "").strip(),
        "pelapor": (req.text_pelapor or "").strip(),
        "orangtua": (req.text_orangtua or "").strip(),
        "ayah": (req.text_ayah or "").strip(),
        "ibu": (req.text_ibu or "").strip(),
        "saksi1": (req.text_saksi1 or "").strip(),
        "saksi2": (req.text_saksi2 or "").strip(),
        "raw_text": (req.raw_text or "").strip(),
        "jenis_pelaporan": req.jenis_pelaporan or "Kelahiran"
    }
    
    has_sections = any([
        sections["peristiwa"],
        sections["pelapor"],
        sections["orangtua"],
        sections["ayah"],
        sections["ibu"],
        sections["saksi1"],
        sections["saksi2"]
    ])
    
    if not has_sections and not sections["raw_text"]:
        raise HTTPException(status_code=400, detail="Silakan isi salah satu atau lebih kotak input data terlebih dahulu.")
        
    engine = (req.ai_engine or "ollama").lower()
    host = req.ollama_host or "http://localhost:11434"
    model = req.model_name or "qwen2.5:7b"
    api_key = req.api_key or ""
    
    if has_sections:
        res = extractor.extract_from_sections(
            sections=sections,
            ai_engine=engine,
            host=host,
            model_name=model,
            api_key=api_key
        )
    else:
        text = sections["raw_text"]
        try:
            if engine == "ollama":
                res = extractor.extract_with_ollama(text, host, model)
            elif engine == "gemini":
                if not api_key:
                    res = extractor.extract_with_smart_regex(text)
                    res["_info"] = "API Key Gemini kosong; menggunakan Smart Regex Parser bawaan."
                else:
                    res = extractor.extract_with_gemini(text, api_key, model or "gemini-2.5-flash")
            elif engine == "openai":
                if not api_key:
                    res = extractor.extract_with_smart_regex(text)
                    res["_info"] = "API Key OpenAI kosong; menggunakan Smart Regex Parser bawaan."
                else:
                    res = extractor.extract_with_openai(text, api_key, model or "gpt-4o-mini")
            else:
                res = extractor.extract_with_smart_regex(text)
        except Exception as e:
            res = extractor.extract_with_smart_regex(text)
            res["_warning"] = f"Panggilan AI ({engine}) dialihkan ke Smart Regex otomatis: {str(e)}"

    if req.jenis_pelaporan:
        res["jenis_pelaporan"] = req.jenis_pelaporan
    return res

@app.get("/api/ollama/status")
def api_ollama_status(host: str = "http://localhost:11434"):
    """
    Cek status koneksi ke Ollama dan ambil daftar model lokal yang tersedia.
    """
    return extractor.get_ollama_status(host)


@app.post("/api/extract")
def api_extract(req: ExtractRequest):
    """
    Ekstrak elemen data dari teks mentah menggunakan AI yang dipilih atau Smart Regex.
    Tidak ada data yang disimpan ke database/disk.
    """
    result = do_extraction(req)
    return {"status": "success", "data": result}


@app.post("/api/generate-pdf")
def api_generate_pdf(req: GeneratePdfRequest):
    """
    Generate PDF resmi F-2.01 A secara langsung dari data terstruktur in-memory.
    Output distreaming langsung tanpa menyimpan file di server.
    """
    if not os.path.exists(TEMPLATE_PDF):
        raise HTTPException(status_code=500, detail="Template F-2.01 A.pdf tidak ditemukan di server.")
    
    try:
        pdf_bytes = pdf_engine.fill_f201a_pdf(TEMPLATE_PDF, req.data, single_page=req.single_page)
        
        filename = f"Formulir_F201A_{req.data.get('jenis_pelaporan', 'Dukcapil')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal generate PDF: {str(e)}")


@app.post("/api/extract-and-generate")
def api_extract_and_generate(req: ExtractAndGenerateRequest):
    """
    Endpoint 1-klik: Terima teks mentah -> Ekstrak data via AI -> Generate PDF -> Stream PDF langsung.
    Tidak ada data yang disimpan ke penyimpanan persisten.
    """
    if not os.path.exists(TEMPLATE_PDF):
        raise HTTPException(status_code=500, detail="Template F-2.01 A.pdf tidak ditemukan di server.")
        
    extracted_data = do_extraction(ExtractRequest(
        raw_text=req.raw_text,
        text_peristiwa=req.text_peristiwa,
        text_pelapor=req.text_pelapor,
        text_orangtua=req.text_orangtua,
        text_ayah=req.text_ayah,
        text_ibu=req.text_ibu,
        text_saksi1=req.text_saksi1,
        text_saksi2=req.text_saksi2,
        ai_engine=req.ai_engine,
        api_key=req.api_key,
        model_name=req.model_name,
        ollama_host=req.ollama_host
    ))
    
    pdf_bytes = pdf_engine.fill_f201a_pdf(TEMPLATE_PDF, extracted_data, single_page=req.single_page)
    filename = f"Formulir_F201A_{extracted_data.get('jenis_pelaporan', 'Kelahiran')}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Extracted-Data": json.dumps(extracted_data),
            "Cache-Control": "no-cache, no-store, must-revalidate"
        }
    )


# Sample raw datasets for instant testing
SAMPLE_DATASETS = {
    "rsia_bunda": """SURAT KETERANGAN KELAHIRAN
RSIA BUNDA MENTENG JAKARTA
No. Reg Medis: 2026/SKL/11-098

Telah lahir seorang bayi hidup:
Nama Bayi: KENZIE ALFATIH PRASETYO
Jenis Kelamin: Laki-laki
Hari, Tanggal Lahir: Rabu, 18 November 2026
Pukul: 07:45 WIB
Tempat Dilahirkan: Rumah Sakit Ibu dan Anak Bunda
Kota Kelahiran: Jakarta Pusat
Kelahiran ke: 1 (Tunggal)
Berat Badan: 3350 gram (3.35 Kg)
Panjang Badan: 50 cm
Lingkar Kepala: 34 cm
Penolong Persalinan: dr. Robert Sp.OG

Identitas Ibu Kandung:
Nama Ibu: DIAN ANGGRAENI
NIK: 3174016508900002
Tempat, Tgl Lahir: Surabaya, 25-08-1990
Kewarganegaraan: WNI

Identitas Ayah Kandung:
Nama Ayah: ARIEF PRASETYO
NIK: 3174011205880003
Tempat, Tgl Lahir: Jakarta, 12-05-1988
Kewarganegaraan: WNI

Nomor Kartu Keluarga: 3174012010150007
Alamat Domisili Keluarga:
Jalan Senayan No. 14 RT 003 RW 002
Kelurahan: Senayan
Kecamatan: Kebayoran Baru
Kota: Jakarta Selatan
Provinsi: DKI Jakarta
Kode Pos: 12190

Data Saksi Kelahiran:
Saksi 1: Bambang Hermanto (NIK: 3174011003800004)
Saksi 2: Dedi Kurniawan (NIK: 3174012004820005)
""",

    "puskesmas": """PUSKESMAS KECAMATAN COBLONG KOTA BANDUNG
SURAT KETERANGAN PERSALINAN
No: 440/124/PKM-CBL/2026

DATA PERSALINAN:
Telah melahirkan seorang bayi perempuan secara normal pada:
Hari: Senin
Tanggal: 16 November 2026
Waktu: Pukul 14.20 WIB
Tempat Persalinan: Puskesmas Coblong
Anak ke: 2 (Dua)
Berat Lahir: 3.1 Kg
Panjang Lahir: 49 cm
Penolong Persalinan: Bidan Siti Rahmawati, A.Md.Keb

BIODATA BAYI:
Nama Bayi: AISHA NAURAH SUBARJO
Jenis Kelamin: Perempuan

BIODATA ORANG TUA:
Nama Ibu: RINA MARLINA
NIK Ibu: 3273014502920004
Tempat, Tanggal Lahir Ibu: Sumedang, 15 Februari 1992
Warganegara: WNI

Nama Ayah: HENDRA SUBARJO
NIK Ayah: 3273011409890001
Tempat, Tanggal Lahir Ayah: Bandung, 14 September 1989
Warganegara: WNI

No. Kartu Keluarga (KK): 3273012408150003
Alamat: Jl. Dago Atas No. 88
Desa/Kelurahan: Dago
Kecamatan: Coblong
Kabupaten/Kota: Kota Bandung
Provinsi: Jawa Barat
""",

    "kematian": """RUMAH SAKIT UMUM DAERAH PASAR MINGGU
SURAT KETERANGAN KEMATIAN
No: 800/SKK/RSUD-PM/XI/2026

Menerangkan bahwa:
Nama Lengkap: RADEN SOERIPTO
NIK: 3174041503520001
Jenis Kelamin: Laki-laki
Umur: 74 Tahun
Nomor Kartu Keluarga: 3174041005080006
Kewarganegaraan: WNI

Telah dinyatakan meninggal dunia pada:
Hari: Minggu
Tanggal Kematian: 15 November 2026
Pukul: 21:15 WIB
Tempat Kematian: Ruang ICU RSUD Pasar Minggu
Sebab Kematian: Sakit biasa / komplikasi usia tua
Yang Menerangkan: Dokter Jaga (dr. Surya Wijaya, Sp.PD)

Data Pelapor (Anak Kandung):
Nama: ANITA KUSUMAWATI
NIK: 3174045506820003
Hubungan: Anak Kandung

Alamat Almarhum:
Kelurahan: Pasar Minggu
Kecamatan: Pasar Minggu
Kota: Jakarta Selatan
Provinsi: DKI Jakarta
""",

    "lahir_mati": """SURAT KETERANGAN LAHIR MATI
RUMAH SAKIT UMUM DAERAH TARAKAN
No: 472.12/SKLM/RSUD-TRK/XI/2026

Telah terjadi peristiwa lahir mati pada:
Hari: Jumat
Tanggal: 14 November 2026
Pukul: 10:30 WIB
Lamanya dalam Kandungan: 8 Bulan
Jenis Kelamin: Laki-laki
Jenis Kelahiran: Tunggal
Kelahiran ke: 1 (Pertama)
Tempat Dilahirkan: Rumah Sakit Umum Daerah Tarakan
Sebab Lahir Mati: Asfiksia Berat / Solusio Plasenta
Penolong Persalinan: dr. Hendra Wijaya, Sp.OG
Yang Menentukan: Dokter Spesialis Kebidanan

Identitas Ibu Kandung:
Nama Ibu: SITI NURHALIZA
NIK: 3171025507940003
Tempat, Tanggal Lahir: Jakarta, 15 Juli 1994
Pekerjaan: Karyawan Swasta
Kewarganegaraan: WNI

Identitas Ayah Kandung:
Nama Ayah: FAHRI ALAMSYAH
NIK: 3171021204910002
Tempat, Tanggal Lahir: Bandung, 12 April 1991
Pekerjaan: Wiraswasta
Kewarganegaraan: WNI

Nomor Kartu Keluarga: 3171022010180005
Alamat: Jl. Kyai Caringin No. 22
Kelurahan: Cideng
Kecamatan: Gambir
Kota: Jakarta Pusat
Provinsi: DKI Jakarta

Data Pelapor (Ayah Kandung):
Nama Pelapor: FAHRI ALAMSYAH
NIK Pelapor: 3171021204910002

Data Saksi:
Saksi 1: M. Yusuf (NIK: 3171021008850001)
Saksi 2: Andi Pratama (NIK: 3171021809880004)
"""
}

SAMPLE_SECTIONS = {
    "rsia_bunda": {
        "peristiwa": """SURAT KETERANGAN KELAHIRAN
RSIA BUNDA MENTENG JAKARTA
No. Reg Medis: 2026/SKL/11-098

Telah lahir seorang bayi hidup:
Nama Bayi: KENZIE ALFATIH PRASETYO
Jenis Kelamin: Laki-laki
Hari, Tanggal Lahir: Rabu, 18 November 2026
Pukul: 07:45 WIB
Tempat Dilahirkan: Rumah Sakit Ibu dan Anak Bunda
Kota Kelahiran: Jakarta Pusat
Kelahiran ke: 1 (Tunggal)
Berat Badan: 3350 gram (3.35 Kg)
Panjang Badan: 50 cm
Lingkar Kepala: 34 cm
Penolong Persalinan: dr. Robert Sp.OG""",

        "pelapor": """Nama Pelapor: ARIEF PRASETYO
NIK: 3174011205880003
Nomor Kartu Keluarga: 3174012010150007
Umur: 38 Tahun
Pekerjaan: Karyawan Swasta
Hubungan: Ayah Kandung
Alamat Domisili: Jalan Senayan No. 14 RT 003 RW 002, Kel. Senayan, Kec. Kebayoran Baru, Jakarta Selatan""",

        "orangtua": """Identitas Ayah Kandung:
Nama Ayah: ARIEF PRASETYO
NIK: 3174011205880003
Tempat, Tgl Lahir: Jakarta, 12-05-1988
Pekerjaan: Karyawan Swasta
Kewarganegaraan: WNI

Identitas Ibu Kandung:
Nama Ibu: DIAN ANGGRAENI
NIK: 3174016508900002
Tempat, Tgl Lahir: Surabaya, 25-08-1990
Pekerjaan: Ibu Rumah Tangga
Kewarganegaraan: WNI""",

        "ayah": """Nama Ayah: ARIEF PRASETYO
NIK: 3174011205880003
Tempat, Tgl Lahir: Jakarta, 12-05-1988
Pekerjaan: Karyawan Swasta
Kewarganegaraan: WNI""",

        "ibu": """Nama Ibu: DIAN ANGGRAENI
NIK: 3174016508900002
Tempat, Tgl Lahir: Surabaya, 25-08-1990
Pekerjaan: Ibu Rumah Tangga
Kewarganegaraan: WNI""",

        "saksi1": """Nama Saksi 1: Bambang Hermanto
NIK: 3174011003800004
Umur: 44 Tahun
Pekerjaan: Wiraswasta
Alamat: Jl. Senayan No. 12 RT 003 RW 002, Jakarta Selatan""",

        "saksi2": """Nama Saksi 2: Dedi Kurniawan
NIK: 3174012004820005
Umur: 42 Tahun
Pekerjaan: Pegawai BUMN
Alamat: Jl. Senayan No. 16 RT 003 RW 002, Jakarta Selatan"""
    },

    "puskesmas": {
        "peristiwa": """PUSKESMAS KECAMATAN COBLONG KOTA BANDUNG
SURAT KETERANGAN PERSALINAN
No: 440/124/PKM-CBL/2026

DATA PERSALINAN:
Telah melahirkan seorang bayi perempuan secara normal:
Nama Bayi: AISHA NAURAH SUBARJO
Jenis Kelamin: Perempuan
Hari, Tanggal: Senin, 16 November 2026
Waktu: Pukul 14.20 WIB
Tempat Persalinan: Puskesmas Coblong
Anak ke: 2 (Dua)
Berat Lahir: 3.1 Kg
Panjang Lahir: 49 cm
Penolong Persalinan: Bidan Siti Rahmawati, A.Md.Keb""",

        "pelapor": """Nama Pelapor: HENDRA SUBARJO
NIK: 3273011409890001
No. Kartu Keluarga (KK): 3273012408150003
Umur: 37 Tahun
Pekerjaan: Wiraswasta
Hubungan: Ayah Kandung
Alamat: Jl. Dago Atas No. 88, Kelurahan Dago, Kecamatan Coblong, Kota Bandung""",

        "orangtua": """Identitas Ayah:
Nama Ayah: HENDRA SUBARJO
NIK Ayah: 3273011409890001
Tempat, Tanggal Lahir Ayah: Bandung, 14 September 1989
Pekerjaan: Wiraswasta
Warganegara: WNI

Identitas Ibu:
Nama Ibu: RINA MARLINA
NIK Ibu: 3273014502920004
Tempat, Tanggal Lahir Ibu: Sumedang, 15 Februari 1992
Pekerjaan: Guru
Warganegara: WNI""",

        "ayah": """Nama Ayah: HENDRA SUBARJO
NIK: 3273011409890001
Tempat, Tanggal Lahir: Bandung, 14 September 1989
Pekerjaan: Wiraswasta
Warganegara: WNI""",

        "ibu": """Nama Ibu: RINA MARLINA
NIK: 3273014502920004
Tempat, Tanggal Lahir: Sumedang, 15 Februari 1992
Pekerjaan: Guru
Warganegara: WNI""",

        "saksi1": """Nama Saksi 1: Agus Sudrajat
NIK: 3273011005850002
Umur: 41 Tahun
Pekerjaan: Pegawai Negeri Sipil
Alamat: Jl. Dago No. 90, Coblong, Bandung""",

        "saksi2": """Nama Saksi 2: Tatang Sutarman
NIK: 3273012108870005
Umur: 39 Tahun
Pekerjaan: Wiraswasta
Alamat: Jl. Dago No. 92, Coblong, Bandung"""
    },

    "kematian": {
        "peristiwa": """RUMAH SAKIT UMUM DAERAH PASAR MINGGU
SURAT KETERANGAN KEMATIAN
No: 800/SKK/RSUD-PM/XI/2026

Nama Lengkap: RADEN SOERIPTO
NIK: 3174041503520001
Jenis Kelamin: Laki-laki
Umur: 74 Tahun
Nomor Kartu Keluarga: 3174041005080006
Hari, Tanggal Kematian: Minggu, 15 November 2026
Pukul: 21:15 WIB
Tempat Kematian: Ruang ICU RSUD Pasar Minggu
Sebab Kematian: Sakit biasa / komplikasi usia tua
Yang Menerangkan: Dokter Jaga (dr. Surya Wijaya, Sp.PD)
Alamat Almarhum: Kel. Pasar Minggu, Kec. Pasar Minggu, Kota Jakarta Selatan, DKI Jakarta""",

        "pelapor": """Nama Pelapor: ANITA KUSUMAWATI
NIK: 3174045506820003
Nomor Kartu Keluarga: 3174041005080006
Umur: 44 Tahun
Hubungan: Anak Kandung
Alamat: Jl. Raya Pasar Minggu No. 45, Jakarta Selatan""",

        "orangtua": """Identitas Orang Tua Almarhum:
Nama Ayah: R. KARTODIRDJO (Alm)
Nama Ibu: NY. SOERATINI (Almh)""",

        "ayah": "Nama Ayah: R. KARTODIRDJO (Alm)",
        "ibu": "Nama Ibu: NY. SOERATINI (Almh)",

        "saksi1": """Nama Saksi 1: H. Mansyur
NIK: 3174041201650002
Umur: 61 Tahun
Pekerjaan: Pensiunan
Alamat: Jl. Pasar Minggu No. 47, Jakarta Selatan""",

        "saksi2": """Nama Saksi 2: Wahyu Hidayat
NIK: 3174042007780004
Umur: 48 Tahun
Pekerjaan: Karyawan Swasta
Alamat: Jl. Pasar Minggu No. 49, Jakarta Selatan"""
    },

    "lahir_mati": {
        "peristiwa": """SURAT KETERANGAN LAHIR MATI
RUMAH SAKIT UMUM DAERAH TARAKAN
No: 472.12/SKLM/RSUD-TRK/XI/2026

Telah terjadi peristiwa lahir mati pada:
Hari: Jumat, Tanggal: 14 November 2026
Pukul: 10:30 WIB
Lamanya dalam Kandungan: 8 Bulan
Jenis Kelamin: Laki-laki
Jenis Kelahiran: Tunggal (Anak ke-1)
Tempat Dilahirkan: Rumah Sakit Umum Daerah Tarakan
Sebab Lahir Mati: Asfiksia Berat / Solusio Plasenta
Penolong: dr. Hendra Wijaya, Sp.OG
Yang Menentukan: Dokter Spesialis Kebidanan""",

        "pelapor": """Nama Pelapor: FAHRI ALAMSYAH
NIK: 3171021204910002
Nomor Kartu Keluarga: 3171022010180005
Umur: 35 Tahun
Pekerjaan: Wiraswasta
Hubungan: Ayah Kandung
Alamat: Jl. Kyai Caringin No. 22, Kel. Cideng, Kec. Gambir, Jakarta Pusat""",

        "orangtua": """Identitas Ayah Kandung:
Nama Ayah: FAHRI ALAMSYAH
NIK: 3171021204910002
Tempat, Tgl Lahir: Bandung, 12 April 1991
Pekerjaan: Wiraswasta
Kewarganegaraan: WNI

Identitas Ibu Kandung:
Nama Ibu: SITI NURHALIZA
NIK: 3171025507940003
Tempat, Tgl Lahir: Jakarta, 15 Juli 1994
Pekerjaan: Karyawan Swasta
Kewarganegaraan: WNI""",

        "ayah": """Nama Ayah: FAHRI ALAMSYAH
NIK: 3171021204910002
Tempat, Tgl Lahir: Bandung, 12 April 1991
Pekerjaan: Wiraswasta
Kewarganegaraan: WNI""",

        "ibu": """Nama Ibu: SITI NURHALIZA
NIK: 3171025507940003
Tempat, Tgl Lahir: Jakarta, 15 Juli 1994
Pekerjaan: Karyawan Swasta
Kewarganegaraan: WNI""",

        "saksi1": """Nama Saksi 1: M. Yusuf
NIK: 3171021008850001
Umur: 41 Tahun
Pekerjaan: Wiraswasta
Alamat: Jl. Cideng Barat No. 10, Jakarta Pusat""",

        "saksi2": """Nama Saksi 2: Andi Pratama
NIK: 3171021809880004
Umur: 38 Tahun
Pekerjaan: Pegawai Swasta
Alamat: Jl. Cideng Timur No. 14, Jakarta Pusat"""
    }
}

@app.get("/api/sample-data/{sample_id}")
def api_sample_data(sample_id: str):
    if sample_id not in SAMPLE_DATASETS:
        raise HTTPException(status_code=404, detail="Sample tidak ditemukan.")
    return {
        "id": sample_id,
        "text": SAMPLE_DATASETS[sample_id],
        "sections": SAMPLE_SECTIONS.get(sample_id, {})
    }


# Serve UI
@app.get("/", response_class=HTMLResponse)
def index_page():
    html_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Frontend static/index.html not found</h1>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
