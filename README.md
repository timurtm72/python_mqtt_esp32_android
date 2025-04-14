
#Мои данные:
~~~
[Мой сайт:] [https://technocom.site123.me/]
[Мое резюме инженер программист МК, ПЛК:] (https://innopolis.hh.ru/resume/782d86d5ff0e9487200039ed1f6f3373384b30)
[Мое резюме инженер программист Java,Java Spring:] (https://innopolis.hh.ru/resume/9e3b451aff03fd23830039ed1f496e79587649)
~~~
# Python MQTT Система Управления и Мониторинга ESP32

Python GUI приложение для управления ESP32 через MQTT протокол. Система позволяет мониторить данные с датчика температуры/влажности DHT и управлять RGB светодиодами через графический пользовательский интерфейс.

## Архитектура проекта

Приложение построено на основе Tkinter для GUI и Paho MQTT для коммуникации:

### Основные компоненты
- `MQTTClient` - класс для работы с MQTT протоколом
- `ESP32ControlApp` - главный класс приложения с GUI
- `FigureCanvasTkAgg` - интеграция графиков Matplotlib в Tkinter

### Модели данных
```python
# Данные RGB светодиода
{
    "red": int,      # 0-255
    "green": int,    # 0-255
    "blue": int,     # 0-255
    "brightness": int # 0-255
}

# Данные с датчика DHT
{
    "temperature": float, # °C
    "humidity": float    # %
}
```

## Основные функции

### Управление RGB светодиодом
- Графические слайдеры для настройки RGB (0-255)
- Слайдер регулировки яркости (0-255)
- Предпросмотр цвета в реальном времени
- Отправка команд через MQTT

### Мониторинг DHT сенсора
- Отображение текущей температуры и влажности
- Построение графиков в реальном времени
- Автоматическое масштабирование осей
- Хранение истории последних 20 измерений

## Технические особенности
- Многопоточная обработка MQTT сообщений
- Асинхронное обновление графического интерфейса
- Автоматическое переподключение к MQTT брокеру
- JSON сериализация для обмена данными
- Динамическое обновление графиков каждые 5 секунд

## Потоки данных

### Входящие (MQTT)
```json
{
  "temperature": 25.6,
  "humidity": 45.2
}
```

### Исходящие (MQTT)
```json
{
  "red": 255,
  "green": 0,
  "blue": 0,
  "brightness": 100
}
```

## Структура проекта
```plaintext
.
└── main.py          # Основной файл приложения
```

## Конфигурация
```python
# MQTT настройки
MQTT_BROKER = "193.43.147.210"
MQTT_PORT = 1883
MQTT_USERNAME = ""
MQTT_PASSWORD = ""

# Топики MQTT
MQTT_TOPIC_DHT = "esp32/sensor/dht"
MQTT_TOPIC_RGB = "esp32/control/rgb"
```

## Требования
- Python 3.x
- Библиотеки:
  - tkinter
  - paho-mqtt
  - matplotlib
  - json
  - threading
  - time

## Интерфейс пользователя
- Вкладка RGB Control:
  - Слайдеры для настройки цвета
  - Предпросмотр выбранного цвета
  - Кнопка отправки настроек на ESP32
- Вкладка DHT Data:
  - Текущие значения температуры/влажности
  - Графики изменения показателей во времени

## Функциональные возможности
- Подключение/отключение к MQTT брокеру
- Индикация статуса соединения
- Обработка ошибок при отправке/получении данных
- Автоматическое форматирование значений на графиках
- Ограничение истории данных для оптимальной производительности

## Запуск приложения
```bash
python main.py
```

## Связанные проекты
- [ESP32 прошивка](https://github.com/timurtm72/esp_idf_esp32_mqtt_android)
- [Flutter приложение](https://github.com/timurtm72/flutter_android_mqtt_python_esp32)
- [Kotlin приложение](https://github.com/timurtm72/kotlin_mqtt_esp32_python)

