import platform
import sys
from datetime import datetime
from config import TOKEN, USERID
import psutil
import pyinotify
import telebot

bot = telebot.TeleBot(TOKEN)


def get_size(bytes: int, suffix: str='B') -> str:
	"""Получаем размер из байтов в более большие форматы. Доступны:
	килобайты, мегабайты, гигабайты, терабайты, петабайты.
	Аргументы:
	 + bytes: int - количество байтов
	 + suffix: str - тип суффикса
	Возвращает:
	 + str - размер"""
	factor = 1024

	for unit in ["", "K", "M", "G", "T", "P"]:
		if bytes < factor:
			return f'{bytes:.2f}{unit}{suffix}'
		bytes /= factor


def submit(text: str) -> None:
	"""Вывод на экран и в лог-файл
	Аргументы:
	 + text: str - текст для вывода"""
	bot.send_message(USERID, text)
	print(text)


class ResourceMonitor:
	"""Монитор системных ресурсов компьютера"""
	def __init__(self):
		# Инициализация объекта - создание переменных
		self.uname = platform.uname()
		self.cpufreq = psutil.cpu_freq()
		self.swap = psutil.swap_memory()
		self.svmem = psutil.virtual_memory()
		self.partitions = psutil.disk_partitions()
		self.if_addrs = psutil.net_if_addrs()
		self.net_io = psutil.net_io_counters()
		self.log = ''

	def call_all(self):
		# Вызов всех функций
		self.system_info()
		self.proc_info()
		self.ram_info()
		self.disk_info()
		self.network_info()

		with open('raspberryjam.txt', 'w') as file:
			file.write(self.log)
		
		with open('raspberryjam.txt', 'r') as file:
			bot.send_document(USERID, file)

	def print_log(self, text):
		self.log += f'{text}\n'

	def system_info(self):
		# Общая информация о системе
		self.print_log('=== Информация о системе ===')
		self.print_log(f'Система: {self.uname.system}')
		self.print_log(f'Имя сетевого узла: {self.uname.node}')
		self.print_log(f'Выпуск: {self.uname.release}')
		self.print_log(f'Версия: {self.uname.version}')
		self.print_log(f'Машина: {self.uname.machine}')
		self.print_log(f'Процессор: {self.uname.processor}')

	def proc_info(self):
		# Информация о процессоре
		self.print_log('=== Информация о процессоре ===')
		self.print_log(f'Физические ядра: {psutil.cpu_count(logical=False)}')
		self.print_log(f'Количество ядер: {psutil.cpu_count(logical=True)}')
		self.print_log(f'Маскимальная частота процессора: {self.cpufreq.max:.2f}МГц')
		self.print_log(f'Минимальная частота процессора: {self.cpufreq.min:.2f}МГц')
		self.print_log(f'Текущая частота процессора: {self.cpufreq.current:.2f}МГц')
		for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
			self.print_log(f'Загруженность ядра {i}: {percentage}%')
		self.print_log(f'Общая загруженность процессора: {psutil.cpu_percent()}%')

	def network_info(self):
		# Информация о сети
		self.print_log('=== Информация о сети ===')
		for inteface_name, interface_addresses in self.if_addrs.items():
			for address in interface_addresses:
				self.print_log(f'=== Информация о интерфейсе сети: {inteface_name} ===')
				if str(address.family) == 'AddressFamily.AF_INET':
					self.print_log(f'Тип интерфейса сети {inteface_name}: {str(address.family)}')
					self.print_log(f'IP интерфейса сети {inteface_name}: {address.address}')
					self.print_log(f'Сетевая маска интерфейса сети {inteface_name}: {address.netmask}')
					self.print_log(f'Широковещательный IP-адрес интерфейса сети {inteface_name}: {address.broadcast}')
				elif str(address.family) == 'AddressFamily.AF_PACKET':
					self.print_log(f'Тип интерфейса сети {inteface_name}: {str(address.family)}')
					self.print_log(f'MAC-адрес интерфейса сети {inteface_name}: {address.address}')
					self.print_log(f'Сетевая маска интерфейса сети {inteface_name}: {address.netmask}')
					self.print_log(f'Широковещательный IP-адрес интерфейса сети {inteface_name}: {address.broadcast}')
				else:
					self.print_log(f'Тип интерфейса сети {inteface_name}: {str(address.family)}')
					self.print_log(f'MAC-адрес интерфейса сети {inteface_name}: {address.address}')
					self.print_log(f'Сетевая маска интерфейса сети {inteface_name}: {address.netmask}')
					self.print_log(f'Широковещательный IP-адрес интерфейса сети {inteface_name}: {address.broadcast}')
		self.print_log(f'Общее количество отправленных байтов: {get_size(self.net_io.bytes_sent)}')
		self.print_log(f'Общее количество полученных байтов: {get_size(self.net_io.bytes_recv)}')

	def disk_info(self):
		# Информация о разделах диска
		self.print_log("=== Информация о дисках ===")
		for partition in self.partitions:
			self.print_log(f'=== Информация о разделе диска: {partition.device} ===')
			self.print_log(f'Файловая система раздела диска {partition.device}: {partition.fstype}')
			try:
				partition_usage = psutil.disk_usage(partition.mountpoint)
			except PermissionError:
				continue
			self.print_log(f'Общий обьем раздела диска {partition.device}: {get_size(partition_usage.total)}')
			self.print_log(f'Используемый обьем раздела диска {partition.device}: {get_size(partition_usage.used)}')
			self.print_log(f'Свободный обьем раздела диска {partition.device}: {get_size(partition_usage.free)}')
			self.print_log(f'Процент объема раздела диска {partition.device}: {get_size(partition_usage.percent)}')

	def ram_info(self):
		# Информация об оперативной памяти и памяти подкачки
		self.print_log('=== Информация об ОЗУ ===')
		self.print_log(f'Объем ОЗУ: {get_size(self.svmem.total)}')
		self.print_log(f'Доступно ОЗУ: {get_size(self.svmem.available)}')
		self.print_log(f'Используется ОЗУ: {get_size(self.svmem.used)}')
		self.print_log(f'Процент ОЗУ: {get_size(self.svmem.percent)}')
		if self.swap:
			self.print_log('=== Информация о памяти подкачки ===')
			self.print_log(f'Объем памяти подкачки: {get_size(self.swap.total)}')
			self.print_log(f'Свободно памяти подкачки: {get_size(self.swap.free)}')
			self.print_log(f'Используется памяти подкачки: {get_size(self.swap.used)}')
			self.print_log(f'Процент памяти подкачки: {self.swap.percent}%')


def infohandler():
	pcmon = ResourceMonitor()
	pcmon.call_all()


class Handler(pyinotify.ProcessEvent):
	def process_IN_OPEN(self, event):
		submit(f'[{datetime.now()}] Открыт: {event.pathname}')
		infohandler()

	def process_IN_MOVED_FROM(self, event):
		submit(f'[{datetime.now()}] Перемещен из: {event.pathname}')
		infohandler()

	def process_IN_CREATE(self, event):
		submit(f'[{datetime.now()}] Создан: {event.pathname}')
		infohandler()

	def process_IN_MODIFY(self, event):
		submit(f'[{datetime.now()}] Модифицирован: {event.pathname}')
		infohandler()

	def process_IN_DELETE(self, event):
		submit(f'[{datetime.now()}] Удален: {event.pathname}')
		infohandler()


class RaspberryJam:
	def __init__(self, dirpath: str, handler):
		self.dirpath = dirpath
		self.multi_event = pyinotify.IN_OPEN | pyinotify.IN_CREATE | pyinotify.IN_MOVED_FROM | pyinotify.IN_MODIFY | pyinotify.IN_DELETE

		self.wm = pyinotify.WatchManager()
		self.handler = handler
		self.notifier = pyinotify.Notifier(self.wm, self.handler)

	def watching(self):
		self.wm.add_watch(self.dirpath, self.multi_event)
		self.notifier.loop()


def main():
	if len(sys.argv) > 1:
		print('Opening Raspberry Jam...')
		print('Raspberry Jam is opened!')

		eventhandler = Handler()
		raspberryjam = RaspberryJam(sys.argv[1], eventhandler)

		raspberryjam.watching()
		bot.polling()
	else:
		print('please, launch with path to directory')


if __name__ == '__main__':
	main()
