"""Public, read-only portfolio demonstration. Never includes the pipeline page."""
import os
os.environ['CVM_DASHBOARD_PUBLIC'] = '1'

import streamlit as st
from src.publication import PUBLIC_PAGES
from src.data.loader import load_and_prepare_base
from src.components.theme import apply_theme

st.set_page_config(page_title='Finance CVM | Kleber Abreu', page_icon='◈', layout='wide')
apply_theme()

icons = ['dashboard', 'domain', 'stacked_bar_chart', 'filter_alt', 'timeline', 'scatter_plot', 'table_chart']
pages = [st.Page(path, title=title, icon=f':material/{icons[i]}:', url_path=url, default=i == 0)
         for i, (path, title, url) in enumerate(PUBLIC_PAGES)]
current_page = st.navigation(pages, position='hidden')
with st.sidebar:
    st.markdown('<div class="sidebar-brand"><div class="monogram">F.</div><div class="brand-title">Finance CVM</div><div class="brand-subtitle">Uma criação de Kleber Abreu</div></div>', unsafe_allow_html=True)
    for page in pages:
        st.page_link(page, label=page.title, icon=page.icon)
    st.divider()
    st.markdown('[← Voltar ao portfólio](https://www.kleberabreu.com.br/projetos/dashboard-cvm/)  \n[Código aberto · MIT ↗](https://github.com/kleberAbreu/finance-cvm-dashboard)')

sample = load_and_prepare_base()
start = sample['Data_Trimestre'].min().strftime('%d/%m/%Y')
end = sample['Data_Trimestre'].max().strftime('%d/%m/%Y')
st.markdown(f'<div class="sample-strip"><strong>DEMONSTRAÇÃO PÚBLICA</strong><span>{sample["Ticker"].nunique()} empresas · {sample["Data_Trimestre"].nunique()} trimestres</span><span class="period">{start} — {end}</span></div><div class="sample-note">Amostra congelada com valores demonstrativos, sem cotações atuais. Não constitui recomendação de investimento.</div>', unsafe_allow_html=True)
current_page.run()
st.caption('Leitura dos valores: mi = milhões · bi = bilhões · tri = trilhões de reais. As exportações usam reais.')
