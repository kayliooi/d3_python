import os
import subprocess
import time


# Define Instances 
instances = ["impl0", "impl1", "impl2", "impl3", "impl4", "impl5"]

class Uad():
  def __init__(self, inst):
    self.inst = inst

  def reset(self):
    return os.system(f'{self.inst} com --action reset')

  def disable(self):
    return os.system(f'{self.inst} com --action disable')

  def enable(self):
    return os.system(f'{self.inst} com --action enable')

  def read_CSR(self):
    try:
      csr_bytes = subprocess.check_output([f'./{self.inst}.exe', 'cfg', '--address', '0x0'])
      csr_str = csr_bytes.decode().strip()
      # csr_bytes = subprocess.check_output(f'./{self.inst} cfg --address 0x0')
      return int(csr_bytes, 0)
    except subprocess.CalledProcessError as e: 
      print(f"[{self.inst}] CSR read failed: {e.output.decode().strip()}") 
      return None

  def write_CSR(self):
      return os.system(f'{self.inst}.exe --address 0x0 --data {hex(value)}')

def drive_signal(unit, value, count=1, silent=True): 
  for _ in range(count): 
    cmd = f"{unit}.exe sig --data {hex(value)}" 
    if silent: 
      subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL) 
    else: 
      os.system(cmd) # optional delay for hardware latching 
      time.sleep(0.001)

def test_enable_disable(ip): 
  print(f"\n[{ip.inst}] Testing enable/disable...")
  ip.reset()
  ip.enable()
  print("CSR after enable:", hex(ip.read_CSR())) 
  ip.disable() 
  csr_val = ip.read_CSR()
  if csr_val is None: 
    print("CSR unavailable after disable (expected).") 
  else:
    print("CSR after disable:", hex(csr_val))
  # print("CSR after disable:", hex(ip.read_CSR()))

def test_bypass(ip):
    ip.reset()
    print(f"\n[{ip.inst}] Testing bypass...")
  
    # Read current CSR
    csr_val = ip.read_CSR()
    if csr_val is None:
        print(f"[{ip.inst}] Cannot read CSR")
        return

    csr_val &= ~(1 << 5)         # HALT = 0
    csr_val &= ~(1 << 0)         # FEN = 0 (bypass)

    # Write back updated CSR
    os.system(f'{ip.inst}.exe cfg --address 0x0 --write {hex(csr_val)}')
    print(f"[{ip.inst}] Bypass mode activated (CSR={hex(csr_val)})")

    input_val = 0xC0
    output = os.popen(f"{ip.inst}.exe sig --data {hex(input_val)}").read().strip()

    if int(output, 16) == input_val:
        print(f"[BYPASS] PASS (output = {output})")
    else:
        print(f"[BYPASS] FAIL (output = {output})")

def test_buffer(ip):
  print(f"\n[{ip.inst}] Testing buffer...")

  ip.reset()
  
  ip.enable()
  
  # ---- HALT AND ENABLE COEFFICIENT ----
  csr_val = ip.read_CSR()
  csr_val |= (1 << 5)          # HALT = 1
  csr_val |= (0b1111 << 1)     #enable coefficient
  os.system(f'{ip.inst}.exe cfg --address 0x0 --write {hex(csr_val)}')

  # ---- CLEAR BUFFER  ----
  csr_val = ip.read_CSR()
  csr_val |= (1 << 17)         # IBCLR = 1
  os.system(f'{ip.inst}.exe cfg --address 0x0 --write {hex(csr_val)}')

  csr_val = ip.read_CSR()
  csr_val &= ~(1 << 17)        #IBCLR = 0
  os.system(f'{ip.inst}.exe cfg --address 0x0 --write {hex(csr_val)}')


  csr_val = ip.read_CSR()
  ibcnt = (csr_val >> 8) & 0xFF
  print(f"[CLEAR] IBCNT after clear before sampling = {ibcnt}")

  # --- SAMPLE 5 INPUT SIGNALS ---
  drive_signal(ip.inst, 0xC0, count=5)

  # ---- READ INPUT BUFFER COUNT ----
  csr_val = ip.read_CSR()
  ibcnt = (csr_val >> 8) & 0xFF
  print(f"[HALT] IBCNT after 5 samples = {ibcnt}")
  
  # ---- OVERFLOW TEST ----
  drive_signal(ip.inst, 0xC0, count=260)
  print("After driving 260 input signals")
  csr_val = ip.read_CSR()
  ibovf = (csr_val >> 16) & 1
  print(f"[OVERFLOW] IBOVF = {ibovf}")

  # --- READ INPUT BUFFER COUNT AGAIN ----
  csr_val = ip.read_CSR()
  csr_val |= (1 << 17)         # IBCLR = 1
  os.system(f'{ip.inst}.exe cfg --address 0x0 --write {hex(csr_val)}')

  csr_val = ip.read_CSR()
  csr_val &= ~(1 << 17)
  os.system(f'{ip.inst}.exe cfg --address 0x0 --write {hex(csr_val)}')

  csr_val = ip.read_CSR()
  ibcnt = (csr_val >> 8) & 0xFF
  print(f"[CLEAR] IBCNT after clear after 260 input signals = {ibcnt}")


if __name__ == "__main__": 
  for name in instances: 
    ip = Uad(name)
    test_enable_disable(ip) 
    test_bypass(ip) 
    test_buffer(ip)

