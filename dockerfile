FROM python:3.12

# Copia o arquivo de requisitos e instala as dependências
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# Copia o script de inicialização para o contêiner
COPY init.sh /init.sh

# Define o script de inicialização como executável
RUN chmod +x /init.sh

# Copiando todos os arquivos para a pasta src
COPY . /src
# Define o diretório de trabalho como /src
WORKDIR /src

# Expõe a porta 8502 (se necessário)
EXPOSE 8503

# Comando de inicialização para executar o script de inicialização
CMD ["/bin/bash", "/init.sh"]
