import tkinter as tk
from tkinter import messagebox, filedialog
import hashlib
import struct
import random
import threading
from collections import Counter
import zlib

# List to store tuples of (PID, Friend Code) with repeating numbers or many zeros
valid_friend_codes = []

def calculate_friend_code(pid):
    if not (0 <= pid < 2**32):
        raise ValueError("PID must be a 32-bit integer (0 to 4294967295).")
    game_id = "JCMR"
    data_block = struct.pack('<I', pid) + game_id.encode('utf-8')
    md5_hash = hashlib.md5(data_block).digest()
    checksum_byte = (md5_hash[0] >> 1) & 0x7F
    fc_decimal = (checksum_byte << 32) | pid
    friend_code = f"{fc_decimal:012d}"
    formatted_friend_code = f"{friend_code[:4]}-{friend_code[4:8]}-{friend_code[8:]}"
    return formatted_friend_code

def friend_code_to_pid(friend_code):
    if len(friend_code) != 14 or friend_code[4] != '-' or friend_code[9] != '-':
        raise ValueError("Friend code must be in the format XXXX-YYYY-ZZZZ.")
    cleaned_code = friend_code.replace("-", "")
    friend_code_int = int(cleaned_code)
    pid = friend_code_int & 0xFFFFFFFF
    return pid

def calculate_pid():
    friend_code = entry_friend_code.get()
    try:
        pid = friend_code_to_pid(friend_code)
        result_label.config(text=f"PID: {pid}")
    except ValueError as ve:
        messagebox.showerror("Input Error", str(ve))

def calculate_friend_code_from_pid():
    pid = entry_pid.get()
    try:
        pid_int = int(pid)
        friend_code = calculate_friend_code(pid_int)
        result_friend_code_label.config(text=f"Friend Code: {friend_code}")
    except ValueError as ve:
        messagebox.showerror("Input Error", str(ve))

def generate_random_pid():
    random_pid = random.randint(0, 2**32 - 1)  # Generate a random 32-bit integer
    entry_pid.delete(0, tk.END)  # Clear the current entry
    entry_pid.insert(0, str(random_pid))  # Insert the generated PID

def show_credits():
    credits_text = "dev by nervosa and day\nver 1.0\nthanx 4 using :D "
    messagebox.showinfo("credits", credits_text)

# Function to check if a friend code has 9 or more zeros or a digit repeated at least 9 times
def has_repeating_numbers_or_zeros(friend_code):
    digits = friend_code.replace("-", "")  # Remove hyphens for counting
    digit_count = Counter(digits)

    # Check if any digit appears 10 or more times
    for digit, count in digit_count.items():
        if count >= 10:
            return True

    # Also check if there are at least 8 zeros
    if digit_count['0'] >= 9:
        return True

    return False

def brute_force_pids():
    global valid_friend_codes
    valid_friend_codes = []  # Clear previous list
    total_pids = 1000000  # Number of PIDs to brute-force
    found_codes = 0
    for _ in range(total_pids):
        pid = random.randint(0, 999999999)  # Generate a random PID between 0 and 999999999
        friend_code = calculate_friend_code(pid)
        if has_repeating_numbers_or_zeros(friend_code):  # Check for repeating numbers or zeros
            valid_friend_codes.append((pid, friend_code))  # Store (PID, Friend Code)
            found_codes += 1
        # Optionally, limit the number of valid codes found
        if found_codes >= 50:  # Stop after finding 50 valid codes (adjust as needed)
            break
    messagebox.showinfo("Brute Force", f"Brute force complete! Found {found_codes} Friend Codes with 9+ repeating digits or 8+ zeros.")

def start_brute_force():
    brute_force_thread = threading.Thread(target=brute_force_pids)
    brute_force_thread.start()

def show_friend_codes():
    if valid_friend_codes:
        friend_codes_str = "\n".join([f"PID: {pid}, Friend Code: {fc}" for pid, fc in valid_friend_codes])
        messagebox.showinfo("Friend Codes with 10+ repeating digits or 9+ zeros", friend_codes_str)
    else:
        messagebox.showinfo("Friend Codes", "No valid Friend Codes found yet.")

# Function to calculate CRC32 (ISO-HDLC)
def calculate_crc32(raw_bytes):
    crc_value = zlib.crc32(raw_bytes) & 0xFFFFFFFF  # Keep it within 32 bits
    return crc_value

def process_file_data(file_path):
    # Read the specified bytes from the file (0x40 to 0x7B)
    with open(file_path, 'rb') as file:
        file.seek(0x40)  # Seek to the 0x40 position
        raw_values = file.read(0x3C)  # Read 0x3C bytes (from 0x40 to 0x7B)

    # Convert to little-endian format
    little_endian_bytes = bytearray()
    for i in range(0, len(raw_values), 4):
        little_endian_bytes.extend(reversed(raw_values[i:i+4]))  # Reverse every 4 bytes for little-endian

    # Calculate CRC32
    crc_value = calculate_crc32(little_endian_bytes)

    # Write CRC value to the specified position (0x7C to 0x7F)
    with open(file_path, 'r+b') as file:
        file.seek(0x7C)  # Seek to the 0x7C position
        crc_bytes = struct.pack('<I', crc_value)[::-1]  # Reverse the bytes
        file.write(crc_bytes)  # Write the reversed CRC value

    return crc_value

def update_crc():
    file_path = filedialog.askopenfilename(title="Select RKP File", filetypes=[("RKP files", "*.rkp"), ("All files", "*.*")])
    if file_path:
        try:
            crc_value = process_file_data(file_path)
            result_crc_label.config(text=f"CRC-32: {crc_value:08X}")  # Display as hex
            messagebox.showinfo("Success", f"CRC-32 calculated and saved to 0x7C: {crc_value:08X}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

# Function to write a decimal number as hex to 0x5C-0x5F in RKP file
def write_hex_to_rkp():
    decimal_value = entry_decimal.get()
    try:
        decimal_value_int = int(decimal_value)

        # Ensure the value can fit in 4 bytes (32 bits)
        if not (0 <= decimal_value_int < 2**32):
            raise ValueError("Decimal number must fit in a 32-bit unsigned integer.")

        # Convert to 4-byte hex (little-endian)
        hex_value = struct.pack('<I', decimal_value_int)  # Little-endian 4-byte hex
        hex_value_reversed = hex_value[::-1]

        # Ask user to select an RKP file
        file_path = filedialog.askopenfilename(title="Select RKP File", filetypes=[("RKP files", "*.rkp"), ("All files", "*.*")])
        
        if file_path:
            with open(file_path, 'r+b') as file:
                file.seek(0x5C)  # Seek to 0x5C
                file.write(hex_value_reversed)  # Write the reversed 4-byte hex value

            messagebox.showinfo("Success", f"Decimal {decimal_value_int} written as hex to 0x5C-0x5F.")
    except ValueError as ve:
        messagebox.showerror("Input Error", str(ve))
    except Exception as e:
        messagebox.showerror("Error", str(e))

# Initialize the GUI
root = tk.Tk()
root.title("FCPID")
root.configure(bg='#E6E6FA')

# Main Frame
main_frame = tk.Frame(root, bg='#E6E6FA')
main_frame.pack(pady=20, padx=20)

# Friend Code Section
friend_code_frame = tk.LabelFrame(main_frame, text="Friend Code", bg='#E6E6FA', font=("Helvetica", 14))
friend_code_frame.pack(padx=10, pady=10, fill="both", expand=True)

instruction_label = tk.Label(friend_code_frame, text="Enter FC (XXXX-YYYY-ZZZZ):", bg='#E6E6FA', font=("Helvetica", 12))
instruction_label.pack(pady=5)

entry_friend_code = tk.Entry(friend_code_frame, width=20, font=("Helvetica", 12), bg='#FFFFFF', borderwidth=2, relief="groove")
entry_friend_code.pack(pady=5)

calculate_pid_button = tk.Button(friend_code_frame, text="Calculate PID", command=calculate_pid, font=("Helvetica", 12), bg='#7B68EE', fg='white', relief="raised")
calculate_pid_button.pack(pady=5)

result_label = tk.Label(friend_code_frame, text="", bg='#E6E6FA', font=("Helvetica", 12))
result_label.pack(pady=10)

# PID Section
pid_frame = tk.LabelFrame(main_frame, text="PID", bg='#E6E6FA', font=("Helvetica", 14))
pid_frame.pack(padx=10, pady=10, fill="both", expand=True)

instruction_label_pid = tk.Label(pid_frame, text="Enter PID (0-swag):", bg='#E6E6FA', font=("Helvetica", 12))
instruction_label_pid.pack(pady=5)

entry_pid = tk.Entry(pid_frame, width=20, font=("Helvetica", 12), bg='#FFFFFF', borderwidth=2, relief="groove")
entry_pid.pack(pady=5)

calculate_friend_code_button = tk.Button(pid_frame, text="fc calc", command=calculate_friend_code_from_pid, font=("Helvetica", 12), bg='#7B68EE', fg='white', relief="raised")
calculate_friend_code_button.pack(pady=5)

result_friend_code_label = tk.Label(pid_frame, text="", bg='#E6E6FA', font=("Helvetica", 12))
result_friend_code_label.pack(pady=10)

# Additional Features Frame
features_frame = tk.LabelFrame(main_frame, text="fc cool", bg='#E6E6FA', font=("Helvetica", 14))
features_frame.pack(padx=10, pady=10, fill="both", expand=True)

start_brute_force_button = tk.Button(features_frame, text="Start Brute Force", command=start_brute_force, font=("Helvetica", 12), bg='#7B68EE', fg='white', relief="raised")
start_brute_force_button.pack(pady=5)

show_friend_codes_button = tk.Button(features_frame, text="Show fc cool", command=show_friend_codes, font=("Helvetica", 12), bg='#7B68EE', fg='white', relief="raised")
show_friend_codes_button.pack(pady=5)

# CRC Update Frame
crc_frame = tk.LabelFrame(main_frame, text="rkp hex cool", bg='#E6E6FA', font=("Helvetica", 14))
crc_frame.pack(padx=10, pady=10, fill="both", expand=True)

update_crc_button = tk.Button(crc_frame, text="then click me", command=update_crc, font=("Helvetica", 12), bg='#7B68EE', fg='white', relief="raised")
update_crc_button.pack(pady=5)

entry_decimal = tk.Entry(crc_frame, width=20, font=("Helvetica", 12), bg='#FFFFFF', borderwidth=2, relief="groove")
entry_decimal.pack(pady=5)

write_hex_button = tk.Button(crc_frame, text="type pid in and click me", command=write_hex_to_rkp, font=("Helvetica", 12), bg='#7B68EE', fg='white', relief="raised")
write_hex_button.pack(pady=5)

result_crc_label = tk.Label(crc_frame, text="", bg='#E6E6FA', font=("Helvetica", 12))
result_crc_label.pack(pady=10)

# Move Credits button to the bottom of the GUI
show_credits_button = tk.Button(main_frame, text="Credits", command=show_credits, font=("Helvetica", 12), bg='#7B68EE', fg='white', relief="raised")
show_credits_button.pack(pady=10)

# Run the GUI
root.mainloop()





