# bibliotecas

import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from datetime import datetime
import psycopg2
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.sql import delete
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

class ScrapingJob():

    def __init__(self):
        self.options = Options()
        #self.options = webdriver.ChromeOptions()
        self.options.add_argument('--ignore-certificate-errors')
        self.options.add_argument('--ignore-ssl-errors')
        self.options.add_argument('--headless') 
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--no-sandbox')
        #self.navegador = webdriver.Remote(options=self.options)
        self.navegador = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        self.url = 'https://jaraguadosulmaisempregos.santacatarinapelaeducacao.com.br/oportunidades?page=1'
        self.navegador.get(self.url) 

        self.schema = {
            'id': int,
            'Nome da Vaga': str,
            'Nome da Empresa': str,
            'Data Publicada': str,
            'Número de Vagas': str,
            'Quantidade de Vagas': int,
            'Senioridade': str,
            'Formato de Disponibilidade': str,
            'Área de Atuação': str,
            'Cidade': str,
            'Região': str,
            'Logo da Empresa': str,
            'Saber Mais': str
        }
        
        self.df:pd.DataFrame = None
        self.data = None
        self.num_pagina = list(range(1,26))

        # Minhas colunas da dataframe e depois do banco de dados
        self.nome_de_vagas = []
        self.nome_empresas = []
        self.data_publicada = []
        self.num_vagas = []
        self.vagas_apenas_numero = []
        self.senioridade = []
        self.formato_disponibilidade = []
        self.area_atuacao = []
        self.cidade = []
        self.regiao = []
        self.logo_empresa = []
        self.saber_mais = []

    def start(self):

        for num in self.num_pagina:

            # controle de página
            self.navegador.get(f'https://jaraguadosulmaisempregos.santacatarinapelaeducacao.com.br/oportunidades?page={num}')
            # elementos que gostaria de selecionar
            elementos_vagas = self.navegador.find_elements(By.CSS_SELECTOR, "p.text_body_b3_bold.font-family-inter")
            elementos_empresa = self.navegador.find_elements(By.CSS_SELECTOR, "p.flex.items-center.gap-1.text_body_b5_regular")
            elementos_data = self.navegador.find_elements(By.XPATH, "//p[@class='flex items-center gap-1 text_body_b5_regular lg:absolute lg:top-6 lg:right-6']")
            caracteristicas_da_vaga = self.navegador.find_elements(By.CLASS_NAME, "tags")
            elementos_cidade = self.navegador.find_elements(By.CSS_SELECTOR, "p.flex.items-center.gap-1.text_body_b5_regular")
            elementos_logotipo = self.navegador.find_elements(By.CSS_SELECTOR, "img.hidden.lg\\:block.card-img")
            elementos_saber_mais = self.navegador.find_elements(By.CLASS_NAME, "card-oportunidade")

            # salvando elementos em uma lista
            self.nome_de_vagas.extend([vaga.text for vaga in elementos_vagas])
            self.nome_empresas.extend([empresa.text.strip() for i, empresa in enumerate(elementos_empresa) if i % 3 == 0])
            self.data_publicada.extend([data.text for data in elementos_data])
            self.num_vagas.extend([feature.text.split('\n')[0] for feature in caracteristicas_da_vaga])
            self.senioridade.extend([feature.text.split('\n')[1] for feature in caracteristicas_da_vaga])
            self.formato_disponibilidade.extend([feature.text.split('\n')[2] for feature in caracteristicas_da_vaga])
            self.area_atuacao.extend([feature.text.split('\n')[3] for feature in caracteristicas_da_vaga])
            self.cidade.extend([elemento.text.strip() for i, elemento in enumerate(elementos_cidade) if (i - 1) % 3 == 0])
            self.regiao.extend([feature.text.split('\n')[4] for feature in caracteristicas_da_vaga])
            self.logo_empresa.extend([elemento.get_attribute("src") for elemento in elementos_logotipo])
            self.saber_mais.extend(elemento.get_attribute("href") for elemento in elementos_saber_mais)

        # Fechando meu navegador
        self.navegador.quit()

        # Criando coluna de vagas apenas com o número
        self.vagas_apenas_numero = [int(num.split()[0]) for num in self.num_vagas]

        # tratamento nas cidades, (adiantando um pouco de ETL)
        self.cidade = ["Jaraguá do Sul/SC" if nome == "" else nome for nome in self.cidade]
    

        data = {'Nome da Vaga': self.nome_de_vagas,
                'Nome da Empresa': self.nome_empresas,
                'Data Publicada': self.data_publicada,
                'Número de Vagas': self.num_vagas,
                'Quantidade de Vagas': self.vagas_apenas_numero,
                'Senioridade': self.senioridade,
                'Formato de Disponibilidade': self.formato_disponibilidade,
                'Área de Atuação': self.area_atuacao,
                'Cidade': self.cidade,
                'Região': self.regiao,
                'Logo da Empresa': self.logo_empresa,
                'Saber Mais': self.saber_mais               
                }
        self.df = pd.DataFrame(data)
        self.df.reset_index(inplace=True)
        self.df.rename(columns={'index': 'id'}, inplace=True)

        # Convertendo tipos de dados
        for column, dtype in self.schema.items():
            self.df[column] = self.df[column].astype(dtype)
        
        # Criando coluna que gerencia a data e horário de atualização
        self.df['Created At'] = datetime.now()

        
        file_path = 'oportunidade_de_empregos_' + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + '.xlsx'
        # Salvando arquivo em Excel
        self.df.to_excel('data//' + file_path, index=False)

        return self.df

############################## INICIA ABAIXO A CLASSE PARA INSERIR AS INFORMAÇÕES NO BANCO DE DADOS ########################

class InsertPostgress(ScrapingJob):
    def __init__(self):
        super().__init__()  # Chame o método __init__ da classe pai
        self.my_dataframe = ScrapingJob()
    
    def start(self):
        self.credenciais()
        self.definindo_schema_da_tabela()
        self.deletando_dados_do_ultimo_web_scraping()
        self.salvando_dados_postgres()
        return print('Tudo Finalizado')

    def credenciais(self):
        # Carregar variáveis de ambiente
        load_dotenv()
        # Definindo variáveis de ambiente
        self.URL_DATABASE_POSTGRES = os.environ.get('URL_DATABASE_POSTGRES')
        self.engine = create_engine(self.URL_DATABASE_POSTGRES)
        self.Session =  sessionmaker(bind=self.engine)
        self.session = self.Session()
    
    def definindo_schema_da_tabela(self):

        # Nome da minha tabela
        self.nome_da_tabela = 'scraping_empregos_jgua'

        # Definir o esquema da tabela
        self.meta = MetaData()

        self.empregos_jaragua = Table(
            self.nome_da_tabela, 
            self.meta,
            Column('id', Integer, primary_key = True, index = True),
            Column('Nome da Vaga', String, index=True),
            Column('Nome da Empresa', String, index=True),
            Column('Data Publicada', String, index=True),
            Column('Número de Vagas', String, index=True),
            Column('Quantidade de Vagas', Integer, index=True),
            Column('Senioridade', String, index=True),
            Column('Formato de Disponibilidade', String, index=True),
            Column('Área de Atuação', String, index=True),
            Column('Cidade', String, index=True),
            Column('Região', String, index=True),
            Column('Logo da Empresa', String, index=True),
            Column('Saber Mais', String, index=True),
            Column('Created At', DateTime(timezone=True), default = func.now(), index=True)
        )

        # Criando a tabela se não existir
        self.meta.create_all(self.engine, checkfirst=True)

    def deletando_dados_do_ultimo_web_scraping(self):

        # Deletando dados da tabela (caso exista)
        self.delete_dados = delete(self.empregos_jaragua)
        self.session.execute(self.delete_dados)
        self.session.commit()
        self.session.close()
   
    def salvando_dados_postgres(self):
        self.my_dataframe.start().to_sql(self.nome_da_tabela, self.engine, if_exists='append', index= False) 


