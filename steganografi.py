from flask import Flask, render_template_string, request, send_file, session
from PIL import Image
import io
from google.colab import output

app = Flask(__name__)
app.secret_key = 'stego_secret_key_udb_v6'

# --- 1. SETTING LIMITASI UKURAN FILE (2 MB) ---
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

# --- LOGIKA STEGANOGRAFI (LSB) ---

def text_to_bin(text):
    return ''.join(format(ord(char), '08b') for char in text)

def bin_to_text(bin_string):
    bytes_data = [bin_string[i:i+8] for i in range(0, len(bin_string), 8)]
    text = ""
    for b in bytes_data:
        if len(b) == 8:
            text += chr(int(b, 2))
    return text

stego_cache = {}

def process_encode(input_image, secret_message):
    img = Image.open(input_image).convert('RGB') # membuka / memanggil si gambar, untuk nantinya digunakan untuk proses penyisipan. lalu gambar diubah ke mode rgb
    pixels = img.load() # memuat data pixel dari gambar, untuk nantinya digunakan untuk proses penyisipan

    plain_text_sample = secret_message # menyimpan teks asli sebelum ditambahkan delimiter untuk kebutuhan visualisasi di interface
    secret_message += "@@" # Delimiter # fungsi untuk tanda proses penyisipan sudah selesai, agar saat proses pembacaan bisa tahu kapan pesan berakhir, sehingga proses pembacaan bisa lebih efisien, karena tidak perlu membaca seluruh gambar jika pesan sudah ditemukan
    bin_msg = text_to_bin(secret_message) # mengubah pesan rahasia menjadi representasi biner, karena proses penyisipan akan dilakukan pada level bit

    msg_idx = 0 # variabel untuk melacak posisi saat ini dalam pesan biner yang akan disisipkan, digunakan untuk memastikan bahwa setiap bit dari pesan disisipkan secara berurutan ke dalam gambar
    width, height = img.size # mendapatkan dimensi gambar width dan height, untuk digunakan dalam iterasi melalui setiap pixel gambar selama proses penyisipan

    # Hitung kapasitas maksimal bit gambar (Hanya menggunakan komponen warna Red)
    max_capacity_bits = width * height # mengalikan lebar dan tinggi gambar untuk mengetahui total pixel yang tersedia (karena 1 pixel menyumbang 1 bit pada komponen warna merah)

    # --- LIMITASI PANJANG PESAN BERDASARKAN KAPASITAS GAMBAR ---
    if len(bin_msg) > max_capacity_bits: # memeriksa apakah panjang pesan biner melebihi kapasitas bit maksimal yang bisa ditampung oleh gambar
        max_chars = (max_capacity_bits // 8) - 2 # menghitung maksimal karakter desimal yang muat (kapasitas dibagi 8 bit, lalu dikurangi 2 karakter untuk tempat si delimiter '@@')
        return None, f"Gambar terlalu kecil! Hanya muat maksimal {max_chars} karakter.", None, None, None # mengembalikan nilai kosong dan pesan error jika gambar tidak muat menampung pesan

    total_msg_bits = len(bin_msg) # menyimpan total panjang bit pesan yang akan disisipkan sebagai batas akhir pelacakan visualisasi
    macro_before_list = [] # membuat list kosong untuk menampung visualisasi biner warna merah (R) SEBELUM diubah
    macro_after_list = [] # membuat list kosong untuk menampung visualisasi biner warna merah (R) SESUDAH diubah

    for y in range(height): # iterasi melalui setiap baris gambar, untuk memastikan bahwa proses penyisipan mencakup seluruh gambar, dimulai dari baris atas hingga bawah
        for x in range(width): # iterasi melalui setiap kolom gambar, untuk memastikan bahwa proses penyisipan mencakup seluruh gambar, dimulai dari kolom kiri hingga kanan
            if msg_idx < len(bin_msg): # memeriksa apakah masih ada bit pesan yang perlu disisipkan, jika sudah semua bit pesan disisipkan, maka proses penyisipan dapat dihentikan
                r, g, b = pixels[x, y] # mendapatkan nilai RGB (misal 12, 5, 90) dari pixel saat ini, untuk digunakan dalam proses penyisipan bit pesan ke dalam komponen warna merah (R) dari pixel
                r_bin_before = format(r, '08b') # mengubah nilai merah (R) asli menjadi representasi biner 8-bit dalam bentuk string untuk dicatat pada log visualisasi 'before'
                current_text_bit = bin_msg[msg_idx] # mengambil 1 bit pesan rahasia pada indeks saat ini yang akan disisipkan ke dalam pixel

                r_bin_list = list(r_bin_before) # mengubah string biner merah menjadi bentuk list [] sehingga kodenya nanti dipisah per digit [1,0,1,0] agar bisa dimanipulasi indeksnya
                r_bin_list[-1] = current_text_bit # menyisipkan bit pesan ke dalam bit paling tidak signifikan (LSB) (paling kanan) dari komponen warna merah (R) dari pixel, dengan menggantikan bit terakhir dari representasi biner merah (R) dengan bit pesan saat ini
                r_bin_after = ''.join(r_bin_list) # join disini untuk mengubah list [1,0,1,0] kembali ke bentuk string biner utuh (misal: 1010)

                pixels[x, y] = (int(r_bin_after, 2), g, b) # memperbarui nilai pixel dengan nilai merah (R) yang telah dimodifikasi, sementara nilai hijau (G) dan biru (B) tetap tidak berubah, untuk menyimpan perubahan yang dilakukan pada pixel saat ini (int(...., 2) menerjemahkan bilangan biner ke bentuk desimal)

                # Mengambil semua bit untuk visualisasi pembuktian
                if msg_idx < total_msg_bits: # memastikan pencatatan visualisasi hanya dilakukan selama bit pesan masih tersedia
                    macro_before_list.append(r_bin_before[:-1] + f"[{r_bin_before[-1]}]") # menyusun string biner lama dengan memberikan tanda kurung siku [] pada bit LSB aslinya, lalu dimasukkan ke list
                    macro_after_list.append(r_bin_after[:-1] + f"<span class='hl-macro-bit'>[{r_bin_after[-1]}]</span>") # menyusun string biner baru dengan membungkus bit LSB baru menggunakan tag HTML span agar nanti menyala hijau di web UI

                msg_idx += 1 # inkrementasi variabel indeks untuk melanjutkan ke bit pesan berikutnya pada iterasi pixel selanjutnya

    macro_before_str = ' '.join(macro_before_list) # menggabungkan seluruh list biner 'before' menjadi satu string panjang yang dipisahkan oleh spasi agar rapi saat ditampilkan
    macro_after_str = ' '.join(macro_after_list) # menggabungkan seluruh list biner 'after' menjadi satu string panjang dengan tag HTML aktif untuk dilempar ke template visualisasi

    # Simpan hasil ke memori (BytesIO) agar bisa langsung diunduh
    img_io = io.BytesIO() # membuat objek BytesIO untuk menyimpan gambar hasil penyisipan dalam memori, sehingga dapat langsung diunduh tanpa perlu menyimpan ke disk terlebih dahulu
    img.save(img_io, 'PNG') # menyimpan data gambar yang telah dimodifikasi ke dalam objek BytesIO dengan format PNG agar bersifat lossless (tidak merusak bit)
    img_io.seek(0) # mengatur posisi pointer dalam objek BytesIO ke awal, untuk memastikan bahwa saat file ini dikirim untuk diunduh, pembacaannya dimulai dari awal file

    return img_io, plain_text_sample, bin_msg, macro_before_str, macro_after_str # mengembalikan semua data yang berhasil diproses termasuk data gambar dan string visualisasi ke route Flask

def process_decode(input_image):
    img = Image.open(input_image).convert('RGB') # membuka / memanggil gambar stego yang diunggah, lalu memastikan formatnya berada dalam mode warna RGB
    pixels = img.load() # memuat data koordinat pixel dari gambar stego untuk memulai proses pembacaan / ekstraksi bit
    width, height = img.size # mendapatkan dimensi lebar dan tinggi gambar stego untuk batas perulangan (looping) pencarian bit
    extracted_bin = "" # variabel untuk menyimpan representasi biner yang diekstrak dari gambar, selama proses pembacaan pesan tersembunyi, bit-bit pesan akan dikumpulkan dalam variabel ini sebelum diubah kembali menjadi teks
    for y in range(height): # melakukan iterasi pixel per baris dari atas sampai bawah gambar
        for x in range(width): # melakukan iterasi pixel per kolom dari kiri sampai kanan gambar
            r, g, b = pixels[x, y] # mengambil nilai RGB dari pixel stego pada koordinat saat ini
            extracted_bin += format(r, '08b')[-1] # mengubah nilai komponen merah (R) ke biner 8-bit, lalu mengambil bit paling terakhir/LSB ([-1]) dan menggabungkannya ke variabel extracted_bin
            if len(extracted_bin) % 8 == 0: # memeriksa apakah bit biner yang terkumpul sudah kelipatan 8 (artinya sudah membentuk 1 byte / 1 karakter utuh)
                current_text = bin_to_text(extracted_bin) # menerjemahkan kumpulan biner yang ada saat ini menjadi karakter teks desimal/string asli
                if "@@" in current_text: # memeriksa apakah karakter penanda selesai "@@" sudah terdeteksi di dalam teks yang diekstrak
                    return current_text.split("@@")[0] # jika "@@" ditemukan, proses langsung dihentikan dan fungsi langsung mengembalikan teks asli di sebelah kiri penanda (pesan rahasia berhasil didapat secara efisien)
    return "Pesan tidak ditemukan." # mengembalikan pesan gagal jika seluruh pixel gambar sudah diperiksa namun tanda penanda "@@" tidak ditemukan

# --- TAMPILAN TEMPLATE UI (HTML & CSS) ---

main_template = """
<!DOCTYPE html>
<html>
<head>
    <title>SteganoWeb - LSB</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f2f5; display: flex; justify-content: center; padding: 50px; }
        .card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; max-width: 500px; }
        h1 { color: #1a73e8; text-align: center; margin-bottom: 30px; }
        h3 { border-bottom: 2px solid #eee; padding-bottom: 10px; color: #555; }
        .section { margin-bottom: 40px; padding: 15px; border: 1px solid #eef; border-radius: 10px; }
        input[type="file"], input[type="text"] { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; transition: 0.3s; }
        .btn-encode { background-color: #1a73e8; color: white; }
        .btn-decode { background-color: #34a853; color: white; margin-top: 10px; }
        button:hover { opacity: 0.8; }
        .result-box { margin-top: 20px; padding: 15px; background: #e7f3ff; border-left: 5px solid #1a73e8; word-wrap: break-word; }
        .error-alert { margin-top: 20px; padding: 15px; background: #fce8e6; border-left: 5px solid #d93025; color: #c5221f; border-radius: 4px; font-weight: bold;}
    </style>
</head>
<body>
    <div class="card">
        <h1>SteganoWeb LSB</h1>

        {% if error_msg %}
        <div class="error-alert">
            ⚠ {{ error_msg }}
        </div>
        {% endif %}

        <div class="section">
            <h3>1. Sembunyikan Pesan (Encode)</h3>
            <form action="/encode" method="post" enctype="multipart/form-data">
                <label>Pilih Gambar Asli (Maks 2MB, Semua Format):</label>
                <input type="file" name="image" accept="image/*" required>
                <label>Pesan Rahasia (Maksimal 100 Karakter):</label>
                <input type="text" name="message" placeholder="Ketik pesan di sini..." maxlength="100" required>
                <button type="submit" class="btn-encode">Proses & Lihat Visualisasi</button>
            </form>
        </div>

        <div class="section">
            <h3>2. Baca Pesan (Decode)</h3>
            <form action="/decode" method="post" enctype="multipart/form-data">
                <label>Pilih Gambar Stego (.PNG hasil unduhan):</label>
                <input type="file" name="image" accept="image/*" required>
                <button type="submit" class="btn-decode">Ekstrak Pesan</button>
            </form>

            {% if decoded_msg %}
            <div class="result-box">
                <strong>Pesan Tersembunyi:</strong><br>
                {{ decoded_msg }}
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

visualize_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Visualisasi Proses Stegano - LSB</title>
    <style>
        body { font-family: 'Courier New', Courier, monospace; background-color: #1e1e24; color: #e0e0e0; padding: 40px; display: flex; justify-content: center; }
        .container { background: #2a2a35; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); width: 100%; max-width: 1100px; }

        .panel-row { width: 100%; border-collapse: collapse; margin-top: 5px; background: #1a1a24; border: 1px solid #444; }
        .panel-row td { padding: 15px; vertical-align: top; border: 1px solid #444; }

        .title-cell { font-weight: bold; color: #ffd43b; width: 20%; font-family: sans-serif; }
        .content-cell { word-break: break-all; line-height: 1.6; }

        .split-box { display: flex; width: 100%; gap: 0px; }
        .split-left { width: 50%; padding: 15px; border-right: 1px solid #444; box-sizing: border-box; word-break: break-all; }
        .split-right { width: 50%; padding: 15px; box-sizing: border-box; word-break: break-all; }
        .split-header { font-weight: bold; color: #4dadf7; margin-bottom: 10px; font-family: sans-serif; text-transform: uppercase; }

        .hl-macro-bit { color: #2ff56c; font-weight: bold; background: #0f3d18; padding: 1px 2px; border-radius: 3px; }
        .btn-download { display: block; width: 100%; text-align: center; background-color: #34a853; color: white; padding: 12px; text-decoration: none; border-radius: 5px; font-weight: bold; font-family: sans-serif; margin: 25px 0; box-sizing: border-box;}
        .btn-download:hover { background-color: #2b8a44; }
        .btn-back { display: inline-block; color: #4dadf7; text-decoration: none; margin-bottom: 15px; font-family: sans-serif;}
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="btn-back">⬅ Kembali ke Menu Utama</a>

        <table class="panel-row">
            <tr>
                <td class="title-cell">pesan :</td>
                <td class="content-cell" style="color: #ff8787; font-weight: bold;">{{ plain_text }}</td>
            </tr>
            <tr>
                <td class="title-cell">kode biner :</td>
                <td class="content-cell" style="letter-spacing: 1px;">{{ bin_text }}</td>
            </tr>
        </table>

        <br>

        <div class="panel-row">
            <div class="split-box">
                <div class="split-left">
                    <div class="split-header">gambar asli</div>
                    <div style="letter-spacing: 1px; line-height: 1.8;">{{ macro_before }}</div>
                </div>
                <div class="split-right">
                    <div class="split-header">after</div>
                    <div style="letter-spacing: 1px; line-height: 1.8;">{{ macro_after | safe }}</div>
                </div>
            </div>
        </div>

        <a href="/download_file" class="btn-download">💾 KLIK DI SINI UNTUK UNDUH GAMBAR STANO (.PNG)</a>

        <p style="text-align: center; color: #888; font-size: 12px;">*Visualisasi menampilkan pemetaan biner secara penuh sesuai panjang karakter yang dimasukkan.</p>
    </div>
</body>
</html>
"""

# --- ROUTING FLASK ---

@app.route('/')
def index():
    return render_template_string(main_template)

@app.errorhandler(413)
def request_entity_too_large(error):
    return render_template_string(main_template, error_msg="Ukuran file terlalu besar! Maksimal ukuran file adalah 2 MB."), 413

@app.route('/encode', methods=['POST'])
def encode():
    file = request.files['image']
    message = request.form['message']

    if file:
        # --- PERBAIKAN: VALIDASI MAKSIMAL 100 KARAKTER DI SISI BACKEND ---
        if len(message) > 100:
            return render_template_string(main_template, error_msg="Input ditolak! Pesan rahasia tidak boleh lebih dari 100 karakter.")

        img_io, plain_text, bin_text, macro_before, macro_after = process_encode(file, message)

        if img_io is None:
            return render_template_string(main_template, error_msg=plain_text)

        stego_cache['current_image'] = img_io
        formatted_bin_text = ' '.join([bin_text[i:i+8] for i in range(0, len(bin_text), 8)])

        return render_template_string(
            visualize_template,
            plain_text=plain_text,
            bin_text=formatted_bin_text,
            macro_before=macro_before,
            macro_after=macro_after
        )

@app.route('/download_file')
def download_file():
    img_io = stego_cache.get('current_image')
    if img_io:
        return send_file(img_io, mimetype='image/png', as_attachment=True, download_name='stego_result.png')
    return "File tidak ditemukan atau sesi kadaluarsa."

@app.route('/decode', methods=['POST'])
def decode():
    file = request.files['image']
    if file:
        msg = process_decode(file)
        return render_template_string(main_template, decoded_msg=msg)

colab_url = output.eval_js("google.colab.kernel.proxyPort(5000)")
print("1. Klik link di bawah ini untuk membuka UI Flask kamu:")
print(colab_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
