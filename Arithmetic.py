def output_hex(n, w):
    """
    convert Decimal integer into Hexadecimal integer and fill zero to assign width
    ex: n=15 w=4 return '000A'
    :param n: decimal integer
    :param w: width
    :return: string
    """
    if n >= 0:
        # n is positive, [2:] ignore 0x at beginning, zfill(w) fill zero to width.
        return (hex(n)[2:].upper()).zfill(w)
    else:
        # n is negative, pow(16, w) + n = 16 ^ w - abs(n), 16's complement.
        return hex(pow(16, w) + n)[2:].upper()


def xc_to_ascii(s):
    """
    convert string into ACSII code.
    ex: C'EOF' return 454F46, X'05' return 05
    :param s: string X'OOO' or C'OOO'
    :return: ASCII code(hexadecimal)
    """
    if s[:2] == 'C\'' and s[-1] == '\'':
        # C'OOO' correct char pattern.
        temp = ''
        for char in s[2:-1]:
            # convert char into ASCII.
            temp += output_hex(ord(char), 2)
        return temp
    elif s[:2] == 'X\'' and s[-1] == '\'':
        # X'OOO' correct byte pattern.
        return s[2:-1]
    else:
        # invalid pattern.
        return ''


def expression(modify, symbol_tab, extref, s, length=0):
    """
    compute operand value use postfix.
    :param modify: modify list
    :param symbol_tab: dict
    :param extref: external reference list
    :param s: operand
    :param length: start address to current code length.
    :return: [loc, positive symbol quantity, negative symbol quantity, is error expression]
    """
    stack = []
    postfix = []
    plus = 0
    minus = 0
    error = False

    if s[0] == '-' or s[0] == '+':
        """
        +OOO-XXX -> 0+OOO-XXX=, -OOO+XXX -> 0-OOO+XXX=
        add 0 in start for detect how many positive and negative quantity easily.
        = detect operand is finish.
        """
        s = '0' + s + '='
    else:
        # OOO+XXX -> 0+OOO+XXX=.
        s = '0+' + s + '='

    temp = ''
    add = True
    rank = {'=': 0, '+': 1, '-': 1, '*': 2, '/': 2}
    for j in range(len(s)):
        if s[j] == '+' or s[j] == '-' or s[j] == '*' or s[j] == '/' or s[j] == '=':
            if temp in symbol_tab:
                if add:
                    plus += 1
                else:
                    minus += 1
                postfix.append(symbol_tab[temp][0])
            elif temp in extref:
                if add:
                    plus += 1
                else:
                    minus += 1
                sign = '+' if add else '-'
                modify.append('M' + output_hex(length, 6) + output_hex(6, 2) + sign + temp)
                postfix.append(0)
            else:
                try:
                    postfix.append(int(temp))
                except ValueError:
                    print(temp + ' is undefined symbol.')
                    postfix.append(0)
                    error = True

            add = (s[j] != '-')
            temp = ''
            while len(stack) > 0 and rank[stack[-1]] >= rank[s[j]]:
                postfix.append(stack.pop())
            stack.append(s[j])
        else:
            temp += s[j]

    stack.pop()

    for a in postfix:
        if a == '+':
            o2 = stack.pop()
            o1 = stack.pop()
            stack.append(o1 + o2)
        elif a == '-':
            o2 = stack.pop()
            o1 = stack.pop()
            stack.append(o1 - o2)
        elif a == '*':
            o2 = stack.pop()
            o1 = stack.pop()
            stack.append(o1 * o2)
        elif a == '/':
            o2 = stack.pop()
            o1 = stack.pop()
            stack.append(o1 / o2)
        else:
            stack.append(a)

    # int, int, int, boolean
    return stack.pop(), plus, minus, error
