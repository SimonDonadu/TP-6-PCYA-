import sys
from datetime import datetime, timedelta, date, time

# ----------------------------------
# Estructuras de Datos
# ----------------------------------
class Cliente:
    def __init__(self, nombre, patente, tipo_vehiculo):
        self.nombre = nombre
        self.patente = patente
        self.tipo_vehiculo = tipo_vehiculo  # 'moto', 'auto', 'SUV', 'pickup', 'van'

class Cochera:
    def __init__(self, id_cochera, tipo):
        self.id = id_cochera
        self.tipo = tipo
        self.ocupada = False
        self.vencimiento = None  # datetime para alquiler mensual

class Servicio:
    def __init__(self, nombre, precios_por_categoria):
        self.nombre = nombre
        self.precios_por_categoria = precios_por_categoria  # dict: {'auto':500, ...}

class Alquiler:
    def __init__(self, cliente, cochera, tipo_alquiler, fecha_inicio, precios_base):
        self.cliente = cliente
        self.cochera = cochera
        self.tipo = tipo_alquiler   # 'mensual', 'diario', 'hora'
        self.fecha_inicio = fecha_inicio
        self.servicios = []
        self.precios_base = precios_base

    def add_servicio(self, servicio):
        self.servicios.append(servicio)

    def passed_time(self):
        delta = datetime.now() - self.fecha_inicio
        if self.tipo == 'mensual':
            return max(delta.days // 30, 1)
        if self.tipo == 'diario':
            return max(delta.days, 1)
        if self.tipo == 'hora':
            return max(int(delta.total_seconds() // 3600), 1)
        return 1

    def cost_details(self):
        detalles = []
        tiempo = self.passed_time()
        tarifa = self.precios_base.get(self.cliente.tipo_vehiculo, {}).get(self.tipo, 0)
        costo_estadia = tarifa * tiempo
        detalles.append((f'Estadía {self.tipo}', tiempo, tarifa, costo_estadia))
        total = costo_estadia
        for s in self.servicios:
            precio_s = s.precios_por_categoria.get(self.cliente.tipo_vehiculo, 0)
            detalles.append((f'Servicio {s.nombre}', 1, precio_s, precio_s))
            total += precio_s
        return detalles, total

    def invoice_text(self):
        detalles, total = self.cost_details()
        lines = ["===== FACTURA =====",
                 f"Cliente: {self.cliente.nombre}",
                 f"Patente: {self.cliente.patente}",
                 f"Cochera: {self.cochera.id}",
                 f"Tipo alquiler: {self.tipo}",
                 "----------------------------"]
        for desc, qty, pu, sub in detalles:
            lines.append(f"{desc}: {qty} × {pu} = {sub}")
        lines.append("----------------------------")
        lines.append(f"TOTAL A PAGAR: {total}\n")
        return "\n".join(lines)

# ----------------------------------
# ParkingLot gestor con CRUD y funcionalidades
# ----------------------------------
class ParkingLot:
    def __init__(self, precios_base):
        self.precios_base = precios_base
        self.clientes = {}    # patente -> Cliente
        self.cocheras = {}    # id -> Cochera
        self.servicios = {}   # nombre -> Servicio
        self.alquileres = []

    def init_cocheras(self, config):
        for tipo, cantidad in config.items():
            for i in range(1, cantidad + 1):
                cid = f"{tipo[0].upper()}{i:02d}"
                self.cocheras[cid] = Cochera(cid, tipo)

    # Clientes
    def add_cliente(self, cliente): self.clientes[cliente.patente] = cliente
    def find_cliente(self, patente): return self.clientes.get(patente)
    def remove_cliente(self, patente): return self.clientes.pop(patente, None)

    # Cocheras
    def add_cochera(self, cochera): self.cocheras[cochera.id] = cochera
    def find_cochera(self, cid): return self.cocheras.get(cid)
    def remove_cochera(self, cid): return self.cocheras.pop(cid, None)

    # Servicios
    def add_servicio(self, servicio): self.servicios[servicio.nombre] = servicio
    def find_servicio(self, nombre): return self.servicios.get(nombre)
    def remove_servicio(self, nombre): return self.servicios.pop(nombre, None)

    # Alquileres
    def register_vehicle(self, patente, tipo_alquiler, fecha_inicio):
        if tipo_alquiler not in ('mensual', 'diario', 'hora'):
            return None, f"Tipo de alquiler inválido: {tipo_alquiler}"
        cliente = self.find_cliente(patente)
        if not cliente:
            return None, 'Cliente no registrado.'
        coch = next((c for c in self.cocheras.values() if not c.ocupada), None)
        if not coch:
            return None, 'No hay cocheras disponibles.'
        coch.ocupada = True
        if tipo_alquiler == 'mensual':
            coch.vencimiento = fecha_inicio + timedelta(days=30)
        alquiler = Alquiler(cliente, coch, tipo_alquiler, fecha_inicio, self.precios_base)
        self.alquileres.append(alquiler)
        return alquiler, None

    def end_rental(self, alquiler):
        txt = alquiler.invoice_text()
        alquiler.cochera.ocupada = False
        self.alquileres.remove(alquiler)
        return txt

    def available_cocheras(self, tipo=None):
        return [c.id for c in self.cocheras.values() if not c.ocupada and (tipo is None or c.tipo == tipo)]

    def grid_status(self):
        return [(c.id, c.tipo, 'Ocupada' if c.ocupada else 'Libre') for c in self.cocheras.values()]

    def availability_report(self):
        return {t: len(self.available_cocheras(t)) for t in self.precios_base.keys()}

    def ranking_temporal(self):
        return sorted(self.availability_report().items(), key=lambda x: x[1], reverse=True)

    def notify_expirations(self):
        now = datetime.now()
        return [(c.id, c.vencimiento) for c in self.cocheras.values() if c.vencimiento and (c.vencimiento - now) <= timedelta(hours=48)]

# ----------------------------------
# Setup inicial con ejemplos
# ----------------------------------

def setup_parking():
    precios = {
        'auto':   {'mensual':1000,'diario':100,'hora':20},
        'moto':   {'mensual':800,'diario':80,'hora':15},
        'SUV':    {'mensual':1200,'diario':120,'hora':25},
        'pickup': {'mensual':1500,'diario':150,'hora':30},
        'van':    {'mensual':1800,'diario':180,'hora':35}
    }
    parking = ParkingLot(precios)
    parking.init_cocheras({'moto':2,'auto':3,'SUV':1,'pickup':1,'van':1})
    parking.add_servicio(Servicio('Lavado', {'auto':500,'moto':300,'SUV':600,'pickup':700,'van':800}))
    parking.add_servicio(Servicio('Encerado', {'auto':300,'moto':200,'SUV':350,'pickup':400,'van':450}))
    parking.add_cliente(Cliente('Demo','XYZ123','auto'))
    return parking

# ----------------------------------
# CLI interactivo sin detección Jupyter
# ----------------------------------
def main():
    parking = setup_parking()
    # Mostrar estado inicial
    print("Grid de cocheras:")
    for cid, tv, st in parking.grid_status():
        print(f"{cid:<4} {tv:<5} {st}")
    print("\nRanking disponibilidad:", parking.ranking_temporal())
    avisos = parking.notify_expirations()
    for cid, venc in avisos:
        print(f"Cochera {cid} vence en <48h: {venc}")
    # Pedir datos al usuario y mostrar cocheras libres
    patente = input("Patente cliente: ")
    cliente = parking.find_cliente(patente)
    if not cliente:
        nombre = input("Nombre cliente: ")
        tipo_v = ''
        while tipo_v not in parking.precios_base:
            tipo_v = input(f"Tipo de vehiculo {list(parking.precios_base.keys())}: ")
        cliente = Cliente(nombre, patente, tipo_v)
        parking.add_cliente(cliente)
    libres_tipo = parking.available_cocheras(cliente.tipo_vehiculo)
    print(f"Cocheras libres para {cliente.tipo_vehiculo}: {libres_tipo}")
    # Selección de tipo y duración
    tipo_alq = ''
    while tipo_alq not in ('mensual','diario','hora'):
        tipo_alq = input("Tipo de alquiler (mensual/diario/hora): ")
    if tipo_alq == 'mensual':
        meses = int(input("Cantidad de meses: "))
        fi = datetime.now() - timedelta(days=30 * meses)
    elif tipo_alq == 'diario':
        dias = int(input("Cantidad de días: "))
        fi = datetime.now() - timedelta(days=dias)
    else:
        horas = int(input("Cantidad de horas: "))
        fi = datetime.now() - timedelta(hours=horas)
    servicios = input("Servicios (coma separados): ")
    sel = [s.strip() for s in servicios.split(',') if s.strip()]
    alquiler, err = parking.register_vehicle(patente, tipo_alq, fi)
    if err:
        print(err)
        return
    for sname in sel:
        s = parking.find_servicio(sname)
        if s:
            alquiler.add_servicio(s)
    print("\n--- FACTURA FINAL ---")
    print(parking.end_rental(alquiler))

if __name__ == '__main__':
    main()
