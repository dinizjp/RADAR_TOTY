#!/bin/bash

# Registrar info no log do cron
LOG_CRON="/home/dinizjp/scripts/RADAR/radar_automation_cron.log"

echo "----- Iniciando Script -----" >> "$LOG_CRON"
echo "Data: $(date)" >> "$LOG_CRON"
echo "Usuário: $(whoami)" >> "$LOG_CRON"
echo "PATH: $PATH" >> "$LOG_CRON"

# Navegar até o diretório do projeto
cd /home/dinizjp/scripts/RADAR || {
  echo "Falha ao acessar o diretório" >> "$LOG_CRON"
  exit 1
}

# Executar o script Python usando o Python do ambiente virtual
/home/dinizjp/scripts/RADAR/venv/bin/python Radar.py >> "$LOG_CRON" 2>&1 || {
  echo "Falha ao executar o script Python" >> "$LOG_CRON"
  exit 1
}

echo "----- Script Finalizado -----" >> "$LOG_CRON"


