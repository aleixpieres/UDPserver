import sys
import os
import socket
from enum import Enum
from struct import pack
import time

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverHostName = socket.gethostname()
serverPort = 12000
serverAdress = (serverHostName,serverPort)


class ErrorCodes(Enum):                     # Declaracio de classe Errors (facil crida)
    NOT_DEFINED = 0
    FILE_NOT_FOUND = 1
    ACCESS_VIOLATION = 2
    DISK_FULL_OR_ALLOCATION_EXCEEDED = 3
    ILLEGAL_OPERATION = 4
    UNKNOWN_TRANSFER_ID = 5
    FILE_ALREADY_EXISTS = 6
    NO_SUCH_USER = 7

#########################################################################################

def send_RQ(Opcode, filename, mode, blocksize, actual_blocksize, serverAdress):

#    Funcio per solicitar RRQ o RWQ
#    Opcode indica si volem fer RRQ o WRQ
#    filename indica el archiu que volem escriure o obtenir del servidor
#    mode indica si utilitzam netascii, octet, mail
#    blocksize es un string que conte 'blksize'
#    actual_blocksize conte el int amb el blocksize

#     +-------+---~~---+---+---~~---+---+---~~---+---+---~~---+---+
#      |  opc  |filename| 0 |  mode  | 0 | blksize| 0 | #octets| 0 |
#      +-------+---~~---+---+---~~---+---+---~~---+---+---~~---+---+

     RQ_message = bytearray()                           #cream un array de bytes buid
     if Opcode == 1 :
         RQ_message.append(0)
         RQ_message.append(1)
     else:
        RQ_message.append(0)
        RQ_message.append(2)

     filename = bytearray(filename.encode('utf-8'))     #cream un array de bytes amb el string
     RQ_message += filename                             #afegim al final del primer array el nostre string en b'
     RQ_message.append(0)
     mode = bytearray(mode.encode('utf-8'))
     RQ_message += mode
     RQ_message.append(0)
     blocksize = bytearray(blocksize.encode('utf-8'))
     RQ_message += blocksize
     RQ_message.append(0)
     actual_blocksize = bytearray(actual_blocksize.encode('utf-8'))
     RQ_message += actual_blocksize
     RQ_message.append(0)
     clientSocket.sendto(RQ_message,serverAdress)

def send_DATA(block_n, data):

#    Funcio per poder enviar data,
#    block_n indica el nombre del pack que s'envia
#    data es un string amb el contingut que volem enviar

#          2 bytes    2 bytes       n bytes
#          ---------------------------------
#  DATA  | 03    |   Block #  |    Data    |
#          ---------------------------------


    DATA = bytearray ()         #cream un array de bytes buid
    DATA.append(0)
    DATA.append(3)              #afegim el OpCode
    block_n = block_n.to_bytes(2, byteorder = 'big') #convertim el noste int a b'
    DATA += block_n
    data = bytearray(data)
    DATA += data
    return DATA

def send_ACK(ack_data, clientAdress):

#    Funcio per poder enviar ack
#    ack_data conte el nombre de pack que esteim rebent
#    clientAdress es on enviem el acknowledgment

#        2 bytes    2 bytes
#             -------------------
#      ACK   | 04    |   Block #  |
#             --------------------

    ack = bytearray()
    ack.append(0)
    ack.append(4)                   #inicialitzam el Opcode per ack
    ack_data = ack_data.to_bytes(2, byteorder = 'big') #convertim el int a b'
    ack += ack_data
    clientAdress.sendto(ack, serverAdress)  #enviam el ack al Servidor


def Serv_Error(data):


#    Funcio per comprovar si el pack conte cap tipus d'error_code

#      2 bytes  2 bytes        string    1 byte
#              ----------------------------------------
#       ERROR | 05    |  ErrorCode |   ErrMsg   |   0  |
#              ----------------------------------------

    opcode = data[:2]
    return int.from_bytes(opcode, byteorder='big') == OpCodes['ERROR']

def Detect_Error(data):
    if Serv_Error(data):
        error_code = int.from_bytes(data[2:4], bytearray = 'big')
        print (ErrorCodes(error_code))

def check_ack(timeout_time, socketsize, clientSocket):

#    Funcio indicadora si hem rebut el acknowledgment del ultim pack
#    retorna un bool amb la resolucio de la primera premisa
#    tambe utilitzam la funcio per fer timeout

#    timeout_time es un int amb el timeout
#    socketsize es int amb el tamany dels pack
#    clientSocket es el socket d'on esperam rebre el acknowledgment


    try:
        print('Waiting for an ACK...')
        clientSocket.settimeout(timeout_time)
        Ack, clientAddress = clientSocket.recvfrom(socketsize)
        if int.from_bytes(Ack[:2],byteorder = 'big') == 4:
            return True
    except socket.timeout:
        return False

#########################################################################################
while 1:
    extern_Server = input('Would you like to communicate with an extern Server?(Y/N):')
    if extern_Server == 'Y' or extern_Server == 'N':
        break
if extern_Server == 'Y':
    Ip_Address = input('Enter the ip address of the Server:(Ex:172.16.254.1)')
    Port = input('Enter the port of the Server:')
    Port = int(Port)
    serverAdress = (Ip_Address,Port)

mode = "netascii"
opt1 = ''
blocksize = "blksize"

while 1:
    opt1 = input('Would you like to GET a file from the server or PUT one on it?(GET/PUT)\n')
    if opt1 == 'GET' or opt1 == 'PUT':
        break

clientSocket.sendto(opt1.encode('utf-8'),(serverHostName,serverPort))

if opt1 == 'GET':
    opcode = 1
    while 1:
        print('Enter the name of the file you want to get from the server')
        aux = input('Would you like any suggestions?(Y/N)')
        if aux == 'Y' or aux == 'N':
            break
    #Des de la lin 161 fins 170, es una funcion per poder mostrar els archius continguts
    #dins un directori, per poder realitzar la sugerencia (Aquesta funcio es pot veure mes cops dins el prog)
    if aux == 'Y':
        path = os.path.dirname(os.path.realpath(__file__)) + '/Serverfiles'
        files = []
        for r, d, f in os.walk(path):
            for file in f:
                files.append(os.path.join(file))
        for f in files:
            print(f)

    filename0 = input('Enter the name of the file you want to get from the server:')



    while 1:
        print('Enter the name of the file you wanna write on:')

        aux = input('Would you like any suggestions?(Y/N)')
        if aux == 'Y' or aux == 'N':
            break
    if aux == 'Y':
            path = os.path.dirname(os.path.realpath(__file__)) + '/text'
            files = []
            for r, d, f in os.walk(path):
                for file in f:
                    files.append(os.path.join(file))
            for f in files:
                print(f)

    filename = input('Enter your filename:')


    socketsize = input('Enter the package size:')
    timeout_time = input('Enter the timeout (seconds):')
    timeout_time = int(timeout_time)
    socketsize = int(socketsize)
    RequestAccepted = False

    while RequestAccepted ==  False:
        #realitzam un bucle per enviar la nostra Request i assegurar la resposta esperant un acknowledgment
        print('Sending Filename and Socketsize...')
        send_RQ(opcode, filename0, mode, blocksize, str(socketsize), serverAdress)
        RequestAccepted = check_ack(timeout_time, socketsize, clientSocket)



    file = open(os.path.dirname(os.path.realpath(__file__))+'/text/'+filename,'wb') #obrim el archiu que volem escriure



    while True:
        pack, clientAddress = clientSocket.recvfrom(socketsize+4)          #pack rebut
        block_n = int.from_bytes(pack[2:4],byteorder = 'big')             #nombre de pack
        print('Receiving data, package number',block_n,'...')
        send_ACK(block_n, clientSocket)                                   #enviam ack
        print('Sending Acknowledgment', block_n)
        file.write(pack[4:])                                              #escribim les dades rebudes, ignorant els 4 primers b'(expl. lin.64)
        if len(pack[4:]) < socketsize:
            print('Successfully got the file')
            break


    file.close()
    clientSocket.close()                                                #finalment tancam el archiu i el servidor
    print('Connection closed')


#########################################################################################

if opt1 == 'PUT':
    opcode = 2
    print('Enter the name of the file you wanna write on:')

    while 1:
        aux = input('Would you like any suggestions?(Y/N)')
        if aux == 'Y' or aux == 'N':
            break
    if aux == 'Y':
        path = os.path.dirname(os.path.realpath(__file__)) + '/Serverfiles'
        files = []
        for r, d, f in os.walk(path):
            for file in f:
                if '.txt' in file:
                    files.append(os.path.join(file))
        for f in files:
            print(f)
    filename0 = input('Enter the name of the file you wanna write on:')



    print('Enter the name of the file you want to put on the server:')

    while 1:
        aux = input('Would you like any suggestions?(Y/N)')
        if aux == 'Y' or aux == 'N':
            break
    if aux == 'Y':
        path = os.path.dirname(os.path.realpath(__file__)) + '/text'
        files = []
        for r, d, f in os.walk(path):
            for file in f:
                if '.txt' in file:
                    files.append(os.path.join(file))
        for f in files:
            print(f)

    filename = input('Enter the name of the file you want to put on the server:')
    socketsize = input('Enter the package size: ')
    timeout_time = input('Enter the timeout (seconds):')
    timeout_time = int(timeout_time)
    socketsize = int(socketsize)
    RequestAccepted = False

    while RequestAccepted ==  False:
        #realitzam un bucle per enviar la nostra Request i assegurar la resposta esperant un acknowledgment
        print('Sending Filename and Socketsize...')
        send_RQ(opcode, filename0, mode, blocksize, str(socketsize), serverAdress)  #enviam RQ
        RequestAccepted = check_ack(timeout_time, socketsize, clientSocket)         #compravam si tenim ack

    file = open(os.path.dirname(os.path.realpath(__file__))+'/text/'+filename,'rb') #obrim el archiu que volem escriure


    pack = file.read(socketsize)
    block_n = 1                 #inciam el contador de pack

    while (pack):
        pack = send_DATA(block_n,pack)                  #pasam les dades pel seu tractament per funcionar amb rfc 1350
        clientSocket.sendto(pack,(serverHostName,serverPort))   #enviam el pack ja tractat
        print('Sending, package number', block_n, '...')
        pack_received = False
        while pack_received == False:                              #esperam el ack del servidor
            pack_received =  check_ack(timeout_time, socketsize, clientSocket)
        print('Acknowledgment received', block_n)
        pack = file.read(socketsize)
        block_n = block_n + 1
        if (block_n == 65535):                       #en cas de arribar al lim de pack 2^16, tornam el contador a 1
            block_n = 1

    if(len(pack[4:]) == 0):          #nomes en el cas que el ultim pack tingues el mateix tamany que el socketsize
        pack = b'0'                                #cream un pack buid
        pack = send_DATA(block_n,pack)
        clientSocket.sendto(pack,(serverHostName,serverPort))   #enviam el pack ja tractat
        print('Sending empty pack, end file', block_n, '...') #enviam pack buid com a final de fitxer
        pack_received = False
        while pack_received == False:                              #esperam el ack del servidor
            pack_received =  check_ack(timeout_time, socketsize, clientSocket)
        print('Acknowledgment received', block_n)

file.close()
print("Done Sending")
clientSocket.close()
print('Connection closed')
