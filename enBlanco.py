# ESTE SCRIPT ES UNA VERSIÓN HECHA A LAS APURADAS DE scrapeHTML.py, DESPUÉS DE DARME CUENTA
# QUE LA BÚSQUEDA VACÍA LEVANTABA TODOS LOS PROYECTOS, PARA GUARDARLOS TODOS EN JSON 

import sys
import os
import pandas as pd
import numpy as np
import re
import time
import json
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from seleniumrequests import Chrome
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import dill
# import matplotlib.pyplot as plt
# import seaborn as sns
# import matplotlib.dates as mdates
# import matplotlib.ticker as ticker
# from urllib.request import urlopen
# import requests


#===CONFIGURACION DE DIRECTORIOS===
cwd = os.getcwd()
src = os.getcwd()+'\\sources\\'
res = os.getcwd()+'\\results\\'
tmp = os.getcwd()+'\\json\\'
sys.setrecursionlimit(6000)


URL = "https://www.hcdn.gob.ar/proyectos/resultados-buscador.html"

#===OPCIONES PARA EL NAVEGADOR DE SELENIUM===
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-extensions")

def packJSON(directorio):
    archivosJson = os.listdir(directorio)
    anios = []
    for jose in archivosJson:
        anios.append((re.search('^\d+',(re.search('\d+.json$', jose)[0]))[0], jose))
    anios = pd.DataFrame.from_records(anios, index=0)
    anios.columns = pd.Index(['anio', 'archivo'])
    porAnio = anios.groupby(by='anio')
    for grupo in porAnio:
        try: archivoZip = zipfile.ZipFile(res+grupo[0]+'.zip', mode='w')
        except: archivoZip = zipfile.ZipFile(res+grupo[0]+'.zip', mode='a')
        for index, anio, archivo in grupo[1].itertuples():
            archivoZip.write(directorio+archivo, os.path.basename(tmp+archivo))
        archivoZip.close()

def escape(cadena):
    escaped = cadena.translate(str.maketrans({"-":  r"\-",
                                          "]":  r"\]",
                                          "\\": r"\\",
                                          "^":  r"\^",
                                          "$":  r"\$",
                                          "*":  r"\*",
                                          ".":  r"\."}))
    return escaped
def limpiarEscapes(cadena):
    cadena2 = ''
    for e in cadena:
        cadena2 += re.sub('(\n|\t)', '', e)
    return cadena2

def tablaInsertar(elemento,indice,_indice):
    tablaHtml = limpiarEscapes(elemento)
    multiTabla = pd.read_html(tablaHtml)[0]
    del tablaHtml
    _indice = pd.Index([_indice])
    multi = pd.MultiIndex.from_product([(_indice),multiTabla.columns])
    multiTabla = multiTabla.transpose()
    multiTabla.set_index(multi, inplace=True)
    for columna in multiTabla.columns:
        try: 
            columna = columna.strip()
            columna = escape(columna)
        except: pass    
    return multiTabla

#===LEE LOS PARÁMETROS DE BÚSQUEDA===

def loadParams(archivo):
    parametros = pd.read_excel(archivo,index_col=0,usecols='B:C') #Leemos los parámetros del archivo excel
    cargaParams ={}
    for variable, parametro in parametros.itertuples():
        if parametro == parametro: #Sólo carga las variables que llenamos
            cargaParams[variable] = parametro
        else:
            continue
    del parametros
    if len(cargaParams['strPalabras']):
        cargaParams['strPalabras'] = cargaParams['strPalabras'].split(",") # Convierte la cadena de palabras claves (si las hay), en un array
    return cargaParams

#====REALIZA LA BÚSQUEDA Y CARGA CADA TEMA EN UNA TUPLA, CON SU PALABRA CLAVE Y LA PÁGINA DE RESULTADOS CORRESPONDIENTE===
def llenarForm(PARAM):
    
    driver = webdriver.Chrome(executable_path= r'C:\Users\jsgoy\OneDrive\Documents\ETEC\2020\Prueba Python\lara\chromedriver.exe', options=chrome_options) #Crea el driver
    driver.get('https://www.hcdn.gob.ar/proyectos/')
    #Detecta los campos del formulario del buscador, y los asigna a un diccionario. Asigna los botones a variables.
    campos ={'strTipo':'//*[@id="strTipo"]',
    'strNumExp':'//*[@id="strNumExp"]',
    'strNumExpOrig':'//*[@id="strNumExpOrig"]',
    'strNumExpAnio':'//*[@id="strNumExpAnio"]',
    'strCamIni':'//*[@id="strCamIni"]',
    'strFirmante':'//*[@id="strFirmante"]',
    'strComision':'//*[@id="strComision"]',
    'strFechaInicio':'//*[@id="strFechaInicio"]',
    'strFechaFin':'//*[@id="strFechaFin"]',
    'strPalabras':'//*[@id="strPalabras"]',
    'strOrdenDelDiaNro':'//*[@id="strOrdenDelDiaNro"]',
    'strOrdenDelDiaAnio':'//*[@id="strOrdenDelDiaAnio"]',
    'strLey':'//*[@id="strLey"]',
    'strDictamenDiputados':'//*[@id="strDictamenDiputados"]',
    'strDictamenSenado':'//*[@id="strDictamenSenado"]',
    'strAprobadoDiputados':'//*[@id="strAprobadoDiputados"]',
    'strAprobadoSenado':'//*[@id="strAprobadoSenado"]',
    'strMostrarTramites':'//*[@id="strMostrarTramites"]',
    'strMostrarDictamenes':'//*[@id="strMostrarDictamenes"]',
    'strMostrarFirmantes':'//*[@id="strMostrarFirmantes"]',
    'strMostrarComisiones':'//*[@id="strMostrarComisiones"]'}
    abrirDatosDeTramitacion = '//*[@id="frmProy"]/div[1]/a[1]'
    abrirOpcionesBuscador = '//*[@id="frmProy"]/div[1]/a[2]'
    mostrarTramite = '//*[@id="strMostrarTramites"]'
    mostrarDictamen = '//*[@id="strMostrarDictamenes"]'
    mostrarFirmantes = '//*[@id="strMostrarFirmantes"]'
    mostrarComisiones = '//*[@id="strMostrarComisiones"]'
    proyPorPagina = '//*[@id="strCantPagina"]'
    enviar = '//*[@id="frmProy"]/div[2]/div[1]/div[1]/input'
    driver.find_element_by_xpath(abrirOpcionesBuscador).click()
    driver.find_element_by_xpath(abrirDatosDeTramitacion).click()
    
    #Comienza a ingresar los datos buscados
    time.sleep(1)
    driver.find_element_by_xpath(enviar).click() #¡ENVIAR!
    resultado = ('', driver) #Si no, deja ese espacio vacío
    return resultado

#====LLAMA LA BÚSQUEDA Y CARGA CADA PROYECTO EN UNA TUPLA, CON SU TEMA Y EL HTML CORRESPONDIENTE
def compilarResultadosTotalHTML():
    
    PARAM = loadParams(src+'cargaParametros.xlsx') #Carga los parámetros desde el archivo Excel
    drivers = [llenarForm(PARAM)]
    htmlProyectos = {} #Esta va a ser nuestra variable principal
    errores=[]
    contador=0
    #Comienza a cargar los proyectos de cada navegador
    
    for elemento in drivers:
        driver = elemento[1] #Navegador con la búsqueda
        #Buscamos cuántas páginas de resultados hay
        try:
            strPaginas = driver.find_elements_by_class_name('detalle-paginador')[0].text
        except:
            strPaginas = 'Página 1 de 1'
        
        intPaginas = int(re.search('Página 1 de (.+?$)', strPaginas).group(1))
        proxima = 2
        fallas = []
        count = 0
        #Cargamos los resultados de cada página hasta la anteúltima, y cargamos cada proyecto en htmlProyectos, en una tupla con la palabra clave (si la hay, o una cadena vacía), y el html de cada proyecto
        for pagina in range(intPaginas-1):
            driver.get('https://www.hcdn.gob.ar/proyectos/resultados-buscador.html?pagina='+str(proxima))
            
            #Si hay un error de servidor (muy comunes), lo registra
            try:
                if driver.find_element_by_xpath('//*[@id="principal-interno"]/div/div/h4').text == "Error del servidor 500":
                    fallas.append(proxima)
            except:
                pass
            proxima += 1
            #Comenzamos a cargar los datos de cada proyecto
            #Identificamos el cuadro contenedor de cada proyecto y lo guardamos en el array webelementosProyecto
            try:
                webelementosProyecto = driver.find_elements_by_class_name('detalle-proyecto')    
            except Exception as e:
                print(e)
                continue
            #Identificamos el HTML interno de cada cuadro, y lo guardamos en htmlFinal
            for proyecto in webelementosProyecto:
                count += 1
                numProy = str(proyecto.find_elements_by_class_name('dp-metadata')[0].find_elements_by_tag_name('span')[1].text)
                try: re.search('\d+-\w+-\d+$', numProy).group()
                except: numProy = re.search('\d+/d+$', numProy).group()
                else: numProy = re.search('\d+-\w+-\d+$', numProy).group()
                if os.path.isfile(tmp+numProy+'.json'):
                    continue
                else: yield (numProy,[{'Palabra Clave':' '}],proyecto.get_attribute('innerHTML')), errores


    
for htmlProyectos, errores in compilarResultadosTotalHTML():
    try:
        strErrores = ''
        for error in errores:
            for pagina in error[1]:
                strErrores += str(error[0])+': '+ str(pagina) +'\n'
        logErrores = open(res+'logErrores.txt', 'wt')
        logErrores.write(strErrores)
        logErrores.close()
    except Exception as e:
        print(e)
        pass
    del errores
    pClave = htmlProyectos[1]
    proyecto = htmlProyectos[-1]
    soup = BeautifulSoup(proyecto, 'html.parser')
    indice = htmlProyectos[0]
    if os.path.isfile(tmp+indice+'.json'): continue
    row = pd.Series(name=indice, dtype=np.float64)
    row['Tipo de Proyecto'] = soup.find_all('h4')[0].string
    datosProy = soup.find(class_='dp-metadata').find_all('span')
    for datos in datosProy:
        try: row[str(datos.contents[0].contents[0].string)] = str(datos.contents[1].string)
        except: pass
    row['Título'] = str(soup.find(class_='dp-texto').string)
    try:
        tablaFirmantes = tablaInsertar(soup.find(class_='dp-firmantes table table-condensed table-striped').prettify().strip(),indice,'Firmantes')
        row = pd.concat([row,tablaFirmantes])
    except: pass
    try:
        tablaGiros = tablaInsertar(soup.find(class_='dp-giros-diputados table table-condensed table-striped').prettify().strip(),indice,'Giros')
        row = pd.concat([row,tablaGiros])
    except:
        pass
    try:
        tablaTramites = tablaInsertar(soup.find(class_='dp-tramites table table-condensed table-striped').prettify().strip(),indice,'Tramites')
        row = pd.concat([row,tablaTramites])
    except:
        pass
    try:
        masDatos = soup.find_all(class_='btn btn-info')
        for key in masDatos[0].attrs.keys():
            if 'href' in key:
                link = pd.Series(data=masDatos[0].attrs[key], name='Link')
                row = row.append(link)
            else:
                pass
    except: pass
    try:
        sumario = soup.findAll(id=re.compile('^sumario\w+'))[0].contents[0].string
        sumario = pd.Series(data=sumario.strip(), name='Sumario')
        row = row.append(sumario)
    except: pass
    row = pd.DataFrame(row)
    row = row.append(pd.DataFrame.from_records(pClave).transpose())
    row = row.transpose()
    first = True
    row = pd.concat({indice: row}, names=['Exp'])
    try: row.to_json(tmp+indice+'.json')
    except: pass
    del pClave, proyecto, row
del htmlProyectos