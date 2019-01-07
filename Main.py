import os
from SICXE import SicXE
from SIC import Sic

path = os.path.abspath('.')
assembly_path = path + '\\assembly\\'
obfigure_path = path + '\\obfigure\\'
object_code_path = path + '\\object_code\\'

figure21 = Sic()
figure21.run(assembly_path + 'Figure2.1.txt', 'opcode.csv', object_code_path + 'object_code2.1.txt')
figure21.figure(obfigure_path + 'obfigure2.1.txt')

print('Figure2.1 Finish')

figure25 = SicXE()
figure25.run(assembly_path + 'Figure2.5.txt', 'opcode.csv', object_code_path + 'object_code2.5.txt')
figure25.figure(obfigure_path + 'obfigure2.5.txt')

print('Figure2.5 Finish')

figure29 = SicXE()
figure29.run(assembly_path + 'Figure2.9.txt', 'opcode.csv', object_code_path + 'object_code2.9.txt')
figure29.figure(obfigure_path + 'obfigure2.9.txt')

print('Figure2.9 Finish')

figure211 = SicXE()
figure211.run(assembly_path + 'Figure2.11.txt', 'opcode.csv', object_code_path + 'object_code2.11.txt')
figure211.figure(obfigure_path + 'obfigure2.11.txt')

print('Figure2.11 Finish')

figure215 = SicXE()
figure215.run(assembly_path + 'Figure2.15.txt', 'opcode.csv', object_code_path + 'object_code2.15.txt')
figure215.figure(obfigure_path + 'obfigure2.15.txt')

print('Figure2.15 Finish')

