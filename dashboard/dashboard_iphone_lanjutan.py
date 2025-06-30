import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# -----------------
# KONFIGURASI HALAMAN
# -----------------
st.set_page_config(
    page_title="Dashboard Analisis iPhone",
    page_icon="📱",
    layout="wide"
)

# -----------------
# FUNGSI BANTUAN
# -----------------
@st.cache_data
def load_data():
    """Memuat dan memproses data dari file CSV."""
    df = pd.read_csv('...\data\iphone_dataset_csv.csv')
    df["Tahun"] = pd.to_numeric(df["Tahun"], errors='coerce')
    df = df.dropna(subset=['Tahun']).sort_values("Tahun").reset_index(drop=True)

    # Perhitungan metrik tambahan untuk analisis
    df['% Pengguna AS dari Global (Aktual)'] = (df['Pengguna Iphone di USA'] / df['Pengguna Iphone di Dunia']) * 100
    df['% Penjualan AS dari Global (Aktual)'] = (df['Jumlah Penjualan Iphone di USA'] / df['Jumlah Penjualan Iphone di Dunia']) * 100
    
    # Pertumbuhan Year-over-Year
    df['YoY Pengguna Global (%)'] = df['Pengguna Iphone di Dunia'].pct_change() * 100
    df['YoY Pengguna AS (%)'] = df['Pengguna Iphone di USA'].pct_change() * 100
    df['YoY Penjualan Global (%)'] = df['Jumlah Penjualan Iphone di Dunia'].pct_change() * 100
    df['YoY Penjualan AS (%)'] = df['Jumlah Penjualan Iphone di USA'].pct_change() * 100
    
    # Penetrasi pasar (Penjualan/Pengguna)
    df['Penetrasi Global (%)'] = (df['Jumlah Penjualan Iphone di Dunia'] / df['Pengguna Iphone di Dunia']) * 100
    df['Penetrasi AS (%)'] = (df['Jumlah Penjualan Iphone di USA'] / df['Pengguna Iphone di USA']) * 100
    
    # Analisis market share
    df['Total Market Share'] = df['Persentase penguasaan pasar IOS'] + df['Persentase penguasaan pasar Android']
    df['Market Share Lainnya'] = 100 - df['Total Market Share']
    
    # ARPU estimation (Average Revenue Per User) - proxy calculation
    # Asumsi harga rata-rata iPhone $600-800
    avg_iphone_price = 700  # USD
    df['Est. Revenue Global (Miliar USD)'] = (df['Jumlah Penjualan Iphone di Dunia'] * avg_iphone_price) / 1_000_000_000
    df['Est. Revenue AS (Miliar USD)'] = (df['Jumlah Penjualan Iphone di USA'] * avg_iphone_price) / 1_000_000_000
    
    return df

def format_number(num):
    """Format angka menjadi lebih mudah dibaca."""
    if pd.isna(num):
        return "N/A"
    if abs(num) >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f}B"
    if abs(num) >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    if abs(num) >= 1_000:
        return f"{num / 1_000:.1f}K"
    return f"{num:.1f}"

def calculate_cagr(start_value, end_value, num_periods):
    """Menghitung Compound Annual Growth Rate."""
    if start_value <= 0 or end_value <= 0 or num_periods <= 0:
        return 0
    return ((end_value / start_value) ** (1 / num_periods) - 1) * 100

def configure_xaxis_all_years(fig, years_data):
    """Konfigurasi sumbu x untuk menampilkan semua tahun."""
    fig.update_xaxes(
        tickmode='array',
        tickvals=years_data,
        ticktext=[str(int(year)) for year in years_data],
        tickangle=0
    )
    return fig

# -----------------
# MAIN APP
# -----------------
# Muat data
df = load_data()

# --- SIDEBAR ---
st.sidebar.title("🔍 Filter & Pengaturan")
tahun_dipilih = st.sidebar.slider(
    "Pilih Rentang Tahun:",
    min_value=int(df['Tahun'].min()),
    max_value=int(df['Tahun'].max()),
    value=(int(df['Tahun'].min()), int(df['Tahun'].max()))
)

# Pilihan analisis
analisis_mode = st.sidebar.selectbox(
    "Mode Analisis:",
    ["Ringkasan Eksekutif", "Analisis Mendalam", "Perbandingan Segmen"]
)

# Filter data berdasarkan rentang tahun yang dipilih
df_filtered = df[(df['Tahun'] >= tahun_dipilih[0]) & (df['Tahun'] <= tahun_dipilih[1])]

# --- HEADER ---
st.title("📱 iPhone Market Analytics Dashboard")
st.markdown(f"Periode Analisis: {tahun_dipilih[0]} - {tahun_dipilih[1]} | Mode: {analisis_mode}")

# --- VALIDASI DATA & INSIGHTS AWAL ---
with st.expander("🔍 Temuan Analisis Data Awal"):
    col1, col2 = st.columns(2)
    with col1:
        st.info("""
        Inkonsistensi Data Terdeteksi:
        - Kolom 'Persentase Pengguna iPhone' tampak tidak konsisten dengan perhitungan aktual
        - Contoh 2023: Tercatat 58.33% vs perhitungan aktual ~10.5%
        - Dashboard menggunakan perhitungan ulang untuk akurasi
        """)
    with col2:
        latest_data = df_filtered.iloc[-1]
        first_data = df_filtered.iloc[0]
        years_span = len(df_filtered) - 1
        
        if years_span > 0:
            user_cagr = calculate_cagr(first_data['Pengguna Iphone di Dunia'], 
                                     latest_data['Pengguna Iphone di Dunia'], years_span)
            sales_cagr = calculate_cagr(first_data['Jumlah Penjualan Iphone di Dunia'], 
                                      latest_data['Jumlah Penjualan Iphone di Dunia'], years_span)
        else:
            user_cagr = sales_cagr = 0
            
        st.success(f"""
        Tren Pertumbuhan ({tahun_dipilih[0]}-{tahun_dipilih[1]}):
        - Pengguna Global CAGR: {user_cagr:.1f}%
        - Penjualan Global CAGR: {sales_cagr:.1f}%
        - Market Share iOS: {latest_data['Persentase penguasaan pasar IOS']:.1f}%
        """)

# --- KPI DASHBOARD ---
if not df_filtered.empty:
    latest = df_filtered.iloc[-1]
    first = df_filtered.iloc[0]
    
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    with kpi1:
        st.metric(
            label="👥 Pengguna Global",
            value=format_number(latest['Pengguna Iphone di Dunia']),
            delta=f"+{format_number(latest['Pengguna Iphone di Dunia'] - first['Pengguna Iphone di Dunia'])}"
        )
    
    with kpi2:
        st.metric(
            label="📱 Penjualan Global",
            value=format_number(latest['Jumlah Penjualan Iphone di Dunia']),
            delta=f"{latest['YoY Penjualan Global (%)']:.1f}% YoY" if pd.notna(latest['YoY Penjualan Global (%)']) else None
        )
    
    with kpi3:
        st.metric(
            label="🇺🇸 Market Share AS",
            value=f"{latest['% Pengguna AS dari Global (Aktual)']:.1f}%",
            delta=f"{latest['% Pengguna AS dari Global (Aktual)'] - first['% Pengguna AS dari Global (Aktual)']:.1f}pp"
        )
    
    with kpi4:
        st.metric(
            label="📊 iOS Market Share",
            value=f"{latest['Persentase penguasaan pasar IOS']:.1f}%",
            delta=f"{latest['Persentase penguasaan pasar IOS'] - first['Persentase penguasaan pasar IOS']:.1f}pp"
        )
    
    with kpi5:
        st.metric(
            label="💰 Est. Revenue Global",
            value=f"${latest['Est. Revenue Global (Miliar USD)']:.0f}B",
            delta=f"{((latest['Est. Revenue Global (Miliar USD)'] - first['Est. Revenue Global (Miliar USD)']) / first['Est. Revenue Global (Miliar USD)'] * 100):.0f}%" if first['Est. Revenue Global (Miliar USD)'] > 0 else None
        )

st.markdown("---")

# --- ANALISIS BERDASARKAN MODE ---
if analisis_mode == "Ringkasan Eksekutif":
    
    # Chart 1: Dual-axis growth trend
    st.subheader("📈 Tren Pertumbuhan Ekosistem iPhone")
    
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=df_filtered['Tahun'],
        y=df_filtered['Pengguna Iphone di Dunia'] / 1_000_000,  # Convert to millions
        name='Pengguna Global (M)',
        mode='lines+markers',
        line=dict(color='#007AFF', width=3),
        yaxis='y1'
    ))
    
    fig1.add_trace(go.Scatter(
        x=df_filtered['Tahun'],
        y=df_filtered['Jumlah Penjualan Iphone di Dunia'] / 1_000_000,  # Convert to millions
        name='Penjualan Global (M)',
        mode='lines+markers',
        line=dict(color='#FF6B35', width=3, dash='dot'),
        yaxis='y2'
    ))
    
    fig1.update_layout(
        title="Pertumbuhan Pengguna vs Penjualan iPhone Global",
        xaxis_title="Tahun",
        yaxis=dict(title="Pengguna (Juta)", side="left"),
        yaxis2=dict(title="Penjualan (Juta)", overlaying="y", side="right"),
        hovermode='x unified',
        height=400
    )
    
    # Konfigurasi sumbu x untuk menampilkan semua tahun
    fig1 = configure_xaxis_all_years(fig1, df_filtered['Tahun'])
    
    st.plotly_chart(fig1, use_container_width=True)
    
    # Chart 2: Market share evolution
    st.subheader("🎯 Evolusi Pangsa Pasar OS Mobile")
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_filtered['Tahun'],
        y=df_filtered['Persentase penguasaan pasar IOS'],
        name='iOS',
        mode='lines+markers',
        fill='tonexty',
        line=dict(color='#007AFF')
    ))
    
    fig2.add_trace(go.Scatter(
        x=df_filtered['Tahun'],
        y=df_filtered['Persentase penguasaan pasar Android'],
        name='Android',
        mode='lines+markers',
        fill='tonexty',
        line=dict(color='#A4C639')
    ))
    
    fig2.update_layout(
        title="Kompetisi iOS vs Android dalam Pangsa Pasar",
        xaxis_title="Tahun",
        yaxis_title="Pangsa Pasar (%)",
        hovermode='x unified',
        height=400
    )
    
    # Konfigurasi sumbu x untuk menampilkan semua tahun
    fig2 = configure_xaxis_all_years(fig2, df_filtered['Tahun'])
    
    st.plotly_chart(fig2, use_container_width=True)

elif analisis_mode == "Analisis Mendalam":
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Penetration analysis
        st.subheader("📊 Analisis Penetrasi Pasar")
        
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=df_filtered['Tahun'],
            y=df_filtered['Penetrasi Global (%)'],
            name='Penetrasi Global',
            marker_color='#007AFF'
        ))
        fig3.add_trace(go.Bar(
            x=df_filtered['Tahun'],
            y=df_filtered['Penetrasi AS (%)'],
            name='Penetrasi AS',
            marker_color='#FF6B35'
        ))
        
        fig3.update_layout(
            title="Tingkat Penetrasi Pasar iPhone",
            xaxis_title="Tahun",
            yaxis_title="Penetrasi (%)",
            barmode='group',
            height=350
        )
        
        # Konfigurasi sumbu x untuk menampilkan semua tahun
        fig3 = configure_xaxis_all_years(fig3, df_filtered['Tahun'])
        
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        # YoY Growth comparison
        st.subheader("📈 Momentum Pertumbuhan YoY")
        
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=df_filtered['Tahun'],
            y=df_filtered['YoY Pengguna Global (%)'],
            name='Pertumbuhan Pengguna Global',
            mode='lines+markers',
            line=dict(color='#007AFF')
        ))
        fig4.add_trace(go.Scatter(
            x=df_filtered['Tahun'],
            y=df_filtered['YoY Penjualan Global (%)'],
            name='Pertumbuhan Penjualan Global',
            mode='lines+markers',
            line=dict(color='#FF6B35', dash='dot')
        ))
        
        fig4.update_layout(
            title="Volatilitas Pertumbuhan Tahunan",
            xaxis_title="Tahun",
            yaxis_title="Pertumbuhan YoY (%)",
            hovermode='x unified',
            height=350
        )
        
        # Konfigurasi sumbu x untuk menampilkan semua tahun
        fig4 = configure_xaxis_all_years(fig4, df_filtered['Tahun'])
        
        st.plotly_chart(fig4, use_container_width=True)
    
    # Revenue estimation
    st.subheader("💰 Estimasi Pendapatan iPhone")
    
    fig5 = go.Figure()
    fig5.add_trace(go.Bar(
        x=df_filtered['Tahun'],
        y=df_filtered['Est. Revenue Global (Miliar USD)'],
        name='Revenue Global',
        marker_color='#34C759'
    ))
    fig5.add_trace(go.Bar(
        x=df_filtered['Tahun'],
        y=df_filtered['Est. Revenue AS (Miliar USD)'],
        name='Revenue AS',
        marker_color='#FF9500'
    ))
    
    fig5.update_layout(
        title="Estimasi Pendapatan iPhone (Asumsi $700/unit)",
        xaxis_title="Tahun",
        yaxis_title="Revenue (Miliar USD)",
        barmode='group',
        height=400
    )
    
    # Konfigurasi sumbu x untuk menampilkan semua tahun
    fig5 = configure_xaxis_all_years(fig5, df_filtered['Tahun'])
    
    st.plotly_chart(fig5, use_container_width=True)

else:  # Perbandingan Segmen
    
    st.subheader("🌍 Analisis Segmentasi Geografis")
    
    # Geographic contribution over time
    fig6 = go.Figure()
    fig6.add_trace(go.Scatter(
        x=df_filtered['Tahun'],
        y=df_filtered['% Pengguna AS dari Global (Aktual)'],
        name='Kontribusi Pengguna AS (%)',
        mode='lines+markers',
        line=dict(color='#FF6B35', width=3)
    ))
    fig6.add_trace(go.Scatter(
        x=df_filtered['Tahun'],
        y=df_filtered['% Penjualan AS dari Global (Aktual)'],
        name='Kontribusi Penjualan AS (%)',
        mode='lines+markers',
        line=dict(color='#007AFF', width=3, dash='dot')
    ))
    
    fig6.update_layout(
        title="Tren Ketergantungan pada Pasar Amerika Serikat",
        xaxis_title="Tahun",
        yaxis_title="Kontribusi terhadap Global (%)",
        hovermode='x unified',
        height=400
    )
    
    # Konfigurasi sumbu x untuk menampilkan semua tahun
    fig6 = configure_xaxis_all_years(fig6, df_filtered['Tahun'])
    
    st.plotly_chart(fig6, use_container_width=True)
    
    # Comparative analysis table
    st.subheader("📋 Perbandingan Metrik Kunci: AS vs Global")
    
    comparison_data = []
    for _, row in df_filtered.iterrows():
        comparison_data.append({
            'Tahun': int(row['Tahun']),
            'Pengguna AS (M)': f"{row['Pengguna Iphone di USA']/1_000_000:.1f}",
            'Pengguna Global (B)': f"{row['Pengguna Iphone di Dunia']/1_000_000_000:.2f}",
            'Share AS (%)': f"{row['% Pengguna AS dari Global (Aktual)']:.1f}%",
            'Penjualan AS (M)': f"{row['Jumlah Penjualan Iphone di USA']/1_000_000:.1f}",
            'Penjualan Global (M)': f"{row['Jumlah Penjualan Iphone di Dunia']/1_000_000:.1f}",
            'Share Penjualan AS (%)': f"{row['% Penjualan AS dari Global (Aktual)']:.1f}%"
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True)

# --- INSIGHTS & REKOMENDASI ---
st.markdown("---")
st.subheader("🎯 Key Insights & Rekomendasi Strategis")

insights_col1, insights_col2 = st.columns(2)

with insights_col1:
    st.info("""
    📊 Temuan Utama:
    
    1. Diversifikasi Geografis Berhasil: Kontribusi AS terhadap total pengguna global menurun dari ~35% (2011) menjadi ~10% (2023)
    
    2. Pertumbuhan User Base Stabil: CAGR pengguna global ~25% menunjukkan adopsi konsisten
    
    3. Duopoli Mobile OS: iOS dan Android menguasai >99% pasar, mengeliminasi pemain lain
    """)

with insights_col2:
    st.warning("""
    ⚠ Area Perhatian:
    
    1. Volatilitas Penjualan: Fluktuasi penjualan tahunan menunjukkan dependensi pada siklus produk
    
    2. Penetrasi Pasar: Rasio penjualan/pengguna menunjukkan pola upgrade yang tidak konsisten
    
    3. Kompetisi Android: Market share Android tetap kuat di ~42-45%
    """)

# Data export
with st.expander("📥 Ekspor Data untuk Analisis Lanjutan"):
    st.markdown("Dataset yang telah diproses dengan metrik tambahan:")
    st.dataframe(df_filtered)
    
    # Download button untuk CSV
    csv = df_filtered.to_csv(index=False)
    st.download_button(
        label="⬇ Download Data CSV",
        data=csv,
        file_name=f'iphone_analysis_{tahun_dipilih[0]}_{tahun_dipilih[1]}.csv',
        mime='text/csv'
    )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
<small>📱 iPhone Analytics Dashboard | Data Analysis by Data Analyst Team | 
Sumber: Dataset iPhone Historical Data</small>
</div>
""", unsafe_allow_html=True)
