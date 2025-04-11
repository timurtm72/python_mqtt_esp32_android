# Импортируем нужные библиотеки
import tkinter as tk                # Основная библиотека для создания графического интерфейса
from tkinter import ttk, messagebox # ttk - улучшенные виджеты, messagebox - для всплывающих сообщений
import paho.mqtt.client as mqtt     # Библиотека для работы с MQTT протоколом - протокол для IoT устройств
import json                         # Для работы с JSON форматом данных
import time                         # Для работы со временем
from matplotlib.figure import Figure # Для создания графиков
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # Адаптер для встраивания графиков в tkinter
import threading                    # Для работы с потоками
import matplotlib.ticker as ticker  # Для форматирования осей графиков
from matplotlib.ticker import FuncFormatter # Для пользовательского форматирования значений на графике

# Настройки подключения к MQTT брокеру
MQTT_BROKER = "193.43.147.210"  # IP-адрес MQTT брокера
MQTT_PORT = 1883                # Стандартный порт для MQTT
MQTT_USERNAME = ""         # Имя пользователя для авторизации
MQTT_PASSWORD = ""    # Пароль для авторизации
MQTT_TOPIC_DHT = "esp32/sensor/dht"  # Топик, куда ESP32 отправляет данные с DHT-сенсора
MQTT_TOPIC_RGB = "esp32/control/rgb"  # Топик для управления RGB-светодиодом

# Класс для работы с MQTT клиентом
class MQTTClient:
    # Функция обработки события подключения
    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:  # rc=0 означает успешное подключение
            print("Connected to MQTT Broker!")
            self.connected = True  # Ставим флаг, что подключены
            # Подписываемся на топик с данными от сенсора
            self.client.subscribe(MQTT_TOPIC_DHT)
        else:  # Если rc не 0, значит ошибка
            print(f"Failed to connect, return code {rc}")
            self.connected = False
    
    # Конструктор класса - инициализация при создании объекта        
    def __init__(self, broker, port, username, password, on_message_callback):
        # Создаем MQTT клиент с версией MQTTv5
        self.client = mqtt.Client(client_id="", protocol=mqtt.MQTTv5)
        # Устанавливаем логин и пароль
        self.client.username_pw_set(username, password)
        # Задаем функции обратного вызова для событий
        self.client.on_connect = self.on_connect  # Вызовется при подключении
        self.client.on_message = on_message_callback  # Вызовется при получении сообщения
        # Сохраняем параметры подключения
        self.broker = broker
        self.port = port
        self.connected = False  # Изначально не подключены
    
    # Метод для подключения к брокеру
    def connect(self):
        try:
            # Подключаемся к брокеру с таймаутом 60 секунд
            self.client.connect(self.broker, self.port, 60)
            # Запускаем обработку MQTT сообщений в отдельном потоке
            self.client.loop_start()
            return True
        except Exception as e:
            # Если произошла ошибка, выводим сообщение
            print(f"Connection error: {e}")
            return False
    
    # Метод для отключения от брокера
    def disconnect(self):
        self.client.loop_stop()  # Останавливаем обработку сообщений
        self.client.disconnect()  # Отключаемся от брокера
    
    # Метод для отправки сообщения в определенный топик
    def publish(self, topic, message):
        if self.connected:  # Проверяем, подключены ли мы
            # Отправляем сообщение
            result = self.client.publish(topic, message)
            status = result[0]  # Получаем статус отправки
            if status == 0:  # 0 означает успешную отправку
                print(f"Message sent to topic {topic}")
                return True
            else:
                print(f"Failed to send message to topic {topic}")
                return False
        else:
            print("Not connected to broker")
            return False

# Главный класс приложения - интерфейс для управления ESP32
class ESP32ControlApp:
    # Конструктор класса
    def __init__(self, root):
        self.root = root  # Корневое окно приложения
        self.root.title("ESP32 MQTT Control")  # Заголовок окна
        self.root.geometry("800x600")  # Начальный размер окна
        self.root.minsize(800, 600)  # Минимальный размер окна
        
        # Массивы для хранения данных для графиков
        self.temp_data = []  # Данные температуры
        self.hum_data = []   # Данные влажности
        self.time_data = []  # Временные метки
        
        # Создаем элементы интерфейса
        self.create_widgets()
        
        # Создаем MQTT клиент с параметрами из глобальных переменных
        self.mqtt_client = MQTTClient(
            MQTT_BROKER, 
            MQTT_PORT, 
            MQTT_USERNAME, 
            MQTT_PASSWORD, 
            self.on_message  # Передаем метод-обработчик сообщений
        )
        
        # Пытаемся подключиться к брокеру при запуске
        self.connect_to_broker()
        
        # Запускаем периодическое обновление графиков
        self._update_graphs()
    
    # Метод для создания всех элементов интерфейса    
    def create_widgets(self):
        # Создаем контейнер для вкладок
        self.tab_control = ttk.Notebook(self.root)
        
        # Создаем первую вкладку для управления RGB светодиодом
        self.tab_rgb = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_rgb, text="RGB Control")
        
        # Создаем вторую вкладку для отображения данных с DHT сенсора
        self.tab_dht = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_dht, text="DHT Data")
        
        # Размещаем контейнер с вкладками в окне
        self.tab_control.pack(expand=1, fill="both")
        
        # Настраиваем содержимое вкладок
        self.setup_rgb_tab()  # Настройка вкладки RGB
        self.setup_dht_tab()  # Настройка вкладки DHT
        
        # Создаем фрейм для отображения статуса подключения внизу окна
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill="x", side="bottom", padx=5, pady=5)
        
        # Метка для отображения статуса
        self.status_label = ttk.Label(self.status_frame, text="Status: Disconnected")
        self.status_label.pack(side="left")
        
        # Кнопка для подключения/отключения
        self.connect_button = ttk.Button(self.status_frame, text="Connect", command=self.connect_to_broker)
        self.connect_button.pack(side="right")
    
    # Метод для настройки вкладки с управлением RGB    
    def setup_rgb_tab(self):
        # Создаем фрейм для слайдеров
        self.rgb_frame = ttk.LabelFrame(self.tab_rgb, text="RGB Controls")
        self.rgb_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Создаем переменные для хранения значений RGB и яркости
        self.red_var = tk.IntVar(value=0)  # Красный (0-255)
        self.green_var = tk.IntVar(value=0)  # Зеленый (0-255)
        self.blue_var = tk.IntVar(value=0)  # Синий (0-255)
        self.brightness_var = tk.IntVar(value=100)  # Яркость (0-255)
        
        # Слайдер для красного цвета
        ttk.Label(self.rgb_frame, text="Red:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.red_slider = ttk.Scale(self.rgb_frame, from_=0, to=255, orient="horizontal", 
                                   variable=self.red_var, command=self.update_color_preview)
        self.red_slider.grid(row=0, column=1, sticky="we", padx=5, pady=5)
        ttk.Label(self.rgb_frame, textvariable=self.red_var).grid(row=0, column=2, padx=5, pady=5)
        
        # Слайдер для зеленого цвета
        ttk.Label(self.rgb_frame, text="Green:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.green_slider = ttk.Scale(self.rgb_frame, from_=0, to=255, orient="horizontal", 
                                     variable=self.green_var, command=self.update_color_preview)
        self.green_slider.grid(row=1, column=1, sticky="we", padx=5, pady=5)
        ttk.Label(self.rgb_frame, textvariable=self.green_var).grid(row=1, column=2, padx=5, pady=5)
        
        # Слайдер для синего цвета
        ttk.Label(self.rgb_frame, text="Blue:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.blue_slider = ttk.Scale(self.rgb_frame, from_=0, to=255, orient="horizontal", 
                                    variable=self.blue_var, command=self.update_color_preview)
        self.blue_slider.grid(row=2, column=1, sticky="we", padx=5, pady=5)
        ttk.Label(self.rgb_frame, textvariable=self.blue_var).grid(row=2, column=2, padx=5, pady=5)
        
        # Слайдер для яркости
        ttk.Label(self.rgb_frame, text="Brightness:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.brightness_slider = ttk.Scale(self.rgb_frame, from_=0, to=255, orient="horizontal", 
                                         variable=self.brightness_var, command=self.update_color_preview)
        self.brightness_slider.grid(row=3, column=1, sticky="we", padx=5, pady=5)
        ttk.Label(self.rgb_frame, textvariable=self.brightness_var).grid(row=3, column=2, padx=5, pady=5)
        
        # Настраиваем, чтобы слайдеры растягивались при изменении размера окна
        self.rgb_frame.columnconfigure(1, weight=1)
        
        # Создаем фрейм для предпросмотра цвета
        self.preview_frame = ttk.LabelFrame(self.tab_rgb, text="Color Preview")
        self.preview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Канвас для отображения выбранного цвета
        self.color_preview = tk.Canvas(self.preview_frame, width=200, height=100, bg="#000000")
        self.color_preview.pack(padx=10, pady=10, expand=True, fill="both")
        
        # Кнопка для отправки значений RGB на ESP32
        self.send_button = ttk.Button(self.tab_rgb, text="Send to ESP32", command=self.send_rgb_values)
        self.send_button.pack(pady=10)
        
    # Метод для настройки вкладки с данными DHT-сенсора    
    def setup_dht_tab(self):
        # Фрейм для отображения текущих значений
        self.current_frame = ttk.LabelFrame(self.tab_dht, text="Current Values")
        self.current_frame.pack(fill="x", padx=10, pady=10)
        
        # Метки для отображения температуры и влажности
        self.temp_label = ttk.Label(self.current_frame, text="Temperature: N/A")
        self.temp_label.pack(side="left", padx=20, pady=10)
        
        self.hum_label = ttk.Label(self.current_frame, text="Humidity: N/A")
        self.hum_label.pack(side="right", padx=20, pady=10)
        
        # Фрейм для графиков исторических данных
        self.graph_frame = ttk.LabelFrame(self.tab_dht, text="Historical Data")
        self.graph_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Создаем фигуру matplotlib для графиков
        self.figure = Figure(figsize=(8, 4), dpi=100)
        
        # Создаем график для температуры (верхний)
        self.temp_plot = self.figure.add_subplot(211)  # 2 строки, 1 столбец, 1-й график
        self.temp_plot.set_title("Temperature (°C)")
        self.temp_plot.set_ylabel("Temperature (°C)")
        self.temp_plot.grid(True)  # Включаем сетку
        
        # Создаем график для влажности (нижний)
        self.hum_plot = self.figure.add_subplot(212)  # 2 строки, 1 столбец, 2-й график
        self.hum_plot.set_title("Humidity (%)")
        self.hum_plot.set_xlabel("Time")
        self.hum_plot.set_ylabel("Humidity (%)")
        self.hum_plot.grid(True)  # Включаем сетку
        
        # Создаем канвас tkinter для отображения графиков matplotlib
        self.canvas = FigureCanvasTkAgg(self.figure, self.graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Устанавливаем автоматическое размещение графиков
        self.figure.tight_layout()
    
    # Метод для обновления предпросмотра цвета при изменении слайдеров    
    def update_color_preview(self, *args):
        # Получаем текущие значения цветов
        r = int(self.red_var.get())
        g = int(self.green_var.get())
        b = int(self.blue_var.get())
        
        # Ограничиваем значения диапазоном 0-255
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        # Создаем цвет в HEX формате (#RRGGBB)
        color = f"#{r:02x}{g:02x}{b:02x}"  # Форматируем каждое значение как 2-значное hex число
        self.color_preview.config(bg=color)  # Устанавливаем цвет фона канваса
    
    # Метод для отправки RGB значений на ESP32    
    def send_rgb_values(self):
        # Проверяем, что мы подключены к брокеру
        if not hasattr(self, 'mqtt_client') or not self.mqtt_client.connected:
            messagebox.showerror("Error", "Not connected to MQTT broker.")
            return
            
        # Получаем значения RGB и яркости
        r = int(self.red_var.get())
        g = int(self.green_var.get())
        b = int(self.blue_var.get())
        brightness = int(self.brightness_var.get())
        
        # Создаем словарь с данными
        data = {
            "red": r,
            "green": g,
            "blue": b,
            "brightness": brightness
        }
        
        # Преобразуем словарь в JSON строку
        payload = json.dumps(data)
        
        # Отправляем данные на ESP32
        success = self.mqtt_client.publish(MQTT_TOPIC_RGB, payload)
        
        # Выводим сообщение об успехе или ошибке
        if success:
            messagebox.showinfo("Success", "RGB values sent to ESP32!")
        else:
            messagebox.showerror("Error", "Failed to send RGB values.")
    
    # Обработчик входящих MQTT сообщений    
    def on_message(self, client, userdata, msg):
        topic = msg.topic  # Топик сообщения
        payload = msg.payload.decode("utf-8")  # Декодируем содержимое из байтов в строку
        
        try:
            # Обрабатываем только сообщения от DHT сенсора
            if topic == MQTT_TOPIC_DHT:
                # Парсим JSON данные
                data = json.loads(payload)
                
                # Извлекаем температуру и влажность, и округляем до 1 знака
                temperature = round(data.get("temperature", 0), 1)
                humidity = round(data.get("humidity", 0), 1)
                
                # Обновляем метки в GUI потоке (важно, т.к. MQTT работает в другом потоке)
                self.root.after(0, lambda: self.update_dht_labels(temperature, humidity))
                
                # Добавляем текущее время для графика
                current_time = time.strftime("%H:%M:%S")
                
                # Ограничиваем максимальное количество точек данных
                max_points = 20
                
                # Добавляем новые данные в массивы
                self.temp_data.append(temperature)
                self.hum_data.append(humidity)
                self.time_data.append(current_time)
                
                # Оставляем только последние max_points точек
                if len(self.temp_data) > max_points:
                    self.temp_data = self.temp_data[-max_points:]
                    self.hum_data = self.hum_data[-max_points:]
                    self.time_data = self.time_data[-max_points:]
                
        except Exception as e:
            print(f"Error processing message: {e}")
    
    # Метод для обновления меток с текущими значениями    
    def update_dht_labels(self, temperature, humidity):
        # Обновляем текст меток с форматированием до 1 знака после запятой
        self.temp_label.config(text=f"Temperature: {temperature:.1f}°C")
        self.hum_label.config(text=f"Humidity: {humidity:.1f}%")
    
    # Метод для обновления графиков    
    def _update_graphs(self):
        # Функция форматирования чисел для осей - одно число после запятой
        def format_axis(x, pos):
            return f"{x:.1f}"
            
        # Обновляем графики температуры и влажности
        try:
            # Очищаем графики
            self.temp_plot.clear()
            self.hum_plot.clear()
            
            # Настраиваем график температуры
            self.temp_plot.set_title("Temperature (°C)")
            self.temp_plot.set_ylabel("Temperature (°C)")
            self.temp_plot.grid(True)
            # Устанавливаем форматирование чисел на оси Y
            self.temp_plot.yaxis.set_major_formatter(FuncFormatter(format_axis))
            
            # Настраиваем график влажности
            self.hum_plot.set_title("Humidity (%)")
            self.hum_plot.set_xlabel("Time")
            self.hum_plot.set_ylabel("Humidity (%)")
            self.hum_plot.grid(True)
            # Устанавливаем форматирование чисел на оси Y
            self.hum_plot.yaxis.set_major_formatter(FuncFormatter(format_axis))
            
            # Если есть данные для отображения
            if self.temp_data and self.hum_data and self.time_data:
                # Округляем данные до одного знака после запятой
                plot_temp_data = [round(t, 1) for t in self.temp_data]
                plot_hum_data = [round(h, 1) for h in self.hum_data]
                
                # Отрисовываем графики: красная линия - температура, синяя - влажность
                self.temp_plot.plot(range(len(plot_temp_data)), plot_temp_data, 'r-')
                self.hum_plot.plot(range(len(plot_hum_data)), plot_hum_data, 'b-')
                
                # Устанавливаем метки времени по оси X
                if len(self.time_data) > 10:
                    # Если точек много, показываем только часть для читаемости
                    step = len(self.time_data) // 5
                    self.temp_plot.set_xticks(range(0, len(self.time_data), step))
                    self.temp_plot.set_xticklabels([self.time_data[i] for i in range(0, len(self.time_data), step)], rotation=45)
                    self.hum_plot.set_xticks(range(0, len(self.time_data), step))
                    self.hum_plot.set_xticklabels([self.time_data[i] for i in range(0, len(self.time_data), step)], rotation=45)
                else:
                    # Если точек мало, показываем все
                    self.temp_plot.set_xticks(range(len(self.time_data)))
                    self.temp_plot.set_xticklabels(self.time_data, rotation=45)
                    self.hum_plot.set_xticks(range(len(self.time_data)))
                    self.hum_plot.set_xticklabels(self.time_data, rotation=45)
            
            # Применяем автоматическое размещение графиков
            self.figure.tight_layout()
            # Обновляем отображение канваса
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error updating graphs: {e}")
        
        # Планируем следующее обновление через 5 секунд
        self.root.after(5000, self._update_graphs)
    
    # Метод для подключения к MQTT брокеру    
    def connect_to_broker(self):
        # Пытаемся подключиться через MQTT клиент
        if self.mqtt_client.connect():
            # Если успешно, обновляем статус и меняем кнопку на "Отключиться"
            self.status_label.config(text="Status: Connected")
            self.connect_button.config(text="Disconnect", command=self.disconnect_from_broker)
        else:
            # Если ошибка, показываем статус
            self.status_label.config(text="Status: Connection Failed")
    
    # Метод для отключения от MQTT брокера    
    def disconnect_from_broker(self):
        # Отключаемся от брокера
        self.mqtt_client.disconnect()
        # Обновляем статус и меняем кнопку на "Подключиться"
        self.status_label.config(text="Status: Disconnected")
        self.connect_button.config(text="Connect", command=self.connect_to_broker)
    
    # Метод вызываемый при закрытии приложения    
    def on_closing(self):
        # Отключаемся от брокера, если подключены
        if hasattr(self, 'mqtt_client'):
            self.mqtt_client.disconnect()
        self.root.destroy()  # Закрываем окно приложения

# Точка входа программы - выполняется только если запущен этот файл напрямую
if __name__ == "__main__":
    root = tk.Tk()  # Создаем корневое окно Tkinter
    app = ESP32ControlApp(root)  # Создаем приложение
    root.protocol("WM_DELETE_WINDOW", app.on_closing)  # Привязываем обработчик закрытия окна
    root.mainloop()  # Запускаем главный цикл обработки событий

#echo "# python_gui_mqtt_esp32" >> README.md
#git init
#git add README.md
#git commit -m "first commit"
#git branch -M main
#git remote add origin https://github.com/timurtm72/python_gui_mqtt_esp32.git
#git push -u origin main