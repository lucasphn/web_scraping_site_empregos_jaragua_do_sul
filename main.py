import schedule
import time
from controller import InsertPostgress

def main():
    insert = InsertPostgress()
    insert.start()

# Agendando a execução nos horários desejados
schedule.every().day.at("09:00").do(main)
schedule.every().day.at("14:00").do(main)
schedule.every().day.at("16:00").do(main)

# Loop para manter o script em execução e verificar os agendamentos
while True:
    schedule.run_pending()
    time.sleep(60)  # Aguarda 60 segundos antes de verificar novamente

#main()