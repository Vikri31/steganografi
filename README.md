# 📖 Dokumentasi & Analisis Baris Demi Baris: Logika Steganografi LSB

Dokumen ini membedah fungsi utama steganografi *Least Significant Bit* (LSB) pada aplikasi web untuk tujuan pembelajaran. Setiap baris kode dijelaskan secara terpisah agar mempermudah pemahaman alur kerja data biner pada citra digital.

---

## 1. Fungsi Penyisipan Pesan (`process_encode`)

Fungsi ini bertanggung jawab untuk mengubah pesan teks menjadi biner, melakukan validasi ukuran, dan menyisipkan bit-bit tersebut ke dalam komponen warna **Merah (Red)** pada gambar asli.

### `img = Image.open(input_image).convert('RGB')`
> Membuka atau memanggil file gambar yang diunggah oleh pengguna, lalu memaksa modenya berubah ke format warna `RGB` (Red, Green, Blue) agar struktur datanya konsisten saat dimanipulasi.

### `pixels = img.load()`
> Memuat matriks data pixel dari gambar ke dalam memori. Ini dilakukan agar kita bisa membaca dan memodifikasi nilai warna desimal di koordinat `[x, y]` secara instan.

### `plain_text_sample = secret_message`
> Menyimpan teks pesan asli dari input pengguna ke variabel baru sebelum dimodifikasi. Variabel ini nantinya dikirim kembali ke antarmuka web untuk kebutuhan log visualisasi.

### `secret_message += "@@"`
> Menambahkan karakter pembatas (*delimiter*) `"@@"` di akhir pesan rahasia. Berfungsi sebagai penanda/sinyal bahwa proses penyisipan telah selesai, sehingga saat proses pembacaan (*decode*), program tahu kapan harus berhenti dan tidak perlu membaca seluruh sisa pixel gambar.

### `bin_msg = text_to_bin(secret_message)`
> Memanggil fungsi pembantu untuk mengonversi seluruh string pesan rahasia (termasuk penanda `"@@"`) menjadi deretan bit biner (0 dan 1), karena manipulasi steganografi bekerja pada level bit terkecil komputer.

### `msg_idx = 0`
> Membuat variabel *pointer* indeks yang dimulai dari `0`. Variabel ini berfungsi untuk melacak bit pesan biner ke-berapa yang sedang antre untuk disisipkan ke dalam gambar.

### `width, height = img.size`
> Mengambil dimensi spasial gambar berupa nilai lebar (`width`) dan tinggi (`height`) dalam satuan pixel untuk digunakan sebagai batas akhir perulangan (*looping*).

### `max_capacity_bits = width * height`
> Menghitung total kapasitas bit maksimal yang bisa ditampung gambar. Karena teknik ini hanya memodifikasi 1 bit (komponen Merah) pada tiap koordinat, maka total kapasitas bit sama dengan jumlah total pixel gambar ($\text{lebar} \times \text{tinggi}$).

### `if len(bin_msg) > max_capacity_bits:`
> Melakukan pengecekan kondisi: apakah total panjang bit pesan rahasia yang akan disisipkan melebihi kapasitas ruang bit yang tersedia pada gambar.

### `max_chars = (max_capacity_bits // 8) - 2`
> Jika gambar kekecilan, baris ini menghitung matematika batas maksimal karakter yang muat. Total bit dibagi `8` untuk dikembalikan ke bentuk karakter teks, lalu dikurangi `2` karakter karena jatahnya termakan oleh *delimiter* `"@@"`.

### `return None, f"Gambar terlalu kecil! Hanya muat maksimal {max_chars} karakter.", None, None, None`
> Menghentikan fungsi dan mengembalikan nilai kosong (`None`) beserta pesan peringatan ke sistem Flask jika pesan rahasia dipastikan tidak muat masuk ke dalam gambar.

### `total_msg_bits = len(bin_msg)`
> Menyimpan jumlah mutlak dari total bit pesan ke dalam variabel baru untuk dijadikan sebagai acuan kondisi batas perekaman log visualisasi bit.

### `macro_before_list = []`
> Membuat sebuah list kosong untuk menampung teks visualisasi representasi biner warna merah (Red) asli sebelum mengalami manipulasi bit.

### `macro_after_list = []`
> Membuat sebuah list kosong untuk menampung teks visualisasi representasi biner warna merah (Red) sesudah bit LSB-nya diganti dengan bit pesan rahasia.

### `for y in range(height):`
> Melakukan perulangan tingkat pertama (luar) untuk menyisir gambar secara vertikal baris demi baris, dimulai dari baris paling atas (`0`) hingga baris paling bawah.

### `for x in range(width):`
> Melakukan perulangan tingkat kedua (dalam) untuk menyisir gambar secara horizontal kolom demi kolom pada baris yang aktif, bergerak dari kiri ke kanan.

### `if msg_idx < len(bin_msg):`
> Memeriksa apakah bit pesan masih tersedia untuk disisipkan. Jika seluruh bit pesan sudah habis tertanam, perulangan pixel akan tetap berjalan namun tidak akan mengubah nilai warna lagi.

### `r, g, b = pixels[x, y]`
> Mengekstrak nilai desimal warna RGB dari koordinat pixel `[x, y]` yang sedang aktif saat ini (misalnya menghasilkan nilai integer Red=150, Green=200, Blue=50).

### `r_bin_before = format(r, '08b')`
> Mengonversi nilai desimal komponen warna Merah (`r`) menjadi string biner sepanjang 8-bit (misalnya desimal `150` diubah menjadi string `'10010110'`) untuk kebutuhan pencatatan log historis.

### `current_text_bit = bin_msg[msg_idx]`
> Mengambil satu digit bit pesan (entah itu karakter `'0'` atau `'1'`) dari string biner pesan rahasia berdasarkan urutan indeks pelacak yang aktif.

### `r_bin_list = list(r_bin_before)`
> Mengonversi string biner warna merah yang berisi 8 karakter menjadi bentuk list karakter (misalnya dari string `'10010110'` dipecah menjadi list `['1', '0', '0', '1', '0', '1', '1', '0']`) agar elemennya bisa dimanipulasi lewat indeks.

### `r_bin_list[-1] = current_text_bit`
> **Inti dari LSB:** Mengganti elemen terakhir atau bit paling tidak signifikan (indeks paling kanan `[-1]`) dari list warna merah tersebut dengan bit pesan rahasia yang diwakili oleh `current_text_bit`.

### `r_bin_after = ''.join(r_bin_list)`
> Menggabungkan kembali elemen-elemen di dalam list karakter biner merah tadi menjadi bentuk string tunggal 8-bit yang utuh (misalnya menjadi `'10010111'`).

### `pixels[x, y] = (int(r_bin_after, 2), g, b)`
> Memperbarui data pixel pada koordinat gambar tersebut. Fungsi `int(r_bin_after, 2)` menerjemahkan kembali string biner baru ke bilangan desimal warna, sementara komponen Hijau (`g`) dan Biru (`b`) dimasukkan kembali tanpa ada perubahan sedikit pun.

### `if msg_idx < total_msg_bits:`
> Memastikan bahwa proses pencatatan visualisasi teks biner hanya dilakukan selama posisi indeks belum melewati panjang bit pesan rahasia.

### `macro_before_list.append(r_bin_before[:-1] + f"[{r_bin_before[-1]}]")`
> Menyusun teks biner lama dengan memotong bit terakhirnya, lalu membungkus bit asli tersebut dengan tanda kurung siku `[...]` agar terlihat jelas posisi LSB aslinya sebelum dimasukkan ke dalam list penampung.

### `macro_after_list.append(r_bin_after[:-1] + f"<span class='hl-macro-bit'>[{r_bin_after[-1]}]</span>")`
> Menyusun teks biner baru dengan membungkus bit LSB baru menggunakan tag HTML `<span>`. Tujuannya agar bit yang berubah tersebut bisa menyala dengan warna hijau saat dirender di halaman web.

### `msg_idx += 1`
> Menaikkan nilai indeks pelacak pesan sebesar 1 angka (`increment`) agar pada perulangan pixel berikutnya, sistem mengambil bit pesan urutan selanjutnya.

### `macro_before_str = ' '.join(macro_before_list)`
> Menggabungkan seluruh elemen list biner visualisasi sebelum modifikasi menjadi satu string teks panjang yang dipisahkan oleh karakter spasi agar rapi.

### `macro_after_str = ' '.join(macro_after_list)`
> Menggabungkan seluruh elemen list biner visualisasi sesudah modifikasi menjadi satu string teks panjang, lengkap dengan tag HTML yang siap diproses oleh mesin template web.

### `img_io = io.BytesIO()`
> Membuat objek *stream* biner di dalam memori RAM komputer (bukan di harddisk/disk eksternal) untuk menampung file gambar hasil manipulasi secara temporer.

### `img.save(img_io, 'PNG')`
> Menyimpan data objek gambar yang pixelnya telah disisipi pesan ke dalam objek memori `img_io` dengan memaksa formatnya menjadi `PNG` (format *lossless* yang menjamin bit warna tidak akan rusak/terkompresi).

### `img_io.seek(0)`
> Memindahkan posisi kursor pembaca internal di dalam objek memori `img_io` kembali ke titik nol (awal file), sehingga saat file diunduh, data dibaca secara lengkap dari byte pertama.

### `return img_io, plain_text_sample, bin_msg, macro_before_str, macro_after_str`
> Mengirimkan seluruh hasil pemrosesan data (termasuk file gambar dalam memori dan variabel teks pembuktian) kembali ke fungsi pemanggil di rute Flask.

---

## 2. Fungsi Pembacaan Pesan (`process_decode`)

Fungsi ini melakukan kebalikan dari proses enkripsi, yaitu membaca bit LSB pada warna merah dari setiap pixel gambar stego hingga menemukan pembatas penanda berhenti.

### `img = Image.open(input_image).convert('RGB')`
> Membuka file gambar hasil steganografi yang diunggah oleh pengguna untuk diekstraksi, serta memastikan modenya berada pada format warna `RGB`.

### `pixels = img.load()`
> Memuat struktur data matriks pixel gambar stego ke dalam memori agar sistem bisa membaca nilai warna pada tiap titik koordinat secara acak maupun berurutan.

### `width, height = img.size`
> Mengambil ukuran lebar dan tinggi dari gambar stego guna menentukan batasan wilayah jangkauan perulangan pembacaan bit.

### `extracted_bin = ""`
> Menginisialisasi variabel string kosong yang akan bertindak sebagai wadah pengumpul atau penampung bit-bit LSB yang berhasil dikupas dari gambar.

### `for y in range(height):`
> Melakukan perulangan luar untuk menyisir baris gambar dari atas ke bawah secara berurutan sesuai urutan penyisipan semula.

### `for x in range(width):`
> Melakukan perulangan dalam untuk menyisir kolom pixel dari kiri ke kanan pada baris yang sedang aktif.

### `r, g, b = pixels[x, y]`
> Membaca nilai warna komponen RGB pada titik koordinat pixel stego `[x, y]` saat ini.

### `extracted_bin += format(r, '08b')[-1]`
> Mengubah nilai desimal komponen warna Merah (`r`) ke bentuk string biner 8-bit, mengambil karakter paling terakhir/LSB lewat indeks `[-1]`, lalu langsung menambahkannya ke ujung variabel pengumpul `extracted_bin`.

### `if len(extracted_bin) % 8 == 0:`
> Pengecekan kondisi: apakah jumlah bit biner yang telah dikumpulkan di dalam variabel sudah mencapai kelipatan `8` (yang menandakan satu karakter teks utuh/1 byte telah terbentuk).

### `current_text = bin_to_text(extracted_bin)`
> Menerjemahkan seluruh rangkaian string biner yang terkumpul saat ini kembali menjadi bentuk teks desimal/string karakter biasa melalui fungsi pembantu.

### `if "@@" in current_text:`
> Memeriksa apakah karakter pembatas rahasia `"@@"` sudah berhasil terbentuk dan terdeteksi di dalam string teks hasil terjemahan sementara tersebut.

### `return current_text.split("@@")[0]`
> Jika tanda `"@@"` valid ditemukan, fungsi pembacaan langsung dihentikan saat itu juga, lalu memotong teks dan mengembalikan potongan string di sebelah kiri tanda pembatas (yaitu isi pesan rahasia yang asli).

### `return "Pesan tidak ditemukan."`
> Jika perulangan luar dan dalam telah selesai memeriksa seluruh pixel gambar namun tanda pembatas `"@@"` tidak kunjung terdeteksi, fungsi akan mengembalikan teks kegagalan ini.
