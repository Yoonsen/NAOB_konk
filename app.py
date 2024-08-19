import streamlit as st
import dhlab.text as dh
from urllib.parse import quote
import dhlab.api.dhlab_api as api
import pandas as pd
from PIL import Image
import urllib
import utils 

# for excelnedlastning
from io import BytesIO
#from pyxlsb import open_workbook as open_xlsb



@st.cache_data
def to_excel(_df):
    """Make an excel object out of a dataframe as an IO-object"""
    df = _df.copy()
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data


@st.cache_data
def konk(_corpus = None, query = None):
    """Create a concordance from a corpus"""
    # exit if corpus is empty
    if _corpus.corpus.empty:
        return pd.DataFrame()
    
    conc = dh.Concordance(_corpus, query, limit = 10000) 
    konkdf = pd.merge(conc.frame, _corpus.frame, on='urn')
    konkdf = konkdf[['urn','year','authors', 'title', 'concordance']].sort_values('year')
    return konkdf


def display_konks_old(conc, search, size, corpus):
    search = quote(search)
    conc['link'] = conc['urn'].apply(lambda c: f"""[{c.split('_')[2]}](https://www.nb.no/items/{c}?searchText={search}) """)
    conc['concordance'] = conc['concordance'].apply(lambda c: c.replace('<b>', '**').replace('</b>','**'))
    conc = conc[['link','year','authors', 'title', 'concordance']].sort_values(by='year')
    return '\n\n'.join(
        [' '.join([str(x[1])] + [" **—** "] + [str(y) for y in x[2:-1]] + [" **—** " + str(x[-1])]) for x in 
         conc.sample(min(int(size), len(konks))).sort_values(by='year').itertuples()])


def display_konks(conc, search):
    conc["url"] = conc.urn.apply(lambda x: format_url(x, search))
    conc['concordance'] = conc['concordance'].apply(lambda c: c.replace('<b>', '**').replace('</b>','**'))
    conc["left_context"] = conc["concordance"].apply(lambda x: x.split("**")[0].strip())
    conc["right_context"] = conc["concordance"].apply(lambda x: x.split("**")[-1].strip())
    conc["target"] = conc["concordance"].apply(lambda x: x.split("**")[1].strip())
    conc["concordance"] = conc["concordance"].apply(lambda x: x.replace("**", ""))
    return conc


def format_url(urn: str, searchterm: str = None):
    """Format document URN to a clickable link"""
    url = f"https://www.nb.no/items/{urn}"
    if searchterm:
        return f"{url}?searchText={searchterm}"
    return url


@st.cache_data
def korpus():
    df = pd.read_csv('naob.csv', header = 0, index_col = 0)
    c = dh.Corpus()
    c.extend_from_identifiers(df.urn.unique().tolist())
    return c.frame


#### NAOB APP ### 
### PAGE LAYOUT ###
st.set_page_config(
    layout="wide",
    page_title="NAOB",
    page_icon=utils.nb_favicon,
    initial_sidebar_state="auto",
    menu_items=None
)

header = st.container()

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)
col5, col6 = st.columns(2)

 
### PAGE WIDGETS ###
with header:
    # Custom header with external style sheet for logos and icons
    st.components.v1.html(utils.header_html, height=40)
    st.title("Søk i NAOBs korpus")


naob = korpus()

#image = Image.open('NB-logo-no-eng-svart.png')
#st.image(image, width = 200)

with col3:
    samplesize = st.number_input("Vis maks antall konkordanser:", 150, help = "Angi maks antall konkordanser som skal vises i gangen.")

with col4:
    filename = st.text_input("Angi et filnavn for konkordansene:", "konkordanser.xlsx", help="Filen vil sannlygvis ligge i mappen ved navn Nedlastninger.")
    
with col1:
    search = st.text_input('Ord og fraser', "leksikografi", help= """Skriv inn ord for å finne match i avsnitt. For alternativer sett OR imellom: 'spise OR spise' men utelat anførselstegn. Grupper ord i fraser ved å omslutte dem med anførselstegn:"spise opp" vil matche når ordene følger på hverandre. Ord kan stå vilkårlig nær hverandre med nøkkelordet NEAR: NEAR(spise opp, 2) får match når ordene maks skilles med to ord. Ord med bindestrek eller punktum må settes i anførselstegn: "Nord-Norge" og "dr.art.". Om to eller flere ord skrives uten anførselstegn rundt vil det bli match i alle avsnitt som inneholder de to ordene. Trunker søke med *, for eksempel spise*.""")

with col2:
    periode = st.values = st.slider(
     'Velg en periode',
     1814, 2024, (1814, 2024))

corpus = naob
if periode != []:
    corpus_id = naob[(naob.year >= periode[0]) & (naob.year <= periode[1])]
    corpus = dh.Corpus()
    corpus.extend_from_identifiers(corpus_id.urn.unique().tolist())

if not search == "":
    konks = konk(corpus, query=search)

    with col5:
        st.markdown(f"Antall konkordanser totalt: **{len(konks)}**")
    
    with col6:
        download_button = st.download_button(
            ":arrow_down: Last ned",
            to_excel(konks),
            filename, 
            help = "Last ned data til en CSV-fil som kan åpnes i excel og andre tabell-programmer."
        )
        if download_button:
            st.toast(f'Lastet ned til `{filename}`', icon=":material/done_outline:")

    #if (samplesize < len(konks)):
    
    if konks.empty:
        st.info(f"Ingen treff", icon=":material/cross:")
    else:
        concordances = display_konks(konks, search)

        split_context = st.toggle("Del opp konkordansene i flere kolonner", False, help="Del opp venstre og høyre kontekst til søkeordet i separate kolonner.")    
        
        if split_context:
            show_columns = ["url", "year", "authors", "title", "left_context", "target", "right_context"]
        else: 
            show_columns = ["url", "year", "authors", "title", "concordance"]

        # Configure columns format
        col_config = {
                "url":st.column_config.LinkColumn("nb.no", display_text = "🔗", width="small"), 
                "year": st.column_config.TextColumn("Årstall"),
                "authors": "Forfatter",
                "title": st.column_config.TextColumn("Tittel", width="medium"),
                "concordance": st.column_config.TextColumn("Konkordans", width="large"), 
                "left_context": st.column_config.TextColumn("Venstre kontekst"), 
                "target": st.column_config.TextColumn("Søkeord"),
                "right_context": st.column_config.TextColumn("Høyre kontekst")
            }

        st.dataframe(
            concordances, 
            column_config = col_config,
            column_order = show_columns, 
            hide_index = True,
            use_container_width=True,
            )
