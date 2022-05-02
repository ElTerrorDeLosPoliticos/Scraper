from fake_headers import Headers

import requests
import json
import time
import datetime
import os
import sqlite3 as sql
import pandas as pd

class Scraper():
    def __init__(self):
        self.auth_data = {
            "fechaDesde": datetime.date.today().strftime("%Y-%m-%d"),
            "fechaHasta": datetime.date.today().strftime("%Y-%m-%d"),
            "visitanteCampo": "1",
            "visitanteNombres": "",
            "empleadoCampo": "2",
            "empleadoNombres": "CONGRESISTA"
        }
    
    def get_data(self):
        headers = Headers(headers=True).generate()
        req = (requests.post('https://wb2server.congreso.gob.pe/regvisitastransparencia/filtrar', data=json.dumps(self.auth_data), headers=headers).json())
        item = Scraper.normalize(self,req)
        return item

    def normalize(self,req):
        Fechas = [(i["fechaVisitaRecepcion"][:8]).replace("/2","/202") for i in req]
        Fechas = [(i[-4:] + i[3:5] + i[:2]) for i in Fechas]
        Visitantes = [i["entidadVisitanteNombreCompleto"]for i in req]
        Tipos_Documento = [i["entidadVisitanteTipoDocumento"] for i in req]
        N_Documentos = [i["entidadVisitanteDocumento"] for i in req]
        Instituciones = [i["entidad"] if i["entidad"]!=None else "" for i in req ]
        Motivos = [i["motivo"] if i["motivo"] is not None else "" for i in req]
        Visitados = [i["empleado"] for i in req]
        Cargos = [i["cargo"] for i in req]
        Oficinas = [i["centroCostoNombre"] for i in req]
        Horas_Ingreso = [i["fechaVisitaRecepcion"][9:] for i in req]
        Horas_Salida = [i["fechaVisitaTermino"] if i["fechaVisitaTermino"] is not None else "" for i in req]
        Observaciones = ["" for i in range(len(Visitantes))]
        
        item = {"Fecha":Fechas, "Visitante":Visitantes,"Tipo_Documento":Tipos_Documento, "N_Documento":N_Documentos, "Institucion":Instituciones, "Motivo":Motivos, "Visitado":Visitados, "Cargo":Cargos, "Oficina":Oficinas, "Hora_Ingreso":Horas_Ingreso,"Hora_Salida":Horas_Salida, "Observacion":Observaciones}
        
        item = pd.DataFrame(data=item)
        item = item.to_json(orient="records")
        item = json.loads(item)
        
        return item
    
    def save_json(self,data):
        with open ("data_congreso.json","w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    
    def save_data_in_db(self):
        """[Save data in Google Cloud Storage]

        Returns:
            [Bool]: [If correct, returns True; else, False]
        """
        with open('data_congreso.json','r', encoding='utf-8') as f:
            data = json.load(f)
        for i in data:
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

    def deleteDuplicates(self):
        conn = sql.connect("/home/fabriziosulca28/Scraper/registro_visitas.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM registro_visitas WHERE rowid NOT IN ( SELECT MIN(rowid) rowid FROM registro_visitas GROUP BY Fecha, Visitante, Tipo_Documento, N_Documento, Institucion, Motivo, Visitado, Cargo, Oficina, Hora_Ingreso, Hora_Salida, Observacion)")
        conn.commit()
        conn.close()
        return True
    
    def upgrade(self):
        conn = sql.connect("/home/fabriziosulca28/Scraper/registro_visitas.db")
        cursor = conn.cursor()
        cursor.execute("SELECT rowid FROM registro_visitas GROUP BY Fecha, Visitante, N_Documento, Hora_Ingreso HAVING COUNT(*) > 1;")
        row_id = cursor.fetchall()
        for i in row_id:
            i = i[0]
            instructions = f"DELETE FROM registro_visitas where rowid={i}"
            cursor.execute(instructions)
        conn.commit()
        conn.close()
        return True


    def insertRow(self, index_n, Fecha, Visitante, Tipo_Documento, N_Documento, Institucion,
                  Motivo, Visitado, Cargo, Oficina, Hora_Ingreso, Hora_Salida,
                  Observacion):
        conn = sql.connect("/home/fabriziosulca28/Scraper/registro_visitas.db")
        cursor = conn.cursor()
        instructions = f"INSERT INTO registro_visitas VALUES ('{index_n}', '{Fecha}', '{Visitante}', '{Tipo_Documento}', '{N_Documento}', '{Institucion}','{Motivo}', '{Visitado}', '{Cargo}', '{Oficina}', '{Hora_Ingreso}', '{Hora_Salida}','{Observacion}')"
        cursor.execute(instructions)
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def compare_new_and_old_item(item):
        """[Compare the new scrapped info with the last file we saved]
        Args:
            item ([dict]): [Dict of dicts with the last data]
        Returns:
            [Bool]: [If scrapped info is equal to last 'data_congreso.json'
            , returns False; else, True]
        """
        if os.path.exists("data_congreso.json"):
            with open("data_congreso.json", "r", encoding="utf-8") as f:
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
        """[Compute all the Congreso scraper code]

        Returns:
            [Bool]: [Returns True if scrapping, saving and uploading was 
            succesful]
        """
        item = Scraper.get_data(self)
        new_data = Scraper.compare_new_and_old_item(item)
        if new_data:
            Scraper.save_json(self,item)
            Scraper.save_data_in_db(self)
            Scraper.Update(self)
            Scraper.upgrade(self)

            print('Database actualizado')
        else:
            print('Tú no has cambiado, pelona')
        return True
