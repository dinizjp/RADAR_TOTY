# RADAR

## Descrição
O projeto RADAR é um script Python que realiza a leitura de emails na caixa "RADAR", buscando mensagens do remetente "radar@toty.app". Ele extrai links para download de arquivos CSV enviados em mensagens HTML, faz o download dos arquivos, concatena os dados ao arquivo de controle mensal em Excel e mantém esse arquivo atualizado no Google Drive. O sistema une as colunas sem duplicatas e garante a inclusão de uma coluna TAG padrão, realizando autenticações automatizadas via Google Drive API.

## Sumário
- [Dependências](#dependências)
- [Instalação](#instalação)
- [Uso](#uso)
- [Estrutura de Pastas](#estrutura-de-pastas)

## Dependências
- requests
- pandas
- beautifulsoup4
- pydrive
- openpyxl

## Instalação
1. Clone ou baixe o repositório.
2. Execute o comando abaixo para instalar as dependências:
```bash
pip install -r requirements.txt
```

## Uso
Execute o script `Radar.py` para realizar o processo completo de leitura de emails, download de CSV, concatenação e atualização do arquivo Excel tanto localmente quanto no Google Drive:

```bash
python Radar.py
```

## Estrutura de Pastas
```plaintext
RAIZ/
│
├── Radar.py
├── requirements.txt
└── Arquivos/
    ├── credentials.json
    ├── mycreds.txt
    └── Radar.log
```

**Observação:** Certifique-se de que os arquivos `credentials.json` e `mycreds.txt` estejam presentes na pasta `Arquivos` e estejam corretamente configurados para garantir a autenticação com o Google Drive.