import sys
import subprocess

def install_required_packages():
    required_packages = ['aiohttp', 'colorama', 'tqdm']
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing {package}...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"{package} installed successfully!")
            except subprocess.CalledProcessError as e:
                print(f"Error installing {package}: {e}")
                sys.exit(1)

try:
    install_required_packages()
except Exception as e:
    print(f"Error during package installation: {e}")
    sys.exit(1)

import os  
import time  
import asyncio  
import aiohttp  
import argparse  
from tqdm import tqdm  
from colorama import init, Fore  
from datetime import datetime

init()

def tampilkan_logo():
    logo = """
    ██╗░░░██╗███╗░░░███╗░█████╗░██████╗░
    ██║░░░██║████╗░████║██╔══██╗██╔══██╗
    ██║░░░██║██╔████╔██║███████║██████╔╝
    ██║░░░██║██║╚██╔╝██║██╔══██║██╔══██╗
    ╚██████╔╝██║░╚═╝░██║██║░░██║██║░░██║
    ░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░╚═╝╚═╝░░╚═╝
     Proxy Formater & Protocol Detector
        Version: 1.0 | Author: UMAR
             t.me/UmarAlAtsary
    """
    print(f"{Fore.WHITE}{logo}{Fore.RESET}")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def tampilkan_menu():
    clear_screen()
    tampilkan_logo()
    print(f"\n{Fore.CYAN}═══ Main Menu ═══{Fore.RESET}")
    print(f"1. Auto Format (Check Protocol)")
    print(f"2. Single Protocol Format")
    print(f"{Fore.CYAN}═════════════════{Fore.RESET}")
    return input(f"{Fore.YELLOW}Select menu [1-2]: {Fore.RESET}")

def tampilkan_submenu():
    print(f"\n{Fore.CYAN}═══ Protocol Selection ═══{Fore.RESET}")
    print("1. HTTP")
    print("2. HTTPS")
    print("3. SOCKS4")
    print("4. SOCKS5")
    print(f"{Fore.CYAN}════════════════════════{Fore.RESET}")
    return input(f"{Fore.YELLOW}Select protocol [1-4]: {Fore.RESET}")

async def check_proxy(session, protokol, ip, port):
    """Cek proxy dengan protokol tertentu"""
    url = 'http://httpbin.org/ip'
    proxy = f"{protokol}://{ip}:{port}"
    
    try:
        async with session.get(url, proxy=proxy, timeout=60) as response:
            if response.status == 200:
                return protokol
    except aiohttp.ClientError:
        return None
    except asyncio.TimeoutError:
        return None
    except Exception as e:
        log_error(f"Error checking proxy {proxy}: {str(e)}")
        return None

async def deteksi_protokol_proxy(ip, port):
    """Deteksi protokol proxy yang berfungsi"""
    protokol_tersedia = ['http', 'https', 'socks4', 'socks5']
    
    async with aiohttp.ClientSession() as session:
        tasks = [check_proxy(session, p, ip, port) for p in protokol_tersedia]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for protokol in results:
            if protokol:
                return protokol
    
    return 'http'

async def format_proxy(proxy):
    """Format proxy menjadi protokol://user:pass@ip:port atau protokol://ip:port"""
    try:
        if not validasi_proxy(proxy):
            return ''
            
        proxy = proxy.strip()
        bagian = proxy.split(':')
        
        if len(bagian) == 4:  # ip:port:user:pass
            ip, port, user, password = bagian
            credentials = f"{user}:{password}@"
        elif len(bagian) == 2:  # ip:port
            ip, port = bagian
            credentials = ''
        elif len(bagian) == 3:  # ip:port:user
            ip, port, user = bagian
            credentials = f"{user}@"
        else:
            return ''

        protokol = await deteksi_protokol_proxy(ip, port)
        return f"{protokol}://{credentials}{ip}:{port}"

    except Exception as e:
        log_error(f"Error formatting proxy {proxy}: {str(e)}")
        return ''

async def process_proxies(proxies, max_concurrent=1000):
    """Proses multiple proxy dengan progress bar modern"""
    semaphore = asyncio.Semaphore(max_concurrent)
    total = len(proxies)
    success_count = 0
    failed_count = 0
    
    pbar = tqdm(
        total=total,
        desc=f"{Fore.CYAN}Progress{Fore.RESET}",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
        ncols=75
    )
    
    async def process_single(proxy):
        nonlocal success_count, failed_count
        async with semaphore:
            result = await format_proxy(proxy)
            if result:
                success_count += 1
                pbar.set_postfix(
                    success=f"{Fore.GREEN}{success_count}{Fore.RESET}", 
                    failed=f"{Fore.RED}{failed_count}{Fore.RESET}"
                )
            else:
                failed_count += 1
                pbar.set_postfix(
                    success=f"{Fore.GREEN}{success_count}{Fore.RESET}", 
                    failed=f"{Fore.RED}{failed_count}{Fore.RESET}"
                )
            pbar.update(1)
            return result
    
    tasks = [process_single(proxy) for proxy in proxies]
    results = await asyncio.gather(*tasks)
    pbar.close()
    return [r for r in results if r]
    
async def format_proxy_single(proxy, protocol):
    """Format proxy dengan protokol tunggal"""
    try:
        proxy = proxy.strip()
        bagian = proxy.split(':')
        
        if len(bagian) == 4:  # ip:port:user:pass
            ip, port, user, password = bagian
            credentials = f"{user}:{password}@"
        elif len(bagian) == 2:  # ip:port
            ip, port = bagian
            credentials = ''
        elif len(bagian) == 3:  # ip:port:user
            ip, port, user = bagian
            credentials = f"{user}@"
        else:
            return ''

        if not port.isdigit() or not (0 < int(port) <= 65535):
            return ''

        return f"{protocol}://{credentials}{ip}:{port}"

    except Exception:
        return ''

async def process_proxies_single(proxies, protocol, max_concurrent=1000):
    """Proses proxy dengan protokol tunggal"""
    semaphore = asyncio.Semaphore(max_concurrent)
    total = len(proxies)
    success_count = 0
    failed_count = 0
    
    pbar = tqdm(
        total=total,
        desc=f"{Fore.CYAN}Progress{Fore.RESET}",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
        ncols=75
    )
    
    async def process_single(proxy):
        nonlocal success_count, failed_count
        async with semaphore:
            result = await format_proxy_single(proxy, protocol)
            if result:
                success_count += 1
                pbar.set_postfix(
                    success=f"{Fore.GREEN}{success_count}{Fore.RESET}", 
                    failed=f"{Fore.RED}{failed_count}{Fore.RESET}"
                )
            else:
                failed_count += 1
                pbar.set_postfix(
                    success=f"{Fore.GREEN}{success_count}{Fore.RESET}", 
                    failed=f"{Fore.RED}{failed_count}{Fore.RESET}"
                )
            pbar.update(1)
            return result
    
    tasks = [process_single(proxy) for proxy in proxies]
    results = await asyncio.gather(*tasks)
    pbar.close()
    return [r for r in results if r]

def validasi_proxy(proxy):
    """Validasi format proxy"""
    try:
        bagian = proxy.split(':')
        if len(bagian) not in [2, 3, 4]:
            return False
            
        ip = bagian[0]
        port = bagian[1]
        
        # Validasi IP
        ip_parts = ip.split('.')
        if len(ip_parts) != 4:
            return False
        for part in ip_parts:
            if not part.isdigit() or not (0 <= int(part) <= 255):
                return False
                
        # Validasi Port
        if not port.isdigit() or not (0 < int(port) <= 65535):
            return False
            
        return True
    except:
        return False

def log_error(error_msg):
    with open('error.log', 'a') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f'[{timestamp}] {error_msg}\n')

def buka_file(filename):
    if os.name == 'nt':  # Windows
        os.system(f'notepad {filename}')
    else:  # Linux/Mac/Termux
        os.system(f'cat {filename}')

async def main(input_file, output_file, max_concurrent):
    try:
        while True:
            pilihan = tampilkan_menu()
            
            if pilihan not in ['1', '2']:
                print(f"{Fore.RED}[Error] Pilihan tidak valid!{Fore.RESET}")
                continue
                
            if not os.path.exists(input_file):
                print(f"{Fore.RED}[Error] File {input_file} tidak ditemukan!{Fore.RESET}")
                return

            try:
                with open(input_file, 'r') as f:
                    proxies = [line.strip() for line in f if line.strip()]
                
                if not proxies:
                    print(f"{Fore.RED}[Error] File input kosong!{Fore.RESET}")
                    return

                print(f"\n{Fore.YELLOW}[Info] Memproses {len(proxies)} proxy...{Fore.RESET}\n")
                
                # Animasi loading
                with tqdm(total=100, desc="Initializing", bar_format="{l_bar}{bar}| {n_fmt}%") as pbar:
                    for i in range(100):
                        time.sleep(0.01)
                        pbar.update(1)
                print("\n")
                
                if pilihan == '1':
                    results = await process_proxies(proxies, max_concurrent)
                else:
                    protocol_choice = tampilkan_submenu()
                    protocol_map = {
                        '1': 'http',
                        '2': 'https',
                        '3': 'socks4',
                        '4': 'socks5'
                    }
                    
                    if protocol_choice not in protocol_map:
                        print(f"{Fore.RED}[Error] Pilihan protokol tidak valid!{Fore.RESET}")
                        continue
                        
                    protocol = protocol_map[protocol_choice]
                    results = await process_proxies_single(proxies, protocol, max_concurrent)
                
                # Animasi saving
                print("\n")
                with tqdm(total=100, desc="Saving results", bar_format="{l_bar}{bar}| {n_fmt}%") as pbar:
                    for i in range(100):
                        time.sleep(0.01)
                        pbar.update(1)
                
                with open(output_file, 'w') as f:
                    f.write('\n'.join(results))
                
                # Tampilkan ringkasan
                print(f"\n{Fore.CYAN}═══ Summary ═══{Fore.RESET}")
                print(f"Total Proxy    : {len(proxies)}")
                print(f"Success        : {Fore.GREEN}{len(results)}{Fore.RESET}")
                print(f"Failed         : {Fore.RED}{len(proxies) - len(results)}{Fore.RESET}")
                print(f"Success Rate   : {Fore.YELLOW}{(len(results)/len(proxies)*100):.1f}%{Fore.RESET}")
                print(f"{Fore.CYAN}═══════════════{Fore.RESET}")
                
                # Tanya apakah ingin membuka file hasil
                buka = input(f"\n{Fore.YELLOW}Open result file? (y/n): {Fore.RESET}").lower()
                if buka == 'y':
                    buka_file(output_file)
                
                # Tanya apakah ingin melanjutkan
                lanjut = input(f"\n{Fore.YELLOW}Process another? (y/n): {Fore.RESET}").lower()
                if lanjut != 'y':
                    break

            except Exception as e:
                log_error(f"Main process error: {str(e)}")
                print(f"{Fore.RED}Error: {str(e)}{Fore.RESET}")
                break
                
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[Info] Program dihentikan oleh user{Fore.RESET}")
        return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Proxy Formatter & Protocol Detector')
    parser.add_argument('-w', '-W', '--workers', type=int, default=5,
                       help='Jumlah concurrent tasks (default: 5)')
    parser.add_argument('-i', '--input', type=str, default='inproxy.txt',
                       help='File input proxy (default: inproxy.txt)')
    parser.add_argument('-o', '--output', type=str, default='outproxy.txt',
                       help='File output proxy (default: outproxy.txt)')
    args = parser.parse_args()

    asyncio.run(main(args.input, args.output, args.workers))
