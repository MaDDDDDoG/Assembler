import csv
import Arithmetic as A


class Sic(object):
    """
    SIC class
    """
    def __init__(self):
        """
        code structure: [location, symbol, operator, operand, object code]
        operator table: {operator: opcode}
        symbol table: {symbol: symbol address}
        """
        self.__code = []
        self.__operator_tab = {}
        self.__symbol_tab = {}
        self.__length = 0
        self.__start_address = 0

    def run(self, code_file, op_file, ob_file):
        """
        run code and generate object code.
        :param code_file: assembly code file(.txt)
        :param op_file: operator file(.csv)
        :param ob_file: object code file(.txt)
        """
        self.__load_code(code_file)
        self.__load_optab(op_file)
        self.pass1()
        name = self.pass2()
        self.object_code(ob_file, name)

    def object_code(self, file_name, name):
        """
        put object code into object code file.
        object_t structure: [row start address, row length, object code]
        Algorithm:
        for i := 0 to code.length -1
            if object_t.length > 60 or address interrupt
                object_t next row

        write header into file
        for i := 0 to object_t.length -1
            write object_t[i] into file
        write end into file

        :param file_name: object code file(.txt).
        :param name: assembly code name.
        """
        TLENGTH = 60
        object_t = []
        first = True
        for index in range(len(self.__code)):
            # Text: T|row start address(6)|row length(2)|object code(60).
            if self.__code[index][2] == 'RESW' or self.__code[index][2] == 'RESB':
                # RESW and RESB interrupt continuous address.
                first = True

            ob_code = self.__code[index][4]
            loc = self.__code[index][0]

            if ob_code != '':
                # has object code.
                if first:
                    # object_t generate new row.
                    object_t.append([loc, 0, ''])
                    first = False

                if object_t[-1][1] * 2 + len(ob_code) > TLENGTH:
                    object_t.append([loc, len(ob_code) // 2, '^' + ob_code])
                else:
                    object_t[-1][2] += '^' + ob_code
                    object_t[-1][1] += len(ob_code) // 2

        with open(file_name, 'w') as file:
            # Header: H|file name(6)|begin address(6)|code length(6)
            file.write('H^' + name.ljust(6) + '^' +
                       A.output_hex(self.__start_address, 6) + '^' + A.output_hex(self.__length, 6) + '\n')

            # Text
            for j in range(len(object_t)):
                file.write('T^' + A.output_hex(object_t[j][0], 6) +
                           '^' + A.output_hex(object_t[j][1], 2) + object_t[j][2] + '\n')

            # End: E|begin address(6)
            file.write('E^' + A.output_hex(object_t[0][0], 6))

    def figure(self, figure_file):
        """
        assembly code write figure.
        :param figure_file: figure name to write(.txt).
        """
        with open(figure_file, 'w') as file:
            for index in range(len(self.__code)):
                # write row into file.
                file.write(self.row(index) + '\n')

    def row(self, index):
        """
        a row of code.
        :param index: row index.
        :return: string (location symbol operator operand object code).
        """
        s = ''
        if self.__code[index][0] != '':
            # if code has location(code[index][0]) then write into row.
            s += A.output_hex(self.__code[index][0], 4).ljust(7)
        else:
            s += ''.ljust(7)

        for j in range(1, 4):
            # write symbol, operator and operand into row.
            s += self.__code[index][j].ljust(15)
        # object code
        s += self.__code[index][4]
        return s

    def __load_code(self, file_name):
        """
        load assembly code into __code.
        code structure: [location, symbol, operator, operand, object code]
        :param file_name: assembly code file(.txt).
        """
        with open(file_name, 'r') as file:
            content = file.readlines()

        for s in content:
            # default set ['', '', '', '', '']
            self.__code.append([''] * 5)
            row = s[:-1].split('\t')
            for i in range(len(row)):
                self.__code[-1][i+1] = row[i]

    def __load_optab(self, file_name):
        """
        load operator table.
        :param file_name: operator table file(.csv).
        """
        with open(file_name, newline='') as csv_file:
            op = csv.reader(csv_file)
            self.__operator_tab = {operator: opcode for operator, opcode, _ in op}

    def pass1(self):
        """
        generate symbol table and address location.
        """
        locctr = 0
        index = 0

        if self.__code[0][2] == 'START':
            # set begin address location START operand, if START is not exist then begin 0.
            locctr += int(self.__code[0][3], 16)
            index = 1
        else:
            locctr = 0

        self.__code[0][0] = locctr
        # store begin address which use H.
        self.__start_address = locctr

        while self.__code[index][2] != 'END':
            if self.__code[index][1] == '.':
                # . is annotation.
                index += 1
                continue

            symbol = self.__code[index][1]
            operator = self.__code[index][2]
            operand = self.__code[index][3]

            if symbol in self.__symbol_tab.keys():
                print(self.row(index) + '   ' + symbol + ' is duplicate symbol')
            elif symbol != '':
                self.__symbol_tab[symbol] = locctr

            if operator in self.__operator_tab.keys():
                self.__code[index][0] = locctr
                locctr += 3
            elif operator == 'WORD':
                self.__code[index][0] = locctr
                locctr += 3
            elif operator == 'BYTE':
                self.__code[index][0] = locctr
                locctr += len(A.xc_to_ascii(operand)) // 2
            elif operator == 'RESW':
                self.__code[index][0] = locctr
                locctr += (int(operand) * 3)
            elif operator == 'RESB':
                self.__code[index][0] = locctr
                locctr += int(operand)
            else:
                print(self.row(index) + '   ' + operator + ' is invalid operation code.')

            index += 1

        # set code length: locctr(last locctr + last byte) - start locctr.
        self.__length = locctr - self.__start_address

    def pass2(self):
        """
        generate object code.
        :return: assembly file name.
        """
        # file name.
        name = ''
        index = 0

        if self.__code[0][2] == 'START':
            # START's symbol is file name.
            name = self.__code[0][1]
            index = 1

        while self.__code[index][2] != 'END':
            if self.__code[index][1] == '.':
                # . is annotation.
                index += 1
                continue

            operator = self.__code[index][2]
            operand = self.__code[index][3]
            x = 0

            if operator in self.__operator_tab.keys():
                address = 0
                if operand != '':
                    if operand[-2:] == ',X':
                        # if operand is index address mode then x=1 and remove ,X.
                        operand = operand[:-2]
                        x = 1

                    if operand in self.__symbol_tab:
                        # check operand in symbol table.
                        address = self.__symbol_tab[operand]
                    else:
                        print(self.row(index) + '   ' + operand + ' is undefined symbol.')

                """
                object code: hexadecimal perform opcode(8 bits)|X(1 bit)|address(15 bits)
                address is decimal integer, if has index address = address + 2^15 = 32768.
                decimal address convert to hexadecimal address.
                """
                self.__code[index][4] = self.__operator_tab[operator] + A.output_hex(address + x * 32768, 4)

            elif operator == 'BYTE':
                # object code: operand perform ascii code. ex: BYTE C'EOF' -> 454f46
                self.__code[index][4] = A.xc_to_ascii(operand)
            elif operator == 'WORD':
                # object code: hexadecimal integer. ex: WORD 3 -> 000003
                self.__code[index][4] = A.output_hex(int(operand), 6)

            index += 1

        return name
