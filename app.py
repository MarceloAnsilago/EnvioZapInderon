import streamlit as st
import pandas as pd
import re
import time
import os
import urllib.parse
import requests
import tkinter as tk
import datetime
import random
from tkinter import filedialog
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Título do aplicativo
st.title('Disparar Mensagens')

#Criar a tabela que apresenta o status dos envios
def atualizar_tabela():
    # Calcular a contagem de cada item na coluna "Status"
    contagem_status = df['Status'].value_counts().reset_index()
    contagem_status.columns = ['Status', 'Quantidade']

    # Atualizar o widget st.table com os novos dados
    st_table.table(contagem_status)
####################################################################################
#Contagem regressiva
def contagem_regressiva_inicial_final(segundos_inicial, segundos_final, mensagem):
    output = st.empty()
    
    # Gere um número aleatório dentro do intervalo de segundos_inicial e segundos_final
    segundos_aleatorios = random.randint(segundos_inicial, segundos_final)

    for i in range(segundos_aleatorios, -1, -1):
        countdown = f"{i:2d}"
        texto = f"Aguardando {countdown} segundos para {mensagem}"
        output.text(texto)
        time.sleep(1)

    output.empty()

#exibir os prints    
def exibir_mensagem_personalizada(mensagem):
    output = st.empty()
    output.text(mensagem)
    time.sleep(3)  # Aguarda 3 segundos
    output.empty()  # Remove a mensagem após 3 segundos

# Variável global para armazenar o caminho do arquivo
caminho_do_arquivo = None

#Abrir o explorer a primeira vez pra buscar o local e salvar a planilha
def salvar_dataframe_como_excel(df):
    global caminho_do_arquivo  # Indica que estamos usando a variável global
    root = tk.Tk()
    root.withdraw()
    root.title("Informe o endereço onde deseja Salvar a Planilha Excel")
    data_atual = datetime.datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Contatos_{data_atual}.xlsx"
    caminho = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Planilhas Excel", "*.xlsx")], initialfile=nome_arquivo)
    if caminho:
        df.to_excel(caminho, index=False)
        caminho_do_arquivo = caminho  # Armazena o caminho do arquivo na variável global
        return caminho_do_arquivo
    else:
        return None

# Tratamento de dados
def preprocess_dataframe(df):
    # Deixando apenas as colunas necessárias
    colunas_a_manter = ['Nome do Titular da Ficha de bovideos', 'Nome da Propriedade','Endereço da Prop.','Dec. Rebanho','Telefone 1','Telefone 2',
                        'Celular']
    # Use o método drop para excluir as colunas que não estão na lista
    df = df[colunas_a_manter]
    
    # Agrupando as 3 colunas com número de telefone
    colunas_a_manter = ['Nome do Titular da Ficha de bovideos','Nome da Propriedade','Endereço da Prop.','Dec. Rebanho' ]

    # Colunas a serem derretidas (Telefone 1, Telefone 2 e Celular)
    colunas_para_derreter = ['Telefone 1', 'Telefone 2', 'Celular']

    # Use o método melt para derreter as colunas de telefone
    df = pd.melt(df, id_vars=colunas_a_manter, value_vars=colunas_para_derreter, value_name='Telefone')

    # Exclua a coluna "Tipo de Telefone" após o derretimento
    df = df.drop(columns=['variable'])
    
    # Combine as colunas 'Nome do Titular da Ficha de bovideos', 'Nome da Propriedade' e 'Endereço da Prop.' em 'Nome'
    df['Nome'] = df.apply(lambda row: f"{row['Nome do Titular da Ficha de bovideos']} - {row['Nome da Propriedade']} - {row['Endereço da Prop.']}", axis=1)

    # Exclua as colunas 'Nome do Titular da Ficha de bovideos', 'Nome da Propriedade' e 'Endereço da Prop.'
    df = df.drop(columns=['Nome do Titular da Ficha de bovideos', 'Nome da Propriedade','Endereço da Prop.'])

    # Reorganize as colunas para colocar 'Nome' como a primeira coluna
    df = df[['Nome'] + [col for col in df.columns if col != 'Nome']]

    # Suponhamos que sua coluna com números de telefone seja chamada 'telefone'
    df['Telefone'] = df['Telefone'].astype(str)  # Certifique-se de que a coluna seja do tipo string
 
    # Substitua todos os caracteres não numéricos, exceto o hífen, por uma string vazia
    df['Telefone'] = df['Telefone'].str.replace(r'[^0-9-]', '', regex=True)

    # Preencha zeros à esquerda para obter um formato consistente (por exemplo, 1234567890)
    df['Telefone'] = df['Telefone'].str.zfill(10)

    # Use o método str.endswith para verificar se os dois últimos dígitos da direita são '00'
    df = df[~df['Telefone'].str.endswith('00')]

    # Adicione '+55' na frente de todos os números de telefone
    df['Telefone'] = '+55' + df['Telefone']

    df['Telefone'] = df['Telefone'].apply(lambda telefone: telefone[:5] + telefone[6:] if len(telefone) == 15 else telefone)
    
    # Crie a coluna "Status" com valor zero
    df["Status"] = "Fila de envio"
    
    # Reordene as colunas para colocar "Status" antes de "Nome"
    df = df[["Status"] + [col for col in df.columns if col != "Status"]]

    # # Adiciona espaços nas posições desejadas
    df['Telefone'] = df['Telefone'].str[:3] + ' ' + df['Telefone'].str[3:5] + ' ' + df['Telefone'].str[5:]
        
    # Reordene as colunas para colocar "Status" antes de "Nome"
    df = df[["Status"] + [col for col in df.columns if col != "Status"]]

    return df  

#carregar a planilha para o upload
uploaded_file = st.file_uploader("Carregar arquivo CSV ou Excel", type=["csv", "xlsx"])
if uploaded_file is not None:
    # Verifique o tipo de arquivo e carregue-o como DataFrame
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
        
    elif uploaded_file.name.endswith('.xlsx'):
        df = pd.read_excel(uploaded_file, engine='openpyxl')
    
    #buscar o endereço onde vai salvar a planilha    
st.header('Tratar dados', divider='rainbow')   
##################################################################################################

with st.form("Meu Formulário"):
#     # Adicione widgets para coletar dados do usuário
    declarou = st.radio("Informe para quem deseja disparar as mensagens", [
        "Continuar de uma lista anterior",
        "Para quem já declarou a campanha atual",
        "Para quem NÃO declarou a campanha atual"
        
    ])

#     # Mostrar resultado com base na escolha do usuário
    if declarou == "Continuar de uma lista anterior":
        df = df
        st.write("Você selecionou: Continuar de onde parou")


    elif declarou == "Para quem já declarou a campanha atual":
        df = preprocess_dataframe(df)
        df = df[df['Dec. Rebanho'] != 0]
     
    elif declarou == "Para quem NÃO declarou a campanha atual":
        df = preprocess_dataframe(df)
        df = df[df['Dec. Rebanho'] != 1]
 # #    Adicione um checkbox para agrupar os contatos (inicialmente marcado)
    agrupar_contatos = st.checkbox("Deseja agrupar os contatos?", value=True)


#     # Verifique o valor do checkbox e ajuste o DataFrame conforme necessário
    if agrupar_contatos:
        if declarou != "Continuar de uma lista anterior":
           st.write("Você selecionou: Agrupar os contatos.")
          # Coloque aqui a estrutura de código para agrupar os contatos
           df = df.groupby(["Status", "Telefone"])["Nome"].apply(lambda x: " || ".join(x)).reset_index()
    else:
           st.write("Você selecionou: Não agrupar os contatos.")
    
# ######################################################################################################

    # Use st.form_submit_button para criar um botão de envio
    submit_button = st.form_submit_button("Tratar dados/Enviar")
    with st.expander("Exibir contatos"):
        # Verifique se o botão de envio foi clicado
        if submit_button:
             st.write(df)
             
##################################################################################################
##################################################################################################
st.header('Definir Mensagens', divider='rainbow')     

# Crie um radio box para selecionar o tipo de mensagem
tipo_mensagem = st.radio("Selecione o tipo de mensagem:", ["Mensagem genérica", "Mensagem, Sim ou Não"])

# Verifique a escolha do usuário
if tipo_mensagem == "Mensagem genérica":
    st.write("Você selecionou: Mensagem genérica")
    # Coloque aqui o código correspondente para a mensagem genérica
elif tipo_mensagem == "Mensagem, Sim ou Não":
    st.write("Você selecionou: Mensagem, Sim ou Não")
    # Coloque aqui o código correspondente para a mensagem complexa
# Verifique a escolha do usuário e exiba o expander correspondente
if tipo_mensagem == "Mensagem genérica":
       # Exiba o expander com a mensagem genérica
    with st.expander("Detalhes da Mensagem Genérica"):
        st.write("Aqui está a mensagem genérica:")
        MensagemGenericaTexto = "Prezado produtor, estamos no final da campanha obrigatória de declaração de rebanho e não consta em nossos dados sua declaração, procure a agencia da IDARON mais próxima a você e providencie o mais breve possivel para se livrar de aborrecimentos, você pode ainda cadastrar pelo site http://sistemas.idaron.ro.gov.br:6555/Login/Index?ReturnUrl=%2f  se tiver senha cadastrada, a IDARON agradece a atenção e deseja-lhe um bom dia"
        mensagemGenerica = st.text_area("Entre com uma mensagem generica",MensagemGenericaTexto)
elif tipo_mensagem == "Mensagem, Sim ou Não":
    # Exiba o expander com a mensagem complexa
    with st.expander("Mensagem, Sim ou Não"):
        mensagemPerguntaTexto = "Olá tudo bem?😊 Esta mensagem é da IDARON de São Miguel do Guaporé. \nO numero -&numero esta cadastrado na *IDARON* para contato com -&nome .\n\nVocê é ele(a)(s) ou responde por ele(a)(s)?\nResponda 1-SIM ou 2-NÃO \n\n1️⃣Sim\n2️⃣Não\n\n👇 Sua resposta "
        mensagemRespSIM = "Prezado produtor(a), a campanha semestral de rebanho começou, aproveite que estamos nos primeiros dias enquanto o movimento na unidade é pequeno e declare já seu rebanho de segunda a sexta das 07:30 as 13:30, você pode declarar tambem pela web pelo site da IDARON http://sistemas.idaron.ro.gov.br:6555/Login/Index?ReturnUrl=%2f "                      
        mensagemRespNAO = "Obrigado por responder, providenciaremos para que seu contato seja retirado de nossas base de dados, nos perdoe pelo incomodo e tenha um ótimo dia"
        mensagemRespNaoentendi ="Desculpe 😞 não entendi sua resposta, vamos tentar denovo?😁\n\nOlá tudo bem?😊 Esta mensagem é da IDARON de São Miguel do Guaporé. \nO numero -&numero esta cadastrado na *IDARON* para contato com -&nome .\n\nVocê é ele(a)(s) ou responde por ele(a)(s)?\nResponda 1-SIM ou 2-NÃO \n\n1️⃣Sim\n2️⃣Não\n\n👇 Sua resposta" 
        mensagemRespContato ="Lamento \nEste contato só opera mensagens automáticas, mas você pode entrar com contato conosco pelo telefone +55 69 9245-2646"

        mensagemPergunta = st.text_area("Insira uma mensagem perguntando Sim ou Não", mensagemPerguntaTexto)
        mensagemSIM = st.text_area("Insira uma mensagem respondendo se SIM",mensagemRespSIM)
        mensagemNAO = st.text_area("Insira uma mensagem respondendo se NÃO",mensagemRespNAO)
        mensagemNentedi = st.text_area("Insira uma mensagem respondendo se NÃO entendeu",mensagemRespNaoentendi)
        mensagemContato = st.text_area("Insira uma mensagem informando o Contato",mensagemRespContato)
        st.write("Esta é uma mensagem mais complexa com detalhes adicionais.")




st.header('Disparar Mensagens', divider='rainbow')  
# # Função para salvar o DataFrame em um arquivo Excel
def salvar_dataframe_em_arquivo(df, caminho):
    df.to_excel(caminho, index=False)

# ################################################################################################
# ################Iniciar logica de envio e leitura de mensagens##################################
# ################################################################################################

agent = {"User-Agent": 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}
api = requests.get("https://editacodigo.com.br/index/api-whatsapp/xgLNUFtZsAbhZZaxkRh5ofM6Z0YIXwwv" ,  headers=agent)
time.sleep(1)
api = api.text
api = api.split(".n.")
bolinha_notificacao = api[3].strip()
contato_cliente = api[4].strip()
caixa_msg = api[5].strip()
msg_cliente = api[6].strip()
dir_path = os.getcwd()
chrome_options2 = Options()
chrome_options2.add_argument(r"user-data-dir=" + dir_path + "/pasta/sessao")


# TelefoneContato ='//*[@id="main"]/header/div[2]/div/div/span'
TelefoneContato ='//*[@id="main"]/header/div[2]/div[1]/div/div/span'
                
####################################################################################################################
#Responder nova mensagem
####################################################################################################################
def ReponderMensagem():
 
    try:      
        # PEGA A BOLINHA VERDE

        bolinha = driver.find_element(By.CLASS_NAME, bolinha_notificacao)
        bolinha = driver.find_elements(By.CLASS_NAME, bolinha_notificacao)
        print("-------------------------------------------------------------")
        print("Encontramos uma nova bolinha")
        print("-------------------------------------------------------------")
        clica_bolinha = bolinha[-1]
        acao_bolinha = webdriver.common.action_chains.ActionChains(driver)
        acao_bolinha.move_to_element_with_offset(clica_bolinha, 0, -20)
        acao_bolinha.click()
        acao_bolinha.perform()
        acao_bolinha.click()
        acao_bolinha.perform()
       
        exibir_mensagem_personalizada("Aguardando a pagina carregar")
        time.sleep(3)
        exibir_mensagem_personalizada("Pagina carregada")
      
        time.sleep(3)
        # PEGA O TELEFONE DO CLIENTE
        
        telefone_cliente = driver.find_element(By.XPATH, TelefoneContato)
        telefone_final = telefone_cliente.text
             
        # PEGA A MENSAGEM DO CLIENTE
        todas_as_msg = driver.find_elements(By.CLASS_NAME, msg_cliente)
        todas_as_msg_texto = [e.text for e in todas_as_msg]
        msg = todas_as_msg_texto[-1]
        
        print(msg)
        print(telefone_final)
########################################################################################################################
        # Verifique se 'telefone_final' está presente na coluna 'Telefone'
        if (df['Telefone'] == telefone_final).any():
            # Encontre o índice da linha onde 'Telefone' é igual a 'telefone_final'
            indice_linha = df.index[df['Telefone'] == telefone_final].tolist()[0]
            # Verifique o valor da coluna 'Status' na mesma linha
            status = df.at[indice_linha, 'Status']
            print("-------------------------------------------------------------")
            print("encontramos o status ",status)
            print("-------------------------------------------------------------")
            if status == 'Aguardando Resposta':
                if msg == '1' or msg.lower() == 'sim':
                    resposta = mensagemSIM
                    criterio = "Envio Completo"
                    disparar(telefone_final, resposta, criterio)
                elif (msg == '2' or  msg.lower() in ['2', 'nao', 'não', 'naõ']) :
                    resposta = mensagemNAO    
                    criterio = 'Respondeu não'   
                    disparar(telefone_final, resposta, criterio)
                # elif (msg != '2' or  msg.lower() in ['2', 'nao', 'não', 'naõ']) and msg != '1' or msg.lower() == 'sim':
                else:
                    resposta = mensagemRespNaoentendi
                    criterio = 'Aguardando Resposta'  # Para não alterar o status
                    resposta = resposta.replace('-&nome', df.loc[indice_linha, 'Nome']) 
                    resposta = resposta.replace('-&numero', telefone_final) 
                    disparar(telefone_final, resposta, criterio)
                
                # Atualize o valor da coluna 'Status' na mesma linha
                df.at[indice_linha, 'Status'] = criterio
                # Salve o DataFrame atualizado em um arquivo
                df.to_excel(caminho_do_arquivo, index=False)
            elif status != 'Aguardando Resposta': 
                resposta = mensagemContato
                disparar(telefone_final, resposta, None)


        atualizar_tabela()
    except: 
        if df[df['Status'] == "Fila de envio"].shape[0] > 0:
            exibir_mensagem_personalizada("Sem novas mensagens, iniciando um novo disparo")
            contagem_regressiva_inicial_final(10, 15, 'para novo disparo')
            print("Sem novas mensagens, iniciando novo disparo.")
            contato = str(df[df['Status'] == "Fila de envio"].iloc[0]['Telefone']) 
            Nome =  str(df[df['Telefone'] == contato].iloc[0]['Nome']) 
            mensagem = mensagemPergunta
            mensagem = mensagem.replace('-&nome', Nome) 
            mensagem = mensagem.replace('-&numero', contato) 
            criterio = "Aguardando Resposta"
            print("Número da coluna 'Telefone' onde 'Status' é igual a 0:")
            exibir_mensagem_personalizada("Enviando nova mensagen")
            disparar(contato, mensagem, criterio)
            df.to_excel(caminho_do_arquivo, index=False) 
            atualizar_tabela()
            print('enviando novas mensagens')
            time.sleep(3)
        else:
            # No rows with 'Fila de envio' in the 'Status' column
            print("-------------------------------------------------------------")
            print("Fila de envios completa")
            print("-------------------------------------------------------------")
            exibir_mensagem_personalizada("Fila de envio completa, aguardando novas mensagens")

def disparar(contato, mensagem, criterio):
    
        mensagem = urllib.parse.quote(mensagem)
            # enviar a mensagem
        link = f"https://web.whatsapp.com/send?phone={contato}&text={mensagem}"

        driver.get(link)
        
        # esperar a tela do whatsapp carregar -> espera um elemento que só existe na tela já carregada aparecer
        while len(driver.find_elements(By.ID, 'side')) < 1: # -> lista for vazia -> que o elemento não existe ainda
            time.sleep(1)
        time.sleep(2) # só uma garantia
            # você tem que verificar se o número é inválido
        if len(driver.find_elements(By.XPATH, '//*[@id="app"]/div/span[2]/div/span/div/div/div/div/div/div[1]')) < 1:
            # enviar a mensagem
            
            driver.find_element(By.XPATH, '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[2]/button/span').click()
            df.loc[df['Telefone'] == contato, 'Status'] = criterio
            webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(3)
        else:
          df.loc[df['Telefone'] == contato, 'Status'] = 'Contato Invalido'
        webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
   

# Crie um expander
with st.expander("Iniciar disparos"):
    
    if st.button("Iniciar Disparos"):  # Verifique se a função st.button está correta
        #Inicia a tabela que mostra o status dos envios
        st_table = st.empty()
    
        # caminho_do_arquivo = salvar_dataframe_como_excel(df)
        if caminho_do_arquivo is None:
                    caminho_do_arquivo = salvar_dataframe_como_excel(df)
        
       # print("o caminho do aquivvvo é ", caminho_do_arquivo)
        st.write("Processo de disparos iniciados'!")
        Servico = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=Servico)
        driver.get('https://web.whatsapp.com')
        while len(driver.find_elements(By.ID, 'side')) < 1:
            time.sleep(1)
        time.sleep(2)
        ################################################################################################
        # esperar a tela do whatsapp carregar -> espera um elemento que só existe na tela já carregada aparecer
        # -> lista for vazia -> que o elemento não existe ainda
        while len(driver.find_elements(By.ID, 'side')) < 1:
            time.sleep(1)
        time.sleep(2)  # só uma garantia
        # Inicie a verificação infinita após o carregamento da página
        while True:
                # time.sleep(1) 
                if tipo_mensagem == "Mensagem, Sim ou Não":   
                    # with st.spinner('Iniciando um novo Disparo...'):
                    ReponderMensagem()   
                   
                    print("-------------------------------------------------------------")
                    print("Aguardando 15 segundos pra sair do código")
                    print("-------------------------------------------------------------")
                elif tipo_mensagem == "Mensagem genérica":
                               # Encontre o valor da coluna "numero" onde o primeiro "status" igual a 0
                    contato = str(df[df['Status'] == "Fila de envio"].iloc[0]['Telefone']) 
                    Nome =  str(df[df['Telefone'] == contato].iloc[0]['Nome']) 
                    mensagem = mensagemGenerica
                    mensagem = mensagem.replace('-&nome', Nome) 
                    mensagem = mensagem.replace('-&numero', contato) 

                    print("Enviando")
                    
                    criterio = "Envio Completo"
                    print("Número da coluna 'Telefone' onde 'Status' é igual a 0:", contato)
                    disparar(contato , mensagem, criterio)
                    df.to_excel(caminho_do_arquivo, index=False) 
                    time.sleep(1)  
                    atualizar_tabela()
# st.header('Disparos efetuados', divider='rainbow')     