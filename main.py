import os
import subprocess

class Uad():
  def __init__(self):
    self.inst = None

  def reset(self):
    return os.system(f'{self.inst} com --action reset')

  def disable(self):
    return os.system(f'{self.inst} com --action disable')

  def enable(self):
    return os.system(f'{self.inst} com --action enable')

  def read_CSR(self):
    csr_bytes = subprocess.check_output(f'./{self.inst} cfg --address 0x0')
    return int(csr_bytes, 0)

test0 = Uad()

test0.inst = "impl0"

test0.reset()
test0.enable()

print(hex(test0.read_CSR()))
