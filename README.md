# RADAR

## Descrição
O projeto RADAR é um script Python que automiza a coleta e atualização de dados através de emails recebidos, processa esses dados em arquivos Excel, e sincroniza-os com o Google Drive. O sistema busca emails específicos, extrai links de CSVs presentes em conteúdo HTML, faz download e consolida esses dados em um arquivo mensal, que é armazenado e atualizado automaticamente no Google Drive.

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
Execute os seguintes passos para instalar as dependências necessárias do projeto:
```bash
pip install -r requirements.txt
```

## Uso
O script principal é o `Radar.py`. Para executar o RADAR, utilize o comando:
```bash
python Radar.py
```
Para automatizar a execução via cron, utilize o script `radar_automation.sh`. Certifique-se de que o ambiente virtual está ativo e execute:
```bash
bash radar_automation.sh
```

## Estrutura de Pastas
```plaintext
radar/
├── Radar.py
├── requirements.txt
├── radar_automation.sh
└── Arquivos/
    └── (arquivos gerados, como credentials.json, mycreds.txt, logs, e arquivos Excel)
```