#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "ALEJANDRO & RAUL"
from socket import *
import sys
import threading
import string
from time import strftime, localtime
import time


lusers = list()
lcanals = list()
threads = list()
th_client = list()
chnextid = 1
connected = True


def hora(opt):
    if opt == 1:
        return strftime("%a, %d %b %Y %H:%M:%S", localtime())
    else:
        return strftime("[%H:%M:%S]", localtime())


def busca_canal(nom):
    for i in range(lcanals.__len__()):
        if lcanals[i].nom.lower() == nom.lower():
            return i
    return -1


def busca_canal_id(cid):
    for i in range(lcanals.__len__()):
        if lcanals[i].id == cid:
            return i
    return -1


def isinchannel(cid, uid):
    _ch = busca_canal_id(cid)
    if _ch != -1:
        return lcanals[_ch].finduser(uid)
    else:
        return False


def busca_usuari(nom):
    for i in range(lusers.__len__()):
        if lusers[i].username.lower() == nom.lower():
            return i
    return -1


def identifica_usuari(idu):
    for i in range(lusers.__len__()):
        if lusers[i].id == idu:
            return i
    return -1


def enviar_broadcast(msg, idu):
    # Enviar un missatge especial a tots els usuaris menys al idu
    for j in range(lusers.__len__()):
        try:
            if lusers[j].id != idu:
                lusers[j].socket.send('003 '+msg)
        except:
            continue


class Usuari:
    def __init__(self, uid, zsocket, nombre):
        self.id = uid            # Unique User ID (UID)
        self.socket = zsocket    # Socket de Connexio
        self.username = nombre  # Alias
        self.canals_owned = list()  # Canals creats per l'usuari (UID)
        self.ausent = False     # AFK

    def addcanal(self, canal):
        self.canals_owned.append(canal)

    def eliminacanal(self, canal):
        self.canals_owned.remove(canal)

    def doausent(self):
        self.ausent = not ausent


class Canal:
    global lusers

    def __init__(self, cid, name, owner, pw):
        self.id = cid        # Unique Channel ID (CID)
        self.nom = name      # Alias
        self.user = owner    # Owner (ID)
        self.password = pw   # Password
        self.llista_usuaris = list()    # Current Users in the Channel (UID)

    def addusuari(self, usuari):
        self.llista_usuaris.append(usuari)

    def delusuari(self, usuari):
        self.llista_usuaris.remove(usuari)

    def enviarmissatge(self, missatge, numeroclient):
        for i in range(self.llista_usuaris.__len__()):
            if self.llista_usuaris[i] != numeroclient:
                idcl = identifica_usuari(self.llista_usuaris[i])
                try:
                    if idcl != -1:
                        lusers[idcl].socket.send(missatge)
                except:
                    continue

    def finduser(self, uid):
        for i in range(self.llista_usuaris.__len__()):
            if self.llista_usuaris[i] == uid:
                return True
        return False


def t_client(num, socket):
    global chnextid
    global lusers
    global lcanals
    global connected
    err = True
    sentence = "250 Welcome Eres el cliente numero %d que se ha conectado\nIndica tu nombre de usuario:  " % num
    socket.send(sentence)
    nombre = ''.split(' ')
    while err:
        try:
            nombre = socket.recv(2048).split(' ')
        except:
            return
        if nombre.__len__() < 2:
            # Bad client
            socket.send('400 ERROR - El programa que estas utilitzant no es compatible amb el servidor!')
            socket.close()
            return
        if busca_usuari(nombre[1]) != -1:
            socket.send('450 BadLogin El nombre ya esta siendo usado por otro usuario\nIndica tu nombre de usuario:   ')
        else:
            err = False
    welcsentence = "Usuari " + nombre[1] + " connectat al servidor."
    print hora(0)+'## '+welcsentence
    enviar_broadcast(welcsentence, num)
    us = Usuari(num, socket, nombre[1])
    lusers.append(us)
    lcanals[0].addusuari(num)
    us.socket.send('200 OK')
    socket.send('250 ###########################################################\n' +
                '\tConectado correctamente al servidor.\n\tBienvenido al servidor '+us.username+'!\n' +
                '\tHora del servidor: '+hora(1)+'\n' +
                '\tUsuarios conectados: {0:d}  Canales Disponibles: {1:d}\n'.format(lusers.__len__(), lcanals.__len__()) +
                '##############################################################\n')

    while connected:
        sentence = ''
        try:
            sentence = socket.recv(2048)
        except:
            # Client desconnectat! Eliminar de forma segura!
            if connected:
                print hora(0)+'@@ '+us.username+' desconnectat sobtadament del servidor.'
                usuari = busca_usuari(us.username)
                if usuari != -1:
                    lusers.remove(lusers[usuari])
                    print hora(0)+'@@ Eliminant '+us.username+' de la base de usuaris.'
            return

        s_sentence = sentence.split(' ')
        s_size = s_sentence.__len__()

        try:
            code = int(s_sentence[0])
            err = False

        except:
            try:
                socket.send('402 BadRequest')
            except:
                return
            err = True

        if not err:
            if code == 100:
                # Missatge Normal
                if s_size < 2:
                    socket.send('403 BadSintax')
                else:
                    channel = busca_canal(s_sentence[1])
                    if channel == -1:
                        socket.send('404 NotFound')

                    elif isinchannel(lcanals[channel].id, num):
                        sentence = '000 '+s_sentence[1]+' '+nombre[1]+' [' + us.username + ' - ' + lcanals[channel].nom + '] '+' '.join(s_sentence[2:])
                        lcanals[channel].enviarmissatge(sentence, num)
                        socket.send('200 OK')

                    else:
                        socket.send('401 NotAuthorized')

            elif code == 101:
                # Missatge Privat
                if s_size < 2:
                    socket.send('403 BadSintax')
                else:
                    usuari = busca_usuari(s_sentence[1])
                    if usuari == -1:
                        socket.send('404 NotFound')
                    else:
                        sentence = '001 '+us.username+' '+' '.join(s_sentence[2:])
                        try:
                            lusers[usuari].socket.send(sentence)
                            socket.send('200 OK')
                        except:
                            socket.send('400 ERROR')

            elif code == 110:
                # Crear Canal i unir al usuari
                if s_size < 2:
                    socket.send('403 BadSintax')
                elif busca_canal(s_sentence[1]) == -1:
                    lcanals.append(Canal(chnextid, s_sentence[1], num, ''))
                    lusers[identifica_usuari(num)].addcanal(chnextid)
                    chnextid += 1
                    lcanals[busca_canal(s_sentence[1])].addusuari(num)
                    socket.send('200 OK Channel ' + s_sentence[1] + ' Created')
                    print hora(0)+'## Canal ' + s_sentence[1] + ' creat. Owner: '+us.username+' Password: []'
                else:
                    socket.send('407 El canal ja existeix.')

            elif code == 111:
                # Posar contrasenya
                if s_size < 3:
                    socket.send('403 BadSintax')
                else:
                    canal = busca_canal(s_sentence[1])
                    if canal == -1:
                        socket.send('404 NotFound')
                    else:
                        if lcanals[canal].user == num:
                            lcanals[canal].password = s_sentence[2]
                            socket.send('200 OK')
                            print hora(0)+'## Canal ' + s_sentence[1] + ' ara te la password: ' + s_sentence[2]
                        else:
                            socket.send('401 Unauthorized')

            elif code == 112:
                # Eliminar password
                if s_size < 2:
                    socket.send('403 BadSintax')
                else:
                    canal = busca_canal(s_sentence[1])
                    if canal == -1:
                        socket.send('404 NotFound')
                    else:
                        if lcanals[canal].user == num:
                            lcanals[canal].password = ''
                            socket.send('200 OK')
                        else:
                            socket.send('401 Unauthorized')

            elif code == 113:
                # Eliminar canal
                if s_size < 2:
                    socket.send('403 BadSintax')
                else:
                    canal = busca_canal(s_sentence[1])
                    if canal == -1:
                        socket.send('404 NotFound')
                    elif lcanals[canal].user == num:
                        nom = lcanals[canal].nom
                        try:
                            # Eliminar del owner el seu canal i avisar a tots els usuaris que pertanyen al canal
                            ind = identifica_usuari(num)
                            lusers[ind].eliminacanal(lcanals[canal].id)
                            lcanals[canal].enviarmissatge('501 '+lcanals[canal].nom, num)
                            lcanals.remove(lcanals[canal])
                            socket.send('200 OK')
                            print hora(0)+'## S\'ha eliminat el canal '+nom+' del servidor. Owner: '+us.username
                        except:
                            print hora(0)+'@@ No s\'ha pogut eliminar el canal '+lcanals[canal].nom+'. User request: '+us.username
                            socket.send('400 ERROR')
                    else:
                        socket.send('401 Unauthorized')

            elif code == 114:
                # AFK
                if s_size < 1:
                    socket.send('403 BadSintax')
                else:
                    lusers[identifica_usuari(num)].doausent()
                    socket.send('200 OK')

            elif code == 116:
                # Kick
                if s_size < 3:
                    socket.send('403 BadSintax')
                else:
                    canal = busca_canal(s_sentence[2])  #busquem el canal
                    if canal == -1:
                        socket.send('404 NotFound')
                    elif lcanals[canal].user == num:
                        kickd = busca_usuari(s_sentence[1]) #busquem l'usuari
                        if kickd == -1:
                            socket.send('404 NotFound')
                        else:
                            lcanals[canal].delusuari(lusers[kickd].id)  #L'eliminem de la llista
                            socket.send('200 OK')
                            print hora(0)+'## '+s_sentence[1] + ' ha estat expulsat del canal ' + lcanals[canal].nom
                            if s_size == 3:
                                sentence = 'Has sigut expulsat del canal ' + s_sentence[2]
                            else:
                                sentence = ' '.join(s_sentence[3:])
                            try:
                                # Enviem al expulsat el missatge
                                lusers[kickd].socket.send('502 '+s_sentence[2]+' '+sentence)
                            except:
                                socket.send('400 ERROR')
                    else:
                        socket.send('401 Unauthorized')

            elif code == 104:
                # Entrar canal amb psw
                if s_size < 3:
                    socket.send('403 BadSintax')
                else:
                    canal = busca_canal(s_sentence[1])
                    if canal == -1:
                        socket.send('404 NotFound')
                    elif not isinchannel(lcanals[canal].id, num):
                        if lcanals[canal].password == s_sentence[2]:
                            lcanals[canal].addusuari(num)
                            socket.send('200 OK')
                        else:
                            socket.send('405 BadPassword')
                    else:
                        socket.send('400 ERROR')

            elif code == 105:
                # Entrar Canal
                if s_size < 2:
                    socket.send('403 BadSintax')
                else:
                    channel = busca_canal(s_sentence[1])
                    if channel == -1:
                        socket.send('404 NotFound')
                    elif not isinchannel(lcanals[channel].id, num):
                        if lcanals[channel].password == '':
                            lcanals[channel].addusuari(num)
                            socket.send('200 OK')
                        else:
                            socket.send('301 PsswRequired')
                    else:
                        socket.send('400 ERROR')

            elif code == 106:
                # Llistar tots els canals
                arcanals = ''
                if s_size < 2:
                    socket.send('403 BadSintax')
                elif s_sentence[1] == 'allch':
                    for i in range(lcanals.__len__()):
                        arcanals += lcanals[i].nom + '\n'

                elif s_sentence[1] == 'allus':
                    for i in range(lusers.__len__()):
                        arcanals += lusers[i].username+'\n'

                socket.send('002 ' + arcanals)

            elif code == 107:
                # Llistar canals on esta l'usuari
                arcanals = ''
                for i in range(lcanals.__len__()):
                    if lcanals[i].finduser(num):
                        arcanals += lcanals[i].nom + '\n'
                socket.send('002 '+arcanals)

            elif code == 108:
                # Listar Canals creats per l'usuari
                arcanals = ''
                for i in range(lcanals.__len__()):
                    if lcanals[i].user == num:
                        arcanals += lcanals[i].nom + '\n'
                socket.send('002 '+arcanals)

            elif code == 120:
                # Llistar Usuaris d'un canal
                if s_size < 2:
                    socket.send('403 BadSintax')
                else:
                    # Busquem el canal
                    canal = busca_canal(s_sentence[1])
                    if canal == -1:
                        socket.send('004 ## El canal no s\'ha trovat!')
                    else:
                        arcanals = ''
                        for i in range(lcanals[canal].llista_usuaris.__len__()):
                            ident = identifica_usuari(lcanals[canal].llista_usuaris[i])
                            if ident > -1:
                                arcanals += lusers[ident].username+'\n'
                        socket.send('002 '+arcanals)

            elif code == 119:
                # Retornar si existeix o no el canal
                canal = busca_canal(s_sentence[1])
                if canal == -1:
                    socket.send('404 NotFound')
                else:
                    socket.send('200 OK')

            elif code == 109:
                # Sortir del canal
                if s_size < 2:
                    socket.send('403 BadSintax')
                else:
                    channel = busca_canal(s_sentence[1])
                    if channel == -1:
                        socket.send('404 NotFound')
                    elif isinchannel(lcanals[channel].id, num):
                        lcanals[channel].delusuari(num)
                        socket.send('200 OK')
                    else:
                        socket.send('400 ERROR')

            elif code == 500:
                # Desconnexio segura del client
                print hora(0)+'## '+us.username+' desconnectat del servidor.'
                try:
                    # Per assegurar la desconnexio
                    socket.send('500')
                except:
                    continue
                usuari = busca_usuari(us.username)
                if usuari != -1:
                    lusers.remove(lusers[usuari])
                    print '~~ Eliminant '+us.username+' de la base de usuaris.'
                return

            else:
                socket.send('402 BadRequest')

    # Tencar per seguretat el socket
    try:
        socket.send('500')
        print hora(0)+'## Desconnectant '+us.username+' del servidor.'
        usuari = busca_usuari(us.username)
        if usuari != -1:
            lusers.remove(lusers[usuari])
            print '~~ Eliminant '+us.username+' de la base de usuaris.'
    except:
        connected = connected


def t_novesconnexions():
    global connected
    serverSocket.listen(1)
    print '\t\t////////////////////'
    print 'The server is ready to receive'
    print 'Local time server: '+hora(1)
    print '\t\t////////////////////\n\n'
    ji = 1
    while connected:
        connectionsockett, addrt = serverSocket.accept()
        t = threading.Thread(target=t_client, args=(ji, connectionsockett))
        th_client.append(t)
        t.start()
        ji += 1


# Default port number server will listen on
serverPort = 12000

# Optional server port number
if len(sys.argv) > 1:
    serverPort = int(sys.argv[1])

# Request IPv4 and TCP communication
serverSocket = socket(AF_INET, SOCK_STREAM)

# The welcoming port that clients first use to connect
serverSocket.bind(('', serverPort))


admin = Usuari(-4, None, 'SERVER_ADMIN')
ch = Canal(0, '0_Hall', -4, '')
lcanals.append(ch)

th = threading.Thread(target=t_novesconnexions)
threads.append(th)
th.start()

time.sleep(1)

while connected:
    # Server Hatmin: El servidor pot executar ordres directament desde terminal.
    raw_sentence = raw_input('|> ')
    scode = raw_sentence.split(' ')
    size_scode = scode.__len__()

    if raw_sentence.__len__() != 0 and not raw_sentence.isspace() and connected:
        if scode[0] == '/broadcast':
            # Comanda Admin: El servidor envia un missatge per difussio directament a tots els usuaris del servidor
            # Aquest missatge es tractat de manera especial per futures implementacions.
            if size_scode < 2:
                print '/broadcast <msg>'
            else:
                enviar_broadcast(' '.join(scode[1:]), admin.id)
        elif scode[0] == '/create':
            # Comanda Admin: Crea un canal on el Server Admin es el propietari
            # Admet directament crear-lo amb contrasenya
            contrasenya = ''
            if size_scode < 2:
                print '/create <ch> [pw]'
            else:
                if size_scode > 2:
                    contrasenya = scode[2]
                lcanals.append(Canal(chnextid, scode[1], admin.id, contrasenya))
                chnextid += 1
                print hora(0)+'## Canal ' + scode[1] + ' creat. Owner: '+admin.username+' Password: ['+contrasenya+']'

        elif scode[0] == '/dc':
            # Comanda Admin: El servidor tenca totes les seves connexions i finalment finalitza el proces.
            connected = False
            serverSocket.close()
        elif scode[0] == '/delete':
            # Comanda Admin: Eliminar un canal del servidor.
            if size_scode < 2:
                print '/delete <ch>'
            elif scode[1] == '0_Hall':
                print hora(0)+'@@ No es pot eliminar el 0_Hall'
            else:
                scanal = busca_canal(scode[1])
                if scanal == -1:
                    print hora(0)+'@@ El canal no existeix.'
                else:
                    snom = lcanals[scanal].nom
                    user = lcanals[scanal].user
                    sind = 0
                    try:
                        # Eliminar del owner el seu canal i avisar a tots els usuaris que pertanyen al canal
                        cnom = ''
                        sind = identifica_usuari(user)
                        lcanals[scanal].enviarmissatge('501 '+snom, admin.id)
                        if sind > -1:
                            lusers[sind].eliminacanal(lcanals[scanal].id)
                            cnom = lusers[sind].nom
                        else:
                            cnom = admin.username
                        lcanals.remove(lcanals[scanal])
                        print hora(0)+'## S\'ha eliminat el canal '+snom+' del servidor. Owner: '+cnom
                    except:
                        print hora(0)+'@@ No s\'ha pogut eliminar el canal '+snom

        elif scode[0] == '/help':
            # Comanda Admin: Mostra totes les comandas que pot executar.
            print '\t\t\t## \t\tHELP\t ##'
            print '> /broadcast <msg> \t\t-- Envia <msg>'
            print '> /create <chname> \t-- Crea un canal amb nom <chname>.'
            print '> /dc \t\t\t\t-- Desconecta el servidor.'
            print '> /delete <ch> \t\t-- Elimina el canal <ch>'
            print '> /help \t\t\t-- Mostra totes les comandes del servidor i una breu descripcio'
            print '> /infoc <ch> \t\t-- Mostra la informacio del canal <ch>'
            print '> /infou <us> \t\t-- Mostra la informacio de l\'usuari <ch>'
            print '> /kick <user> <ch> [msg] - Expulsa al <user> del canal <ch>.'
            print '> /kicks <user> [msg] -- Expulsa al <user> del servidor.'
            print '> /list \t\t\t-- Dona totes les subordres de la comanda /list.'
            print '> /list <allch/allus/owned/users <ch>> -- Subordres especifiques del /list'
            print '> /say <ch> <msg> \t-- Dona totes les subordres de la comanda /list.'
            print '> /tell <user> [msg] -- Envia un missatge privat al <user>.'

        elif scode[0] == '/infoc':
            # Comanda Admin: Mostra la info del canal.
            if size_scode < 2:
                print '/infoc <ch>'
            else:
                scanal = busca_canal(scode[1])
                if scanal == -1:
                    print hora(0)+'@@ Canal no trobat'
                else:
                    propietari = ''
                    try:
                        if lcanals[scanal].user == admin.id:
                            propietari = admin.username
                        else:
                            propietari = lusers[identifica_usuari(lcanals[scanal].user)].username
                        straux = '%d' % lcanals[scanal].id
                        print hora(0)+'## ID: '+straux+' | Nom: '+lcanals[scanal].nom+' | Propietari: '+propietari+' | Contrasenya: ['+lcanals[scanal].password+']'
                    except:
                        print hora(0)+'@@ Error al obtenir info del canal.'

        elif scode[0] == '/infou':
            # Comanda Admin: Mostra informació de l'usuari.
            if size_scode < 2:
                print '/infou <us>'
            else:
                susuari = busca_usuari(scode[1])
                if susuari == -1:
                    print hora(0)+'@@ Usuari no trobat.'
                else:
                    idaux = '%d' % lusers[susuari].id
                    print hora(0)+'## ID: '+idaux+' | Nom: '+lusers[susuari].username+' | AFK?: '+str(lusers[susuari].ausent)
                    ssentence = 'Canals Creats: '
                    for z in range(lusers[susuari].canals_owned.__len__()):
                        scanal = busca_canal_id(lusers[susuari].canals_owned[z])
                        ssentence += lcanals[scanal].nom + ' | '
                    print ssentence

        elif scode[0] == '/kick':
            # Comanda Admin: Expulsa al usuari del canal
            if size_scode < 3:
                print '/kick <us> <ch> [msg]'
            else:
                scanal = busca_canal(scode[2])
                skickd = busca_usuari(scode[1])
                if scanal == -1:
                    print hora(0)+'@@ Canal no trobat'
                elif skickd == -1:
                    print hora(0)+'@@ Usuari no trobat'
                else:
                    lcanals[scanal].delusuari(lusers[skickd].id)
                    print hora(0)+'## '+scode[1] + ' ha estat expulsat del canal ' + lcanals[scanal].nom
                    if size_scode == 3:
                        ssentence = 'Has sigut expulsat del canal ' + scode[2]
                    else:
                        ssentence = ' '.join(scode[3:])
                    try:
                        # Enviem al expulsat el missatge
                        lusers[skickd].socket.send('502 '+scode[2]+' '+ssentence)
                    except:
                        print hora(0)+'@@ No s\'ha pogut expulsar al usuari del canal.'

        elif scode[0] == '/kicks':
            # Comanda Admin: Expulsar al usuari del servidor
            ssentence = '503 Kickfromserver '
            if size_scode < 2:
                print '/kicks <user> [msg]'
            else:
                user = busca_usuari(scode[1])
                if user == -1:
                    print hora(0)+'@@ Usuari no es troba en la base de dades.'
                else:
                    if size_scode > 2:
                        ssentence += ' '.join(scode[2:])
                    else:
                        ssentence += 'Has sigut expulsat del servidor!'
                    lusers[user].socket.send(ssentence)
                    lusers[user].socket.close()
                    lusers.remove(lusers[user])
                    print hora(0)+'## Usuari expulsat del servidor'
                    print hora(0)+'~~ Eliminant '+scode[1]+' de la base de usuaris.'

        elif scode[0] == '/list':
            # Comanda Admin: Mostra totes les subcomandes i les seves funcionalitats
            ssentence = ''
            if size_scode == 1:
                print '## \t\t\t**\tLlista de subcomandes\t** '
                print '/list\t\t\t\t-- Mostra totes les subcomandes del /list.'
                print '/list allch\t\t\t-- Mostra tots els canals del servidor.'
                print '/list allus\t\t\t-- Mostra tots els usuaris del servidor.'
                print '/list users <ch>\t-- Mostra tots els usuaris en el canal especificat.'
            elif scode[1] == 'allch':
                # Comanda Admin: Mostra tots els canals del servidor.
                print hora(0)+'## \t\t--\tLlista de tots els canals:\t--\n'
                # Llistar tots els canals
                for z in range(lcanals.__len__()):
                    ssentence += lcanals[z].nom + ' | '
                print ssentence

            elif scode[1] == 'allus':
                # Comanda Admin: Mostra tots els usuaris del servidor
                print hora(0)+'## \t\t--\tLlista de tots els usuaris:\t--\n'
                for z in range(lusers.__len__()):
                    ssentence += lusers[z].username+' | '
                print ssentence

            elif scode[1] == 'users' and size_scode > 2:
                # Comanda Admin: Mostra tots els usuaris en un canal
                scanal = busca_canal(scode[2])
                if scanal == -1:
                    print hora(0)+'@@ No es troba el canal'
                else:
                    print hora(0)+'## \t\t--\tLlista de tots els usuaris en el canal:\t--\n'
                    sarcanals = ''
                    for z in range(lcanals[scanal].llista_usuaris.__len__()):
                        sident = identifica_usuari(lcanals[scanal].llista_usuaris[z])
                        if sident > -1:
                            sarcanals += lusers[sident].username+' | '
                    print sarcanals

            else:
                # /list no reconegut
                print hora(0)+'@@ Comanda no reconeguda/incorrecta. Fes /list per mostrar totes les subordres.'

        elif scode[0] == '/say':
            # Comanda Admin: Envia un missatge en un canal concret
            if size_scode < 3:
                print '/say <ch> <msg>'
            else:
                scanal = busca_canal(scode[1])
                if scanal == -1:
                    print '@@ Canal no trobat!'
                else:
                    ssentence = '000 '+scode[1]+' '+admin.username+' ['+admin.username+' - '+scode[1]+'] '+' '.join(scode[2:])
                    lcanals[scanal].enviarmissatge(ssentence, admin.id)

        elif scode[0] == '/tell':
            # Comanda Admin:
            if size_scode < 3:
                print '/tell <us> <msg>'
            else:
                susuari = busca_usuari(scode[1])
                if susuari == -1:
                    print hora(0)+'@@ Usuari no trobat!'
                else:
                    ssentence = '001 '+admin.username+' '+' '.join(scode[2:])
                    try:
                        lusers[susuari].socket.send(ssentence)
                    except:
                        print hora(0)+'@@ No s\ha pogut enviar el missatge'

        elif scode[0][0] == '/':
            # Comandes no implementades
            print 'Comanda no reconeguda'
        else:
            # Text pla, no aplicable al server admin
            print 'Si us plau, entra una comanda. Mes info en /help'

print '\t\t////////////////////'
print '\t\tServer shutdown'
print '\t'+hora(1)
print '\tAlejandro Jurnet | Raul Sanchez'
print '\t\t////////////////////'

# $function(esedtrhyjthaegh DAUDE)
exit(4)