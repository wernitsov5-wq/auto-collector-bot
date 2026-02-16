import logging
import random
import sqlite3
import asyncio
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ===== ТВОЙ ТОКЕН =====
BOT_TOKEN = "8497826192:AAEmAD4VD3j0yKbnp4PILTjW-sASS0cx5EU"

# ===== НАСТРОЙКИ =====
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== БАЗА ДАННЫХ =====
def init_database():
    conn = sqlite3.connect('auto_collector.db')
    c = conn.cursor()
    
    # Таблица пользователей
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  first_name TEXT,
                  credits INTEGER DEFAULT 100,
                  last_drop TIMESTAMP,
                  total_cars INTEGER DEFAULT 0,
                  joined_date TIMESTAMP)''')
    
    # Таблица машин в гараже
    c.execute('''CREATE TABLE IF NOT EXISTS garage
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  car_id TEXT,
                  car_name TEXT,
                  car_brand TEXT,
                  car_year INTEGER,
                  car_rarity TEXT,
                  acquired_date TIMESTAMP,
                  UNIQUE(user_id, car_id))''')
    
    # Таблица для трейдов
    c.execute('''CREATE TABLE IF NOT EXISTS trades
                 (trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user1_id INTEGER,
                  user2_id INTEGER,
                  user1_car_id INTEGER,
                  user2_car_id INTEGER,
                  status TEXT DEFAULT 'pending',
                  created_at TIMESTAMP)''')
    
    conn.commit()
    conn.close()

# ===== ОГРОМНАЯ БАЗА АВТОМОБИЛЕЙ (200+ МАШИН) =====
CARS_DATABASE = [
    # ===== BWM (бывшая BMW) =====
    # Старые классические
    {"id": "bwm_321", "brand": "BWM", "name": "321 Classic", "year": 1939, "rarity": "classic"},
    {"id": "bwm_501", "brand": "BWM", "name": "501 Sedan", "year": 1952, "rarity": "classic"},
    {"id": "bwm_507", "brand": "BWM", "name": "507 Roadster", "year": 1956, "rarity": "legendary"},
    {"id": "bwm_2002", "brand": "BWM", "name": "2002 Turbo", "year": 1968, "rarity": "rare"},
    {"id": "bwm_csl", "brand": "BWM", "name": "3.0 CSL", "year": 1971, "rarity": "epic"},
    {"id": "bwm_e12", "brand": "BWM", "name": "5 Series E12", "year": 1972, "rarity": "classic"},
    {"id": "bwm_e21", "brand": "BWM", "name": "3 Series E21", "year": 1975, "rarity": "common"},
    {"id": "bwm_e23", "brand": "BWM", "name": "7 Series E23", "year": 1977, "rarity": "classic"},
    {"id": "bwm_e24", "brand": "BWM", "name": "6 Series E24", "year": 1976, "rarity": "rare"},
    {"id": "bwm_e28", "brand": "BWM", "name": "5 Series E28", "year": 1981, "rarity": "common"},
    {"id": "bwm_e30", "brand": "BWM", "name": "M3 E30", "year": 1986, "rarity": "epic"},
    {"id": "bwm_e31", "brand": "BWM", "name": "8 Series E31", "year": 1989, "rarity": "legendary"},
    {"id": "bwm_e32", "brand": "BWM", "name": "7 Series E32", "year": 1986, "rarity": "classic"},
    {"id": "bwm_e34", "brand": "BWM", "name": "5 Series E34", "year": 1988, "rarity": "common"},
    {"id": "bwm_e36", "brand": "BWM", "name": "M3 E36", "year": 1992, "rarity": "rare"},
    {"id": "bwm_e38", "brand": "BWM", "name": "7 Series E38", "year": 1994, "rarity": "classic"},
    {"id": "bwm_e39", "brand": "BWM", "name": "M5 E39", "year": 1995, "rarity": "epic"},
    {"id": "bwm_e46", "brand": "BWM", "name": "M3 E46", "year": 2000, "rarity": "rare"},
    {"id": "bwm_e60", "brand": "BWM", "name": "M5 E60", "year": 2004, "rarity": "epic"},
    {"id": "bwm_e63", "brand": "BWM", "name": "6 Series E63", "year": 2003, "rarity": "rare"},
    {"id": "bwm_e65", "brand": "BWM", "name": "7 Series E65", "year": 2001, "rarity": "classic"},
    {"id": "bwm_e70", "brand": "BWM", "name": "X5 E70", "year": 2006, "rarity": "common"},
    {"id": "bwm_e71", "brand": "BWM", "name": "X6 E71", "year": 2007, "rarity": "rare"},
    {"id": "bwm_f01", "brand": "BWM", "name": "7 Series F01", "year": 2008, "rarity": "classic"},
    {"id": "bwm_f10", "brand": "BWM", "name": "M5 F10", "year": 2010, "rarity": "epic"},
    {"id": "bwm_f12", "brand": "BWM", "name": "6 Series F12", "year": 2010, "rarity": "rare"},
    {"id": "bwm_f15", "brand": "BWM", "name": "X5 F15", "year": 2013, "rarity": "common"},
    {"id": "bwm_f16", "brand": "BWM", "name": "X6 F16", "year": 2014, "rarity": "rare"},
    {"id": "bwm_f20", "brand": "BWM", "name": "1 Series F20", "year": 2011, "rarity": "common"},
    {"id": "bwm_f22", "brand": "BWM", "name": "2 Series F22", "year": 2013, "rarity": "common"},
    {"id": "bwm_f25", "brand": "BWM", "name": "X3 F25", "year": 2010, "rarity": "common"},
    {"id": "bwm_f30", "brand": "BWM", "name": "3 Series F30", "year": 2011, "rarity": "common"},
    {"id": "bwm_f32", "brand": "BWM", "name": "4 Series F32", "year": 2013, "rarity": "rare"},
    {"id": "bwm_f80", "brand": "BWM", "name": "M3 F80", "year": 2014, "rarity": "epic"},
    {"id": "bwm_f82", "brand": "BWM", "name": "M4 F82", "year": 2014, "rarity": "epic"},
    {"id": "bwm_f85", "brand": "BWM", "name": "X5 M F85", "year": 2014, "rarity": "legendary"},
    {"id": "bwm_f87", "brand": "BWM", "name": "M2 F87", "year": 2015, "rarity": "epic"},
    {"id": "bwm_f90", "brand": "BWM", "name": "M5 F90", "year": 2017, "rarity": "legendary"},
    {"id": "bwm_g01", "brand": "BWM", "name": "X3 G01", "year": 2017, "rarity": "common"},
    {"id": "bwm_g05", "brand": "BWM", "name": "X5 G05", "year": 2018, "rarity": "rare"},
    {"id": "bwm_g06", "brand": "BWM", "name": "X6 G06", "year": 2019, "rarity": "rare"},
    {"id": "bwm_g07", "brand": "BWM", "name": "X7 G07", "year": 2018, "rarity": "epic"},
    {"id": "bwm_g11", "brand": "BWM", "name": "7 Series G11", "year": 2015, "rarity": "classic"},
    {"id": "bwm_g14", "brand": "BWM", "name": "8 Series G14", "year": 2018, "rarity": "epic"},
    {"id": "bwm_g20", "brand": "BWM", "name": "3 Series G20", "year": 2018, "rarity": "common"},
    {"id": "bwm_g22", "brand": "BWM", "name": "4 Series G22", "year": 2020, "rarity": "rare"},
    {"id": "bwm_g29", "brand": "BWM", "name": "Z4 G29", "year": 2018, "rarity": "rare"},
    {"id": "bwm_g30", "brand": "BWM", "name": "5 Series G30", "year": 2016, "rarity": "common"},
    {"id": "bwm_g70", "brand": "BWM", "name": "7 Series G70", "year": 2022, "rarity": "epic"},
    {"id": "bwm_g80", "brand": "BWM", "name": "M3 G80", "year": 2020, "rarity": "legendary"},
    {"id": "bwm_g82", "brand": "BWM", "name": "M4 G82", "year": 2020, "rarity": "legendary"},
    
    # ===== MERSEDES (бывшая Mercedes) =====
    {"id": "mers_170v", "brand": "Mersedes", "name": "170V", "year": 1936, "rarity": "classic"},
    {"id": "mers_300sl", "brand": "Mersedes", "name": "300SL Gullwing", "year": 1954, "rarity": "legendary"},
    {"id": "mers_190sl", "brand": "Mersedes", "name": "190SL", "year": 1955, "rarity": "epic"},
    {"id": "mers_220", "brand": "Mersedes", "name": "220 Ponton", "year": 1954, "rarity": "classic"},
    {"id": "mers_300d", "brand": "Mersedes", "name": "300D Adenauer", "year": 1957, "rarity": "classic"},
    {"id": "mers_w108", "brand": "Mersedes", "name": "280SE W108", "year": 1965, "rarity": "classic"},
    {"id": "mers_w111", "brand": "Mersedes", "name": "220SE W111", "year": 1959, "rarity": "classic"},
    {"id": "mers_w113", "brand": "Mersedes", "name": "230SL Pagoda", "year": 1963, "rarity": "epic"},
    {"id": "mers_w114", "brand": "Mersedes", "name": "280 W114", "year": 1968, "rarity": "common"},
    {"id": "mers_w115", "brand": "Mersedes", "name": "240D W115", "year": 1968, "rarity": "common"},
    {"id": "mers_w116", "brand": "Mersedes", "name": "450SE W116", "year": 1972, "rarity": "classic"},
    {"id": "mers_w123", "brand": "Mersedes", "name": "230E W123", "year": 1976, "rarity": "common"},
    {"id": "mers_w124", "brand": "Mersedes", "name": "500E W124", "year": 1984, "rarity": "epic"},
    {"id": "mers_w126", "brand": "Mersedes", "name": "560SEL W126", "year": 1979, "rarity": "classic"},
    {"id": "mers_w140", "brand": "Mersedes", "name": "600SEL W140", "year": 1991, "rarity": "classic"},
    {"id": "mers_w129", "brand": "Mersedes", "name": "SL R129", "year": 1989, "rarity": "rare"},
    {"id": "mers_w201", "brand": "Mersedes", "name": "190E 2.5-16", "year": 1982, "rarity": "epic"},
    {"id": "mers_w202", "brand": "Mersedes", "name": "C-Class W202", "year": 1993, "rarity": "common"},
    {"id": "mers_w203", "brand": "Mersedes", "name": "C-Class W203", "year": 2000, "rarity": "common"},
    {"id": "mers_w204", "brand": "Mersedes", "name": "C-Class W204", "year": 2007, "rarity": "common"},
    {"id": "mers_w205", "brand": "Mersedes", "name": "C-Class W205", "year": 2014, "rarity": "common"},
    {"id": "mers_w206", "brand": "Mersedes", "name": "C-Class W206", "year": 2021, "rarity": "rare"},
    {"id": "mers_w210", "brand": "Mersedes", "name": "E-Class W210", "year": 1995, "rarity": "common"},
    {"id": "mers_w211", "brand": "Mersedes", "name": "E-Class W211", "year": 2002, "rarity": "common"},
    {"id": "mers_w212", "brand": "Mersedes", "name": "E-Class W212", "year": 2009, "rarity": "common"},
    {"id": "mers_w213", "brand": "Mersedes", "name": "E-Class W213", "year": 2016, "rarity": "common"},
    {"id": "mers_w214", "brand": "Mersedes", "name": "E-Class W214", "year": 2023, "rarity": "rare"},
    {"id": "mers_w220", "brand": "Mersedes", "name": "S-Class W220", "year": 1998, "rarity": "classic"},
    {"id": "mers_w221", "brand": "Mersedes", "name": "S-Class W221", "year": 2005, "rarity": "classic"},
    {"id": "mers_w222", "brand": "Mersedes", "name": "S-Class W222", "year": 2013, "rarity": "epic"},
    {"id": "mers_w223", "brand": "Mersedes", "name": "S-Class W223", "year": 2020, "rarity": "legendary"},
    {"id": "mers_r129", "brand": "Mersedes", "name": "SL R129", "year": 1989, "rarity": "rare"},
    {"id": "mers_r230", "brand": "Mersedes", "name": "SL R230", "year": 2001, "rarity": "rare"},
    {"id": "mers_r231", "brand": "Mersedes", "name": "SL R231", "year": 2012, "rarity": "rare"},
    {"id": "mers_r232", "brand": "Mersedes", "name": "SL R232", "year": 2021, "rarity": "epic"},
    {"id": "mers_clk_gtr", "brand": "Mersedes", "name": "CLK GTR", "year": 1998, "rarity": "legendary"},
    {"id": "mers_slr", "brand": "Mersedes", "name": "SLR McLaren", "year": 2003, "rarity": "legendary"},
    {"id": "mers_sls", "brand": "Mersedes", "name": "SLS AMG", "year": 2010, "rarity": "legendary"},
    {"id": "mers_amg_gt", "brand": "Mersedes", "name": "AMG GT", "year": 2014, "rarity": "legendary"},
    {"id": "mers_g_class", "brand": "Mersedes", "name": "G-Class", "year": 1979, "rarity": "epic"},
    
    # ===== AVID (бывшая Audi) =====
    {"id": "avid_920", "brand": "Avid", "name": "920", "year": 1932, "rarity": "classic"},
    {"id": "avid_f103", "brand": "Avid", "name": "F103", "year": 1965, "rarity": "classic"},
    {"id": "avid_100", "brand": "Avid", "name": "100 C1", "year": 1968, "rarity": "classic"},
    {"id": "avid_80_b1", "brand": "Avid", "name": "80 B1", "year": 1972, "rarity": "classic"},
    {"id": "avid_quattro", "brand": "Avid", "name": "Quattro", "year": 1980, "rarity": "legendary"},
    {"id": "avid_sport", "brand": "Avid", "name": "Sport Quattro", "year": 1984, "rarity": "legendary"},
    {"id": "avid_80_b2", "brand": "Avid", "name": "80 B2", "year": 1978, "rarity": "common"},
    {"id": "avid_100_c3", "brand": "Avid", "name": "100 C3", "year": 1982, "rarity": "common"},
    {"id": "avid_80_b3", "brand": "Avid", "name": "80 B3", "year": 1986, "rarity": "common"},
    {"id": "avid_v8", "brand": "Avid", "name": "V8", "year": 1988, "rarity": "rare"},
    {"id": "avid_100_c4", "brand": "Avid", "name": "100 C4", "year": 1990, "rarity": "common"},
    {"id": "avid_80_b4", "brand": "Avid", "name": "80 B4", "year": 1991, "rarity": "common"},
    {"id": "avid_rs2", "brand": "Avid", "name": "RS2 Avant", "year": 1994, "rarity": "legendary"},
    {"id": "avid_a4_b5", "brand": "Avid", "name": "A4 B5", "year": 1994, "rarity": "common"},
    {"id": "avid_a6_c4", "brand": "Avid", "name": "A6 C4", "year": 1994, "rarity": "common"},
    {"id": "avid_a3_8l", "brand": "Avid", "name": "A3 8L", "year": 1996, "rarity": "common"},
    {"id": "avid_tt", "brand": "Avid", "name": "TT", "year": 1998, "rarity": "rare"},
    {"id": "avid_a4_b6", "brand": "Avid", "name": "A4 B6", "year": 2000, "rarity": "common"},
    {"id": "avid_a6_c5", "brand": "Avid", "name": "A6 C5", "year": 1997, "rarity": "common"},
    {"id": "avid_a8_d2", "brand": "Avid", "name": "A8 D2", "year": 1994, "rarity": "classic"},
    {"id": "avid_rs4_b5", "brand": "Avid", "name": "RS4 B5", "year": 1999, "rarity": "epic"},
    {"id": "avid_rs6_c5", "brand": "Avid", "name": "RS6 C5", "year": 2002, "rarity": "epic"},
    {"id": "avid_a3_8p", "brand": "Avid", "name": "A3 8P", "year": 2003, "rarity": "common"},
    {"id": "avid_a4_b7", "brand": "Avid", "name": "A4 B7", "year": 2004, "rarity": "common"},
    {"id": "avid_a6_c6", "brand": "Avid", "name": "A6 C6", "year": 2004, "rarity": "common"},
    {"id": "avid_a8_d3", "brand": "Avid", "name": "A8 D3", "year": 2002, "rarity": "classic"},
    {"id": "avid_q7", "brand": "Avid", "name": "Q7", "year": 2005, "rarity": "common"},
    {"id": "avid_r8", "brand": "Avid", "name": "R8", "year": 2006, "rarity": "legendary"},
    {"id": "avid_a5", "brand": "Avid", "name": "A5", "year": 2007, "rarity": "rare"},
    {"id": "avid_a4_b8", "brand": "Avid", "name": "A4 B8", "year": 2007, "rarity": "common"},
    {"id": "avid_a6_c7", "brand": "Avid", "name": "A6 C7", "year": 2010, "rarity": "common"},
    {"id": "avid_a8_d4", "brand": "Avid", "name": "A8 D4", "year": 2009, "rarity": "classic"},
    {"id": "avid_rs5", "brand": "Avid", "name": "RS5", "year": 2010, "rarity": "epic"},
    {"id": "avid_rs7", "brand": "Avid", "name": "RS7", "year": 2013, "rarity": "legendary"},
    {"id": "avid_a3_8v", "brand": "Avid", "name": "A3 8V", "year": 2012, "rarity": "common"},
    {"id": "avid_a4_b9", "brand": "Avid", "name": "A4 B9", "year": 2015, "rarity": "common"},
    {"id": "avid_a6_c8", "brand": "Avid", "name": "A6 C8", "year": 2018, "rarity": "rare"},
    {"id": "avid_a8_d5", "brand": "Avid", "name": "A8 D5", "year": 2017, "rarity": "epic"},
    {"id": "avid_etron", "brand": "Avid", "name": "e-tron", "year": 2018, "rarity": "epic"},
    {"id": "avid_rs6_c8", "brand": "Avid", "name": "RS6 C8", "year": 2019, "rarity": "legendary"},
    {"id": "avid_rsq8", "brand": "Avid", "name": "RS Q8", "year": 2019, "rarity": "legendary"},
    {"id": "avid_q8", "brand": "Avid", "name": "Q8", "year": 2018, "rarity": "epic"},
    
    # ===== PORSCH (бывшая Porsche) =====
    {"id": "porsch_356", "brand": "Porsch", "name": "356", "year": 1948, "rarity": "legendary"},
    {"id": "porsch_550", "brand": "Porsch", "name": "550 Spyder", "year": 1953, "rarity": "legendary"},
    {"id": "porsch_911_901", "brand": "Porsch", "name": "911 (901)", "year": 1963, "rarity": "legendary"},
    {"id": "porsch_911_964", "brand": "Porsch", "name": "911 Carrera 4", "year": 1989, "rarity": "epic"},
    {"id": "porsch_911_993", "brand": "Porsch", "name": "911 Turbo", "year": 1993, "rarity": "epic"},
    {"id": "porsch_911_996", "brand": "Porsch", "name": "911 GT3", "year": 1999, "rarity": "epic"},
    {"id": "porsch_911_997", "brand": "Porsch", "name": "911 GT3 RS", "year": 2006, "rarity": "legendary"},
    {"id": "porsch_911_991", "brand": "Porsch", "name": "911 Turbo S", "year": 2011, "rarity": "legendary"},
    {"id": "porsch_911_992", "brand": "Porsch", "name": "911 GT3", "year": 2018, "rarity": "legendary"},
    {"id": "porsch_914", "brand": "Porsch", "name": "914", "year": 1969, "rarity": "rare"},
    {"id": "porsch_924", "brand": "Porsch", "name": "924", "year": 1976, "rarity": "common"},
    {"id": "porsch_944", "brand": "Porsch", "name": "944", "year": 1982, "rarity": "common"},
    {"id": "porsch_968", "brand": "Porsch", "name": "968", "year": 1991, "rarity": "rare"},
    {"id": "porsch_928", "brand": "Porsch", "name": "928", "year": 1977, "rarity": "classic"},
    {"id": "porsch_959", "brand": "Porsch", "name": "959", "year": 1986, "rarity": "legendary"},
    {"id": "porsch_carrera_gt", "brand": "Porsch", "name": "Carrera GT", "year": 2003, "rarity": "mythical"},
    {"id": "porsch_918", "brand": "Porsch", "name": "918 Spyder", "year": 2013, "rarity": "mythical"},
    {"id": "porsch_boxster", "brand": "Porsch", "name": "Boxster", "year": 1996, "rarity": "rare"},
    {"id": "porsch_cayman", "brand": "Porsch", "name": "Cayman", "year": 2005, "rarity": "rare"},
    {"id": "porsch_cayenne", "brand": "Porsch", "name": "Cayenne", "year": 2002, "rarity": "common"},
    {"id": "porsch_macan", "brand": "Porsch", "name": "Macan", "year": 2013, "rarity": "rare"},
    {"id": "porsch_panamera", "brand": "Porsch", "name": "Panamera", "year": 2009, "rarity": "epic"},
    {"id": "porsch_taycan", "brand": "Porsch", "name": "Taycan", "year": 2019, "rarity": "legendary"},
    
    # ===== FERRARY (бывшая Ferrari) =====
    {"id": "ferr_125s", "brand": "Ferrary", "name": "125 S", "year": 1947, "rarity": "mythical"},
    {"id": "ferr_166", "brand": "Ferrary", "name": "166 Inter", "year": 1948, "rarity": "legendary"},
    {"id": "ferr_250", "brand": "Ferrary", "name": "250 GT", "year": 1954, "rarity": "legendary"},
    {"id": "ferr_250_gto", "brand": "Ferrary", "name": "250 GTO", "year": 1962, "rarity": "mythical"},
    {"id": "ferr_275", "brand": "Ferrary", "name": "275 GTB", "year": 1964, "rarity": "legendary"},
    {"id": "ferr_330", "brand": "Ferrary", "name": "330 P4", "year": 1967, "rarity": "mythical"},
    {"id": "ferr_dino", "brand": "Ferrary", "name": "Dino 246 GT", "year": 1968, "rarity": "epic"},
    {"id": "ferr_daytona", "brand": "Ferrary", "name": "365 GTB/4 Daytona", "year": 1968, "rarity": "legendary"},
    {"id": "ferr_308", "brand": "Ferrary", "name": "308 GTB", "year": 1975, "rarity": "epic"},
    {"id": "ferr_288_gto", "brand": "Ferrary", "name": "288 GTO", "year": 1984, "rarity": "legendary"},
    {"id": "ferr_f40", "brand": "Ferrary", "name": "F40", "year": 1987, "rarity": "mythical"},
    {"id": "ferr_f50", "brand": "Ferrary", "name": "F50", "year": 1995, "rarity": "mythical"},
    {"id": "ferr_355", "brand": "Ferrary", "name": "F355", "year": 1994, "rarity": "epic"},
    {"id": "ferr_360", "brand": "Ferrary", "name": "360 Modena", "year": 1999, "rarity": "epic"},
    {"id": "ferr_550", "brand": "Ferrary", "name": "550 Maranello", "year": 1996, "rarity": "epic"},
    {"id": "ferr_enzo", "brand": "Ferrary", "name": "Enzo", "year": 2002, "rarity": "mythical"},
    {"id": "ferr_f430", "brand": "Ferrary", "name": "F430", "year": 2004, "rarity": "epic"},
    {"id": "ferr_599", "brand": "Ferrary", "name": "599 GTB", "year": 2006, "rarity": "epic"},
    {"id": "ferr_458", "brand": "Ferrary", "name": "458 Italia", "year": 2009, "rarity": "legendary"},
    {"id": "ferr_f12", "brand": "Ferrary", "name": "F12berlinetta", "year": 2012, "rarity": "legendary"},
    {"id": "ferr_laferrari", "brand": "Ferrary", "name": "LaFerrari", "year": 2013, "rarity": "mythical"},
    {"id": "ferr_488", "brand": "Ferrary", "name": "488 GTB", "year": 2015, "rarity": "legendary"},
    {"id": "ferr_sf90", "brand": "Ferrary", "name": "SF90 Stradale", "year": 2019, "rarity": "mythical"},
    {"id": "ferr_roma", "brand": "Ferrary", "name": "Roma", "year": 2020, "rarity": "legendary"},
    {"id": "ferr_296", "brand": "Ferrary", "name": "296 GTB", "year": 2021, "rarity": "legendary"},
    
    # ===== LAMBORGHI (бывшая Lamborghini) =====
    {"id": "lamb_350gt", "brand": "Lamborghi", "name": "350 GT", "year": 1964, "rarity": "legendary"},
    {"id": "lamb_miura", "brand": "Lamborghi", "name": "Miura", "year": 1966, "rarity": "mythical"},
    {"id": "lamb_espada", "brand": "Lamborghi", "name": "Espada", "year": 1968, "rarity": "epic"},
    {"id": "lamb_countach", "brand": "Lamborghi", "name": "Countach", "year": 1974, "rarity": "mythical"},
    {"id": "lamb_diablo", "brand": "Lamborghi", "name": "Diablo", "year": 1990, "rarity": "legendary"},
    {"id": "lamb_murcielago", "brand": "Lamborghi", "name": "Murciélago", "year": 2001, "rarity": "legendary"},
    {"id": "lamb_gallardo", "brand": "Lamborghi", "name": "Gallardo", "year": 2003, "rarity": "epic"},
    {"id": "lamb_reventon", "brand": "Lamborghi", "name": "Reventón", "year": 2007, "rarity": "mythical"},
    {"id": "lamb_aventador", "brand": "Lamborghi", "name": "Aventador", "year": 2011, "rarity": "mythical"},
    {"id": "lamb_veneno", "brand": "Lamborghi", "name": "Veneno", "year": 2013, "rarity": "mythical"},
    {"id": "lamb_huracan", "brand": "Lamborghi", "name": "Huracán", "year": 2014, "rarity": "legendary"},
    {"id": "lamb_centenario", "brand": "Lamborghi", "name": "Centenario", "year": 2016, "rarity": "mythical"},
    {"id": "lamb_urus", "brand": "Lamborghi", "name": "Urus", "year": 2017, "rarity": "epic"},
    {"id": "lamb_sian", "brand": "Lamborghi", "name": "Sián", "year": 2019, "rarity": "mythical"},
    
    # ===== LADDA (бывшая Lada) =====
    {"id": "ladda_2101", "brand": "Ladda", "name": "2101", "year": 1970, "rarity": "classic"},
    {"id": "ladda_2102", "brand": "Ladda", "name": "2102", "year": 1971, "rarity": "classic"},
    {"id": "ladda_2103", "brand": "Ladda", "name": "2103", "year": 1972, "rarity": "classic"},
    {"id": "ladda_2104", "brand": "Ladda", "name": "2104", "year": 1984, "rarity": "common"},
    {"id": "ladda_2105", "brand": "Ladda", "name": "2105", "year": 1979, "rarity": "common"},
    {"id": "ladda_2106", "brand": "Ladda", "name": "2106", "year": 1976, "rarity": "common"},
    {"id": "ladda_2107", "brand": "Ladda", "name": "2107", "year": 1982, "rarity": "common"},
    {"id": "ladda_2108", "brand": "Ladda", "name": "2108", "year": 1984, "rarity": "common"},
    {"id": "ladda_2109", "brand": "Ladda", "name": "2109", "year": 1987, "rarity": "common"},
    {"id": "ladda_21099", "brand": "Ladda", "name": "21099", "year": 1990, "rarity": "common"},
    {"id": "ladda_2110", "brand": "Ladda", "name": "2110", "year": 1995, "rarity": "common"},
    {"id": "ladda_2111", "brand": "Ladda", "name": "2111", "year": 1997, "rarity": "common"},
    {"id": "ladda_2112", "brand": "Ladda", "name": "2112", "year": 1999, "rarity": "common"},
    {"id": "ladda_2113", "brand": "Ladda", "name": "2113", "year": 2004, "rarity": "common"},
    {"id": "ladda_2114", "brand": "Ladda", "name": "2114", "year": 2001, "rarity": "common"},
    {"id": "ladda_2115", "brand": "Ladda", "name": "2115", "year": 1997, "rarity": "common"},
    {"id": "ladda_niva", "brand": "Ladda", "name": "Niva 4x4", "year": 1977, "rarity": "epic"},
    {"id": "ladda_samara", "brand": "Ladda", "name": "Samara", "year": 1984, "rarity": "common"},
    {"id": "ladda_110", "brand": "Ladda", "name": "110", "year": 1995, "rarity": "common"},
    {"id": "ladda_111", "brand": "Ladda", "name": "111", "year": 1997, "rarity": "common"},
    {"id": "ladda_112", "brand": "Ladda", "name": "112", "year": 1999, "rarity": "common"},
    {"id": "ladda_kalina", "brand": "Ladda", "name": "Kalina", "year": 2004, "rarity": "common"},
    {"id": "ladda_priora", "brand": "Ladda", "name": "Priora", "year": 2007, "rarity": "common"},
    {"id": "ladda_granta", "brand": "Ladda", "name": "Granta", "year": 2011, "rarity": "common"},
    {"id": "ladda_vesta", "brand": "Ladda", "name": "Vesta", "year": 2015, "rarity": "rare"},
    {"id": "ladda_xray", "brand": "Ladda", "name": "XRAY", "year": 2015, "rarity": "rare"},
    
    # ===== GAZ =====
    {"id": "gaz_a", "brand": "GAZ", "name": "A", "year": 1932, "rarity": "classic"},
    {"id": "gaz_m1", "brand": "GAZ", "name": "M-1", "year": 1936, "rarity": "classic"},
    {"id": "gaz_12", "brand": "GAZ", "name": "12 ZIM", "year": 1949, "rarity": "legendary"},
    {"id": "gaz_13", "brand": "GAZ", "name": "13 Chaika", "year": 1959, "rarity": "legendary"},
    {"id": "gaz_14", "brand": "GAZ", "name": "14 Chaika", "year": 1977, "rarity": "legendary"},
    {"id": "gaz_21", "brand": "GAZ", "name": "21 Volga", "year": 1956, "rarity": "epic"},
    {"id": "gaz_22", "brand": "GAZ", "name": "22 Volga", "year": 1962, "rarity": "epic"},
    {"id": "gaz_24", "brand": "GAZ", "name": "24 Volga", "year": 1968, "rarity": "epic"},
    {"id": "gaz_3102", "brand": "GAZ", "name": "3102 Volga", "year": 1981, "rarity": "rare"},
    {"id": "gaz_3110", "brand": "GAZ", "name": "3110 Volga", "year": 1997, "rarity": "common"},
    {"id": "gaz_31105", "brand": "GAZ", "name": "31105 Volga", "year": 2004, "rarity": "common"},
    {"id": "gaz_69", "brand": "GAZ", "name": "69", "year": 1953, "rarity": "epic"},
]

# Редкости и их шансы
RARITY_WEIGHTS = {
    "common": 40,     # 40% шанс
    "rare": 25,       # 25% шанс
    "epic": 15,       # 15% шанс
    "classic": 10,    # 10% шанс
    "legendary": 7,   # 7% шанс
    "mythical": 3     # 3% шанс
}

# Эмодзи для редкости
RARITY_EMOJI = {
    "common": "⚪",
    "rare": "🔵",
    "epic": "🟣",
    "classic": "🔴",
    "legendary": "🟠",
    "mythical": "💎"
}

# ===== ПОЛУЧИТЬ СЛУЧАЙНУЮ МАШИНУ =====
def get_random_car():
    """Выбирает случайную машину с учетом редкости"""
    # Сначала выбираем редкость
    rarities = list(RARITY_WEIGHTS.keys())
    weights = list(RARITY_WEIGHTS.values())
    selected_rarity = random.choices(rarities, weights=weights)[0]
    
    # Фильтруем машины по редкости
    cars_of_rarity = [car for car in CARS_DATABASE if car["rarity"] == selected_rarity]
    
    # Если нет машин такой редкости (на всякий случай), берем любую
    if not cars_of_rarity:
        return random.choice(CARS_DATABASE)
    
    # Выбираем случайную машину из этой редкости
    return random.choice(cars_of_rarity)

# ===== КОМАНДА СТАРТ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    conn = sqlite3.connect('auto_collector.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, first_name, joined_date, last_drop) VALUES (?, ?, ?, ?, ?)",
              (user.id, user.username, user.first_name, datetime.now(), datetime.now() - timedelta(minutes=6)))
    conn.commit()
    conn.close()

    # ОТПРАВЛЯЕМ ПРИВЕТСТВИЕ
    await update.message.reply_text(
        f"🚗 **AUTO COLLECTOR** 🚗\n\n"
        f"Привет, {user.first_name}!\n"
        f"💰 Кредитов: 100\n\n"
        f"**КОМАНДЫ:**\n"
        f"🎲 /drop - Получить машину (каждые 5 мин)\n"
        f"🚘 /garage - Мой гараж\n"
        f"📊 /collection - Статистика коллекции\n"
        f"🤝 /trade @user [id] - Обмен с друзьями\n"
        f"🏆 /top - Топ коллекционеров\n"
        f"💎 /rarity - Редкости машин\n\n"
        f"🚗 *Все названия марок являются вымышленными*",
        parse_mode='Markdown'
        
    
    
    )
    
    # Считаем статистику
    total_cars = len(CARS_DATABASE)
    brands = set(car["brand"] for car in CARS_DATABASE)
    
    await update.message.reply_text(
        f"🚗 **AUTO COLLECTOR** 🚗\n\n"
        f"Привет, {user.first_name}!\n"
        f"💰 Кредитов: 100\n\n"
        f"📊 **В игре:**\n"
        f"• {total_cars} уникальных машин\n"
        f"• {len(brands)} марок\n"
        f"• 6 уровней редкости\n\n"
        "**КОМАНДЫ:**\n"
        "🎲 /drop - Получить машину (каждые 5 мин)\n"
        "🚘 /garage - Мой гараж\n"
        "📊 /collection - Статистика коллекции\n"
        "🤝 /trade @user [id] - Обмен с друзьями\n"
        "🏆 /top - Топ коллекционеров\n"
        "💎 /rarity - Редкости машин",
        parse_mode='Markdown'
    )
    
async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ Функция test вызвана!")
    await update.message.reply_text("✅ ТЕСТ РАБОТАЕТ!")
    
# ===== ПОЛУЧИТЬ МАШИНУ =====
async def drop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    conn = sqlite3.connect('auto_collector.db')
    c = conn.cursor()
    
    # Проверяем время последнего дропа
    c.execute("SELECT last_drop FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    
    if not result:
        await update.message.reply_text("❌ Сначала зарегистрируйся через /start")
        conn.close()
        return
    
    last_drop = datetime.fromisoformat(result[0])
    now = datetime.now()
    
    # Проверяем, прошло ли 5 минут (300 секунд)
    if (now - last_drop).total_seconds() < 300:
        time_left = 300 - (now - last_drop).total_seconds()
        minutes = int(time_left // 60)
        seconds = int(time_left % 60)
        await update.message.reply_text(f"⏳ Подожди {minutes} мин {seconds} сек до следующего дропа!")
        conn.close()
        return
    
    # Получаем случайную машину
    car = get_random_car()
    
    # Добавляем в гараж
    c.execute("INSERT INTO garage (user_id, car_id, car_name, car_brand, car_year, car_rarity, acquired_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (user_id, car["id"], car["name"], car["brand"], car["year"], car["rarity"], now))
    
    # Обновляем время дропа и счетчик машин
    c.execute("UPDATE users SET last_drop=?, total_cars=total_cars+1 WHERE user_id=?", (now, user_id))
    conn.commit()
    conn.close()
    
    # Эмодзи для редкости
    rarity_emoji = RARITY_EMOJI.get(car["rarity"], "⚪")
    rarity_text = {
        "common": "Обычная",
        "rare": "Редкая",
        "epic": "Эпическая",
        "classic": "Классическая",
        "legendary": "Легендарная",
        "mythical": "Мифическая"
    }.get(car["rarity"], car["rarity"])
    
    await update.message.reply_text(
        f"🎉 **ТЫ ПОЛУЧИЛ МАШИНУ!** 🎉\n\n"
        f"🚗 **{car['brand']} {car['name']}**\n"
        f"📅 Год: {car['year']}\n"
        f"{rarity_emoji} Редкость: {rarity_text}\n\n"
        f"ID: `{car['id']}`\n\n"
        f"💾 Машина добавлена в гараж!\n"
        f"Следующий дроп через 5 минут.",
        parse_mode='Markdown'
    )

# ===== ГАРАЖ =====
async def garage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('auto_collector.db')
    c = conn.cursor()
    
    # Получаем все машины пользователя
    c.execute("SELECT car_brand, car_name, car_year, car_rarity, car_id FROM garage WHERE user_id=? ORDER BY acquired_date DESC", (user_id,))
    cars = c.fetchall()
    
    # Получаем статистику
    c.execute("SELECT total_cars FROM users WHERE user_id=?", (user_id,))
    total = c.fetchone()[0]
    
    conn.close()
    
    if not cars:
        await update.message.reply_text("🚘 Твой гараж пуст! Используй /drop, чтобы получить машину.")
        return
    
    # Группируем по брендам
    brands = {}
    for car in cars:
        brand = car[0]
        if brand not in brands:
            brands[brand] = []
        brands[brand].append(car)
    
    text = f"🚘 **ТВОЙ ГАРАЖ** 🚘\n\n"
    text += f"📊 Всего машин: {total}\n\n"
    
    for brand, brand_cars in brands.items():
        text += f"**{brand}** ({len(brand_cars)}):\n"
        for car in brand_cars[:5]:  # Показываем первые 5 каждой марки
            rarity_emoji = RARITY_EMOJI.get(car[3], "⚪")
            text += f"{rarity_emoji} {car[1]} ({car[2]})\n"
        if len(brand_cars) > 5:
            text += f"... и еще {len(brand_cars) - 5}\n"
        text += "\n"
    
    text += "🔍 Для детального просмотра используй /collection"
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ===== КОЛЛЕКЦИЯ (ДЕТАЛЬНО) =====
async def collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('auto_collector.db')
    c = conn.cursor()
    
    # Получаем все машины
    c.execute("SELECT car_brand, car_name, car_year, car_rarity, car_id FROM garage WHERE user_id=? ORDER BY car_rarity DESC, car_brand", (user_id,))
    cars = c.fetchall()
    
    # Статистика по редкостям
    rarity_counts = {rarity: 0 for rarity in RARITY_WEIGHTS.keys()}
    
    for car in cars:
        rarity_counts[car[3]] = rarity_counts.get(car[3], 0) + 1
    
    conn.close()
    
    if not cars:
        await update.message.reply_text("📊 Коллекция пуста!")
        return
    
    text = "📊 **ДЕТАЛЬНАЯ КОЛЛЕКЦИЯ** 📊\n\n"
    
    # Статистика по редкостям
    text += "**Статистика:**\n"
    for rarity, count in rarity_counts.items():
        if count > 0:
            rarity_emoji = RARITY_EMOJI.get(rarity, "⚪")
            rarity_text = {
                "common": "Обычные",
                "rare": "Редкие",
                "epic": "Эпические",
                "classic": "Классические",
                "legendary": "Легендарные",
                "mythical": "Мифические"
            }.get(rarity, rarity)
            text += f"{rarity_emoji} {rarity_text}: {count}\n"
    
    text += f"\n**Всего машин:** {len(cars)}\n\n"
    
    # Последние 10 машин
    text += "**Последние машины:**\n"
    for car in cars[:10]:
        rarity_emoji = RARITY_EMOJI.get(car[3], "⚪")
        text += f"{rarity_emoji} {car[0]} {car[1]} ({car[2]}) — ID: `{car[4]}`\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ===== ТОП КОЛЛЕКЦИОНЕРОВ =====
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('auto_collector.db')
    c = conn.cursor()
    
    c.execute("SELECT username, total_cars FROM users ORDER BY total_cars DESC LIMIT 10")
    top_users = c.fetchall()
    conn.close()
    
    if not top_users:
        await update.message.reply_text("🏆 Топ пока пуст!")
        return
    
    text = "🏆 **ТОП КОЛЛЕКЦИОНЕРОВ** 🏆\n\n"
    for i, (username, total) in enumerate(top_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} @{username or 'Аноним'} — {total} машин\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ===== РЕДКОСТИ =====
async def rarity_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💎 **РЕДКОСТИ МАШИН** 💎\n\n"
        "⚪ Обычная (40%) — шанс 40%\n"
        "🔵 Редкая (25%) — шанс 25%\n"
        "🟣 Эпическая (15%) — шанс 15%\n"
        "🔴 Классическая (10%) — шанс 10%\n"
        "🟠 Легендарная (7%) — шанс 7%\n"
        "💎 Мифическая (3%) — шанс 3%\n\n"
        f"📊 Всего машин в игре: {len(CARS_DATABASE)}"
    )

# ===== ТРЕЙД (ОБМЕН) =====
async def trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "🤝 **ТРЕЙД** 🤝\n\n"
            "Формат: /trade @user car_id\n"
            "Пример: /trade @username bwm_e30\n\n"
            "Чтобы найти ID машины, используй /collection"
        )
        return
    
    target_username = context.args[0].replace('@', '')
    car_id = context.args[1]
    
    conn = sqlite3.connect('auto_collector.db')
    c = conn.cursor()
    
    # Проверяем, есть ли у пользователя такая машина
    c.execute("SELECT * FROM garage WHERE user_id=? AND car_id=?", (user_id, car_id))
    car = c.fetchone()
    
    if not car:
        await update.message.reply_text("❌ У тебя нет такой машины!")
        conn.close()
        return
    
    # Ищем целевого пользователя
    c.execute("SELECT user_id FROM users WHERE username=?", (target_username,))
    target = c.fetchone()
    
    if not target:
        await update.message.reply_text(f"❌ Пользователь @{target_username} не найден!")
        conn.close()
        return
    
    target_id = target[0]
    
    if target_id == user_id:
        await update.message.reply_text("❌ Нельзя трейдить сам с собой!")
        conn.close()
        return
    
    # Создаем трейд
    c.execute("INSERT INTO trades (user1_id, user2_id, user1_car_id, created_at) VALUES (?, ?, ?, ?)",
              (user_id, target_id, car[0], datetime.now()))
    trade_id = c.lastrowid
    conn.commit()
    conn.close()
    
    # Кнопки для принятия/отказа
    keyboard = [
        [InlineKeyboardButton("✅ Принять", callback_data=f"accept_trade_{trade_id}")],
        [InlineKeyboardButton("❌ Отказать", callback_data=f"reject_trade_{trade_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🤝 **ТРЕЙД ПРЕДЛОЖЕН** 🤝\n\n"
        f"От: @{update.effective_user.username or 'Игрок'}\n"
        f"Кому: @{target_username}\n"
        f"Машина: {car[3]} {car[4]} ({car[5]}) — {car[6]}\n\n"
        f"@{target_username}, прими или отклони предложение!",
        reply_markup=reply_markup
    )

# ===== ОБРАБОТКА КНОПОК =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name
    
    if data.startswith("accept_trade_"):
        trade_id = int(data.replace("accept_trade_", ""))
        
        conn = sqlite3.connect('auto_collector.db')
        c = conn.cursor()
        
        # Получаем информацию о трейде
        c.execute("SELECT * FROM trades WHERE trade_id=? AND status='pending'", (trade_id,))
        trade = c.fetchone()
        
        if not trade:
            await query.edit_message_text("❌ Трейд уже неактивен!")
            conn.close()
            return
        
        trade_id, user1_id, user2_id, user1_car_id, user2_car_id, status, created_at = trade
        
        # Проверяем, что принимает правильный пользователь
        if user_id != user2_id:
            await query.edit_message_text("❌ Это не твой трейд!")
            conn.close()
            return
        
        # Получаем информацию о машине
        c.execute("SELECT * FROM garage WHERE id=?", (user1_car_id,))
        car1 = c.fetchone()
        
        # Обмениваемся машинами
        c.execute("UPDATE garage SET user_id=? WHERE id=?", (user2_id, user1_car_id))
        c.execute("UPDATE trades SET status='completed' WHERE trade_id=?", (trade_id,))
        conn.commit()
        conn.close()
        
        await query.edit_message_text(
            f"✅ **ТРЕЙД ЗАВЕРШЕН!**\n\n"
            f"Машина {car1[3]} {car1[4]} ({car1[5]}) передана @{username}!"
        )
    
    elif data.startswith("reject_trade_"):
        trade_id = int(data.replace("reject_trade_", ""))
        
        conn = sqlite3.connect('auto_collector.db')
        c = conn.cursor()
        c.execute("UPDATE trades SET status='rejected' WHERE trade_id=?", (trade_id,))
        conn.commit()
        conn.close()
        
        await query.edit_message_text("❌ Трейд отклонен.")

# ===== ЗАПУСК БОТА =====
def main():
    print("=" * 50)
    print("🚗 ЗАПУСК AUTO COLLECTOR")
    print("=" * 50)
    
    if BOT_TOKEN == "ВСТАВЬ_СВОЙ_ТОКЕН_СЮДА":
        print("❌ ОШИБКА: Ты не вставил токен!")
        print("Получи токен у @BotFather и вставь его в переменную BOT_TOKEN")
        return
    
    init_database()
    print(f"✅ Загружено машин: {len(CARS_DATABASE)}")
    print(f"✅ Редкостей: {len(RARITY_WEIGHTS)}")
    print("✅ База данных готова")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("drop", drop))
    application.add_handler(CommandHandler("garage", garage))
    application.add_handler(CommandHandler("collection", collection))
    application.add_handler(CommandHandler("top", top))
    application.add_handler(CommandHandler("rarity", rarity_info))
    application.add_handler(CommandHandler("trade", trade))
    
    # Кнопки
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ Бот запущен!")
    print("✅ Дроп каждые 5 минут")
    print("✅ Команды: /drop, /garage, /collection, /top, /rarity, /trade")
    print("✅ Нажми Ctrl+C для остановки")
    print("=" * 50)
    
    application.run_polling()

if __name__ == "__main__":

    main()



