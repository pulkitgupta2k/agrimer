from helper import *
import time

if __name__ == "__main__":
    while True:
        get_all_details()
        gsheet_load()
        print("sleeping...")
        time.sleep(86400)