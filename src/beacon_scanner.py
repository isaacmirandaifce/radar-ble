import asyncio
import time
from bleak import BleakScanner

class BeaconScanner:
    """
    Biblioteca para escanear continuamente dispositivos BLE na proximidade,
    mantendo um histórico persistente de todos os dispositivos encontrados.
    """
    def __init__(self):
        self.beacons = {} 
        self.scanner = BleakScanner(detection_callback=self._callback)

    def _callback(self, device, advertisement_data):
        mac = device.address
        nome = advertisement_data.local_name or device.name or "Desconhecido"
        rssi = advertisement_data.rssi
        
        self.beacons[mac] = {
            "nome": nome,
            "mac": mac,
            "rssi": rssi,
            "last_seen": time.time(),
            "detalhes": advertisement_data.manufacturer_data
        }

    async def start(self):
        await self.scanner.start()

    async def stop(self):
        await self.scanner.stop()

    def get_all_beacons(self, timeout=3.0, name_filter=None):
        """
        Retorna a lista de TODOS os beacons já vistos.
        Adiciona a flag 'is_active' se foi visto nos últimos 'timeout' segundos.
        """
        current_time = time.time()
        result = []
        
        for mac, data in list(self.beacons.items()):
            if name_filter is None or name_filter.lower() in data["nome"].lower():
                # Calcula se o beacon deu sinal recentemente
                is_active = (current_time - data["last_seen"]) <= timeout
                
                # Cria uma cópia dos dados e adiciona o status
                beacon_info = data.copy()
                beacon_info["is_active"] = is_active
                result.append(beacon_info)
        
        # Ordena a lista: Primeiro os Online (True), depois pelo sinal (maior para o menor)
        result.sort(key=lambda x: (x["is_active"], x["rssi"]), reverse=True)
        return result
