import csv
import Arithmetic as A


class SicXE(object):
    """
    SICXE class
    """
    def __init__(self):
        """
        code structure: [location, block, symbol, operator, operand, program counter, object code]
        modify structure: [(string)]
        operator table: {operator: [opcode, format]}
        symbol table: {symbol: [symbol address, symbol block]}
        literal table: {ascii code: [operand, length, location, block, whether append in code]}
        block table:[0, block 0 location, block 1 location, ...], 0 index for absolutely term.
        register table: {register: register numbering}
        extdef: {external definition for external symbol: address}
        extref: [external reference(string)]
        base: base register
        main: whether this program is main program
        """
        self.__code = []
        self.__modify = []
        self.__operator_tab = {}
        self.__symbol_tab = {}
        self.__literal_tab = {}
        self.__extdef = {}
        self.__extref = []
        self.__block_tab = [0]
        self.__register_tab = {'A': '0', 'X': '1', 'L': '2', 'PC': '8', 'SW': '9',
                               'B': '3', 'S': '4', 'T': '5', 'F': '6'}
        self.__base = 0
        self.__start_address = 0
        self.__length = 0
        self.__main = True

    def run(self, code_file, op_file, ob_file):
        """
        run code and generate object code.
        :param code_file: assembly code file(.txt)
        :param op_file: operator file(.csv)
        :param ob_file: object code file(.txt)
        """
        self.__load_optab(op_file)
        self.__load_code(code_file)
        self.__main = True
        start = 0
        end = 0
        while self.__code[end][3] != 'END':
            temp, end, name = self.pass1(start)
            self.pass2(start)
            self.object_code(ob_file, start, temp, name)
            self.__symbol_tab.clear()
            self.__literal_tab.clear()
            self.__extdef.clear()
            self.__extref.clear()
            self.__modify.clear()
            self.__block_tab = [0]
            self.__base = 0
            self.__start_address = 0
            self.__length = 0
            self.__main = False
            start = temp

    def object_code(self, file_name, start, end, name):
        """
        put object code into object code file.
        object_t structure: [block, row start address, row length, object code]
        Algorithm:
        for i := 0 to code.length -1
            if object_t.length > 60 or address interrupt
                object_t next row

        write header into file
        for i := 0 to object_t.length -1
            write object_t[i] into file
        write end into file

        :param file_name: object code file(.txt).
        :param start: this program start index.
        :param end: this program end index.
        :param name: assembly code name.
        """
        TLENGTH = 60
        object_t = []
        first = True

        for index in range(start, end):
            # Text: T|row start address(6)|row length(2)|object code(60).
            if self.__code[index][3] == 'RESW' or self.__code[index][3] == 'RESB':
                # RESW and RESB interrupt continuous address.
                first = True

            ob_code = self.__code[index][6]
            loc = self.__code[index][0]
            block = self.__code[index][1]

            if ob_code != '':
                # has object code.
                if first:
                    # object_t generate new row.
                    object_t.append([block, self.__real_address(loc, block), 0, ''])
                    first = False

                if block != object_t[-1][0] or object_t[-1][2] * 2 + len(ob_code) > TLENGTH:
                    object_t.append([block, self.__real_address(loc, block), len(ob_code) // 2, '^' + ob_code])
                else:
                    object_t[-1][3] += '^' + ob_code
                    object_t[-1][2] += len(ob_code) // 2

        with open(file_name, 'a') as file:
            if self.__main:
                # if this program is main program then clear file content.
                file.seek(0, 0)
                file.truncate()

            # Header: H|file name(6)|begin address(6)|code length(6)
            file.write('H^' + name.ljust(6) + '^' +
                       A.output_hex(self.__start_address, 6) + '^' + A.output_hex(self.__length, 6) + '\n')

            if len(self.__extdef.keys()) > 0:
                n = 1
                j = 0
                for key in self.__extdef.keys():
                    # EXTDEF: D|(extdef(6)|extdef address(6)) * 6
                    if n == 1:
                        file.write('D^' + key.ljust(6) + '^' +
                                   A.output_hex(self.__real_address(self.__extdef[key][0], self.__extdef[key][1]), 6))
                        n += 1
                    else:
                        file.write('^' + key.ljust(6) + '^' +
                                   A.output_hex(self.__real_address(self.__extdef[key][0], self.__extdef[key][1]), 6))
                        n += 1

                    if n == 6 or j == len(self.__extdef.keys()) - 1:
                        # if n == 6 or last one then next row.
                        file.write('\n')
                        n = 1

                    j += 1

            if len(self.__extref) > 0:
                # EXTREF: R|exref(6) * 12
                n = 1
                j = 0
                for s in self.__extref:
                    if n == 1:
                        file.write('R^' + s.ljust(6))
                        n += 1
                    else:
                        file.write('^' + s.ljust(6))
                        n += 1

                    if n == 12 or j == len(self.__extref) - 1:
                        # if n == 12 or last one then next row.
                        file.write('\n')
                        n = 1

                    j += 1

            # Text
            for j in range(len(object_t)):
                file.write('T^' + A.output_hex(object_t[j][1], 6) +
                           '^' + A.output_hex(object_t[j][2], 2) + object_t[j][3] + '\n')

            for s in self.__modify:
                file.write(s + '\n')

            if self.__main:
                # End: E|first executable instruction address(6)
                file.write('E' + A.output_hex(object_t[0][1], 6) + '\n\n\n')
            else:
                # control section End: E
                file.write('E' + '\n\n\n')

    def row(self, index):
        """
        a row of code.
        :param index: row index.
        :return: string (location block symbol operator operand object code).
        """
        s = ''
        if self.__code[index][0] != '':
            # if code has loc(code[index][0]) then write into row.
            s += A.output_hex(self.__code[index][0], 4).ljust(7)
        else:
            s += ''.ljust(7)

        s += str(self.__code[index][1]).ljust(3)

        for j in range(2, 5):
            # write symbol, operator and operand into row.
            s += self.__code[index][j].ljust(15)
        # object code
        s += self.__code[index][6]
        return s

    def figure(self, figure_file):
        """
        assembly code write figure.
        :param figure_file: figure name to write(.txt).
        """
        with open(figure_file, 'w') as file:
            for index in range(len(self.__code)):
                # write row into file.
                file.write(self.row(index) + '\n')

    def __load_code(self, file_name):
        """
        load assembly code into __code.
        code structure: [location, block, symbol, operator, operand, program counter, object code]
        :param file_name: assembly code file(.txt).
        """
        with open(file_name, 'r') as file:
            content = file.readlines()
        for s in content:
            # loc, block, symbol, operator, operand.
            self.__code.append([''] * 5)
            # cut by tab.
            row = s[:-1].split('\t')
            for i in range(2, len(row)+2):
                self.__code[-1][i] = row[i - 2]
            # program counter
            self.__code[-1].append(0)
            # object code
            self.__code[-1].append('')

    def __load_optab(self, file_name):
        """
        load operator table.
        operator table structure: {operator: [opcode, format]}
        :param file_name: operator table file(.csv).
        """
        with open(file_name, newline='') as csv_file:
            op = csv.reader(csv_file)
            self.__operator_tab = {key: [opcode, format_] for key, opcode, format_ in op}

    def __real_address(self, loc, block):
        """
        convert address.
        :param loc: address
        :param block: this address's block
        :return: real address
        """
        return loc + self.__block_tab[block+1]

    def pass1(self, start):
        """
        generate symbol table and address location and corresponding block.
        generate block table and literal table.
        handle literal, EQU, LTOG, ORG, CSECT, EXTDEF, EXTREF.
        :param start: start index.
        :return: next start index, end index, assembly code file name.
        """
        locctr = 0
        index = start
        name = ''
        block_counter = 0
        current_block = 0
        # default block = 0.
        block_number = {'': 0}

        if self.__main and self.__code[start][3] == 'START':
            # set begin address location START operand, if START is not exist then begin 0.
            locctr += int(self.__code[0][4], 16)
            self.__code[start][0] = locctr
            self.__code[start][1] = current_block
            self.__base = locctr
            name = self.__code[start][2]
            index += 1

        if not self.__main and self.__code[start][3] == 'CSECT':
            self.__code[index][0] = locctr
            self.__code[index][1] = current_block
            name = self.__code[index][2]
            index += 1

        self.__start_address = locctr
        # block table initialize [0], 0 index for absolutely term.
        self.__block_tab.append(locctr)

        while self.__code[index][3] != 'END':
            if self.__code[index][2] == '.':
                # . is annotation.
                index += 1
                continue
            elif self.__code[index][3] == 'CSECT':
                # control section end.
                index -= 1
                break
            elif self.__code[index][2] == '' and self.__code[index][3] == '' and self.__code[index][4] == '':
                # blank line.
                index += 1
                continue

            symbol = self.__code[index][2]
            operator = self.__code[index][3]
            operand = self.__code[index][4]
            extend = 0

            if symbol in self.__symbol_tab.keys():
                print(self.row(index) + '   ' + symbol + ' is duplicate symbol')
            elif symbol != '':
                self.__symbol_tab[symbol] = [locctr, current_block]

            if symbol in self.__extdef.keys():
                # external definition for external symbol.
                self.__extdef[symbol][0] = locctr
                self.__extdef[symbol][1] = current_block

            if operator[0] == '+':
                # remove + ,ex: +ADD to ADD.
                extend = 1
                operator = operator[1:]

            if operand != '' and operand[0] == '=':
                """
                key = ascii code ex: =X'05' -> key = '05'
                literal table: {ascii code: [operand, length, location, block, whether append in code]}
                """
                key = A.xc_to_ascii(operand[1:])
                self.__literal_tab[key] = [operand, len(key) // 2, 0, current_block, False]

            if operator in self.__operator_tab.keys():
                self.__code[index][0] = locctr
                self.__code[index][1] = current_block
                locctr = locctr + int(self.__operator_tab[operator][1]) + extend
                self.__length = self.__length + int(self.__operator_tab[operator][1]) + extend
            elif operator == 'WORD':
                self.__code[index][0] = locctr
                self.__code[index][1] = current_block
                locctr += 3
                self.__length += 3
            elif operator == 'RESW':
                self.__code[index][0] = locctr
                self.__code[index][1] = current_block
                locctr += (int(self.__code[index][4]) * 3)
                self.__length += (int(self.__code[index][4]) * 3)
            elif operator == 'RESB':
                self.__code[index][0] = locctr
                self.__code[index][1] = current_block
                locctr += int(self.__code[index][4])
                self.__length += int(self.__code[index][4])
            elif operator == 'BYTE':
                self.__code[index][0] = locctr
                self.__code[index][1] = current_block
                locctr += len(A.xc_to_ascii(operand)) // 2
                self.__length += len(A.xc_to_ascii(operand)) // 2
            elif operator == 'LTORG':
                # append literal table which do not append to code.
                for key in self.__literal_tab.keys():
                    if not self.__literal_tab[key][4]:
                        self.__code.insert(index + 1, [locctr, current_block, '*', self.__literal_tab[key][0], '', 0, key])
                        self.__literal_tab[key][2] = locctr
                        self.__literal_tab[key][3] = current_block
                        self.__literal_tab[key][4] = True
                        locctr += self.__literal_tab[key][1]
                        self.__length += self.__literal_tab[key][1]
                        index += 1
            elif operator == 'EQU':
                loc = 0
                if operand == '*':
                    # * program counter.
                    loc = locctr
                    self.__symbol_tab[symbol] = [loc, current_block]
                    self.__code[index][1] = current_block
                else:
                    if operand.find('*') < 0 and operand.find('/') < 0:
                        """
                        operand dose not contain multiplication and division.
                        loc is computed operand value.
                        plus and minus are positive symbol quantity and negative symbol quantity in operand.
                        error is whether operand is valid.
                        """
                        loc, plus, minus, error = A.expression(self.__modify, self.__symbol_tab, self.__extref, operand)

                        if plus == 1 and minus == 0 and not error:
                            self.__symbol_tab[symbol] = [loc, current_block]
                            self.__code[index][1] = current_block
                        elif plus == minus and not error:
                            # block -1 for absolutely term.
                            self.__symbol_tab[symbol] = [loc, -1]
                        else:
                            """
                            pair of symbol has opposite sign(plus == minus)
                            except signal symbol(plus == 1 and minus == 0) and
                            integer(plus == 0 and minus == 0).
                            """
                            print(self.row(index) + '   ' + operand + ' is error expression.')
                    else:
                        # operand contain multiplication and division.
                        print(self.row(index) + '   ' + operand + ' is error expression.')

                self.__code[index][0] = loc
            elif operator == 'ORG':
                """
                loc is computed operand value.
                error is whether operand is valid.
                """
                loc, plus, minus, error = A.expression(self.__modify, self.__symbol_tab, self.__extref, operand)
                if error:
                    print(self.row(index) + '   ' + operand + ' is error expression.')
                else:
                    # change Locctr temporarily.
                    locctr = loc
            elif operator == 'USE':
                # change block.
                self.__block_tab[current_block+1] = locctr
                if operand in block_number.keys():
                    block = block_number[operand]
                    locctr = self.__block_tab[block+1]
                else:
                    # new block name.
                    block_counter += 1
                    block_number[operand] = block_counter
                    locctr = 0
                    self.__block_tab.append(0)

                current_block = block_number[operand]
                self.__code[index][0] = locctr
                self.__code[index][1] = current_block
            elif operator == 'EXTDEF':
                # external definition for external symbol.
                for key in operand.split(','):
                    self.__extdef[key] = [0, 0]
            elif operator == 'EXTREF':
                # external reference.
                self.__extref = operand.split(',')
            elif operator != 'BASE' and operator != 'NOBASE':
                print(self.row(index) + '   ' + operator + ' is invalid operation code')

            # code[index][5] is program counter.
            self.__code[index][5] = locctr
            index += 1

        end = index
        self.__block_tab[current_block+1] = locctr

        # locctr = first block address.
        locctr = self.__block_tab[1]

        for key in self.__literal_tab.keys():
            # append remaining literal to code.
            if not self.__literal_tab[key][4]:
                index += 1
                self.__code.insert(index, [locctr, 0, '*', self.__literal_tab[key][0], '', 0, key])
                self.__literal_tab[key][2] = locctr
                locctr += self.__literal_tab[key][1]
                self.__length += self.__literal_tab[key][1]

        block_length = self.__block_tab[1]
        self.__block_tab[1] = self.__start_address

        for j in range(2, len(self.__block_tab)):
            """
            compute block table.
            block = [0, block 0 locctr, block 1 loocctr....] -> [0, start address, start address + block 0 length....]
            """
            temp = self.__block_tab[j]
            self.__block_tab[j] = self.__block_tab[j-1] + block_length
            block_length = temp

        # next section start index, end index, assembly file name.
        return index + 1, end, name

    def pass2(self, start):
        """
        generate object code
        """
        index = start

        if self.__main and self.__code[start][3] == 'START':
            index += 1

        if not self.__main and self.__code[start][3] == 'CSECT':
            index += 1

        while self.__code[index][3] != 'END':
            if self.__code[index][2] == '.':
                # . is annotation.
                index += 1
                continue
            elif self.__code[index][3] == 'CSECT':
                # control section end.
                break
            elif self.__code[index][2] == '' and self.__code[index][3] == '' and self.__code[index][4] == '':
                # blank line.
                index += 1
                continue

            operator = self.__code[index][3]
            operand = self.__code[index][4]
            n, i, x, b, p, e = [0] * 6

            if operator[0] == '+':
                # check format 4 and remove +.
                operator = operator[1:]
                e = 1

            if operator in self.__operator_tab.keys():
                if self.__operator_tab[operator][1] == '1':
                    # format 1
                    # object code: opcode 8 bit.
                    self.__code[index][6] = self.__operator_tab[operator][0]
                elif self.__operator_tab[operator][1] == '2':
                    # format 2 register.
                    r1, r2 = '0', '0'
                    temp = operand.split(',')

                    if len(temp) == 1:
                        # one register.
                        if temp[0] in self.__register_tab.keys():
                            r1 = self.__register_tab[temp[0]]
                        else:
                            print(self.row(index) + '   ' + temp[0] + ' is invalid register.')

                        # object code: opcode 8 bit + register1 4 bit + register2 4 bit.
                        self.__code[index][6] = self.__operator_tab[operator][0] + r1 + r2
                    elif len(temp) == 2:
                        # two register.
                        if temp[0] in self.__register_tab.keys():
                            r1 = self.__register_tab[temp[0]]
                        else:
                            print(self.row(index) + '   ' + temp[0] + ' is invalid register.')

                        if temp[1] in self.__register_tab.keys():
                            r2 = self.__register_tab[temp[1]]
                        else:
                            print(self.row(index) + '   ' + temp[1] + ' is invalid register.')

                        # object code: opcode 8 bit + register1 4 bit + register2 4 bit.
                        self.__code[index][6] = self.__operator_tab[operator][0] + r1 + r2
                    else:
                        print(self.row(index) + '   ' + operand + ' is invalid operand.')
                else:
                    # format 3 or format 4
                    if operand != '':
                        if operand[-2:] == ',X':
                            # check operand has index or not and remove ,X.
                            operand = operand[:-2]
                            x = 1

                        if operand[0] == '@':
                            # check operand is @(indirect) and remove @.
                            n = 1
                            operand = operand[1:]
                        elif operand[0] == '#':
                            # check operand is #(immediate) and remove #.
                            i = 1
                            operand = operand[1:]
                        else:
                            # neither indirect nor immediate. n=1 i=1.
                            n = 1
                            i = 1
                    else:
                        # no operand.
                        n = 1
                        i = 1

                    """
                    test operand correct and type.
                    type: symbol, immediate address mode which contain integer #integer, literal =X or =C.
                    """
                    address = 0
                    is_address = True

                    if operand in self.__symbol_tab.keys():
                        # address = symbol address + block address.
                        address = self.__real_address(self.__symbol_tab[operand][0], self.__symbol_tab[operand][1])
                    elif operand in self.__extref:
                        address = 0
                    elif i == 1 and n == 0:
                        # immediate address mode operand can contain integer
                        try:
                            is_address = False
                            address = int(operand)
                        except ValueError:
                            print(self.row(index) + '   ' + '#' + operand + ' is error operand.')
                    elif operand == '':
                        # no operand
                        is_address = False
                    elif operand[0] == '=':
                        # address = literal address + literal's block address.
                        key = A.xc_to_ascii(operand[1:])
                        address = self.__real_address(self.__literal_tab[key][2], self.__literal_tab[key][3])
                    else:
                        print(self.row(index) + '   ' + operand + ' is undefined symbol.')

                    if e == 0:
                        """"
                        format three.
                        first step check PC relative, if can not, check BASE relative, if can not, output error.
                        """
                        if is_address:
                            if -2048 <= address - self.__code[index][5] <= 2047:
                                # PC relative, -2048 <= displacement <= 2047. code[i][5] is program counter.
                                p = 1
                                address = address - self.__code[index][5]
                            elif 0 <= address - self.__base <= 4095:
                                # BASE relative, 0 <= displacement <= 4095.
                                b = 1
                                address = address - self.__base
                            elif not(i == 1 and n == 0):
                                print(self.row(index) + ' can not use format three.')

                        """
                        generate format 3 object code
                        first item: opcode|n|i  opcode 6 bits and n, i each 1 bit convert to 2 columns hexadecimal.
                        second item: x|b|p|e  x, b, p, e each 1 bit convert to 1 column hexadecimal.
                        third item: displacement 12 bit convert to 3 column hexadecimal.
                        """
                        self.__code[index][6] = A.output_hex((int(self.__operator_tab[operator][0], 16) + n * 2 + i * 1), 2) + \
                                                A.output_hex(x * 8 + b * 4 + p * 2 + e * 1, 1) + \
                                                A.output_hex(address, 3)
                    else:
                        """
                        format four.
                        generate format 4 object code
                        first item: opcode|n|i  opcode 6 bits and n, i each 1 bit convert to 2 columns hexadecimal.
                        second item: x|b|p|e  x, b, p, e each 1 bit convert to 1 column hexadecimal.
                        third item: address 20 bit convert to 5 column hexadecimal.
                        """
                        if not (i == 1 and n == 0) and is_address:
                            # immediate address mode relocation.
                            m = 'M' + A.output_hex(self.__code[index][0] - self.__code[start][0] + 1, 6) + A.output_hex(5, 2)
                            # if operand is external reference then modify + operand.
                            m += ('+' + operand) if operand in self.__extref else ''
                            self.__modify.append(m)

                        self.__code[index][6] = A.output_hex(int(self.__operator_tab[operator][0], 16) + n * 2 + i * 1, 2) + \
                                                A.output_hex(x * 8 + b * 4 + p * 2 + e * 1, 1) + \
                                                A.output_hex(address, 5)
            elif operator == 'BYTE':
                # object code: operand perform ascii code. ex: BYTE C'EOF' -> 454f46
                self.__code[index][6] = A.xc_to_ascii(operand)
            elif operator == 'WORD':
                # object code: convert decimal integer into 6 columns hexadecimal.
                number, plus, minus, error = A.expression(self.__modify, self.__symbol_tab, self.__extref, operand,
                                                          self.__code[index][0] - self.__code[start][0])
                if not error:
                    self.__code[index][6] = A.output_hex(number, 6)
            elif operator == 'BASE':
                # reset Base register.
                if operand == '*':
                    self.__base = self.__code[index][5]
                elif operand in self.__symbol_tab.keys():
                    self.__base = self.__real_address(self.__symbol_tab[operand][0], self.__symbol_tab[operand][1])
                else:
                    print(self.row(index) + '   ' + operand + ' is undefined symbol.')
            elif operator == 'NOBASE':
                self.__base = 0

            index += 1
