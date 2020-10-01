import sys
import os
import socket
from enum import Enum
from struct import pack
import time


serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverHost = socket.gethostname()
serverPort = 1025
serverSocket.bind((serverHost,serverPort))


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
def send_ACK(ack_data, serverSocket):
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
    serverSocket.sendto(ack,clientAddress)  #enviam el ack al Servidor

def send_DATA(block_n, data):
#    Funcio per poder enviar data,
#    block_n indica el nombre del pack que s'envia
#    data es un string amb el contingut que volem enviar

#          2 bytes    2 bytes       n bytes
#          ---------------------------------
#  DATA  | 03    |   Block #  |    Data    |
#          ---------------------------------

    DATA = bytearray ()          #cream un array de bytes buid
    DATA.append(0)
    DATA.append(3)               #afegim el OpCode
    block_n = block_n.to_bytes(2, byteorder = 'big') #convertim el noste int a b'
    DATA += block_n
    DATA += data
    return DATA

def check_ack(timeout_time, socketsize, clientSocket):

#    Funcio indicadora si hem rebut el acknowledgment del ultim pack
#    retorna un bool amb la resolucio de la primera premisa
#    tambe utilitzam la funcio per fer timeout

#    timeout_time es un int amb el timeout
#    socketsize es int amb el tamany dels pack
#    clientSocket es el socket d'on esperam rebre el acknowledgment

    try:
        Ack, clientAddress = clientSocket.recvfrom(socketsize)
        print('Waiting for an ACK...')
        if int.from_bytes(Ack[:2],byteorder = 'big') == 4:
            return True
        clientSocket.settimeout(timeout_time)
    except socket.timeout:
        return False

#########################################################################################
print ('Server listening....')


while True:

    opt1, clientAddress = serverSocket.recvfrom(1024) #rebem la opcio que ha triat el client(GET/PUT)
    opt1 = opt1.decode('utf-8')
    print('Got connection from', clientAddress)
    print('Option recieved,', opt1)
    filename = ''

    if opt1 == 'GET':
        Request, clientAddress = serverSocket.recvfrom(1024)
        block_n = 0                     #inicialitzam el contador

        send_ACK(block_n, serverSocket)

        i = 2
        #Del primer pack  extreim nomes el contingut del filename
        while True:
            if Request[i:i+1] == b'\x00':
                break
            filename += Request[i:i+1].decode('utf-8')
            i += 1
        print('filename is', filename)

        i += 18
        socketsize = ''
        #Del primer pack extreim nomes el contingut del socketsize
        while True:
            if Request[i:i+1] == b'\x00':
                break
            socketsize += Request[i:i+1].decode('utf-8')
            i += 1
        print('Socketsize is',socketsize)

        socketsize = int(socketsize)
        filename = str(filename)
        file = open(os.path.dirname(os.path.realpath(__file__)) + '/Serverfiles/' + filename,'rb') #obrim on volem escriure
        pack = file.read(socketsize)
        block_n = 1

        while (pack):
            pack = send_DATA(block_n,pack)          #pasam les dades pel seu tractament per funcionar amb rfc 1350
            serverSocket.sendto(pack,clientAddress)     #enviam el pack ja tractat
            print('Sending, package number', block_n, '...')
            pack_received = False
            while pack_received == False:           #esperam el ack del servidor
                pack_received =  check_ack(20, socketsize, serverSocket)
            print('Acknowledgment received', block_n)
            pack = file.read(socketsize)
            block_n = block_n + 1
            if (block_n == 65535):              #en cas de arribar al lim de pack 2^16, tornam el contador a 1
                block_n = 1

        if(len(pack[4:]) == 0):          #nomes en el cas que el ultim pack tingues el mateix tamany que el socketsize
            pack = b'0'                                #cream un pack buid
            pack = send_DATA(block_n,pack)
            serverSocket.sendto(pack,clientAddress)
            print('Sending empty pack, end file', block_n, '...') #enviam pack buid com a final de fitxer
            pack_received = False
            while pack_received == False:
                pack_received =  check_ack(20, socketsize, serverSocket)
                print('Acknowledgment received', block_n)

        file.close()
        print( "Done Sending")



####################################################################################

    else:

        Request, clientAddress = serverSocket.recvfrom(1024)
        block_n = 0

        send_ACK(block_n, serverSocket)

        i = 2
        #Del primer pack  extreim nomes el contingut del filename
        while True:
            if Request[i:i+1] == b'\x00':
                break
            filename += Request[i:i+1].decode('utf-8')
            i += 1
        print('filename is', filename)
        filename = str(filename)
        i += 18
        socketsize = ''
        #Del primer pack extreim nomes el contingut del socketsize
        while True:
            if Request[i:i+1] == b'\x00':
                break
            socketsize += Request[i:i+1].decode('utf-8')
            i += 1
        print('Socketsize is',socketsize)
        socketsize = int(socketsize)

        file = open(os.path.dirname(os.path.realpath(__file__))+'/Serverfiles/' + filename,'wb')

        pack, clientAddress = serverSocket.recvfrom(socketsize+4) #pack rebut
        block_n = int.from_bytes(pack[2:4],byteorder = 'big')   #nombre de pack
        print('Receiving data, package number',block_n,'...')
        send_ACK(block_n, serverSocket)                     #enviam ack
        print('Sending Acknowledgment', block_n)

        while (pack[4:]):
            file.write(pack[4:])                        #escribim les dades rebudes, ignorant els 4 primers b'(expl. lin.64)
            pack, clientAddress = serverSocket.recvfrom(socketsize+4)
            print('Receiving data, package number',block_n,'...')
            block_n = int.from_bytes(pack[2:4],byteorder = 'big')
            send_ACK(block_n, serverSocket)
            print('Sending Acknowledgment', block_n)
            if len(pack[4:]) < socketsize:
                break
        file.close()
        print("Done Receiving")
