########## IMPORTATIONS ##########
import tft_config    #Module natif qui prend en charge la configuration de l'écran
import tft_buttons    #Module natif qui prend en charge l'utilisation des boutons
import st7789    #Module natif qui prend en charge une partie de l'affichage sur l'écran
import vga2_8x16    #Police d'écriture native
import vga2_8x8    #Police d'écriture native
import vga2_bold_16x32    #Police d'écriture native
import network    #Module natif qui prend en charge la connexion à un point d'accès wifi
from time import sleep    #Le module time
import ntptime    #Module natif qui permet d'utiliser le protocole ntp (Network Time Protocol)
from machine import RTC    #Module natif qui permet de faire énormément de choses mais qui dans ce cas va régler l'horloge interne
import json    #Module natif qui permet de convertir le résultat des requêtes en un format utilisable en python
import urequests    #Module natif qui permet de faire des requêtes sur internet
from login_wifi import SSID, PASSWORD    #Fichier login_wifi.py qui permet de modifier les logins wifi de l'esp32
                                         #(fait dans un autre fichiers pour réduire les risques d'erreurs)

########## ECRAN ##########
ecran_initialise = False #Variable global pour savoir si l'écran est initialisé ou pas
tft = tft_config.config(1) #Variable globale qui représente l'écran et qui en utilisant des méthodes permet de faire des choses avec
def afficher_texte(txt, x=0, y=0, alaligne=False, police=vga2_8x16): #Fonction qui permet d'afficher du texte à l'écran
    global ecran_initialise
    if not ecran_initialise:
        initialisation()
    if not alaligne:
        tft.fill(st7789.BLACK)
    tft.text(police, txt, x, y, st7789.WHITE, st7789.BLACK)

def deinit(): #Fonction qui déinitialise l'écran
    global ecran_initialise
    if ecran_initialise:
        tft.deinit()
        ecran_initialise = False

def initialisation(): #Fonction qui initialise l'écran
    global ecran_initialise 
    tft.init()
    ecran_initialise = True
    
########## INTERNET ##########
wlan = network.WLAN(network.STA_IF) #Variable global qui permet de s'occuper d'accéder à internet
wlan.active(True) #Activation du point d'accès
def do_connect(ssid=SSID, password=PASSWORD): #Fonction qui permet de se connecter à un accès internet
    wlan.connect(ssid, password) #Lancement en arrière plan de la connexion
    essai = 0
    while wlan.isconnected() == False: #Tant que la connexion n'est pas faite...
        essai += 1
        afficher_texte('Connecting.  ', 0, 0, True) #Affichage de message
        sleep(0.5)
        afficher_texte('Connecting.. ', 0, 0, True)
        sleep(0.5)
        afficher_texte('Connecting...', 0, 0, True)
        sleep(0.5)
        if essai == 10: #Si il y a 10 essais de connexions qui n'aboutissent pas...
            break #Sortie de la boucle while
    if essai == 10: #Si il y a 10 essais de connexions qui n'aboutissent pas... 
        afficher_texte('Connexion impossible...', 0, 0) 
        afficher_texte('Tentez de modifier login_wifi.py', 0, 20, True) #Affichage du message d'erreur...
        while True: #Puis une boucle infini pour ne pas exécuter le reste du code qui ne fonctionnera pas
            pass
    afficher_texte('Connected to :', 0, 0) #Sinon message qui indique que l'esp32 est connecté
    afficher_texte(ssid, 0, 20, True)
    sleep(1)
    tft.fill(st7789.BLACK) #Remplit l'écran en noir

def disconnect(): #Fonction qui permet de se déconnecter d'un réseau
    wlan.disconnect()    
    
########## HEURE ##########
ntptime.host = 'ntp.unice.fr' #Définition du site où la demande de l'heure est faite
def set_heure(): #Fonction qui règle l'heure de l'horloge interne en demandant au serveur
    if not wlan.isconnected(): #Si pas connecté, se connecte au réseau
        do_connect()
    ntptime.settime() #Règle l'horloge interne de l'esp32 selon l'heure donnée par le serveur

def get_heure(): #Fonction qui renvoie une liste du format : 
                 #[année, mois, jour, jour de la semaine, heure, minute, seconde, milliseconde] 
    heure = list(RTC().datetime()) #Récupération de l'heure interne
    heure[4] += 1 #Décalage horaire
    if heure[4] == 24:
        heure[4] = 0
    if len(str(heure[6]))==1: #Ajout d'un 0 si l'heure, la minute ou la seconde ne comporte qu'un chiffre
        heure[6] = '0' + str(heure[6])
    if len(str(heure[4]))==1:
        heure[4] = '0' + str(heure[4])
    if len(str(heure[5]))==1:
        heure[5] = '0' + str(heure[5])
    return heure  
    
def afficher_heure(): #Fonction qui permet d'afficher en gros au milieu de l'écran l'heure avec les secondes
    temps = get_heure() #Définition de l'heure actuelle
    afficher_texte("Menu ->", 264, 0, True) #Affichage permettant de savoir sur quel bouton appuyer pour retourner au menu
    while bouton_droite.value() == 1: #Tant que le bouton de droite n'est pas appuyé
        if get_heure()[6] != temps[6]: #Si l'heure actuelle diffère de celle définie en dehors de la boucle
            afficher_texte(f"{temps[4]} : {temps[5]} : {temps[6]}", 64, 69, True, vga2_bold_16x32) #Affichage de l'heure
            temps = get_heure() #Définition de l'heure pour recommencer la vérification du if
    menu() #Affichage du menu
    while bouton_droite.value() == 0: #Tant que le bouton de droite est appuyé, ne rien faire
        pass
        
########## METEO ##########
adresse_meteo = "https://api.openweathermap.org/data/2.5/weather?lat=43.95&lon=4.8167&appid=6dc180325a613e8fe2292078d342022a&lang=fr"
#Variable globale qui définit le lien de l'API de météo
def meteo(): #Fonction qui fait une requête au serveur de météo et qui renvoie une liste de certaines infos
    if not wlan.isconnected(): #Si pas connecté, se connecte au réseau
        do_connect()
    data = json.loads(urequests.get(adresse_meteo).text) #Fait la requête et la convertie pour être utilisable en python
    temperature = str(round(data.get("main").get("temp") - 273.15, 1)) #Température en kelvin puis en celsius
    if len(temperature) == 3: #Si la temp est de ce format : 1.2 fait de la temp ce format : 01.2
        temperature = '0' + temperature
    humidite = str(data.get("main").get("humidity")) # Humidité
    if len(humidite) == 1: #Comme pour la temperature
        humidite = '0' + humidite
    vent_vitesse = data.get("wind").get("speed") * 3.6 # vitesse du vent en m/s puis en Km/h
    vent_orientation = data.get("wind").get("deg")  # origine du vent en degré
    image = 'image/' + data.get('weather')[0].get('icon') + '.png' #Récupération du code de l'image puis mise dans le bon format
    description = data.get('weather')[0].get('description') #Description de la météo
    nom_ville = f"{data.get('name')}, {data.get('sys').get('country')}" #Récupération du nom de la ville
    return [temperature, humidite, str(round(vent_vitesse)), str(vent_orientation), image, description, nom_ville]
    
def station_meteo(): #Fonction qui s'occupe d'afficher les données de la météo et qui s'actualise toutes les minutes
    actualisation = True #Variables qui dit si oui ou non la météo doit s'actualiser chaque minutes
    while actualisation: #Boucle while tant que actualisation == True
        data = meteo() #Récupère les infos de la météo
        heure = get_heure() #Récupère l'heure
        afficher_texte("Menu ->", 264, 0, False) #Affiche le texte pour le retour au menu
        
        longueur = int((320-(len(data[6]))*8)/2) #Affiche le nom de la ville 
        for i in range(len(data[6])):            #Lettre par lettre pour éviter les problèmes dû aux accents
            if data[6][i] == '\xe9':
                lettre = 130
            elif data[6][i] == '\xe8':
                lettre = 138
            elif data[6][i] == '\xe0':
                lettre = 133
            elif data[6][i] == '\xe7':
                lettre = 135
            else:
                lettre = data[6][i]
            afficher_texte(lettre, longueur, 5, True)
            longueur += 8

        tft.fill_rect(0, 44, 320, 1, st7789.WHITE) #Fait une barre blanche pour séparer le nom de la ville du reste
        
        #Affichage de la température
        temp = [data[0][0]+data[0][1], data[0][2]+data[0][3]]
        
        afficher_texte('Temp', 28, 50, True)
        afficher_texte(temp[0], 20, 67, True, vga2_bold_16x32)
        afficher_texte(temp[1], 52, 81, True, vga2_8x16)
        afficher_texte('o', 52, 67, True, vga2_8x8)
        afficher_texte('C', 60, 67, True, vga2_8x16)
        
        #Affichage de l'heure et des minutes
        afficher_texte(f"{heure[4]} : {heure[5]}", 132, 25, True)
        
        #Affichage de l'humidité
        x = 20
        if len(data[1]) == 3:
            x -= 8
        afficher_texte("Humid", 24, 105, True)
        afficher_texte(data[1] + '%', x, 122, True, vga2_bold_16x32)
        
        #Affichage de l'image selon le code donné
        tft.png(data[4], 110, 30, True)    
        
        #Affichage du vent avec sa vitesse et sa direction
        y = 67
        if len(data[2]) == 1:
            x = 252
        elif len(data[2]) == 2:
            x = 244
        else:
            x = 236
        afficher_texte('Vent', 260, 50, True)
        afficher_texte(data[2], x, y, True, vga2_bold_16x32)
        afficher_texte('Km/h', x + len(data[2])*16, y+14, True) 
        
        y = 122
        if len(data[3]) == 1:
            x = 264
        elif len(data[3]) == 2:
            x = 256
        else:
            x = 248
        afficher_texte("Direc", 256, 105, True)
        afficher_texte(data[3], x, y, True, vga2_bold_16x32)
        afficher_texte('o', x + len(data[3])*16, y, True, vga2_8x8)
        
        #Affichage de la description qui correspond à l'image
        longueur = int((320-(len(data[5]))*8)/2)
        for i in range(len(data[5])):
            if data[5][i] == '\xe9':
                lettre = 130
            elif data[5][i] == '\xe8':
                lettre = 138
            elif data[5][i] == '\xe0':
                lettre = 133
            elif data[5][i] == '\xe7':
                lettre = 135
            else:
                lettre = data[5][i]
            afficher_texte(lettre, longueur, 108, True)
            longueur += 8
        
        #Attente pour actualisation avec retour possible au menu
        while True:
            if get_heure()[5] != heure[5]: #Si la minute change on refait un tour de la boucle principale
                break
            if bouton_droite.value() == 0: #Si on appuie sur le bouton de droite on sort des boucles pour retourner au menu
                actualisation = False
                break
    menu() #Affichage du menu
    while bouton_droite.value() == 0: #Ne rien faire tant que le bouton de droite est appuyé
        pass

########## BOUTONS ##########    
boutons = tft_buttons.Buttons() #Récupération des boutons de l'esp32   
bouton_gauche = boutons.left  #Définition des boutons dans des variables
bouton_droite = boutons.right
#bouton_gauche.value() == 0 si appuie, 1 si relâché
#bouton_droite.value() == 0 si appuie, 1 si relâché

def wait(): #Fonction qui permet de récupérer l'appui d'un bouton et
    while True: #qui attend son relâchement avant de renvoyer le bouton appuyé
        if bouton_gauche.value() == 0:
            while bouton_gauche.value() == 0:
                pass
            return 'gauche'
        if bouton_droite.value() == 0:
            while bouton_droite.value() == 0:
                pass
            return 'droite'
        
########## MENU ##########
def menu(): #Fonction qui affiche le menu
    tft.fill(st7789.BLACK) #Remplit l'écran en noir
    longueur = 256 #Et affiche ce que font les boutons
    mot = "Météo ->"
    for i in range(len(mot)):
        if mot[i] == '\xe9':
            lettre = 130
        else:
            lettre = mot[i]
        afficher_texte(lettre, longueur, 0, True)
        longueur += 8
    afficher_texte("Heure ->", 256, 154, True)
    
    longueur = 56
    mot = "Station Météo"
    for i in range(len(mot)):
        if mot[i] == '\xe9':
            lettre = 130
        else:
            lettre = mot[i]
        afficher_texte(lettre, longueur, 69, True, vga2_bold_16x32)
        longueur += 16
    afficher_texte("By Robin.C", 0, 154, True)
           
########## MAIN ##########
def main(): #Fonction principale qui s'occupe de tout
    if not wlan.isconnected(): #Si pas connecté, se connecte au réseau
        do_connect()
    set_heure()
    menu()
    
    while True: #Boucle infini qui appelle les fonctions
        bouton = wait()
        if bouton == 'gauche':
            tft.fill(st7789.BLACK)
            afficher_heure()
        if bouton == 'droite':
            tft.fill(st7789.BLACK)
            station_meteo()

########## DÉMARRAGE ##########
#Essaie d'exécuter main() et si ça plante ou si l'exécution est interrompu
#Déinitialise l'écran pour éviter des problèmes lors d'autres exécutions
#Et désactive aussi le point d'accès pour encore une fois éviter des problèmes
try:
    main()
finally:
    deinit()
    wlan.active(False) 