"""Public, read-only portfolio demonstration. Never includes the pipeline page."""
import os
os.environ['CVM_DASHBOARD_PUBLIC'] = '1'

import streamlit as st
from src.publication import PUBLIC_PAGES
from src.data.loader import load_and_prepare_base

st.set_page_config(page_title='Dashboard Financeiro CVM | Kleber Abreu', page_icon='📊', layout='wide')

st.sidebar.markdown('[← Portfólio de Kleber Abreu](https://www.kleberabreu.com.br/projetos/dashboard-cvm/)')
st.sidebar.markdown('[Código aberto · MIT](https://github.com/kleberAbreu/finance-cvm-dashboard)')

df = load_and_prepare_base()
start = df['Data_Trimestre'].min().strftime('%d/%m/%Y')
end = df['Data_Trimestre'].max().strftime('%d/%m/%Y')
st.info(f'Demonstração pública · amostra congelada de {df["Ticker"].nunique()} empresas, '
        f'de {start} a {end}. Valores demonstrativos; não são cotações atuais. '
        'Use os filtros para explorar o produto. Não constitui recomendação de investimento.')

st.caption('Escala dos cards: mi = milhões; bi = bilhões; tri = trilhões de reais. As exportações usam reais.')

pages = [st.Page(path, title=title, url_path=url, default=i == 0)
         for i, (path, title, url) in enumerate(PUBLIC_PAGES)]
st.navigation(pages).run()
