import plotly.express as px
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
import requests
from streamlit_lottie import st_lottie


access_token = 'pk.eyJ1IjoiYWJkdWxrZXJpbW5lc2UiLCJhIjoiY2s5aThsZWlnMDExcjNkcWFmaWUxcmh3YyJ9.s-4VLvmoPQFPXdu9Mcd6pA'
px.set_mapbox_access_token(access_token)

def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


lottie_help = load_lottie_url("https://lottie.host/24732ed7-f894-45a7-b8e8-417ddea4eadf/DlwqEbFfqF.json")


# IMPORT DATA
file_path = r"assets/dgv_CariDurumListesiFH.xlsx"

movement_table = pd.read_excel(file_path, sheet_name='MOVEMENT_TABLE')
customer_table = pd.read_excel(file_path, sheet_name='CUSTOMER_TABLE')

movement_table.columns = movement_table.columns.str.replace(" ","_")


# DF TO GDF
gdf_customer_table = gpd.GeoDataFrame(customer_table,geometry=gpd.points_from_xy(customer_table.Boylam, customer_table.Enlem), crs="EPSG:4326")


gdf_customer_table_join = gdf_customer_table.merge(movement_table, how="left", on="Cari_ID")

st.set_page_config(
    page_title="İnsani Yardım",
    page_icon=":bar_chart:",
    layout="wide"
)

# Page Title and Animation
upper_left_col, upper_middle_col, upper_right_col = st.columns(3)

with upper_left_col:
    st.title("İnsani Yardım")

with upper_middle_col:
    st_lottie(lottie_help, height=250)

with upper_right_col:
    st.write(" ")


# ---- SIDEBAR ----
st.sidebar.header("Filtreleme Yapınız:")
evrak = st.sidebar.multiselect(
    "Evrak Tipi Seçiniz:",
    options=gdf_customer_table_join["Evrak_Tipi"].unique(),
    default=gdf_customer_table_join["Evrak_Tipi"].unique()
)

firma = st.sidebar.multiselect(
    "Firma Seçiniz:",
    options=movement_table["Firma"].unique(),
    default=movement_table["Firma"].unique(),
)

birim = st.sidebar.multiselect(
    "Birim Seçiniz:",
    options=movement_table["Birim"].unique(),
    default=movement_table["Birim"].unique()
)

gdf_customer_table_join_selection = gdf_customer_table_join.query(
    "Evrak_Tipi == @evrak"
)

movement_table_selection = movement_table.query(
    "Firma == @firma & Birim == @birim & Evrak_Tipi == @evrak"
)

# Check if the dataframe is empty:
if movement_table_selection.empty:
    st.warning("Mevcut filtre ayarlarına göre veri mevcut değil!")
    st.stop() # This will halt the app from further execution.

if gdf_customer_table_join_selection.empty:
    st.warning("Mevcut filtre ayarlarına göre veri mevcut değil!")
    st.stop() # This will halt the app from further execution.


# ---- MAINPAGE ----

# Indicators
toplam_yardim_alan_kisi = int(gdf_customer_table_join_selection['Cari_Tanim_x'].nunique())
toplam_yardim_yapan_firma = int(gdf_customer_table_join_selection['Firma'].nunique())
toplam_yardim_yapan_evrak = int(gdf_customer_table_join_selection['Evrak_Tipi'].nunique())

left_indicator, middle_indicator, right_indicator = st.columns(3)

with left_indicator:
    st.subheader("Toplam Yardım Alan Kişi Sayısı:")
    st.subheader(f"  {toplam_yardim_alan_kisi}")

with middle_indicator:
    st.subheader("Toplam Yardım Yapan Firma Sayısı:")
    st.subheader(f"  {toplam_yardim_yapan_firma}")

with right_indicator:
    st.subheader("Toplam Yardım Yapan Evrak Tipi Sayısı:")
    st.subheader(f"  {toplam_yardim_yapan_evrak}")

st.markdown("""---""")


# MAP
fig_map = px.scatter_mapbox(gdf_customer_table_join_selection, lat="Enlem", lon="Boylam",size="Çıkış",size_max=50,
            color=gdf_customer_table_join_selection['Evrak_Tipi'], color_continuous_scale=px.colors.cyclical.IceFire,
            hover_name="Cari_Tanim_x",zoom=12)
fig_map.update_layout(mapbox_style="carto-positron", mapbox_accesstoken=access_token)
        # fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},  # remove the white gutter between the frame and map
                          # hover appearance
                          hoverlabel=dict(
                              bgcolor="black",  # white background
                              font_size=16,  # label font size
                              font_family="Inter")  # label font
                          )
map_col = st.columns(1)[0]

with map_col:
    map_col.plotly_chart(fig_map, use_container_width=True)

# Charts

movement_table_pie_firma = movement_table_selection.groupby("Firma").agg({"Cari_ID":"count", "Stok":"count", "Evrak_Tipi":"count"}).rename(columns={"Cari_ID":"KISI_SAYISI","Stok":"STOK_SAYISI","Evrak Tipi":"EVRAK_SAYISI"}).reset_index()
fig_left_graph = go.Figure(data=[go.Pie(hole=0.3, labels=movement_table_pie_firma["Firma"],
                                                values=movement_table_pie_firma["KISI_SAYISI"])])
fig_left_graph.update_traces(hoverinfo='label+percent', textinfo='value', textfont_size=8,
                             marker=dict(line=dict(color='#000000', width=2)))
fig_left_graph.update_layout(
            title=f"Firmalara Göre Kişi Sayısı",
)
fig_left_graph.add_annotation(
            text="<b>Lejant Üzerinden Seçim Yapabilirsiniz</b>",
            align="left",
            showarrow=False,
            xref="paper",
            yref="paper",
            font=dict(color="white", size=12, family="Times New Roman"),
            bgcolor="rgba(0,0,0,0)",
            y=1.10,
            x=0.80,
            xanchor="left",
        )


fig_middle_graph =  px.bar(movement_table_selection[movement_table_selection["Birim"] == "Kg."], color = "Stok",
                           x="Cari_Tanim", y="Çıkış", facet_col="Evrak_Tipi")
fig_middle_graph.update_layout(
            title=f"Evrak Tipine Göre Yardım Alan Kişi Sayısı",
)


movement_table_pie_evrak = movement_table_selection.groupby("Evrak_Tipi").agg({"Cari_ID": "count", "Stok": "count", "Firma": "count"}).rename(
            columns={"Cari_ID": "KISI_SAYISI", "Stok": "STOK_SAYISI", "Firma": "FIRMA_SAYISI"}).reset_index()

fig_right_graph = go.Figure(data=[go.Pie(hole=0.3, labels=movement_table_pie_evrak["Evrak_Tipi"],
                                                 values=movement_table_pie_evrak["KISI_SAYISI"])])
fig_right_graph.update_traces(hoverinfo='label+percent', textinfo='value', textfont_size=8,
                                      marker=dict(line=dict(color='#000000', width=2)))
fig_right_graph.update_layout(
            title=f"Evrak Tipine Göre Yardım Alan Kişi Sayısı",
)
fig_right_graph.add_annotation(
            text="<b>Lejant Üzerinden Seçim Yapabilirsiniz</b>",
            align="left",
            showarrow=False,
            xref="paper",
            yref="paper",
            font=dict(color="white", size=12, family="Times New Roman"),
            bgcolor="rgba(0,0,0,0)",
            y=1.10,
            x=0.95,
            xanchor="left",
        )

left_chart, middle_chart, right_chart = st.columns(3)

with left_chart:
    left_chart.plotly_chart(fig_left_graph, use_container_width=True)

with middle_chart:
    middle_chart.plotly_chart(fig_middle_graph, use_container_width=True)

with right_chart:
    right_chart.plotly_chart(fig_right_graph, use_container_width=True)
