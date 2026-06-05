import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
import base64
import os
import pickle
from PIL import Image

# --- 💾 データの永続保存（ローカルファイル管理）ロジック ---
DB_FILE = "vsm_stored_data.pkl"

def load_persistent_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "rb") as f:
                data = pickle.load(f)
                if "samples" not in data:
                    if any("clean_x" in v or "H_plot" in v for v in data.values() if isinstance(v, dict)):
                        cleaned_samples = {}
                        for k, v in data.items():
                            if isinstance(v, dict) and ("clean_x" in v or "H_plot" in v):
                                if "clean_x" in v:
                                    cleaned_samples[k] = v
                                else:
                                    cx = [x for x in v["H_plot"] if x is not None]
                                    cy = [y for y in v["M_plot"] if y is not None]
                                    info = v.get("Info", {})
                                    if "ΔH [T]" not in info and "ΔH(+)" in info:
                                        info["ΔH [T]"] = info["ΔH(+)"]
                                    cleaned_samples[k] = {
                                        "clean_x": cx, "clean_y": cy,
                                        "color": v.get("color", "#1f77b4"),
                                        "Info": info, "favorite": v.get("favorite", False)
                                    }
                        data = {"samples": cleaned_samples, "collections": {}}
                    else:
                        data = {"samples": {}, "collections": {}}
                return data
        except:
            return {"samples": {}, "collections": {}}
    return {"samples": {}, "collections": {}}

def save_persistent_data(data):
    with open(DB_FILE, "wb") as f:
        pickle.dump(data, f)

# ==========================================
# ⚙️ アプリケーション設定 & アイコン読み込み
# ==========================================
# 実行中のスクリプト（app.py）と同じディレクトリの絶対パスを取得
current_dir = os.path.dirname(os.path.abspath(__file__))
# 同じディレクトリ内にあるアイコン画像のパスを作成
icon_path = os.path.join(current_dir, "vsm_icon.jpg")

try:
    # 1. カスタムヘッダーUI用のBase64エンコード
    with open(icon_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    img_html = f'<img src="data:image/jpeg;base64,{encoded_string}" height="45" style="margin-right:12px; border-radius:8px; vertical-align:middle; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">'
    
    # 2. ページタブ用のPIL Image読み込み
    page_icon = Image.open(icon_path)

except FileNotFoundError:
    # 画像が見つからなかった場合のフォールバック（絵文字）
    img_html = '<span style="font-size:35px; margin-right:12px; vertical-align:middle;">🧲</span>'
    page_icon = "🧲"

# --- ページ設定 ---
st.set_page_config(
    page_title="VSM Plotter", 
    page_icon=page_icon, 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 💅 カスタムCSS (ピンクベースUI ＆ インスタ風カードスタイル) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'M PLUS Rounded 1c', sans-serif !important; }
    
    .stApp { background-color: #FFFDFD; }
    
    header[data-testid="stHeader"] { background: transparent !important; }
    
    .custom-header {
        display: flex; justify-content: flex-start; align-items: center;
        padding: 15px 40px 15px 80px; 
        background-color: #FFFFFF; border-bottom: 2px solid #FFE4E8;
        position: sticky; top: 0; z-index: 999; margin-top: -60px; margin-bottom: 25px;
        margin-left: -4rem; margin-right: -4rem; box-shadow: 0 2px 10px rgba(238, 79, 111, 0.05);
    }
    .header-logo { display: flex; align-items: center; font-size: 26px; font-weight: 700; color: #EE4F6F; letter-spacing: 1.5px; }
    
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 2px solid #FFE4E8; padding-top: 10px; }
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div { border-radius: 8px !important; }
    div[data-baseweb="input"] > div:focus-within, div[data-baseweb="select"] > div:focus-within { border-color: #EE4F6F !important; }
    [data-testid="stAlert"] { background-color: #FFF5F7 !important; border: 1px solid #FFB6C1 !important; color: #EE4F6F !important; border-radius: 8px !important; }
    [data-testid="stAlert"] svg { fill: #EE4F6F !important; }
    [data-testid="stFileUploadDropzone"] { background-color: #FFFFFF !important; border: 2px dashed #FFB6C1 !important; border-radius: 12px !important; padding: 15px !important; min-height: 60px !important; }
    [data-testid="stFileUploadDropzone"]:hover { background-color: #FFF5F7 !important; border-color: #EE4F6F !important; }
    [data-testid="stFileUploadDropzone"] svg { color: #EE4F6F !important; width: 25px !important; }
    
    .stButton > button { background-color: #FFFFFF !important; color: #EE4F6F !important; border: 2px solid #FFB6C1 !important; border-radius: 20px !important; font-weight: bold !important; transition: all 0.2s; }
    .stButton > button:hover { background-color: #FFF5F7 !important; border-color: #EE4F6F !important; }
    .stButton > button[kind="primary"] { background-color: #EE4F6F !important; color: white !important; border: none !important; box-shadow: 0 4px 10px rgba(238, 79, 111, 0.2) !important; }
    .stButton > button[kind="primary"]:hover { background-color: #D8425F !important; box-shadow: 0 6px 15px rgba(238, 79, 111, 0.3) !important; transform: translateY(-2px); }
    
    textarea { font-family: monospace !important; font-size: 13px !important; background-color: #FAFAFA !important; }
    .streamlit-expanderHeader { background-color: #FFF5F7; border-radius: 8px; color: #EE4F6F !important; font-weight: bold; padding: 6px 12px !important; }
    .top-bar-container { background-color: #FFFFFF; padding: 10px 15px; border-radius: 12px; border: 1px solid #FFE4E8; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(238, 79, 111, 0.05); }
    
    .instagram-card {
        background-color: #FFFFFF;
        border: 1px solid #FFE4E8;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(238, 79, 111, 0.03);
        transition: all 0.3s ease;
    }
    .instagram-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(238, 79, 111, 0.08);
        border-color: #FFB6C1;
    }
    .card-title { font-size: 18px; font-weight: 700; color: #EE4F6F; margin-bottom: 8px; display: flex; align-items: center; gap: 6px; }
    .card-meta { font-size: 13px; color: #888888; margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)

st.markdown(f'<div class="custom-header"><div class="header-logo">{img_html}VSM</div></div>', unsafe_allow_html=True)

if "db" not in st.session_state:
    st.session_state.db = load_persistent_data()

if "load_collection" not in st.session_state:
    st.session_state.load_collection = None

distinct_colors = ['#000000', '#D62728', '#1F77B4', '#2CA02C', '#FF7F0E', '#9467BD']

# --- 解析ロジック ---
def split_multi_cycle_segments(H, M):
    if len(H) < 10: return {}
    H_smooth = np.convolve(H, np.ones(5)/5, mode='same')
    maxima = np.where((H_smooth[1:-1] > H_smooth[:-2]) & (H_smooth[1:-1] > H_smooth[2:]))[0] + 1
    minima = np.where((H_smooth[1:-1] < H_smooth[:-2]) & (H_smooth[1:-1] < H_smooth[2:]))[0] + 1
    extrema = sorted(list(maxima) + list(minima))
    extrema = [0] + extrema + [len(H)]
    
    segments = []
    for idx in range(len(extrema)-1):
        start_p, end_p = extrema[idx], extrema[idx+1]
        if end_p - start_p < 10: continue
        h_seg, m_seg = H[start_p:end_p], M[start_p:end_p]
        direction = "Forward" if h_seg[-1] < h_seg[0] else "Backward"
        segments.append({"H": h_seg, "M": m_seg, "dir": direction})
        
    fwd_count, bwd_count = 1, 1
    labeled_segments = {}
    for seg in segments:
        if seg["dir"] == "Forward":
            label = f"{fwd_count}周期目 往路(Forward)"
            fwd_count += 1
        else:
            label = f"{bwd_count}周期目 復路(Backward)"
            bwd_count += 1
        labeled_segments[label] = seg
    return labeled_segments

def calc_diamagnetic_slope(H_data, M_data, H_min, H_max):
    H = np.array(H_data)
    M = np.array(M_data)
    pos_mask = (H >= H_min) & (H <= H_max)
    neg_mask = (H >= -H_max) & (H <= -H_min)
    slope_pos, slope_neg = 0, 0
    if np.sum(pos_mask) > 1: slope_pos, _ = np.polyfit(H[pos_mask], M[pos_mask], 1)
    if np.sum(neg_mask) > 1: slope_neg, _ = np.polyfit(H[neg_mask], M[neg_mask], 1)
    if np.sum(pos_mask) > 1 and np.sum(neg_mask) > 1: return (slope_pos + slope_neg) / 2
    elif np.sum(pos_mask) > 1: return slope_pos
    elif np.sum(neg_mask) > 1: return slope_neg
    return 0.0

def calc_m_offset(H_data, M_data, H_min, H_max):
    H = np.array(H_data)
    M = np.array(M_data)
    pos_mask = (H >= H_min) & (H <= H_max)
    neg_mask = (H >= -H_max) & (H <= -H_min)
    if np.sum(pos_mask) > 1 and np.sum(neg_mask) > 1:
        return (np.mean(M[pos_mask]) + np.mean(M[neg_mask])) / 2.0
    return 0.0

def safe_interp(x_eval, x_data, y_data):
    sort_idx = np.argsort(x_data)
    return np.interp(x_eval, x_data[sort_idx], y_data[sort_idx], left=np.nan, right=np.nan)

def optimize_H_shift_symmetric_split(H_fwd, M_fwd, H_bwd, M_bwd, H_min_fit, H_max_fit):
    if len(H_fwd) == 0 or len(H_bwd) == 0: return 0.0
    trial_shifts = np.linspace(-0.1, 0.1, 401)
    min_mse, best_s = float('inf'), 0.0
    eval_H_pos = np.linspace(H_min_fit, H_max_fit, 100)
    eval_H_neg = np.linspace(-H_max_fit, -H_min_fit, 100)
    for s in trial_shifts:
        M_f_pos = safe_interp(eval_H_pos, H_fwd - s, M_fwd)
        M_b_pos = safe_interp(eval_H_pos, H_bwd + s, M_bwd)
        M_f_neg = safe_interp(eval_H_neg, H_fwd - s, M_fwd)
        M_b_neg = safe_interp(eval_H_neg, H_bwd + s, M_bwd)
        valid_pos = ~np.isnan(M_f_pos) & ~np.isnan(M_b_pos)
        valid_neg = ~np.isnan(M_f_neg) & ~np.isnan(M_b_neg)
        mse_pos, mse_neg, count = 0, 0, 0
        if np.sum(valid_pos) > 10: mse_pos = np.sum((M_f_pos[valid_pos] - M_b_pos[valid_pos])**2); count += np.sum(valid_pos)
        if np.sum(valid_neg) > 10: mse_neg = np.sum((M_f_neg[valid_neg] - M_b_neg[valid_neg])**2); count += np.sum(valid_neg)
        if count > 20:
            mse = (mse_pos + mse_neg) / count
            if mse < min_mse: min_mse = mse; best_s = s
    return best_s

def create_vsm_plot(tick_s, auto_x, x_min, x_max, x_dtick, auto_y, y_min, y_max, y_dtick):
    fig = go.Figure()
    title_fixed_size = 20
    
    # 【エラー対策】目盛り間隔(dtick)が0やマイナスになるとPlotlyがクラッシュするため安全な値に上書き
    safe_x_dtick = x_dtick if x_dtick > 0 else 0.1
    safe_y_dtick = y_dtick if y_dtick > 0 else 100.0

    layout_args = dict(
        height=650, 
        template="simple_white", hovermode="closest",
        
        legend=dict(
            orientation="v", yanchor="top", y=1.0, xanchor="left", x=1.02,
            font=dict(size=12, color="black"), bgcolor="rgba(255,255,255,0)"
        ),
        
        xaxis=dict(
            # 最新のPlotly仕様に合わせて title の書き方を変更
            title=dict(text="μ₀<i>H</i> [T]", font=dict(size=title_fixed_size, color='black')),
            automargin=False,
            tickfont=dict(size=tick_s, color='black'), 
            mirror='allticks', ticks='inside', tickcolor='black', showline=True, linecolor='black', 
            linewidth=2.5, tickwidth=2.5, ticklen=8, color='black', 
            range=[x_min, x_max] if not auto_x else None, 
            tickmode='linear' if not auto_x else 'auto', 
            tick0=0 if not auto_x else None, 
            dtick=safe_x_dtick if not auto_x else None,
            zeroline=True, zerolinewidth=1.0, zerolinecolor='black'
        ),
        yaxis=dict(
            # 最新のPlotly仕様に合わせて title の書き方を変更
            title=dict(text="<i>M</i> [kA/m]", font=dict(size=title_fixed_size, color='black')),
            automargin=False,
            tickfont=dict(size=tick_s, color='black'), 
            mirror='allticks', ticks='inside', tickcolor='black', showline=True, linecolor='black', 
            linewidth=2.5, tickwidth=2.5, ticklen=8, color='black', 
            range=[y_min, y_max] if not auto_y else None, 
            tickmode='linear' if not auto_y else 'auto', 
            tick0=0 if not auto_y else None, 
            dtick=safe_y_dtick if not auto_y else None,
            zeroline=True, zerolinewidth=1.0, zerolinecolor='black'
        ),
        
        shapes=[
            dict(type="line", x0=-10, x1=10, y0=0, y1=0, line=dict(color="black", width=1.0)),
            dict(type="line", x0=0, x1=0, y0=-10000, y1=10000, line=dict(color="black", width=1.0))
        ],
        margin=dict(l=80, r=200, t=50, b=80)
    )
    fig.update_layout(**layout_args)
    return fig
def parse_trim_ranges(range_str):
    trim_list = []
    if range_str:
        clean_ranges = range_str.replace('〜', '~').replace('，', ',').split(',')
        for part in clean_ranges:
            if '~' in part:
                try:
                    vals = [float(x.strip()) for x in part.split('~')]
                    trim_list.append((min(vals), max(vals)))
                except: pass
    return trim_list

# ==========================================
# ⚙️ 左サイドバー：すべての設定項目
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ 解析パラメータ")
    
    with st.expander(":material/straighten: 試料パラメータ", expanded=True):
        col1, col2 = st.columns(2)
        with col1: Area = st.number_input("面積(cm²)", value=0.902, step=0.01)
        with col2: Thick = st.number_input("膜厚(nm)", value=24.0, step=0.1)
        Vol = Area * Thick * 1e-7
        st.caption(f"体積: {Vol:.3e} cm³")
        
    with st.expander(":material/auto_fix_high: 補正・フィット", expanded=True):
        col_s, col_f = st.columns(2)
        with col_s: start = st.number_input("Start(T)", value=1.3, step=0.1)
        with col_f: finish = st.number_input("Finish(T)", value=1.6, step=0.1)
        do_shift_correction = st.checkbox("H軸ズレ自動補正(左右対称)", value=True)
        do_m_shift_correction = st.checkbox("M軸ズレ自動補正(上下対称)", value=True) 
        do_bg_correction = st.checkbox("反磁性成分を引く", value=True)
        N_factor = st.number_input("反磁界係数 N", value=1.0, step=0.1)
        do_demag_correction = st.checkbox("反磁界補正", value=False)
        
    with st.expander("✂️ プロセスごとの領域カット", expanded=True):
        st.caption("カンマ区切りで複数指定可能\n例: `0.08~0.5, 1.2~1.5`")
        do_trimming = st.checkbox("カット処理を有効にする", value=True)
        
        st.markdown("**1周期目**")
        trim_f1 = st.text_input("往路(Forward) の除外範囲", value="")
        trim_b1 = st.text_input("復路(Backward) の除外範囲", value="")
        st.markdown("**2周期目**")
        trim_f2 = st.text_input("往路(Forward) の除外範囲(2回目)", value="")
        trim_b2 = st.text_input("復路(Backward) の除外範囲(2回目)", value="")
        
        trim_dict = {
            "1周期目 往路(Forward)": parse_trim_ranges(trim_f1),
            "1周期目 復路(Backward)": parse_trim_ranges(trim_b1),
            "2周期目 往路(Forward)": parse_trim_ranges(trim_f2),
            "2周期目 復路(Backward)": parse_trim_ranges(trim_b2)
        }

    with st.expander("🔄 全体表示オンオフ", expanded=False):
        use_f1 = st.checkbox("1周期目 往路", value=True)
        use_b1 = st.checkbox("1周期目 復路", value=True)
        use_f2 = st.checkbox("2周期目 往路", value=True)
        use_b2 = st.checkbox("2周期目 復路", value=True)
        process_switches = {
            "1周期目 往路(Forward)": use_f1, "1周期目 復路(Backward)": use_b1,
            "2周期目 往路(Forward)": use_f2, "2周期目 復路(Backward)": use_b2
        }

    with st.expander(":material/palette: 描画範囲", expanded=False):
        tick_size = st.number_input("目盛りサイズ", value=15, step=1)
        st.write("X軸 [T]")
        auto_x = st.checkbox("X軸自動", value=False)
        cx1, cx2 = st.columns(2)
        with cx1: x_min = st.number_input("X min", value=-0.25, step=0.05, disabled=auto_x)
        with cx2: x_max = st.number_input("X max", value=0.25, step=0.05, disabled=auto_x)
        x_dtick = st.number_input("X 間隔", value=0.1, step=0.05, disabled=auto_x)
        
        st.write("Y軸 [kA/m]")
        auto_y = st.checkbox("Y軸自動", value=False)
        cy1, cy2 = st.columns(2)
        with cy1: y_min = st.number_input("Y min", value=-500.0, step=100.0, disabled=auto_y)
        with cy2: y_max = st.number_input("Y max", value=500.0, step=100.0, disabled=auto_y)
        y_dtick = st.number_input("Y 間隔", value=200.0, step=100.0, disabled=auto_y)

# ==========================================
# メインエリア: タブUI
# ==========================================
tab1, tab2, tab3 = st.tabs(["📂 データの読み込みと補正", "📈 保存データの重ね合わせ", "🎬 保存済みコレクション"])

if st.session_state.load_collection is not None:
    saved_set = st.session_state.db["collections"][st.session_state.load_collection]
    default_select = saved_set["samples"]
else:
    default_select = list(st.session_state.db["samples"].keys())

with tab1:
    uploaded_files = st.file_uploader(".VSMファイルをドロップ", type=["vsm"], accept_multiple_files=True, label_visibility="collapsed")
        
    if uploaded_files:
        fig_preview = create_vsm_plot(tick_size, auto_x, x_min, x_max, x_dtick, auto_y, y_min, y_max, y_dtick)
        current_batch_results = []
        current_batch_data = {} 
        
        for i, file in enumerate(uploaded_files):
            content = file.getvalue()
            try:
                df_raw = pd.read_csv(io.BytesIO(content), skiprows=40, usecols=[1,2,3], encoding='shift-jis')
            except: continue
            
            H_full = df_raw.iloc[:, 0].values / 1e4
            M_full = (df_raw.iloc[:, 1].values / Vol)
            ang_full = df_raw.iloc[:, 2].values
            df_file = pd.DataFrame({'H(T)': H_full, 'M(kA/m)': M_full, 'ang': ang_full})
            
            for ang_val, group in df_file.groupby('ang'):
                name_label = f"{file.name} ({ang_val}°)"
                H_raw_group = group['H(T)'].values
                M_raw_group = group['M(kA/m)'].values
                
                peak_idx = np.argmax(H_raw_group)
                valley_idx = np.argmin(H_raw_group)
                first_turn = min(peak_idx, valley_idx)
                if 0 < first_turn < len(H_raw_group) // 2:
                    H_raw_group = H_raw_group[first_turn:]
                    M_raw_group = M_raw_group[first_turn:]
                
                segments = split_multi_cycle_segments(H_raw_group, M_raw_group)
                H_fwd_fit, M_fwd_fit, H_bwd_fit, M_bwd_fit = [], [], [], []
                
                for label, seg in segments.items():
                    if not process_switches.get(label, True): continue
                    h, m = seg["H"].copy(), seg["M"].copy()
                    
                    if do_trimming:
                        valid_h, valid_m = [], []
                        for val_h, val_m in zip(h, m):
                            is_trimmed = False
                            for t_min, t_max in trim_dict.get(label, []):
                                if t_min <= val_h <= t_max:
                                    is_trimmed = True
                                    break
                            if not is_trimmed:
                                valid_h.append(val_h); valid_m.append(val_m)
                        h, m = np.array(valid_h), np.array(valid_m)
                        
                    if len(h) == 0: continue
                    if "Forward" in label:
                        H_fwd_fit.extend(h); M_fwd_fit.extend(m)
                    else:
                        H_bwd_fit.extend(h); M_bwd_fit.extend(m)
                
                if not H_fwd_fit and not H_bwd_fit: continue
                H_fwd_fit = np.array(H_fwd_fit) if H_fwd_fit else np.array([])
                M_fwd_fit = np.array(M_fwd_fit) if M_fwd_fit else np.array([])
                H_bwd_fit = np.array(H_bwd_fit) if H_bwd_fit else np.array([])
                M_bwd_fit = np.array(M_bwd_fit) if M_bwd_fit else np.array([])
                
                s_shift, slope, m_offset = 0.0, 0.0, 0.0
                
                if do_shift_correction and len(H_fwd_fit) > 10 and len(H_bwd_fit) > 10:
                    s_shift = optimize_H_shift_symmetric_split(H_fwd_fit, M_fwd_fit, H_bwd_fit, M_bwd_fit, start, finish)
                
                H_shifted_all, M_all = [], []
                for label, seg in segments.items():
                    if not process_switches.get(label, True): continue
                    h = seg["H"].copy()
                    h = h - s_shift if "Forward" in label else h + s_shift
                    H_shifted_all.extend(h); M_all.extend(seg["M"])
                
                if do_bg_correction and len(H_shifted_all) > 10:
                    slope = calc_diamagnetic_slope(H_shifted_all, M_all, start, finish)
                    
                if do_m_shift_correction and len(H_shifted_all) > 10:
                    m_offset = calc_m_offset(H_shifted_all, M_all, start, finish)
                
                plot_x, plot_y = [], []
                clean_x, clean_y = [], []
                
                for label, seg in segments.items():
                    if not process_switches.get(label, True): continue
                    h_raw, m_raw = seg["H"], seg["M"]
                    
                    for hr, mr in zip(h_raw, m_raw):
                        is_trimmed = False
                        if do_trimming:
                            for t_min, t_max in trim_dict.get(label, []):
                                if t_min <= hr <= t_max:
                                    is_trimmed = True
                                    break
                        
                        h_shift = hr - s_shift if "Forward" in label else hr + s_shift
                        
                        m_vert_corrected = mr - m_offset
                        m_bg = m_vert_corrected - (h_shift * slope) if do_bg_correction else m_vert_corrected
                        h_final = h_shift - (N_factor * m_bg) if do_demag_correction else h_shift
                        
                        if is_trimmed:
                            plot_x.append(None); plot_y.append(None)
                        else:
                            plot_x.append(h_final); plot_y.append(m_bg)
                            clean_x.append(h_final); clean_y.append(m_bg)
                
                clean_x_arr = np.array(clean_x)
                clean_y_arr = np.array(clean_y)
                pos_mask = (clean_x_arr >= start) & (clean_x_arr <= finish)
                neg_mask = (clean_x_arr >= -finish) & (clean_x_arr <= -start)
                high_field_mask = pos_mask | neg_mask
                if np.sum(high_field_mask) > 0: Ms = float(np.mean(np.abs(clean_y_arr[high_field_mask])))
                else: Ms = float(np.max(np.abs(clean_y_arr))) if len(clean_y_arr)>0 else 0.0
                
                line_color = distinct_colors[i % len(distinct_colors)]
                fig_preview.add_trace(go.Scatter(x=plot_x, y=plot_y, name=name_label, mode='lines+markers', line=dict(width=2.5, color=line_color), connectgaps=False, marker=dict(size=4, color=line_color)))
                
                current_batch_results.append({"Sample": name_label, "Ms [kA/m]": Ms, "ΔH [T]": s_shift, "ΔM [kA/m]": m_offset, "Slope": slope})
                current_batch_data[name_label] = {"plot_x": plot_x, "plot_y": plot_y, "clean_x": clean_x, "clean_y": clean_y, "color": line_color, "Info": {"Ms [kA/m]": Ms, "ΔH [T]": s_shift, "ΔM [kA/m]": m_offset, "Slope": slope}, "favorite": False}

        st.plotly_chart(fig_preview, use_container_width=True)
        
        st.markdown("### 📊 解析結果サマリー")
        if current_batch_results:
            df_batch = pd.DataFrame(current_batch_results)
            st.dataframe(df_batch[["Sample", "Ms [kA/m]", "ΔH [T]", "ΔM [kA/m]", "Slope"]].style.format({"Ms [kA/m]": "{:.2f}", "ΔH [T]": "{:.5f}", "ΔM [kA/m]": "{:.2f}", "Slope": "{:.4e}"}), use_container_width=True)
            st.write("")
            if st.button("💖 いいね！ (データをストックして保存)", type="primary", use_container_width=True):
                for k, v in current_batch_data.items():
                    st.session_state.db["samples"][k] = v
                save_persistent_data(st.session_state.db)
                st.success("✅ キープしました！隣のタブで一括重ね描きが可能です。")

with tab2:
    if not st.session_state.db["samples"]:
        st.warning("ストックされたデータがありません。「📂 データの読み込みと補正」タブで『💖 いいね！』を押してください。")
    else:
        st.markdown('<div class="top-bar-container">', unsafe_allow_html=True)
        col_filter, col_sel = st.columns([1, 4], gap="medium")
        show_fav_only = col_filter.checkbox("💖 お気に入りのみ表示", value=False)
        
        available_options = list(st.session_state.db["samples"].keys())
        if show_fav_only:
            available_options = [n for n in available_options if st.session_state.db["samples"][n].get("favorite", False)]
        
        valid_defaults = [d for d in default_select if d in available_options]
        selected_samples = col_sel.multiselect("重ね描き・出力するデータを選択してください", options=available_options, default=valid_defaults, label_visibility="collapsed")
        
        col_fav, col_del, _ = st.columns([1.5, 1.5, 3])
        if col_fav.button("💖 選択データをお気に入り登録 / 解除"):
            for s in selected_samples:
                st.session_state.db["samples"][s]["favorite"] = not st.session_state.db["samples"][s].get("favorite", False)
            save_persistent_data(st.session_state.db)
            st.rerun()
        if col_del.button("🗑️ 選択データを削除"):
            for s in selected_samples:
                if s in st.session_state.db["samples"]: del st.session_state.db["samples"][s]
            save_persistent_data(st.session_state.db)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        if selected_samples:
            fig_compare = create_vsm_plot(tick_size, auto_x, x_min, x_max, x_dtick, auto_y, y_min, y_max, y_dtick)
            compare_results = []
            export_dfs = [] 
            
            for idx, sample in enumerate(selected_samples):
                data = st.session_state.db["samples"][sample]
                display_name = f"💖 {sample}" if data.get("favorite", False) else sample
                auto_color = distinct_colors[idx % len(distinct_colors)]
                
                fig_compare.add_trace(go.Scatter(x=data.get("plot_x", data.get("clean_x")), y=data.get("plot_y", data.get("clean_y")), name=display_name, mode='lines+markers', line=dict(width=2.5, color=auto_color), connectgaps=False, marker=dict(size=4, color=auto_color)))
                
                info = data["Info"].copy()
                info["Sample"] = display_name
                compare_results.append(info)
                
                temp_df = pd.DataFrame({"Sample": display_name, "H_corrected [T]": data["clean_x"], "M_corrected [kA/m]": data["clean_y"]})
                export_dfs.append(temp_df)

            st.plotly_chart(fig_compare, use_container_width=True)
            
            st.write("")
            with st.expander("🎬 この重ね合わせグラフをコレクション（保存済み）に保存する", expanded=False):
                col_cname, col_cbtn = st.columns([3, 1])
                c_name = col_cname.text_input("コレクション名（例：Co組成依存性、角度比較など）", value="")
                if col_cbtn.button("📥 コレクションに保存", type="primary", use_container_width=True):
                    if c_name.strip():
                        st.session_state.db["collections"][c_name.strip()] = {
                            "samples": selected_samples,
                            "count": len(selected_samples)
                        }
                        save_persistent_data(st.session_state.db)
                        st.success(f"📌 コレクション『{c_name}』に保存しました！『🎬 保存済みコレクション』タブからいつでも見られます。")
                    else:
                        st.error("コレクション名を入力してください。")
            
            st.write("")
            st.markdown("### 📋 サマリー ＆ 出力")
            if compare_results:
                df_comp = pd.DataFrame(compare_results)
                display_cols = ["Sample", "Ms [kA/m]"]
                if "ΔH [T]" in df_comp.columns: display_cols.append("ΔH [T]")
                if "ΔM [kA/m]" in df_comp.columns: display_cols.append("ΔM [kA/m]")
                if "Slope" in df_comp.columns: display_cols.append("Slope")
                
                st.dataframe(df_comp[display_cols].style.format({"Ms [kA/m]": "{:.2f}", "ΔH [T]": "{:.5f}", "ΔM [kA/m]": "{:.2f}", "Slope": "{:.4e}"}), use_container_width=True)
                
                col_bottom_left, col_bottom_right = st.columns([3, 1])
                with col_bottom_left:
                    tsv_text = df_comp[display_cols].to_csv(sep="\t", index=False)
                    st.text_area("Origin / Excel 直貼り用（右上の📄アイコンでコピー）", value=tsv_text, height=100)
                with col_bottom_right:
                    if export_dfs:
                        st.write("")
                        csv = pd.concat(export_dfs, ignore_index=True).to_csv(index=False).encode('utf-8-sig')
                        st.download_button(label="📥 プロット用CSV 一括ダウンロード", data=csv, file_name="VSM_overlaid_data.csv", mime="text/csv", type="primary", use_container_width=True)

with tab3:
    if not st.session_state.db.get("collections"):
        st.info("📌 保存されたコレクションがありません。隣の『📈 保存データの重ね合わせ』タブから、お気に入りのグラフを名前を付けて保存してください。")
    else:
        st.markdown("### 🗂️ 保存済みアルバム一覧")
        st.caption("Instagramの保存済みコレクションのように、過去に作成したグラフの組み合わせをいつでも復元できます。")
        
        cols = st.columns(3)
        for idx, (c_name, c_data) in enumerate(st.session_state.db["collections"].items()):
            col_target = cols[idx % 3]
            
            with col_target:
                st.markdown(f"""
                <div class="instagram-card">
                    <div class="card-title">📁 {c_name}</div>
                    <div class="card-meta">📊 含まれるデータ数: {c_data['count']} 個</div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("📝 含まれるサンプル一覧を確認", expanded=False):
                    for s in c_data["samples"]:
                        st.caption(f"• {s}")
                
                cb1, cb2 = st.columns(2)
                if cb1.button("🔄 グラフを復元する", key=f"restore_{c_name}", type="primary", use_container_width=True):
                    st.session_state.load_collection = c_name
                    st.success(f"📊 『{c_name}』をロードしました！隣の『📈 保存データの重ね合わせ』タブを開いてください。")
                    st.rerun()
                    
                if cb2.button("🗑️ 削除", key=f"del_col_{c_name}", use_container_width=True):
                    del st.session_state.db["collections"][c_name]
                    if st.session_state.load_collection == c_name:
                        st.session_state.load_collection = None
                    save_persistent_data(st.session_state.db)
                    st.rerun()