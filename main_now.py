import schedule
import time
from controller import InsertPostgress

def main():
    insert = InsertPostgress()
    insert.start()


main()