FROM python:3.12

# Copia o arquivo de requisitos e instala as dependências
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# Copia todo o conteúdo do diretório atual para o diretório /src no contêiner
COPY . /src

# Define o diretório de trabalho como /src
WORKDIR /src

# Expõe a porta 8502 (se necessário)
EXPOSE 8503

# Comando de inicialização para executar o seu script Python
CMD ["python", "main.py"]
