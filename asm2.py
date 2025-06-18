import streamlit as st
import re
import requests
from bs4 import BeautifulSoup

# Danh sách từ dừng tiếng Việt
url_stopwords = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT3rt3sFA0x_mQ0GI1S8rBDowX_vYkFwrh_3Q2OQOWQoXAHguS0rhVgFhztEIoT2pJWKm5utvFsqUi0/pubhtml"
phan_hoi_stopwords = requests.get(url_stopwords)
phan_hoi_stopwords.encoding = "utf-8"
stop_words = set(phan_hoi_stopwords.text.split())

# Danh sách chuyên mục trên VnExpress
danh_muc_urls = {
    "Kinh doanh": "https://vnexpress.net/kinh-doanh",
    "Khoa học - Công nghệ": "https://vnexpress.net/khoa-hoc-cong-nghe",
    "Bất động sản": "https://vnexpress.net/bat-dong-san", 
    "Sức khỏe": "https://vnexpress.net/suc-khoe",
    "Thể thao": "https://vnexpress.net/the-thao",
    "Giải trí": "https://vnexpress.net/giai-tri",
    "Pháp luật": "https://vnexpress.net/phap-luat",
    "Giáo dục": "https://vnexpress.net/giao-duc",
    "Ô tô - Xe máy": "https://vnexpress.net/oto-xe-may",
    "Du lịch": "https://vnexpress.net/du-lich"
}

# Hàm làm sạch văn bản
def lam_sach_van_ban(van_ban):
    van_ban = van_ban.lower()
    van_ban = re.sub(r"[^\w\s]", "", van_ban)
    van_ban = re.sub(r"\s+", " ", van_ban).strip()
    return van_ban

# Hàm tách từ trong câu
def tach_tu(van_ban):
    return van_ban.split(" ")

# Hàm đếm từ
def dem_tu(danh_sach_tu):
    tan_suat_tu = {}
    for tu in danh_sach_tu:
        tan_suat_tu[tu] = tan_suat_tu.get(tu, 0) + 1
    return tan_suat_tu

# Hàm lấy tiêu đề và mô tả bài báo từ VnExpress
def lay_du_lieu(url):
    phan_hoi = requests.get(url)
    phan_hoi.encoding = "utf-8"
    phan_tich = BeautifulSoup(phan_hoi.text, "html.parser")

    # Lấy tiêu đề bài báo
    bai_viet = phan_tich.find_all("h3", class_="title-news")
    tieu_de = [lam_sach_van_ban(bv.text.strip()) for bv in bai_viet]

    # Lấy mô tả bài báo
    mo_ta_bai_viet = phan_tich.find_all("p", class_="description")
    mo_ta = [lam_sach_van_ban(mt.text.strip()) for mt in mo_ta_bai_viet]

    # Kết hợp tiêu đề và mô tả thành một danh sách nội dung
    return tieu_de + mo_ta

# Huấn luyện dữ liệu
du_lieu_huan_luyen = {chuyen_muc: lay_du_lieu(url) for chuyen_muc, url in danh_muc_urls.items()}

du_lieu_sach = {chuyen_muc: [lam_sach_van_ban(text) for text in du_lieu_huan_luyen[chuyen_muc]] for chuyen_muc in du_lieu_huan_luyen}
du_lieu_tach_tu = {chuyen_muc: [tach_tu(text) for text in du_lieu_sach[chuyen_muc]] for chuyen_muc in du_lieu_sach}
tan_suat_tu_huan_luyen = {chuyen_muc: dem_tu(sum(du_lieu_tach_tu[chuyen_muc], [])) for chuyen_muc in du_lieu_tach_tu}
tong_so_tu_huan_luyen = {chuyen_muc: len(sum(du_lieu_tach_tu[chuyen_muc], [])) for chuyen_muc in du_lieu_tach_tu}

# Danh sách từ vựng
tu_vung = []
for chuyen_muc in tan_suat_tu_huan_luyen.values():
    tu_vung.extend(chuyen_muc)
tu_vung = set(tu_vung) 
tong_tu_vung = len(tu_vung)

# Hàm dự đoán
def phan_loai_van_ban(van_ban):
    van_ban = lam_sach_van_ban(van_ban)
    danh_sach_tu = tach_tu(van_ban)
    xac_suat_the_loai = {chuyen_muc: 1 / len(danh_muc_urls) for chuyen_muc in danh_muc_urls.keys()}

    for tu in danh_sach_tu:
        for chuyen_muc in danh_muc_urls.keys():
            tan_suat_tu = tan_suat_tu_huan_luyen[chuyen_muc].get(tu, 0)
            p_tu = (tan_suat_tu + 1) / (tong_so_tu_huan_luyen[chuyen_muc] + tong_tu_vung)
            xac_suat = p_tu * xac_suat_the_loai[chuyen_muc]
            xac_suat_the_loai[chuyen_muc] = xac_suat
    return max(xac_suat_the_loai, key=xac_suat_the_loai.get)

# Giao diện Streamlit
st.title("PHÂN LOẠI VĂN BẢN THEO THỂ LOẠI")
st.write("Các thể loại: Kinh doanh, Khoa học - Công nghệ, Bất động sản, Sức khỏe, Thể thao, Giải trí, Pháp luật, Giáo dục, Ô tô - Xe máy, Du lịch")

lua_chon = st.selectbox("Chọn cách nhập nội dung: (1: Nhập tay, 2: Tải file .txt)", [1, 2])
noi_dung = ""
if lua_chon == 1:
    noi_dung = st.text_area("Nhập nội dung văn bản:", height=300)
elif lua_chon == 2:
    file = st.file_uploader("Tải lên file .txt", type=["txt"])
    if file is not None:
        noi_dung = file.read().decode("utf-8")
        st.text_area("Nội dung file:", noi_dung, height=200) 

if st.button("Phân loại"):
    if noi_dung.strip() == "":
        st.warning("Vui lòng nhập nội dung hoặc tải file.")
    else:
        the_loai = phan_loai_van_ban(noi_dung)
        st.success(f"Văn bản thuộc thể loại: {the_loai.upper()}")
