import sys

def signedIntToBin(val: int, size: int) -> str:
    """turn a signed decimal into binary via two's complement and return a string of size bits"""
    return bin(val if val>=0 else val+(1<<size))[2:]

def binToHex(bits: str, instSize: int) -> str:
    """convert a string of binary digits into instSize hex digits and return a string of hex digits"""
    return '0'*(instSize - len(hex(int(bits, 2))[2:])) + hex(int(bits, 2))[2:]

def regToBin(reg: str, bitsPerReg: int) -> str:
    """convert a register name into its n-bit binary encoding and return a string"""
    bits = str(bin(int(reg[1:])))[2:]
    bits = '0'*(bitsPerReg-len(bits)) + bits
    return bits

def readLines(fileName: str) -> list[str]:
    """return the lines of fileName as a list"""
    f = open(fileName, 'r')
    out = f.readlines()
    f.close()
    return out

def findInstruction(inst: list[str], mappings: dict[str:str]) -> list[str]:
    """given a coded instruction, return the format of the instruction as a list"""
    format = []
    if((inst[0].upper() + 'imm') in mappings.keys()): #true if operands of instruction can be either a register or an immediate
        #figure out whether to use the immediate version or the register version
        if(inst[-1].lower()[0] == 'x'): #the last operand is a register
            format = mappings[inst[0].upper()]
        else: #the last operand must be an immediate
            format = mappings[inst[0].upper() + 'imm']
    else:
        format = mappings[inst[0].upper()]
    return format

def encodeImm(imm: str, operand: str, lineNum: int) -> str:
    """given the immediate argument, operand format and lineNum, return the binary encoded immediate"""
    if(imm[:2] == '0x'): #if the immediate number is hex, convert to int
        imm = int(imm, 16)
    elif(imm[:2] == '0b'): #if the immediate number is binary, convert to int
        imm = int(imm, 2)
    else: #immediate number must be decimal, convert to int
        imm = int(imm, 10)
    size = int(operand[0:operand.find('imm')]) #size is the number that precedes 'imm' in the mapping
    binaryimm = signedIntToBin(imm, size) #convert signed decimal immediate to binary
    binaryimm = '0'*(size - len(binaryimm)) + binaryimm #pad zeroes to match correct length
    if(len(binaryimm) > size): #detect if user coded too large of an immediate
        print("warning: immediate too large on line " + str(lineNum)+ ". Behavior undefined") 
    return binaryimm
    
def encodeReg(reg: str, bitsPerReg: int, lineNum: int) -> str:
    """given the immediate argument, bitsPerReg and lineNum, return the binary encoded register"""
    registerEncoding = regToBin(reg, bitsPerReg)
    if(len(registerEncoding) > bitsPerReg):
        print("warning: register not found on line " + str(lineNum)+ ". Behavior undefined") 
    return registerEncoding

def encodeLabel(label: str, operand: str, lineNum:str, instIndex: int, labelMap: dict[str:int]) -> str:
    """given a label argument, operand format, lineNum, instruction Index, and labelMappings, retur the encoded pc-relative offset"""
    pcRelativeOffset: int = labelMap[label] - instIndex
    size = int(operand[0:operand.find('label')]) #size is the number that precedes 'label'
    encodedOffset = signedIntToBin(pcRelativeOffset, size)
    encodedOffset = '0'*(size - len(encodedOffset)) + encodedOffset
    if(len(encodedOffset) > size): #detect if branching too far away
        print("warning: branching to a label too far away on line " + str(lineNum)+ ". Behavior undefined")
    return encodedOffset 


def encode(instruction: str, instMappings: dict[str:str], bitsPerReg: int, lineNum: int, instIndex: int, labelMappings: dict[str:int], dataMap: dict[str:int]) -> str:
    """encode an assembly isntruction into binary and return a string"""
    instruction = instruction.replace(',', '') #getting rid of unnecessary characters
    instruction = instruction.replace('[', '')
    instruction = instruction.replace(']', '')
    inst = instruction.split()
    format = findInstruction(inst, instMappings) #identifies the isntruction
    encoding = ''
    encoding += format[0] #adds opcode
    argIndex = 1 
    for operand in format[1:]: #iterates through all the operands in the instruction format
        if ('R' in operand): #encode register
            encoding += encodeReg(inst[argIndex], bitsPerReg, lineNum)
            argIndex += 1
        elif ('imm' in operand): #encode immediate
            encoding += encodeImm(inst[argIndex], operand, lineNum) 
            argIndex += 1
        elif ('label' in operand): #encode pc-relative offset
            encoding += encodeLabel(inst[argIndex], operand, lineNum, instIndex, labelMappings)
            argIndex += 1
        elif ('dataLab' in operand): #encode label address
            num = bin(dataMap[inst[argIndex]])[2:]
            num = '0'*(int(operand[:operand.find('dataLab')]) - len(num)) + num
            encoding += num
            argIndex += 1
        else: #encode constant set of bits
            encoding += operand 
    return encoding

def idInstructionLabels(fileName: str, instMap: dict[str:str]) -> dict[str:int]:
    """identify all the instruction labels in a file and return a dictionary mapping labels to addresses"""
    f = open(fileName, 'r')
    labelMap: dict[str:int]  = {}
    lines = f.readlines()
    linenum = 0 #line counter
    instIndex = 0 #instruction index
    for line in lines:
        if '.data' in line: #once you get to the data segment, stop
            break
        line = line[0:line.find('//')] if line.find('//') > -1 else line #remove commented portion
        linenum += 1
        if len(line.split()) == 0: #empty line, ignore it
            continue
        elif(':' in line): #label on this line
            labelMap[line[0:line.find(':')].strip()] = instIndex
            if (len(line.split())>1 and line.upper().split()[1] in instMap): #there is an instruction inline with the label
                instIndex += 1
        elif (line.upper().split()[0] in instMap): #first word in the line is a mneumonic
            instIndex += 1
        else:
            print("unrecognized symbol on line " + str(linenum))
            return {}
    return labelMap

def idDataLabels(fileName: str, instMap: dict[str:str]) -> dict[str:int]:
    dataMap: dict[str:str]  = {}
    lines = readLines(fileName)
    index = 0 #line counter
    for line in lines: #this loop makes sure the line index is where the data segment starts
        index+=1
        if '.data' in line:
            break
    out = open(fileName[0:fileName.find('.')] + '_data.o', 'w') #open output file
    out.write("v3.0 hex words addressed\n") #write header for logism to read

    nextPointerLocation = 0
    nextPointerValue = 0x0800
    while index < len(lines): #this should be the first line of the data segment
        tokens = lines[index].split()
        index += 1
        if(len(tokens) == 0): #empty line
            continue
        label = tokens[0][:-1] #label is the first token excluding the colon
        directive = tokens[1].upper()  #second token should be directive
        format = instMap[directive]
        size = int(format[0])
        for i,f in enumerate(format[1:]):
            if f == 'list': #the rest of the line should be a bunch of numbers
                dataMap[label] = nextPointerLocation #write the address of the pointer in the map
                #put the pointer into the file
                intTo4DigitHex = lambda n: '0'*(4 - len(hex(n)[2:]))+hex(n)[2:]
                out.write(intTo4DigitHex(nextPointerLocation) + ": " + intTo4DigitHex(nextPointerValue)[2:] + " " + intTo4DigitHex(nextPointerValue)[:2] + "\n")
                #write the actual data into the file
                out.write(intTo4DigitHex(nextPointerValue) + ": ")
                for x in tokens[i+2:]:
                    #remove the colon, convert the hex, and add to file
                    num = binToHex(signedIntToBin(int(x.replace(',', '')), size*8), size*2)
                    for j in range(len(num)-2, -2, -2):
                        out.write(num[j:j+2]+ " ") 
                out.write("\n")
                nextPointerValue += size * len(tokens[i+2:])
                nextPointerLocation+=2
                break
            if f == 'string': #the rest of the line should be a string with ""
                dataMap[label] = nextPointerLocation #write address of the pointer in the map
                #put the pointer into the file
                intTo4DigitHex = lambda n: '0'*(4 - len(hex(n)[2:]))+hex(n)[2:]
                out.write(intTo4DigitHex(nextPointerLocation) + ": " + intTo4DigitHex(nextPointerValue)[2:] + " " + intTo4DigitHex(nextPointerValue)[:2] + "\n")
                #write the actual data into the file
                out.write(intTo4DigitHex(nextPointerValue) + ": ")
                stuffInQuotes = ""
                for word in tokens[i+2:]:
                    stuffInQuotes += word + " "
                for c in stuffInQuotes[1:-2]:
                    #c is the current letter
                    ascii = ord(c)#convert the letter to it's ascii code
                    num = binToHex(signedIntToBin(ascii, 8), 2)
                    out.write(num + " ")
                out.write("00\n") #append null pointer
                nextPointerValue += size * len(tokens[i+2][1:len(tokens[i+2])-1]) + 1
                nextPointerLocation += 2
    out.close()
    return dataMap

def cleanLine(inst: str) -> str :
    """remove the label, comment and trailing whitespace of a string and return a string"""
    inst = inst[0:inst.find('//')] if inst.find('//') > -1 else inst #remove commented portion
    inst = inst[inst.find(':')+1:] if inst.find(':') > -1 else inst #remove labeled portion
    return inst.strip() #remove trailing whitespace and return

def readArch(fileName: str) -> tuple[any]:
    """given the intruction set architechture, return tuple containing bitsPerReg, instructionSize, and instructionMappings"""
    manual = readLines(fileName) #load instructionSetArchitechture file
    bitsPerReg = int(manual[0].split()[1]) #read the required size of register encodings
    instructionSize = int(manual[1].split()[1]) #read number of hex digits per encoded instruction
    mappings = {}   #create instruction mapping from the instructionSetArchitechture file
    for i in range(2, len(manual)):   
        line = manual[i].split()
        mappings[line[0]] = line[1:]
    return (bitsPerReg, instructionSize, mappings)

def encodeFile(inputfile: str, outputfile: str):
    """encode the code written in inputfile and write the encodings to outputfile"""
    architechture = readArch('v2InstructionSetArchitechture.txt')
    bitsPerReg: int = architechture[0]
    instSize: int = architechture[1]
    instMap: dict[str:str] = architechture[2]
    dataMap: dict[str:int] = idDataLabels(inputfile, instMap)
    labelMappings = idInstructionLabels(inputfile, instMap)
    encodings = []
    instIndex = 0 #counts instructions encoded
    lineNum = 0 #line counter
    instructions = readLines(inputfile) #load code file
    for inst in instructions: #encode the instructions line by line
        if '.data' in inst:
            break
        lineNum += 1
        inst = cleanLine(inst) #remove comment, label, and trailing whitespace
        if(len(inst) == 0): #skip empty lines or commented lines
            continue 
        encodings += binToHex(encode(inst, instMap, bitsPerReg, lineNum, instIndex, labelMappings, dataMap), instSize) + ' ' #encode instruction and append a space
        print("encoded instruction " + str(inst))
        instIndex += 1
    out = open(outputfile, 'w') #open output file
    out.write("v3.0 hex words plain\n") #write header for logism to read
    out.writelines(encodings) #write the encodings
    out.close()
    print("finished encoding " + str(instIndex) + " instructions.")

def main():
    argc = len(sys.argv)
    if argc == 2:
        encodeFile(sys.argv[1], 'a.o')
        return 0
    elif argc == 4:
        if(sys.argv[2] != '-o'):
            print("usage: python .\project2Assemblerv2.py <input file> [-o outputfile]")
            return 1;
        encodeFile(sys.argv[1], sys.argv[3])
    else:
        print("usage: python .\project2Assemblerv2.py <input file> [-o outputfile]")
        return 1;

if __name__ == '__main__':
    main()
