import os
import io
import imaplib
import email
import requests
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from email.utils import parsedate_to_datetime
import logging
from logging.handlers import RotatingFileHandler

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# --------------- CONFIGURAÇÕES ---------------



# Carrega variáveis do .env (por padrão procura na raiz do projeto)
load_dotenv()

# Agora recupera cada variável
IMAP_SERVER     = os.getenv('IMAP_SERVER')
EMAIL_ACCOUNT   = os.getenv('EMAIL_ACCOUNT')
EMAIL_PASSWORD  = os.getenv('EMAIL_PASSWORD')
FROM_SENDER     = os.getenv('FROM_SENDER')
LOG_FILE        = os.getenv('LOG_FILE')
DRIVE_FOLDER_ID = os.getenv('DRIVE_FOLDER_ID')


ARQUIVOS_DIR = "Arquivos"
if not os.path.exists(ARQUIVOS_DIR):
    os.makedirs(ARQUIVOS_DIR, exist_ok=True)

CREDENTIALS_JSON = os.path.join(ARQUIVOS_DIR, "credentials.json")
MYCREDS_TXT = os.path.join(ARQUIVOS_DIR, "mycreds.txt")

# Colunas fixas na ordem desejada
fixed_columns = [
    "Loja (ID)",
    "Loja (Nome)",
    "Cliente (ID)",
    "Cliente (Nome)",
    "Cliente (Telefone)",
    "Data da Venda",
    "Valor",
    "Recorrências",
    "Pontos",
    "Atendente",
    "TAG"
]

# --------------- CONFIGURAÇÃO DO LOGGING ---------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = RotatingFileHandler(os.path.join(ARQUIVOS_DIR, LOG_FILE), maxBytes=5*1024*1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(formatter)
logger.addHandler(console)

# --------------- FUNÇÕES AUXILIARES ---------------

def get_drive_service():
    logger.info("Autenticando no Google Drive...")
    gauth = GoogleAuth()
    if os.path.exists(CREDENTIALS_JSON):
        gauth.LoadClientConfigFile(CREDENTIALS_JSON)
    else:
        logger.error("credentials.json não encontrado na pasta 'Arquivos'.")
        return None

    if os.path.exists(MYCREDS_TXT):
        gauth.LoadCredentialsFile(MYCREDS_TXT)
    else:
        gauth.LocalWebserverAuth()

    if gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()

    gauth.SaveCredentialsFile(MYCREDS_TXT)
    return GoogleDrive(gauth)

def download_file_from_drive(file_name):
    """Tenta baixar o arquivo com nome file_name do Drive.
       Retorna o caminho local do arquivo baixado ou None se não encontrado."""
    drive = get_drive_service()
    if not drive:
        return None

    query = f"title='{file_name}' and trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()

    if not file_list:
        logger.info(f"Arquivo '{file_name}' não encontrado no Google Drive.")
        return None

    file_drive = file_list[0]
    local_path = os.path.join(ARQUIVOS_DIR, file_name)
    file_drive.GetContentFile(local_path)
    logger.info(f"Arquivo '{file_name}' baixado do Google Drive com sucesso.")
    return local_path

def upload_to_drive(file_path, file_name, folder_id=None):
    logger.info("Enviando arquivo atualizado ao Google Drive...")
    drive = get_drive_service()
    if not drive:
        return

    # Apaga arquivos com o mesmo nome para evitar duplicatas
    query = f"title='{file_name}' and trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()
    for f in file_list:
        f.Delete()

    file = drive.CreateFile({"title": file_name})
    if folder_id:
        file['parents'] = [{"id": folder_id}]
    file.SetContentFile(file_path)
    file.Upload()
    logger.info(f"Arquivo '{file_name}' enviado com sucesso ao Google Drive!")

def get_emails_since(start_date_str):
    logger.info("Conectando ao servidor IMAP...")
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    except imaplib.IMAP4.error as e:
        logger.error(f"Falha na autenticação IMAP: {e}")
        return []
    except Exception as e:
        logger.error(f"Erro inesperado na conexão IMAP: {e}")
        return []

    logger.info("Selecionando a pasta 'RADAR'...")
    status, _ = mail.select("RADAR")
    if status != 'OK':
        logger.error("Não foi possível selecionar a pasta RADAR.")
        mail.logout()
        return []

    logger.info(f"Buscando emails do remetente '{FROM_SENDER}' a partir de '{start_date_str}'...")
    status, message_ids = mail.search(None, f'(FROM "{FROM_SENDER}" SINCE "{start_date_str}")')

    if status != 'OK':
        logger.error("Erro ao buscar emails.")
        mail.close()
        mail.logout()
        return []

    if not message_ids[0]:
        logger.warning("Não foi encontrado nenhum email nesse período/pasta.")
        mail.close()
        mail.logout()
        return []

    msg_id_list = message_ids[0].split()
    all_messages = []
    for msg_id in msg_id_list:
        try:
            status, msg_data = mail.fetch(msg_id, '(RFC822)')
            if status == 'OK' and msg_data and msg_data[0]:
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                all_messages.append(msg)
            else:
                logger.warning(f"Não foi possível fazer fetch do email ID: {msg_id}")
        except Exception as e:
            logger.error(f"Erro ao buscar o email ID {msg_id}: {e}")

    mail.close()
    mail.logout()

    logger.info(f"Total de {len(all_messages)} emails obtidos." if all_messages else "Nenhuma mensagem completa obtida.")
    return all_messages

def extract_html_content(msg):
    for part in msg.walk():
        ctype = part.get_content_type()
        if ctype == "text/html":
            try:
                return part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='replace')
            except Exception as e:
                logger.error(f"Falha ao decodificar HTML: {e}")
    return None

def extract_csv_link_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    link_tag = soup.find('a', string="Baixar CSV")
    if link_tag and link_tag.get('href'):
        return link_tag['href']
    return None

def download_csv_from_link(csv_url):
    try:
        response = requests.get(csv_url, timeout=30)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logger.error(f"Falha ao baixar CSV do link: {e}")
        return None

def unify_columns(df_existing, df_new):
    all_columns = set(df_existing.columns) | set(df_new.columns)
    # Garante a presença da coluna TAG
    all_columns = all_columns.union({"TAG"})

    df_existing = df_existing.reindex(columns=all_columns)
    df_new = df_new.reindex(columns=all_columns)

    return df_existing, df_new

def main():
    logger.info("Início da execução do script.")
    
    # Data do dia atual (se quiser o dia anterior, ajuste para -1 dia se necessário)
    hoje = datetime.now() #- timedelta(days=2)
    start_date_str = hoje.strftime("%d-%b-%Y")
    mes_ano = hoje.strftime('%Y_%m')  # Ex: 2024_12
    nome_arquivo = f"RADAR_{mes_ano}.xlsx"
    file_path = os.path.join(ARQUIVOS_DIR, nome_arquivo)

    # Tenta baixar o arquivo do Drive antes de ler localmente
    downloaded_path = download_file_from_drive(nome_arquivo)
    if downloaded_path and os.path.exists(downloaded_path):
        file_path = downloaded_path
        logger.info(f"Arquivo mensal '{file_path}' carregado do Drive com sucesso.")
        try:
            df_existente = pd.read_excel(file_path)
        except Exception as e:
            logger.error(f"Falha ao carregar o arquivo existente '{file_path}': {e}")
            df_existente = pd.DataFrame(columns=["TAG"])
    else:
        # Não existe arquivo no Drive para este mês, cria um DF vazio com TAG
        df_existente = pd.DataFrame(columns=["TAG"])
        logger.info("Nenhum arquivo mensal existente no Drive. Será criado um novo DataFrame.")

    messages = get_emails_since(start_date_str)
    if not messages:
        logger.warning("Nenhum email obtido hoje. Encerrando execução.")
        return

    all_dfs = []

    for i, msg in enumerate(messages, start=1):
        logger.info(f"Processando email {i} de {len(messages)}")
        html_content = extract_html_content(msg)
        if not html_content:
            logger.warning(f"Não foi possível extrair HTML do email {i}. Pulando este email.")
            continue

        csv_url = extract_csv_link_from_html(html_content)
        if csv_url:
            csv_data = download_csv_from_link(csv_url)
            if csv_data:
                try:
                    df_csv = pd.read_csv(io.BytesIO(csv_data), sep=',')
                    all_dfs.append(df_csv)
                    logger.info(f"CSV do email {i} processado com sucesso!")
                except Exception as e:
                    logger.error(f"Falha ao ler CSV do email {i}: {e}")
            else:
                logger.warning(f"Não foi possível baixar o CSV do email {i}.")
        else:
            logger.warning(f"Nenhum link para CSV encontrado no email {i}.")

    if all_dfs:
        try:
            df_novos = pd.concat(all_dfs, ignore_index=True)
            
            # Unifica colunas e garante coluna TAG
            df_existente, df_novos = unify_columns(df_existente, df_novos)
            
            df_final = pd.concat([df_existente, df_novos], ignore_index=True)

            # Reindexa para garantir a ordem das colunas
            df_final = df_final.reindex(columns=fixed_columns)

            try:
                df_final.to_excel(file_path, index=False)
                logger.info(f"Arquivo '{file_path}' atualizado com sucesso.")

                # Sobe para o Google Drive
                upload_to_drive(file_path, nome_arquivo, folder_id=DRIVE_FOLDER_ID)

            except Exception as e:
                logger.error(f"Falha ao salvar ou enviar o arquivo Excel: {e}")
        except Exception as e:
            logger.error(f"Falha ao concatenar DataFrames: {e}")
    else:
        logger.warning("Nenhum CSV foi encontrado para combinar hoje.")

    logger.info("Execução do script finalizada.")

if __name__ == "__main__":
    main()
