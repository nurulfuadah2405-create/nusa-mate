# ===== BAGIAN 1: Impor, pengaturan halaman, warna, dan gaya CSS =====
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Nusa Mete | Dashboard Jambu Mete NTT",
    page_icon="🌰",
    layout="wide",
    initial_sidebar_state="expanded",
)

HIJAU = "#1F4D3A"
HIJAU_SEDANG = "#2F6B4F"
HIJAU_MUDA = "#8DB580"
JINGGA = "#D98324"
TERAKOTA = "#B5482A"
PASIR = "#EADBC0"
TEKS = "#2B2A26"
SKALA_METE = ["#F6EBD3", "#E9B872", "#D98324", "#9C4A1A"]
PALET_GARIS = [HIJAU_SEDANG, JINGGA, TERAKOTA, "#4C8CA8", "#7B5EA7", "#6B665B"]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Fraunces:wght@600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1280px; }
h1, h2, h3 { font-family: 'Fraunces', serif !important; color: #1F4D3A; }
#MainMenu, footer { visibility: hidden; }
.hero { background: linear-gradient(120deg, #1F4D3A 0%, #2F6B4F 55%, #D98324 150%);
  border-radius: 22px; padding: 28px 34px; margin-bottom: 18px; color: #FBF7EF; }
.hero h1 { color: #FBF7EF !important; margin: 0; font-size: 2.5rem; padding: 0; }
.hero p { margin: 6px 0 0 0; opacity: .92; font-size: 1.02rem; }
.chip { display: inline-block; background: rgba(255,255,255,.16); border-radius: 99px;
  padding: 3px 13px; margin: 14px 8px 0 0; font-size: .82rem; }
.kpi { background: #fff; border: 1px solid #EADBC0; border-top: 5px solid var(--aksen);
  border-radius: 18px; padding: 16px 18px; height: 100%; }
.kpi-label { font-size: .78rem; color: #6B665B; text-transform: uppercase;
  letter-spacing: .06em; }
.kpi-value { font-family: 'Fraunces', serif; font-size: 1.9rem; color: #1F4D3A;
  line-height: 1.15; margin-top: 4px; }
.kpi-value span { font-family: 'DM Sans', sans-serif; font-size: .9rem;
  color: #6B665B; }
.kpi-delta { font-size: .85rem; font-weight: 500; margin-top: 4px; }
.baik { color: #2F6B4F; } .buruk { color: #B5482A; } .netral { color: #6B665B; }
.insight { background: #FFF6E3; border-left: 5px solid #D98324; border-radius: 10px;
  padding: 12px 16px; font-size: .95rem; margin: 6px 0 14px 0; }
div[data-testid="stVerticalBlockBorderWrapper"] { background: #fff;
  border-radius: 18px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ===== BAGIAN 2: Fungsi bantu (format angka, kartu KPI, tema grafik) =====
def angka(x, desimal=0):
    """Format angka gaya Indonesia, misalnya 1.234,5."""
    if x is None or pd.isna(x):
        return "-"
    teks = f"{x:,.{desimal}f}"
    return teks.replace(",", "_").replace(".", ",").replace("_", ".")


def persen_ubah(baru, lama):
    if lama is None or pd.isna(lama) or lama == 0:
        return None
    return (baru - lama) / lama * 100


def delta_html(baru, lama, tahun_lama, naik_baik=True):
    d = persen_ubah(baru, lama)
    if d is None:
        return '<div class="kpi-delta netral">belum ada tahun pembanding</div>'
    panah = "▲" if d >= 0 else "▼"
    kelas = "baik" if (d >= 0) == naik_baik else "buruk"
    return (
        f'<div class="kpi-delta {kelas}">{panah} {angka(abs(d), 1)}% '
        f"dibanding {tahun_lama}</div>"
    )


def kartu(label, nilai, satuan, delta, aksen):
    return (
        f'<div class="kpi" style="--aksen:{aksen}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{nilai} <span>{satuan}</span></div>'
        f"{delta}</div>"
    )


def daftar(nama):
    nama = list(nama)
    if len(nama) <= 1:
        return "".join(nama)
    return ", ".join(nama[:-1]) + " dan " + nama[-1]


def tema(fig, tinggi=380, judul=None):
    fig.update_layout(
        height=tinggi,
        margin=dict(l=10, r=10, t=60 if judul else 20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color=TEKS, size=13),
        separators=",.",
        legend=dict(orientation="h", y=-0.18, x=0, title_text=""),
        hoverlabel=dict(bgcolor="white", font_size=13),
    )
    if judul:
        fig.update_layout(
            title=dict(
                text=judul,
                x=0.01,
                font=dict(family="Fraunces, serif", size=18, color=HIJAU),
            )
        )
    fig.update_xaxes(showgrid=False, linecolor=PASIR)
    fig.update_yaxes(gridcolor="#EFE6D2", zeroline=False)
    return fig


def tampil(fig):
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ===== BAGIAN 3: Memuat data dari Neon (cadangan: berkas CSV) =====
KOLOM_ANGKA = [
    "luas_tm_ha",
    "luas_tbm_ha",
    "luas_tt_tr_ha",
    "produksi_ton",
    "produktivitas_kg_ha",
    "produktivitas_hitung",
]

SQL = """
    SELECT kode_wilayah, nama_wilayah, tahun,
           luas_tm_ha, luas_tbm_ha, luas_tt_tr_ha,
           produksi_ton, produktivitas_kg_ha, produktivitas_hitung,
           status_data, updated_at
    FROM jambu_mete_pusat
    ORDER BY kode_wilayah, tahun
"""


def baca_neon():
    import psycopg2

    koneksi = psycopg2.connect(st.secrets["neon"]["url"])
    try:
        with koneksi.cursor() as cur:
            cur.execute(SQL)
            baris = cur.fetchall()
            kolom = [k[0] for k in cur.description]
    finally:
        koneksi.close()
    return pd.DataFrame(baris, columns=kolom)


def rapikan(df):
    df = df.copy()
    df["kode_wilayah"] = df["kode_wilayah"].astype(str)
    df["tahun"] = df["tahun"].astype(int)
    for k in KOLOM_ANGKA:
        df[k] = pd.to_numeric(df[k].astype(float), errors="coerce")
    df["status_data"] = df["status_data"].fillna("BELUM ADA")
    df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce", utc=True)
    areal = df[["luas_tm_ha", "luas_tbm_ha", "luas_tt_tr_ha"]].sum(axis=1)
    df["total_areal_ha"] = areal
    pembagi = areal.where(areal > 0)
    df["porsi_tt_tr"] = df["luas_tt_tr_ha"] / pembagi * 100
    df["porsi_tm"] = df["luas_tm_ha"] / pembagi * 100
    df["porsi_tbm"] = df["luas_tbm_ha"] / pembagi * 100
    df["selisih_produktivitas"] = (
        df["produktivitas_kg_ha"] - df["produktivitas_hitung"]
    )
    return df


@st.cache_data(ttl=600, show_spinner="Mengambil data dari Neon...")
def muat_data():
    try:
        df, sumber, catatan = baca_neon(), "Neon PostgreSQL", ""
    except Exception as galat:
        csv = Path(__file__).parent / "data" / "jambu_mete_pusat.csv"
        df = pd.read_csv(csv, dtype={"kode_wilayah": str})
        sumber = "Berkas CSV"
        catatan = f"Koneksi Neon tidak dipakai ({type(galat).__name__})."
    return rapikan(df), sumber, catatan


df_all, sumber_data, catatan_data = muat_data()


# ===== BAGIAN 4: Filter di sidebar dan perhitungan dasar =====
tahun_list = sorted(df_all["tahun"].unique())
semua_wilayah = sorted(df_all["nama_wilayah"].unique())

with st.sidebar:
    st.markdown("### 🌰 Nusa Mete")
    st.caption("Filter berlaku untuk seluruh halaman dashboard.")
    tahun = st.select_slider(
        "Tahun analisis", options=tahun_list, value=tahun_list[-1]
    )
    pilih = st.multiselect(
        "Kabupaten/Kota",
        semua_wilayah,
        default=semua_wilayah,
        placeholder="Pilih satu atau lebih wilayah",
    )
    if st.button("Muat ulang data", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.caption(f"Sumber data: {sumber_data}")
    if catatan_data:
        st.caption(catatan_data)

if not pilih:
    st.warning("Pilih minimal satu kabupaten/kota pada panel kiri.")
    st.stop()

df = df_all[df_all["nama_wilayah"].isin(pilih)]
now = df[df["tahun"] == tahun].copy()
tahun_lalu = tahun - 1

tren = (
    df.groupby("tahun")
    .agg(
        produksi=("produksi_ton", "sum"),
        tm=("luas_tm_ha", "sum"),
        tbm=("luas_tbm_ha", "sum"),
        tt=("luas_tt_tr_ha", "sum"),
    )
    .reset_index()
)
tren["produktivitas"] = tren["produksi"] / tren["tm"] * 1000
tren["porsi_tt"] = tren["tt"] / (tren["tm"] + tren["tbm"] + tren["tt"]) * 100

baris_ini = tren[tren["tahun"] == tahun].iloc[0]
cari_lalu = tren[tren["tahun"] == tahun_lalu]
baris_lalu = cari_lalu.iloc[0] if len(cari_lalu) else None


def nilai_lalu(kolom):
    return None if baris_lalu is None else baris_lalu[kolom]


rata_produktivitas = baris_ini["produktivitas"]


# ===== BAGIAN 5: Header dan kartu KPI =====
terbaru = df["updated_at"].max()
teks_update = terbaru.strftime("%d/%m/%Y") if pd.notna(terbaru) else "-"
st.markdown(
    '<div class="hero"><h1>🌰 Nusa Mete</h1>'
    "<p>Pusat pantau produksi, produktivitas, dan struktur umur tanaman "
    "jambu mete di Nusa Tenggara Timur.</p>"
    f'<span class="chip">{len(pilih)} kabupaten/kota</span>'
    f'<span class="chip">Tahun {tahun_list[0]} sampai {tahun_list[-1]}</span>'
    f'<span class="chip">Data diperbarui {teks_update}</span></div>',
    unsafe_allow_html=True,
)

perlu_cek = int((now["status_data"] == "PERLU CEK").sum())
kpi = st.columns(5)
kpi[0].markdown(
    kartu(
        f"Produksi {tahun}",
        angka(baris_ini["produksi"]),
        "ton",
        delta_html(baris_ini["produksi"], nilai_lalu("produksi"), tahun_lalu),
        HIJAU_SEDANG,
    ),
    unsafe_allow_html=True,
)
kpi[1].markdown(
    kartu(
        "Produktivitas rata-rata",
        angka(rata_produktivitas),
        "kg/ha",
        delta_html(rata_produktivitas, nilai_lalu("produktivitas"), tahun_lalu),
        JINGGA,
    ),
    unsafe_allow_html=True,
)
kpi[2].markdown(
    kartu(
        "Luas tanaman menghasilkan",
        angka(baris_ini["tm"]),
        "ha",
        delta_html(baris_ini["tm"], nilai_lalu("tm"), tahun_lalu),
        HIJAU_MUDA,
    ),
    unsafe_allow_html=True,
)
kpi[3].markdown(
    kartu(
        "Areal tua atau rusak",
        angka(baris_ini["tt"]),
        "ha",
        delta_html(baris_ini["tt"], nilai_lalu("tt"), tahun_lalu, naik_baik=False),
        TERAKOTA,
    ),
    unsafe_allow_html=True,
)
kelas_cek = "buruk" if perlu_cek else "baik"
kpi[4].markdown(
    kartu(
        "Data perlu dicek",
        str(perlu_cek),
        f"dari {len(now)} wilayah",
        f'<div class="kpi-delta {kelas_cek}">'
        f'{"Periksa tab Data & Kualitas" if perlu_cek else "Semua data sesuai"}</div>',
        "#6B665B",
    ),
    unsafe_allow_html=True,
)
st.write("")

tab_ringkas, tab_produktif, tab_remaja, tab_banding, tab_data = st.tabs(
    ["📊 Ringkasan", "🌿 Produktivitas", "♻️ Peremajaan",
     "🔍 Banding Wilayah", "🧾 Data & Kualitas"]
)


# ===== BAGIAN 6: Tab Ringkasan =====
with tab_ringkas:
    urut = now.sort_values("produksi_ton", ascending=False)
    total_produksi = now["produksi_ton"].sum()
    ada_sah = (now["status_data"] != "PERLU CEK").any()
    if len(urut) >= 3 and total_produksi > 0 and ada_sah:
        tiga = urut.head(3)
        porsi_tiga = tiga["produksi_ton"].sum() / total_produksi * 100
        sah = now[now["status_data"] != "PERLU CEK"]
        tinggi = sah.loc[sah["produktivitas_kg_ha"].idxmax()]
        rendah = sah.loc[sah["produktivitas_kg_ha"].idxmin()]
        st.markdown(
            f'<div class="insight">Pada {tahun}, {daftar(tiga["nama_wilayah"])} '
            f"menyumbang {angka(porsi_tiga, 1)}% produksi dari wilayah terpilih. "
            "Di antara data berstatus sesuai, produktivitas tertinggi tercatat di "
            f'{tinggi["nama_wilayah"]} '
            f'({angka(tinggi["produktivitas_kg_ha"])} kg/ha) dan terendah di '
            f'{rendah["nama_wilayah"]} '
            f'({angka(rendah["produktivitas_kg_ha"])} kg/ha).'
            "</div>",
            unsafe_allow_html=True,
        )

    kiri, kanan = st.columns([3, 2])
    with kiri.container(border=True):
        fig = go.Figure()
        fig.add_bar(
            x=tren["tahun"],
            y=tren["produksi"],
            name="Produksi (ton)",
            marker_color=HIJAU_SEDANG,
            texttemplate="%{y:,.0f}",
            textposition="outside",
            cliponaxis=False,
        )
        fig.add_scatter(
            x=tren["tahun"],
            y=tren["produktivitas"],
            name="Produktivitas (kg/ha)",
            yaxis="y2",
            mode="lines+markers",
            line=dict(color=JINGGA, width=3),
            marker=dict(size=10, line=dict(color="white", width=2)),
        )
        fig.update_layout(
            yaxis=dict(title="ton", range=[0, tren["produksi"].max() * 1.2]),
            yaxis2=dict(
                title="kg/ha",
                overlaying="y",
                side="right",
                showgrid=False,
                range=[0, tren["produktivitas"].max() * 1.5],
            ),
        )
        fig.update_xaxes(type="category")
        tampil(tema(fig, 400, "Tren produksi dan produktivitas"))

    with kanan.container(border=True):
        komposisi = pd.DataFrame(
            {
                "Kelompok": ["TM (menghasilkan)", "TBM (belum menghasilkan)",
                             "TT/TR (tua atau rusak)"],
                "ha": [now["luas_tm_ha"].sum(), now["luas_tbm_ha"].sum(),
                       now["luas_tt_tr_ha"].sum()],
            }
        )
        fig = px.pie(
            komposisi,
            names="Kelompok",
            values="ha",
            hole=0.62,
            color="Kelompok",
            color_discrete_map={
                "TM (menghasilkan)": HIJAU_SEDANG,
                "TBM (belum menghasilkan)": HIJAU_MUDA,
                "TT/TR (tua atau rusak)": TERAKOTA,
            },
        )
        fig.update_traces(textinfo="percent", sort=False, textfont_size=14)
        fig.add_annotation(
            text=f"{angka(komposisi['ha'].sum())}<br>ha",
            showarrow=False,
            font=dict(size=18, family="Fraunces, serif", color=HIJAU),
        )
        tampil(tema(fig, 400, f"Komposisi areal {tahun}"))

    kiri, kanan = st.columns(2)
    with kiri.container(border=True):
        sepuluh = now.nlargest(10, "produksi_ton").sort_values("produksi_ton")
        fig = px.bar(
            sepuluh,
            x="produksi_ton",
            y="nama_wilayah",
            orientation="h",
            color="produktivitas_kg_ha",
            color_continuous_scale=SKALA_METE,
            labels={"produksi_ton": "Produksi (ton)", "nama_wilayah": "",
                    "produktivitas_kg_ha": "kg/ha"},
        )
        fig.update_traces(texttemplate="%{x:,.0f}", textposition="outside",
                          cliponaxis=False)
        fig.update_coloraxes(colorbar=dict(title="kg/ha", thickness=10, len=0.7))
        fig.update_xaxes(range=[0, sepuluh["produksi_ton"].max() * 1.2])
        tampil(tema(fig, 430, f"10 produsen terbesar {tahun}"))

    with kanan.container(border=True):
        peta = now[now["produksi_ton"] > 0]
        fig = px.treemap(
            peta,
            path=[px.Constant("NTT"), "nama_wilayah"],
            values="produksi_ton",
            color="produktivitas_kg_ha",
            color_continuous_scale=SKALA_METE,
            labels={"produktivitas_kg_ha": "kg/ha"},
        )
        fig.update_traces(
            texttemplate="%{label}<br>%{value:,.0f} ton",
            marker=dict(cornerradius=6),
        )
        fig.update_coloraxes(colorbar=dict(title="kg/ha", thickness=10, len=0.7))
        tampil(tema(fig, 430, "Peta pohon produksi (warna = produktivitas)"))


# ===== BAGIAN 7: Tab Produktivitas dan Peremajaan =====
with tab_produktif:
    kiri, kanan = st.columns([3, 2])
    with kiri.container(border=True):
        pivot = df.pivot_table(
            index="nama_wilayah", columns="tahun", values="produktivitas_kg_ha"
        )
        pivot = pivot.sort_values(pivot.columns[-1], ascending=False)
        fig = px.imshow(
            pivot,
            text_auto=".0f",
            aspect="auto",
            color_continuous_scale=SKALA_METE,
            labels=dict(color="kg/ha", x="", y=""),
        )
        fig.update_xaxes(side="top", type="category")
        fig.update_coloraxes(colorbar=dict(thickness=10, len=0.6))
        tampil(tema(fig, max(380, 26 * len(pivot) + 90),
                    "Peta panas produktivitas (kg/ha)"))

    with kanan.container(border=True):
        selisih = now.assign(
            selisih=now["produktivitas_kg_ha"] - rata_produktivitas,
            posisi=lambda d: d["produktivitas_kg_ha"].ge(rata_produktivitas).map(
                {True: "Di atas rata-rata", False: "Di bawah rata-rata"}
            ),
        ).sort_values("selisih")
        fig = px.bar(
            selisih,
            x="selisih",
            y="nama_wilayah",
            orientation="h",
            color="posisi",
            color_discrete_map={"Di atas rata-rata": HIJAU_SEDANG,
                                "Di bawah rata-rata": TERAKOTA},
            labels={"selisih": "Selisih (kg/ha)", "nama_wilayah": ""},
        )
        tampil(tema(fig, max(380, 26 * len(selisih) + 90),
                    f"Selisih terhadap rata-rata {angka(rata_produktivitas)} kg/ha"))

    with st.container(border=True):
        sebar = now[(now["luas_tm_ha"] > 0) & (now["produksi_ton"] > 0)]
        fig = px.scatter(
            sebar,
            x="luas_tm_ha",
            y="produksi_ton",
            size="total_areal_ha",
            color="produktivitas_kg_ha",
            color_continuous_scale=SKALA_METE,
            hover_name="nama_wilayah",
            log_x=True,
            log_y=True,
            size_max=42,
            labels={"luas_tm_ha": "Luas TM (ha)", "produksi_ton": "Produksi (ton)",
                    "produktivitas_kg_ha": "kg/ha",
                    "total_areal_ha": "Total areal (ha)"},
        )
        garis_x = [sebar["luas_tm_ha"].min(), sebar["luas_tm_ha"].max()]
        fig.add_scatter(
            x=garis_x,
            y=[x * rata_produktivitas / 1000 for x in garis_x],
            mode="lines",
            line=dict(color=TEKS, dash="dash", width=1.5),
            name="Rata-rata NTT",
            hoverinfo="skip",
        )
        fig.update_coloraxes(colorbar=dict(title="kg/ha", thickness=10, len=0.7))
        tampil(tema(fig, 460, "Luas TM dan produksi (titik di atas garis putus-putus: "
                              "di atas rata-rata)"))

with tab_remaja:
    now = now.copy()
    batas_produktif = rata_produktivitas
    batas_tua = now["porsi_tt_tr"].median()

    def kuadran(baris):
        rendah = baris["produktivitas_kg_ha"] < batas_produktif
        tua = baris["porsi_tt_tr"] >= batas_tua
        if rendah and tua:
            return "Prioritas peremajaan"
        if tua:
            return "Siapkan peremajaan"
        if rendah:
            return "Perbaiki budidaya"
        return "Relatif sehat"

    now["kuadran"] = now.apply(kuadran, axis=1)

    def minmax(s):
        rentang = s.max() - s.min()
        return (s - s.min()) / rentang if rentang else s * 0

    now["ipp"] = (
        0.5 * minmax(now["porsi_tt_tr"])
        + 0.5 * (1 - minmax(now["produktivitas_kg_ha"]))
    ) * 100

    kiri, kanan = st.columns(2)
    with kiri.container(border=True):
        susun = now.sort_values("porsi_tt_tr")
        fig = go.Figure()
        for kolom, nama, warna in [
            ("porsi_tm", "TM", HIJAU_SEDANG),
            ("porsi_tbm", "TBM", HIJAU_MUDA),
            ("porsi_tt_tr", "TT/TR", TERAKOTA),
        ]:
            fig.add_bar(x=susun[kolom], y=susun["nama_wilayah"], name=nama,
                        orientation="h", marker_color=warna,
                        hovertemplate="%{y}: %{x:.1f}%<extra>" + nama + "</extra>")
        fig.update_layout(barmode="stack")
        fig.update_xaxes(range=[0, 100], ticksuffix="%")
        tampil(tema(fig, max(420, 26 * len(susun) + 100),
                    f"Struktur umur tanaman {tahun}"))

    with kanan.container(border=True):
        now["label"] = now["nama_wilayah"].where(
            now["kuadran"].isin(["Prioritas peremajaan", "Siapkan peremajaan"]), ""
        )
        fig = px.scatter(
            now,
            x="produktivitas_kg_ha",
            y="porsi_tt_tr",
            color="kuadran",
            size="total_areal_ha",
            size_max=36,
            text="label",
            hover_name="nama_wilayah",
            color_discrete_map={
                "Prioritas peremajaan": TERAKOTA,
                "Siapkan peremajaan": JINGGA,
                "Perbaiki budidaya": "#4C8CA8",
                "Relatif sehat": HIJAU_SEDANG,
            },
            labels={"produktivitas_kg_ha": "Produktivitas (kg/ha)",
                    "porsi_tt_tr": "Porsi TT/TR (%)", "kuadran": ""},
        )
        fig.update_traces(textposition="top center", textfont_size=11)
        fig.add_vline(x=batas_produktif, line_dash="dash", line_color=TEKS,
                      opacity=0.5)
        fig.add_hline(y=batas_tua, line_dash="dash", line_color=TEKS, opacity=0.5)
        fig.update_yaxes(ticksuffix="%")
        tampil(tema(fig, max(420, 26 * len(now) + 100), "Kuadran peremajaan"))

    with st.container(border=True):
        st.markdown("#### Indeks Prioritas Peremajaan (IPP)")
        st.caption(
            "IPP = 50% porsi TT/TR + 50% kebalikan produktivitas, masing-masing "
            "diskalakan 0 sampai 100 di antara wilayah terpilih. Ini indeks "
            "penyaring untuk latihan, bukan indikator resmi."
        )
        tabel = now.sort_values("ipp", ascending=False)[
            ["nama_wilayah", "kuadran", "porsi_tt_tr", "produktivitas_kg_ha",
             "luas_tt_tr_ha", "ipp"]
        ]
        st.dataframe(
            tabel,
            hide_index=True,
            width="stretch",
            column_config={
                "nama_wilayah": "Kabupaten/Kota",
                "kuadran": "Kelompok",
                "porsi_tt_tr": st.column_config.NumberColumn(
                    "TT/TR (%)", format="%.1f"),
                "produktivitas_kg_ha": st.column_config.NumberColumn(
                    "Produktivitas (kg/ha)", format="%.0f"),
                "luas_tt_tr_ha": st.column_config.NumberColumn(
                    "Luas TT/TR (ha)", format="%.0f"),
                "ipp": st.column_config.ProgressColumn(
                    "IPP", min_value=0, max_value=100, format="%.0f"),
            },
        )


# ===== BAGIAN 8: Tab Banding Wilayah dan Data & Kualitas =====
with tab_banding:
    METRIK = {
        "Produksi (ton)": "produksi_ton",
        "Produktivitas (kg/ha)": "produktivitas_kg_ha",
        "Luas TM (ha)": "luas_tm_ha",
        "Luas TBM (ha)": "luas_tbm_ha",
        "Luas TT/TR (ha)": "luas_tt_tr_ha",
    }
    awal = list(now.nlargest(3, "produksi_ton")["nama_wilayah"])
    kol1, kol2 = st.columns([3, 2])
    banding = kol1.multiselect(
        "Wilayah yang dibandingkan (maksimal 6)",
        pilih,
        default=awal,
        max_selections=6,
    )
    nama_metrik = kol2.radio("Indikator", list(METRIK), horizontal=True)
    kolom_metrik = METRIK[nama_metrik]

    if banding:
        sub = df[df["nama_wilayah"].isin(banding)]
        with st.container(border=True):
            fig = px.line(
                sub,
                x="tahun",
                y=kolom_metrik,
                color="nama_wilayah",
                markers=True,
                color_discrete_sequence=PALET_GARIS,
                labels={kolom_metrik: nama_metrik, "tahun": "", "nama_wilayah": ""},
            )
            fig.update_traces(line=dict(width=3), marker=dict(size=9))
            fig.update_xaxes(type="category")
            tampil(tema(fig, 420, f"{nama_metrik} per tahun"))

        lebar = sub.pivot_table(index="nama_wilayah", columns="tahun",
                                values=kolom_metrik)
        pertama, terakhir = lebar.columns[0], lebar.columns[-1]
        lebar["Perubahan (%)"] = (
            (lebar[terakhir] - lebar[pertama]) / lebar[pertama] * 100
        )
        lebar.columns = [str(k) for k in lebar.columns]
        st.dataframe(
            lebar.reset_index().rename(columns={"nama_wilayah": "Kabupaten/Kota"}),
            hide_index=True,
            width="stretch",
            column_config={
                "Perubahan (%)": st.column_config.NumberColumn(format="%.1f")
            },
        )
    else:
        st.info("Pilih minimal satu wilayah untuk dibandingkan.")

with tab_data:
    c1, c2, c3 = st.columns(3)
    c1.metric("Baris data terfilter", angka(len(df)))
    c2.metric("Status SESUAI", angka((df["status_data"] == "SESUAI").sum()))
    c3.metric("Status PERLU CEK", angka((df["status_data"] == "PERLU CEK").sum()))

    cek = df[df["status_data"] != "SESUAI"]
    if len(cek):
        st.markdown("#### Baris yang perlu diperiksa")
        st.caption(
            "Produktivitas resmi tidak sama dengan produksi dibagi luas TM. "
            "Periksa sumber aslinya sebelum angka ini dikutip."
        )
        st.dataframe(
            cek[["nama_wilayah", "tahun", "produksi_ton", "luas_tm_ha",
                 "produktivitas_kg_ha", "produktivitas_hitung",
                 "selisih_produktivitas", "status_data"]],
            hide_index=True,
            width="stretch",
        )
    else:
        st.success("Seluruh baris pada wilayah terpilih berstatus SESUAI.")

    st.markdown("#### Seluruh data")
    tampilan = df.drop(columns=["updated_at", "porsi_tm", "porsi_tbm"])
    st.dataframe(tampilan, hide_index=True, width="stretch", height=380)
    st.download_button(
        "Unduh data terfilter (CSV)",
        data=df.drop(columns=["updated_at"]).to_csv(index=False).encode("utf-8"),
        file_name="nusa_mete_data.csv",
        mime="text/csv",
    )

st.caption(
    "Nusa Mete | Data jambu mete NTT 2022-2025 dari basis data Neon "
    "(tabel jambu_mete_pusat). Produktivitas rata-rata dihitung dari total "
    "produksi dibagi total luas TM."
)
