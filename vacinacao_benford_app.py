import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import base64
import streamlit as st


st.title('Benford´s law App')

st.markdown("""
Este app apresenta a Benford´s law aplicada em datasets do portal openDataSUS referente a vacinação do Covid-19!
* **Data source:** https://opendatasus.saude.gov.br/dataset/covid-19-vacinacao
""")
st.sidebar.header('Atributos de Entrada')
st.sidebar.selectbox('Estados',('Acre',' Alagoas',' Amapá',' Amazonas',' Bahia',' Ceará',' Distrito Federal',' Espírito Santo',' Goiás',' Maranhão',' Mato Grosso',' Mato Grosso do Sul',' Minas Gerais',' Paraná',' Paraíba',' Pará',' Pernambuco',' Piauí',' Rio de Janeiro',' Rio Grande do Norte',' Rio Grande do Sul',' Rondonia',' Roraima',' Santa Catarina',' Sergipe',' São Paulo',' Tocantins'))


url = "https://raw.githubusercontent.com/kelvins/Municipios-Brasileiros/main/csv/municipios.csv"

# dataset com os códigos IBGE para os municípios brasileiros
dfloc = pd.read_csv(url, 
                   dtype={"codigo_ibge":"object"})


def tratacodigo(x):
    return x[0:-1] 

dfloc.codigo_ibge = dfloc.codigo_ibge.apply(tratacodigo)
dfloc = dfloc.set_index("codigo_ibge")

UF = "AC" #Definindo Estado. Mudar aqui o valor para obter dataset de outro estado

#colunas disponíveis nos arquivos de vacinação
colunas = ['document_id', 'paciente_id', 'paciente_idade',
       'paciente_datanascimento', 'paciente_enumsexobiologico',
       'paciente_racacor_codigo', 'paciente_racacor_valor',
       'paciente_endereco_coibgemunicipio', 'paciente_endereco_copais',
       'paciente_endereco_nmmunicipio', 'paciente_endereco_nmpais',
       'paciente_endereco_uf', 'paciente_endereco_cep',
       'paciente_nacionalidade_enumnacionalidade', 'estabelecimento_valor',
       'estabelecimento_razaosocial', 'estalecimento_nofantasia',
       'estabelecimento_municipio_codigo', 'estabelecimento_municipio_nome',
       'estabelecimento_uf', 'vacina_grupoatendimento_codigo',
       'vacina_grupoatendimento_nome', 'vacina_categoria_codigo',
       'vacina_categoria_nome', 'vacina_lote', 'vacina_fabricante_nome',
       'vacina_fabricante_referencia', 'vacina_dataaplicacao',
       'vacina_descricao_dose', 'vacina_codigo', 'vacina_nome',
       'sistema_origem', 'data_importacao_rnds', 'id_sistema_origem']

colunadatas = [] #Configurando colunas de datas
for i in colunas:
    if "data" in i:
        colunadatas.append(i)


df = pd.read_csv(f"https://s3-sa-east-1.amazonaws.com/ckan.saude.gov.br/PNI/vacina/uf/2021-05-25/uf%3D{UF}/part-00000-b6cdd746-4f91-45c3-8716-efd6d4734c52.c000.csv", 
                 parse_dates = colunadatas, 
                 dtype={"estabelecimento_municipio_codigo":"object"},
                 delimiter=";")

municipios = [i for i in df.estabelecimento_municipio_codigo.unique()] #obtendo os códigos de todos os municípios do estado UF
dftemp = df.groupby(['estabelecimento_municipio_codigo','vacina_dataaplicacao'],as_index=False).agg({'document_id':'count'}).sort_values(by="vacina_dataaplicacao")
dftemp2 = dftemp.set_index(["vacina_dataaplicacao", "estabelecimento_municipio_codigo"])
dftemp2["primeiro_digito"] = dftemp2["document_id"].apply(lambda x: int(str(x)[0]))#capturando dados de primeiros dígitos dos municípios

dftemp3 = dftemp2.reset_index() 

dicios = dict() #criando dicionário com a frequência dos primeiros dígitos
for i in municipios:
    dfmun = dftemp3[dftemp3["estabelecimento_municipio_codigo"]==i]
    freq = dfmun["primeiro_digito"].value_counts().to_dict()
    dicios[i] = [i/len(dfmun) for i in freq.values()]
    
BENFORD = [30.1, 17.6, 12.5, 9.7, 7.9, 6.7, 5.8, 5.1, 4.6] #distribuição esperada da lei de Benford   
benforddic = dict()
for i in range(len(BENFORD)):
    benforddic[i+1] = BENFORD[i]/100 #criando o dicionário com valores Benford
distdf = pd.DataFrame.from_dict(dicios, orient="index")
distdf.columns = [1,2,3,4,5,6,7,8,9]

distdf = distdf.append(benforddic, ignore_index=True) #incluindo a referência dos valores Benford


municipios.append(0)

distdf.index = municipios #alterando índice para os códigos de municípios

distdf = distdf.rename(index={0:"Dist_Benford"}) #Formatação final dos nomes dos índices
distdf = distdf.dropna() #retirando linhas com valores faltantes 
distdf.index.name = "codigo_ibge"

distdfT = distdf.T

st.header('Aplicação na UF selecionada')


if st.button('Show Analysis'):
    st.write('Data Dimension: ' + str(distdf.join(dfloc["nome"])[['nome', 1, 2, 3, 4, 5, 6, 7, 8, 9]].shape[0]) + ' rows and ' + str(distdf.join(dfloc["nome"])[['nome', 1, 2, 3, 4, 5, 6, 7, 8, 9]].shape[1]) + ' columns.')
    st.dataframe(distdf.join(dfloc["nome"])[['nome', 1, 2, 3, 4, 5, 6, 7, 8, 9]])
    # Download dataframe
    # https://discuss.streamlit.io/t/how-to-download-file-in-streamlit/1806
    def filedownload(df):
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()  # strings <-> bytes conversions
        href = f'<a href="data:file/csv;base64,{b64}" download="BenfordAnalysis.csv">Download CSV File</a>'
        return href

    st.markdown(filedownload(distdf.join(dfloc["nome"])[['nome', 1, 2, 3, 4, 5, 6, 7, 8, 9]]), unsafe_allow_html=True)

if st.button('Show LinePlot'):
        st.header('Benford LinePlot')        
        sns.lineplot(data=distdfT, dashes=False);
        st.set_option('deprecation.showPyplotGlobalUse', False)
        st.pyplot()
