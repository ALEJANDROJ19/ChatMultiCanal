# coding=utf-8
__author__ = "ALEJANDRO & RAUL"
import sys
from socket import *
import threading
import time
from multiprocessing import Pipe
import string

# Cola de eventos. Comunicacion entre el receptor y el emisor:
e_rcv, e_snd = Pipe(False)
connected = False
current_channel = '0_Hall'
afk = False
useless = 0
__hall = '0_Hall'
lastuserarrival = ''
lastprivateuserarrival = ''
lastchannelarrival = ''
username = ''


def pitcher():
    # Funcion que realiza el thread enviador
    # su unica funcion es la de capturar mensajes del teclado y transformarlos en codigos comprensibles
    # por el servidor o configurar el cliente.
    time.sleep(1)
    # Cola de eventos usada: e_rcv || Tiempo maximo de bloqueo espera de respuesta por el servidor: 2 segundos
    # Fase 1: Loggin
    global connected
    global useless
    global current_channel
    global afk
    global __hall
    global lastprivateuserarrival
    while not connected:
        raw_sentence = ''
        raw_sentence = raw_input('> Usuari:  ')

        if raw_sentence.__len__() != 0 and not raw_sentence[0].isspace():
            try:
                clientSocket.send('150 '+raw_sentence)
            except:
                print '@@ El servidor no respon...'
                return
            if e_rcv.poll(2):
                connected = e_rcv.recv() == '200'
            else:
                print 'Server time out...'
        else:
            print '## Nombre de usuario no valido!'

    # Fase 2: Comunication
    while connected:
        if e_rcv.poll():
            # Error: No puede haber elementos en la cola de eventos si no hemos realizado ninguna peticion
            print 'ERROR INTERN'
            clientSocket.send('500')
            return

        raw_sentence = raw_input('> ')
        scode = raw_sentence.split(' ')
        size_scode = scode.__len__()

        if raw_sentence.__len__() != 0 and not raw_sentence.isspace() and connected:
            # Comandes del client. No totes interactuen amb el servidor!
            if scode[0] == '/afk':
                # Comanda: Ficar/Treure del estat ausent a l'usuari.
                afk = not afk
                if afk:
                    print '## Mode AFK activat'
                    clientSocket.send('114 on')
                else:
                    print '## Mode AFK desactivat'
                    clientSocket.send('114 off')

                if e_rcv.poll(2):
                    # Solo para vaciar la cola de eventos... No nos interesa el 200 OK
                    if e_rcv.recv() == '200':
                        useless = 0
                else:
                    print 'Server time out...'

            elif scode[0] == '/cd':
                # Comanda: Centrar-se en un canal per escriure. Pot ser que el client no tingui permis per escriure.
                # Si no rep cap nom de canal, per defecte va al canal 0_Hall
                if size_scode < 2:
                    current_channel = __hall
                    print 'Estas escrivint en el canal '+__hall
                else:
                    clientSocket.send('119 '+scode[1])
                    if e_rcv.poll(2):
                        if e_rcv.recv() == '200':
                            current_channel = scode[1]
                            print '## Estas escrivint en el canal '+scode[1]
                    else:
                        print 'Server time out...'

            elif scode[0] == '/create':
                # Comanda: Crear un canal en el servidor. El usuari que l'ha creat es el channel admin d'aquest.
                # El usuari es centra automaticament en el canal en cas d'exit
                if size_scode == 1:
                    print '/create <channel>'
                else:
                    clientSocket.send('110 '+scode[1])
                    if e_rcv.poll(2):
                        if e_rcv.recv() == '200':
                            current_channel = scode[1]
                            print '## Estas escrivint en el canal '+scode[1]
                    else:
                        print 'Server time out...'

            elif scode[0] == '/dc':
                clientSocket.send('500 ClientDisconnect')
                return

            elif scode[0] == '/delete':
                # Comanda: Eliminar un canal en el servidor. Nomes el channel admin pot eliminar-lo.
                # El usuari es centra en el 0_Hall en cas de que el canal eliminat sigui el que estava centrat.
                # Si no rep cap nom de canal, intenta eliminar en el que esta centrat.
                if size_scode == 1:
                    # Eliminar el current
                    clientSocket.send('113 '+current_channel)
                else:
                    # Eliminar el que ens passen
                    clientSocket.send('113 '+scode[1])

                if e_rcv.poll(2):
                    if e_rcv.recv() == '200':
                        current_channel = __hall
                        print 'Canal eliminat'
                else:
                    print 'Server time out...'

            elif scode[0] == '/delpw':
                # Comanda: Eliminar la contrasenya del canal. Nomes el channel admin pot eliminar-lo.
                # Si no rep cap nom de canal, intenta eliminar en el que esta centrat.
                canalaeliminar = ''
                if size_scode == 1:
                    # Eliminar del current
                    if current_channel == __hall:
                        print '@@ No tens permis per modificar el canal '+__hall
                    else:
                        clientSocket.send('112 '+current_channel)
                        canalaeliminar = current_channel
                else:
                    # Eliminar el que ens passen
                    if scode[1] == __hall:
                        print '@@ No tens permis per modificar el canal '+__hall
                    else:
                        clientSocket.send('112 '+scode[1])
                        canalaeliminar = scode[1]

                if canalaeliminar.__len__() != 0:
                    if e_rcv.poll(2):
                        if e_rcv.recv() == '200':
                            print '## Password del canal '+canalaeliminar+' eliminat'
                    else:
                        print 'Server time out...'

            elif scode[0] == '/join':
                # Comanda: Entrar en un canal. Automaticament el canal seleccionat per escriure es aquest.
                # Tambe es pot entrar directament en un canal amb contrasenya
                if size_scode == 1:
                    # Mostrar una llista dels canals
                    clientSocket.send('106 allch')
                elif size_scode == 2:
                    # Entrar al canal
                    clientSocket.send('105 '+scode[1])
                    if e_rcv.poll(2):
                        if e_rcv.recv() == '200':
                            current_channel = scode[1]
                            print '## Has entrat al canal '+scode[1]
                    else:
                        print 'Server time out...'
                else:
                    # Entrar al canal amb contrassenya
                    clientSocket.send('104 '+scode[1]+' '+scode[2])
                    if e_rcv.poll(2):
                        if e_rcv.recv() == '200':
                            current_channel = scode[1]
                            print '## Has entrat al canal '+scode[1]
                    else:
                        print 'Server time out...'

            elif scode[0] == '/help':
                # Comanda offline: Mostra totes les comandes del servidor i una breu descripcio
                print '\t\t\t## \t\tHELP\t ##'
                print '> /afk \t\t\t\t-- Entrar/Sortir del mode AFK.'
                print '> /cd [ch] \t\t\t-- Seleccionar un canal per escriure.'
                print '> /create <chname> \t-- Crea un canal amb nom <chname>.'
                print '> /dc \t\t\t\t-- Desconecta el client del servidor.'
                print '> /delete <ch> \t\t-- Elimina el canal <ch>'
                print '> /delpw <ch> \t\t-- Elimina la contrasenya del canal <ch>'
                print '> /help \t\t\t-- Mostra totes les comandes del servidor i una breu descripcio'
                print '> /join \t\t\t-- Mostra una llista de canals que es pot unir l\'usuari.'
                print '> /join <ch> [pw] \t-- Entra en el canal <ch>.'
                print '> /kick <user> <ch> [msg] - Expulsa al <user> del canal <ch>.'
                print '> /kicks <user> [msg] - Expulsa al <user> del servidor.'
                print '> /leave \t\t\t-- Mostra una llista dels canals als que esta unit el usuari.'
                print '> /leave <ch> \t\t-- Surt del canal <ch>'
                print '> /list \t\t\t-- Dona totes les subordres de la comanda /list.'
                print '> /list <allch/allus/me/mute/owned/users <ch>> - Subordres especifiques del /list'
                print '> /mute <user> \t\t-- Muteja al <usuari>.'
                print '> /r <Msg> \t\t\t-- Respon a l\'ultim usuari en privat'
                print '> /setpw <ch> <pw> <pw> - Possa en el canal <ch> la contrasenya <pw>'
                print '> /tell <user> [msg] - Envia un missatge privat al <user>.'

            elif scode[0] == '/kick':
                # Comanda: Expulsar un usuari del canal.
                # Es pot enviar un missatge opcional al usuari
                if size_scode < 3:
                    print '/kick <user> <channel> [Optional Message]'
                else:
                    clientSocket.send('116 '+' '.join(scode[1:]))
                    if e_rcv.poll(2):
                        if e_rcv.recv() == '200':
                            print '## Has expulsat a l\'usuari '+scode[1]+' del canal '+scode[2]
                        else:
                            print 'Server time out...'

            elif scode[0] == '/leave':
                # Comanda: Sortir d'un canal. Si no es dona el canal, es surt del que estas actualment.
                # Per defecte et situa en el 0_Hall. No es pot sortir del 0_Hall.
                if size_scode == 1:
                    ch_leave = current_channel
                else:
                    ch_leave = scode[1]

                # Sortir del canal actual
                if ch_leave == __hall:
                    print '@@ No es pot sortir del canal '+ch_leave+'.'
                else:
                    # 109 <ch>
                    clientSocket.send('109 '+ch_leave)
                    if e_rcv.poll(2):
                        if e_rcv.recv() == '200':
                            print '## Has sortit del canal '+ch_leave+'.'
                            current_channel = __hall
                    else:
                        print 'Server time out...'

            elif scode[0] == '/list':
                # Mirem si a continuacio de /list hi ha alguna subcomanda de no ser aixi es mostren les subcomandes
                if size_scode == 1:
                    print '## \t\t\t**\tLlista de subcomandes\t** '
                    print '/list\t\t\t\t-- Mostra totes les subcomandes del /list.'
                    print '/list allch\t\t\t-- Mostra tots els canals del servidor.'
                    print '/list allus\t\t\t-- Mostra tots els usuaris del servidor.'
                    print '/list me\t\t\t-- Mostra tots els canals on el client esta connectat.'
                    # print '/list mute'
                    print '/list owned\t\t\t-- Mostra tots els canals dels quals el usuari es propietari.'
                    print '/list users <ch>\t-- Mostra tots els usuaris en el canal especificat.'
                elif scode[1] == 'allch':
                    print '## \t\t--\tLlista de tots els canals:\t--\n'
                    clientSocket.send('106 ' + scode[1])
                elif scode[1] == 'allus':
                    print '## \t\t--\tLlista de tots els usuaris:\t--\n'
                    clientSocket.send('106 ' + scode[1])
                elif scode[1] == 'me':
                    print '## \t\t--\tLlista de tots els canals on estas connectat:\t--\n'
                    clientSocket.send('107 ')
                elif scode[1] == 'mute':
                    print '@@ Comanda no implementada....'
                elif scode[1] == 'owned':
                    print '## \t\t--\tLlista de tots els canals creats:\t--\n'
                    clientSocket.send('108 ')
                elif scode[1] == 'users':
                    canalamostrar = ''
                    if size_scode == 2:
                        # Current
                        canalamostrar = current_channel
                    else:
                        canalamostrar = scode[2]
                    print '## \t\t--\tLlista de tots els usuaris en el canal '+canalamostrar+':\t--\n'
                    clientSocket.send('120 ' + canalamostrar)
                else:
                    print '@@ Comanda no reconeguda!'
                    print '## \t\t\t**\tLlista de subcomandes\t** '
                    print '/list\t\t\t\t-- Mostra totes les subcomandes del /list.'
                    print '/list allch\t\t\t-- Mostra tots els canals del servidor.'
                    print '/list allus\t\t\t-- Mostra tots els usuaris del servidor.'
                    print '/list me\t\t\t-- Mostra tots els canals on el client esta connectat.'
                    # print '/list mute'
                    print '/list owned\t\t\t-- Mostra tots els canals dels quals el usuari es propietari.'
                    print '/list users <ch>\t-- Mostra tots els usuaris en el canal especificat.'

            elif scode[0] == '/mute':
                wait()
            elif scode[0] == '/r':
                # Comanda: Respondre al ultim usuari que ens ha enviat un missatge privat o mostrar l'ultim usuari que
                # t'ha enviat el missatge
                if size_scode < 2 or lastprivateuserarrival == '':
                    if lastprivateuserarrival == '':
                        print 'Ningun usuari t\'ha enviat un missatge privat'
                    else:
                        print '## L\'ultim usuari que t\'ha enviat un missatge privat es: '+lastprivateuserarrival
                else:
                    # Missatge privat definit per l'usuari
                    sentence = '101 '+lastprivateuserarrival+' '+' '.join(scode[1:])
                    clientSocket.send(sentence)
                    if e_rcv.poll(2):
                        if e_rcv.recv() == '200':
                            print '## Missatge enviat correctament'
                    else:
                            print 'Server time out...'

            elif scode[0] == '/setpw':
                # Comanda: Posar password (scode[2]) en canal (scode[1])
                if size_scode < 2:
                    print '/setpw <Channel> [password]'
                else:
                    if size_scode == 2:
                        # Comanda /setpw <CurrentChannel> Pw
                        sentence = '111 '+current_channel+' '+scode[1]
                    else:
                        sentence = '111 ' +scode[1]+' '+scode[2]

                    clientSocket.send(sentence)
                    if e_rcv.poll(2):
                        if e_rcv.recv() == '200':
                            print '## Password afegida correctament'
                    else:
                            print 'Server time out...'

            elif scode[0] == '/tell':
                # Comanda: Enviar un missatge privat a un usuari concret.
                sentence = ''
                if size_scode < 2:
                    print '/tell <User> [Msg]'
                elif size_scode == 2:
                    # Missatge privat sense missatge, enviar el predefinit
                    sentence = '101 '+scode[1]+' T\'ha enviat un avis.'
                else:
                    # Missatge privat amb cos definit per l'usuari
                    sentence = '101 '+scode[1]+' '+' '.join(scode[2:])

                clientSocket.send(sentence)
                if e_rcv.poll(2):
                    if e_rcv.recv() == '200':
                        print 'Missatge enviat correctament'
                else:
                    print 'Server time out...'

            elif scode[0][0] == '/':
                # Comandes no implementades
                print 'Comanda no reconeguda'
            else:
                # Enviar al canal per defecte:
                if afk:
                    print 'Estas AFK. Desactiva el AFK per poder enviar missatges!'
                else:
                    clientSocket.send('100 '+current_channel+' '+' '.join(scode[:]))
                    if e_rcv.poll(2):
                        if e_rcv.recv() != '200':
                            print '@@ ERR: No s\'ha pogut enviar el missatge!'
                    else:
                        print 'Server time out...'

    return


def catcher():
    # Funcion que realiza el thread recividor.
    # Decodifica los mensajes entrantes y gestiona mensajes bloqueantes e interrupciones.
    global lastchannelarrival
    global lastuserarrival
    global lastprivateuserarrival
    global current_channel
    while 1:
        try:
            rc_sentence = clientSocket.recv(2048).split(' ')
        except:
            print 'Conexion perdida con el host... finalizando el programa...'
            return
        size_rc = rc_sentence.__len__()

        # Codigos no bloqueantes: Los gestiona el catcher. Picher no espera recibirlos
        if rc_sentence[0] == '000':
            # Mensaje normal
            lastuserarrival = rc_sentence[2]     # For future uses
            lastchannelarrival = rc_sentence[1]  # For future uses
            print ' '.join(rc_sentence[3:])

        elif rc_sentence[0] == '001':
            # Mensaje privado
            lastprivateuserarrival = rc_sentence[1]
            print '['+lastprivateuserarrival+']: '+' '.join(rc_sentence[2:])
        elif rc_sentence[0] == '002' or rc_sentence[0] == '004':
            # Mensaje positivo/negativo del servidor
            if size_rc > 1:
                print ' '.join(rc_sentence[1:])

        elif rc_sentence[0] == '003':
            # Broadcast!
            print '[BROADCAST] > '+' '.join(rc_sentence[1:])

        # Codigos bloqueantes: Pitcher necesita codigo de confirmacion/error para poder continuar
        elif rc_sentence[0] == '200':
            # 200 OK
            e_snd.send(rc_sentence[0])

        # Codigo especial: Mensaje de bienvenida al servidor.
        elif rc_sentence[0] == '250':
            # Welcome message
            print '###'+' '.join(rc_sentence[1:])

        # Interrupciones: Mensajes que realizan cambios en el contexto del cliente.
        # Pueden terminar la ejecucion del programa, modificar variables o informar al usuario
        elif rc_sentence[0] == '500':
            # Servidor desconectat de forma segura
            print 'El servidor s\'ha desconnectat.'
            return
        elif rc_sentence[0] == '501':
            # Canal eliminat! Mirem si el current_channel es el del eliminat.
            if current_channel == rc_sentence[1]:
                print '## Canal '+rc_sentence[1]+' elimintat!\n## Estas escribint en el canal '+__hall
                current_channel = __hall
            else:
                print '## Canal '+rc_sentence[1]+' elimintat!'
        elif rc_sentence[0] == '502':
            # Interrupcio! Usuari expulsat del canal.
            print '$$ '+' '.join(rc_sentence[2:])
            if rc_sentence[1] == current_channel:
                current_channel = __hall
                print '## Estas escribint en el canal '+__hall

        elif rc_sentence[0] == '503':
            # Interrupcio! Usuari expulsat del servidor
            print '$$ '+' '.join(rc_sentence[2:])
            return

        # Codigos bloqueantes de error: Codigos de la familia 300 y 400 que son respuesta a una peticion a
        # servidor por parte del pitcher.
        # En futuras implementaciones se pueden poner mensajes personalizados para mostrar los codigos de error.
        # Actualmente: Poner codigo en el pull_events y mostrar mensaje estandar del servidor.
        else:
            e_snd.send(rc_sentence[0])
            if size_rc > 1:
                # Por seguridad. Todos los mensajes tienen que ser minimo de tamanyo 2
                print '## '+' '.join(rc_sentence[1:])

    return

# Thread de control del pitcher y el catcher. Solo inicia el programa y espera a su finalizacion.
# No participa en el intercambio de mensajes cliente/servidor mas que para establecer la conexion

# serverName = 'chat.alejandroj19.koding.io'
serverName = 'localhost'
serverPort = 12000

# Optional server name argument
if len(sys.argv) > 1:
    serverName = sys.argv[1]

# Optional server port number
if len(sys.argv) > 2:
    serverPort = int(sys.argv[2])

# Request IPv4 and TCP communication
clientSocket = socket(AF_INET, SOCK_STREAM)

# Open the TCP connection to the server at the specified port
try:
    clientSocket.connect((serverName, serverPort))
except:
    print 'No es pot connectar amb el servidor'
    print 'Server: '+serverName
    print 'Port: %d' % serverPort
    exit(-4)

rec = threading.Thread(target=catcher, name='Catcher')
rec.start()

env = threading.Thread(target=pitcher, name='Pitcher')
env.start()


if env.isAlive() and rec.isAlive():
    print('Cliente conectado correctamente')
    while rec.isAlive():
        i = 0
    print 'Cerrando el programa. Apreta ENTER para salir...'
    connected = False
    env.join()
    print 'Done... bye!\nChatMultiCanal: Alejandro Jurnet | Raul Sanchez'
else:
    print('Error al iniciar el cliente')