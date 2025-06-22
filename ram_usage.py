import time
import psutil
import os

def get_memory_info():
    # RAM principale
    virtual_mem = psutil.virtual_memory()
    used_ram_gb = virtual_mem.used / (1024 ** 3)
    total_ram_gb = virtual_mem.total / (1024 ** 3)

    # Cache Swap
    swap = psutil.swap_memory()
    used_swap_gb = swap.used / (1024 ** 3)

    return {
        "used_ram_gb": used_ram_gb,
        "total_ram_gb": total_ram_gb,
        "used_swap_gb": used_swap_gb
    }

def monitor(interval=5, log_file="ram_log.txt", duration=None):
    start_time = time.time()
    print("Monitoring RAM... Press Ctrl+C to stop.\n")
    with open(log_file, "w") as log:
        log.write("Time(s)\tUsed RAM (GB)\tTotal RAM (GB)\tSwap (GB)\n")

        try:
            while True:
                mem = get_memory_info()
                elapsed = time.time() - start_time

                line = f"{elapsed:.1f}\t{mem['used_ram_gb']:.2f}\t\t{mem['total_ram_gb']:.2f}\t\t{mem['used_swap_gb']:.2f}"
                print(line)
                log.write(line + "\n")

                time.sleep(interval)
                if duration and elapsed > duration:
                    break
        except KeyboardInterrupt:
            print("\nStopped.")

if __name__ == "__main__":
    monitor(interval=5)  # ogni 5 secondi
