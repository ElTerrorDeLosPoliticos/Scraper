from fake_headers import Headers
from bs4 import BeautifulSoup

import json
import requests
import time
import os.path
import pandas as pd
import sqlite3 as sql

class Scraper:
    def __init__(self):
        self.item = {}
    
    def scraping(self):
        """[Returns 'items', a dict of dictionaries with 
        IDs(numbers) as keys and visits as values. Items contains all info about a day]

        Returns:
            [Dict]: [Dict of dicts about the visitor logs record of Palacio de 
            Gobierno]
        """
        headers = Headers(headers=True).generate()
        link = 'https://appw.presidencia.gob.pe/visitas/transparencia/'
        HTML = BeautifulSoup((requests.get(link, headers=headers).content), 'html.parser')
        HTML = HTML.select('tr')[6]
        HTML = HTML.find_all_next('tr')
        ns_orden = [x.get_text() for x in sum([HTML[len(HTML)-i-1].find_all('td')[0::11] for i in range(len(HTML))],[])][::-1]
        fechas = [(x.get_text()[-4:] + x.get_text()[3:5] + x.get_text()[:2] ) for x in sum([HTML[len(HTML)-i-1].find_all('td')[1::11] for i in range(len(HTML))],[])]
        visitantes = [x.get_text() for x in sum([HTML[len(HTML)-i-1].find_all('td')[2::11] for i in range(len(HTML))],[])]
        n_documentos = [x.get_text() for x in sum([HTML[len(HTML)-i-1].find_all('td')[3::11] for i in range(len(HTML))],[])]
        tipo_documentos = [i[:3] for i in n_documentos]
        n_documentos = [i[4:] for i in n_documentos]
        instituciones = [x.get_text() for x in sum([HTML[len(HTML)-i-1].find_all('td')[4::11] for i in range(len(HTML))],[])]
        motivos = [x.get_text() for x in sum([HTML[len(HTML)-i-1].find_all('td')[5::11] for i in range(len(HTML))],[])]
        visitados = [x.get_text() for x in sum([HTML[len(HTML)-i-1].find_all('td')[6::11] for i in range(len(HTML))],[])]
        cargos = [x.get_text() for x in sum([HTML[len(HTML)-i-1].find_all('td')[7::11] for i in range(len(HTML))],[])]
        oficinas = [x.get_text() for x in sum([HTML[len(HTML)-i-1].find_all('td')[7::11] for i in range(len(HTML))],[])]
        horas_ingreso = [x.get_text() for x in sum([HTML[len(HTML)-i-1].find_all('td')[8::11] for i in range(len(HTML))],[])]
        horas_salida = [x.get_text() for x in sum([HTML[len(HTML)-i-1].find_all('td')[9::11] for i in range(len(HTML))],[])]
        observaciones = [x.get_text() for x in sum([HTML[len(HTML)-i-1].find_all('td')[10::11] for i in range(len(HTML))],[])]

        df = list(zip(ns_orden, fechas, visitantes, tipo_documentos, n_documentos, instituciones, motivos, visitados, cargos, oficinas, horas_ingreso, horas_salida, observaciones))
        
        for n_orden, fecha, visitante, tipo_documento, n_documento, institucion, motivo, visitado, cargo, oficina, hora_ingreso, hora_salida, observacion in df:
            self.item[n_orden] = {}
            self.item[n_orden]["Fecha"] = fecha
            self.item[n_orden]["Visitante"] = visitante
            self.item[n_orden]["Tipo_Documento"] = tipo_documento
            self.item[n_orden]["N_Documento"] = n_documento
            self.item[n_orden]["Institucion"] = institucion
            self.item[n_orden]["Motivo"] = motivo
            self.item[n_orden]["Visitado"] = visitado
            self.item[n_orden]["Cargo"] = cargo
            self.item[n_orden]["Oficina"] = oficina
            self.item[n_orden]["Hora_Ingreso"] = hora_ingreso
            self.item[n_orden]["Hora_Salida"] = hora_salida
            self.item[n_orden]["Observacion"] = observacion
        return self.item

    def save_json(self, item):
        """[Save visitor logs records (data_presidencia.json)]

        Args:
            item ([dict]): [Dict of dicts with the last data]

        Returns:
            [Bool]: [If saved, returns True; else, False]
        """
        with open('data_presidencia.json', "w", encoding='utf-8') as f:
            json.dump(item, f, indent=4, ensure_ascii=False)
        return True

    
    def save_data_in_db(self):
        """[Sava data_presidencia.json in cloud_storage]

        Returns:
            [Bool]: [If correct, returns True; else, False]
        """
        with open('data_presidencia.json','r', encoding='utf-8') as f:
            data = json.load(f)
            a = list(filter(lambda x: x["Cargo"]=="PRESIDENCIA DE LA REPÚBLICA", data.values()))
        for i in a:
            inputs = list(i.values())
            index_n = Scraper.last_dbindex(self)
            Scraper.insertRow(self, index_n, inputs[0],inputs[1],inputs[2],inputs[3],inputs[4],inputs[5],inputs[6],inputs[7],inputs[8],inputs[9],inputs[10],inputs[11])
        Scraper.deleteDuplicates(self)
        print('Done it')
        return True

    def last_dbindex(self):
        conn = sql.connect("/home/fabriziosulca28/Scraper/registro_visitas.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registro_visitas ORDER BY rowid DESC LIMIT 1")
        index = (cursor.fetchone())[0]
        conn.commit()
        conn.close
        return index

    def insertRow(self, index_n, Fecha, Visitante, Tipo_Documento, N_Documento, Institucion,
                  Motivo, Visitado, Cargo, Oficina, Hora_Ingreso, Hora_Salida,
                  Observacion):
        conn = sql.connect("/home/fabriziosulca28/Scraper/registro_visitas.db")
        cursor = conn.cursor()
        instructions = f"INSERT INTO registro_visitas VALUES ('{index_n}', '{Fecha}', '{Visitante}', '{Tipo_Documento}', '{N_Documento}', '{Institucion}','{Motivo}', '{Visitado}', '{Cargo}', '{Oficina}', '{Hora_Ingreso}', '{Hora_Salida}','{Observacion}')"
        cursor.execute(instructions)
        conn.commit()
        conn.close()

    def deleteDuplicates(self):
        conn = sql.connect("/home/fabriziosulca28/Scraper/registro_visitas.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM registro_visitas WHERE rowid NOT IN ( SELECT MIN(rowid) rowid FROM registro_visitas GROUP BY Fecha, Visitante, Tipo_Documento, N_Documento, Institucion, Motivo, Visitado, Cargo, Oficina, Hora_Ingreso, Hora_Salida, Observacion)")
        conn.commit()
        conn.close()
   
    @staticmethod
    def compare_new_and_old_item(item):
        """[Compare last 'data_presidencia.json' with newer item]

        Args:
            item ([Dict]): [Last scrapped information]

        Returns:
            [Bools]: [If information was NOT upgraded, returns False; upgraded
            and others, True]
        """
        if os.path.exists("data_presidencia.json"):
            with open("data_presidencia.json", "r", encoding="utf-8") as f:
                old_item = json.load(f)
            if item == old_item:
                return False
            else:
                return True

    def Update(self):
        os.system('git pull origin main')
        os.system('git add -A')
        os.system('git commit -m' + '"' + time.strftime("%d/%m/%Y" + ' ' + "%H:%M:%S") + '"')
        os.system('git push')
        return True            
            
    def compute(self):
        """[Compute all the Palacio de Gobierno scraper code]

        Returns:
            [Bool]: [Returns True if scrapping, saving and uploading was 
            succesful]
        """
        x = Scraper()
        item = x.scraping()
        new_data = x.compare_new_and_old_item(item)
        if new_data:
            x.save_json(item)
            x.save_data_in_db()
            x.Update()
            print('Database actualizado')
        else:
            print('Tú no has cambiado, pelona')
        
        return True
