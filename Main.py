from machine import Pin, ADC, I2C
import time
import math
from neopixel import NeoPixel as pix
from pcf8523 import PCF8523


######## Paramètres utilisateur.ice ######################## 

nb_vals = 10 #Nombre de valeurs dont on fait la moyenne pour obtenir la valeur finale. !!!!Doit être un diviseur de 30!!!!

mesures_start_time = 7 #Heure de début de mesure
mesures_stop_time = 22  #heure de fin de mesure

#Ajouter un paramètre d'intervalle de temps de mesure. Pour le moment et par défaut, c'est toute les 30 minutes


#### Initialisation des objets harware (capteurs et RTC) ###

capteurs = [ADC(Pin(26)), ADC(Pin(27)), ADC(Pin(28))]
            #B				G				R

i2c = I2C(1)
rtc = PCF8523( i2c )
led = pix(Pin(22),1)
print(led)


######## Constantes et varibales de calcul #################

SML_const = [1./(.133*.7*12.72454), 1./(.36*.7*4.702718), 1./(.79*.85*1.779092)]

S_table = [
[0.0129,0.848684210526316],
[0.0144,0.676056338028169],
[0.0158,0.58955223880597],
[0.0179,0.497222222222222],
[0.0189,0.480916030534351],
[0.0198,0.441964285714286],
[0.0213,0.426],
[0.023,0.397923875432526],
[0.0294,0.355072463768116],
[0.052,0.302325581395349],
[0.0657,0.292],
[0.0818,0.284918146987113],
[0.103,0.283746556473829],
[0.133,0.286637931034483],
[0.173,0.295726495726496],
[0.218,0.302777777777778],
[0.263,0.313095238095238],
[0.31,0.333333333333333],
[0.364,0.385185185185185],
[0.413,0.472689075630252],
[0.45,0.472689075630252],
[0.495,0.518759169985328],
[0.609,0.635566687539136],
[0.837,0.868798007058335],
[0.9449,0.97785366863293],
[0.966,0.9898555179834],
[1.,1.]]




M_table = [
[0.0136,0.894736842105263],
[0.016,0.751173708920188],
[0.0188,0.701492537313433],
[0.0224,0.622222222222222],
[0.0246,0.625954198473282],
[0.0264,0.589285714285714],
[0.0289,0.578],
[0.0323,0.558823529411765],
[0.0443,0.535024154589372],
[0.083,0.482558139534884],
[0.108,0.48],
[0.135,0.470219435736677],
[0.1727,0.475757575757576],
[0.227,0.489224137931035],
[0.289,0.494017094017094],
[0.363,0.504166666666667],
[0.431,0.513095238095238],
[0.503,0.540860215053763],
[0.584,0.617989417989418],
[0.659,0.745798319327731],
[0.71,0.745798319327731],
[0.775,0.812198700482079],
[0.92,0.960133583802964],
[0.9501,0.986194727008511],
[0.9571,0.990479147262755],
[0.9677,0.991597499743826],
[1.,1.]]



SML = [0,0,0]

buffers = [[],[],[]]

XYZ = [0,0,0] #Couleur mesurée dans l'espace CIE
RGB = [0,0,0] #Couleurs mesurée dans l'espace linéaire RGB
temperature = 0 #Température de la couleur mesurée


##### Drapeaux de timings ################################# 

mesures_on = False #si True, mesure active, si False, mesure inactive
mesure_faite = False
min_derniere_mesure = 0

file_name = '' #File name

##led
led[0]=(255,0,0)
led.write()
time.sleep(.5)
led[0]=(0,0,0)
led.write()
time.sleep(.5)
led[0]=(255,0,0)
led.write()
time.sleep(.5)
led[0]=(0,0,0)
led.write()

running = True


### Fonctions #############################################

def on_button_pressed(p):
    global running
    running = False

button = Pin(10, Pin.IN, Pin.PULL_DOWN)
button.irq(on_button_pressed)



def interpoler_coef(valeur,table_id) : #Fonction d'interpolation des coeficients dans la table de normalisation des mesures
    global S_table
    global M_table
    
    #Choix de la table 
    if table_id == 'S':
        table = S_table
    elif table_id == 'M' :
        table = M_table
    
    #Positionnement de la valeur dans la table (non optimal, on pourrait faire de la partition fusion, ou chercher une fonction builtin)
    i = 1
    while valeur >= table[i][0] and i < len(table)-1 :
        i = min(i+1,len(table)-1)
        
    print('valeur entre les entrees', i-1,' ', table[i-1],' et ', i,' ',table[i])
    
    #interpolation
    i_val = table[i-1][1] + ((valeur-table[i-1][0])/(table[i][0]-table[i-1][0])) *(table[i][1]-table[i-1][1])
    
    print(table_id, ' valeur : ',valeur,'valeur i :',valeur/i_val,' coef : ',i_val)
    
    return i_val
    
    

def normaliser(valeur,table_id) :
    
    if table_id == 0 :
        coef = interpoler_coef(valeur,'S')
    elif table_id == 1 :
        coef = interpoler_coef(valeur,'M')
    else :
        coef = 1
        
    return valeur/coef
    

def lire_capteur() : #Lis et ajoute au buffer la valeur normalisée pour chaque catpeur
    #Rajouter moyenne 
    global capteurs
    global buffers
    
    #variables locales
    local_buffs = [[],[],[]]
    local_moy = [0,0,0]
    local_compte = 0
    
    #Mesure sur 2 secondes
    while local_compte < 20 :
        for i in range(len(capteurs)) :
            local_buffs[i].append(capteurs[i].read_u16()/65635.0)
        local_compte += 1
        time.sleep(.1)
    
    for i in range(len(capteurs)) :
        #Moyenne des mesures
        for val in local_buffs[i] :
            local_moy[i] += val
        local_moy[i] = local_moy[i]/len(local_buffs[i])
        
        #Normalisation et ajout au buffer gloabal
        buffers[i].append(normaliser(local_moy[i],i))
        
    #Affichage de debugg
    print(buffers)
    
    
    
def moyenne() :
    global buffers
    global SML
    global nb_vals
    
    for i in range(len(buffers)) :
            for v in buffers[i] :
                SML[i] += v
            
            SML[i] /= nb_vals

    print(SML)
        
                
def SML_to_XYZ() :
    global SML
    global XYZ
    
    s = SML[0]
    m = SML[1]
    l = SML[2]
    
    XYZ[0] = 1.9102*l - 1.11212*m + .20191*s
    XYZ[1] = .37095*l + .62905*m
    XYZ[2] = s
    
    print(XYZ)

def XYZ_to_RGB() :
    global XYZ
    global RGB
    
    X = XYZ[0]
    Y = XYZ[1]
    Z = XYZ[2]
    
    RGB[0] = 3.1956*X + 2.4478*Y - 0.1434*Z
    RGB[1] = -2.5455*X + 7.0492*Y + .9963*Z
    RGB[2] = Z
    
    print(RGB)
    
    
def XYZ_to_Kalvin() :
    
    global XYZ
    global xyZ
    global temperature
    
    X = XYZ[0]
    Y = XYZ[1]
    Z = XYZ[2]
    
    x = X/(X+Y+Z)
    y = Y/(X+Y+Z)
    print('x : ',x, ' y : ',y)
    xe = .3320
    ye = .1858
    n = (x-xe)/(y-ye)
    print(' n : ',n)
    print('n : ',n)
    
    temperature= -449.*n*n*n + 3525.*n*n - 6823.3*n + 5520.33

def is_full_mesure_time() -> bool :
    global rtc
    global mesure_on
    global mesure_faite
    
    time_array = time.localtime(rtc.datetime)
    
    if time_array[4]%30 == 0 and mesures_on :
        return True
    else :
        return False

def is_small_mesure_time() -> bool :
    
    global rtc
    global mesures_on
    global nb_vals
    global mesure_faite
    global min_derniere_mesure
    
    time_array = time.localtime(rtc.datetime)
    min_from_mesure = time_array[4]%(30/nb_vals)
    #print('min_from_mesure : ',min_from_mesure)

    if min_from_mesure == 0 and not(mesure_faite) and mesures_on :
        mesure_faite = True
        min_derniere_mesure = time_array[4]
        return True
    else :
        if time_array[4] != min_derniere_mesure :
            mesure_faite = False
            
        return False

def is_day_start () -> bool :
    global file_name
    global rtc
    global mesures_on
    global mesures_start_time
    
    time_array = time.localtime(rtc.datetime)
    #print(str(time_array[3])+'h'+str(time_array[4]))
    
    if time_array[3] >= mesures_start_time and not(mesures_on)  :
        mesures_on = True
        print('Creation du fichier...')
        file_name = 'Mesures_du_'+str(time_array[2])+'_'+str(time_array[1])+'_'+str(time_array[0])+'.txt'
        print(file_name + ' Fichier cree avec succes')

def is_day_end() -> bool :
    global rtc
    global mesures_on
    global mesures_stop_time
    
    time_array = time.localtime(rtc.datetime)
    
    if time_array[3] == mesures_stop_time :
        mesure_on = False
    
    

def write_mesure_to_file() :
    global file_name
    global XYZ
    global RGB
    global temperature
    global rtc
    
    print('writing to file ',file_name)
    
    time_array = time.localtime(rtc.datetime)
    print(time_array)
    
    
    f= open(file_name,'a')
    content = ''
    content += '\n' + str(time_array[3])+'h'+str(time_array[4])
    content += ' ' + ' R: '+str(RGB[0]) +' | G: '+str(RGB[1]) + ' | B: '+str(RGB[2])
    content += '||     '  + 'X: '+str(XYZ[0]) +' | Y: '+str(XYZ[1]) + ' | Z: '+str(XYZ[2])
    content += '||     '  + 'Temperature : ' + str(temperature)
    content += '||S: '+ str(SML[0]) + ' M: '+str(SML[1])+' L: '+str(SML[2]) 
    f.write(content)
    f.close()


########## Boucle principale ###########################
print('Preparation a l execution d la boucle princiaple')

while running:
    #print('boucle principale en cours d execution')
    time_array = time.localtime(rtc.datetime)
    #print(str(time_array[3])+'h'+str(+time_array[4]))
    # Vérifie si on est dans la plage horaire de mesure définie par l'utilisateur
    if is_day_start() :
        mesure_on = True
        print('mesure actives')
    
    if is_day_end() :
        mesure_on = False
    
    
    
    if is_small_mesure_time() :
        print('Petite mesure...')
        lire_capteur() #Mesure, normalisation et ajout aux buffers
        print('fait')
        
    if is_full_mesure_time() and len(buffers[0]) > 0 :
        print('Calculs...')
        lire_capteur() 
        moyenne() 		# Moyenne de chaque buffer
        SML_to_XYZ() 	# Passage dans l'espace colorimetrique de travail CIE 1931 (norme chelou)
        XYZ_to_RGB() 	# Calcul de la valeur RGB
        XYZ_to_Kalvin()	# Calcul de la température de la couleur
        print('fait')
        
        write_mesure_to_file() #Ecriture des valeurs dans le fichier 
        print('Données écrites')
        
        buffers = [[],[],[]] #Reinitialisation des buffers
        
        led[0]=(max(min(int(RGB[1]*255),255),0),
                max(min(int(RGB[0]*255),255),0),
                max(min(int(RGB[2]*255),255),0))
        led.write()

    time.sleep(2)
print('Execution interrompue, programme termine')
        
    
###################"""" Legacy code######################### 

#     log = ''
#     
#     buffer_N =[]
#     buffer_B =[]
#     buffer_R =[]
#     
#     for i in range(nb_values) :
#         #Acquisition et normalissation de la valuer
#         value_N = lightsensor_N.read_u16()
#         value_N = value_N/65635
#         
#         value_B = lightsensor_B.read_u16()
#         value_B = value_B/65635
#         
#         value_R = lightsensor_R.read_u16()
#         value_R = value_R/65635
#         
#         #Ajout de la valeur au buffer
#         buffer_N.append(value_N)
#         buffer_R.append(value_R)
#         buffer_B.append(value_B)
#         
#         #Attente de qq ms
#         time.sleep(intervalle/nb_values)
#     
#     #Calcul de la valuer moyenne
#     val_moyenne_N = 0
#     val_moyenne_B = 0
#     val_moyenne_R = 0
#     
#     for i in range(nb_values) :
#         val_moyenne_N += buffer_N[i]
#         val_moyenne_B += buffer_B[i]
#         val_moyenne_R += buffer_R[i]
#         
#     
#     val_moyenne_N /= nb_values
#     val_moyenne_B /= nb_values
#     val_moyenne_R /= nb_values
#     
#     
#     print(val_moyenne_N)
#     print(val_moyenne_B)
#     print(val_moyenne_R)
#     
#     
#     V_bc = 1-((2.2*(val_moyenne_N-val_moyenne_B)/val_moyenne_N))
#     V_rc = 1-((1.15*(val_moyenne_N-val_moyenne_R)/val_moyenne_N))
#     
#     temperature = 1000+(V_bc/V_rc)*11000
#     print('Temperature : ', temperature)
#     
#     
#     f=open('mesures03.txt','a')
#     mesures = f.read()
#     mesures += '\n' + str(temperature)
#     f.write(mesures)
#     f.close()
#     
#     
#     print('V_bc : ', V_bc)
#     print('V_rc : ', V_rc)
#     
#     
#     #print(rtc.readfrom(104,4))
#     
    
    