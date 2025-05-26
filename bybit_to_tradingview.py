import requests
import os

# URL для получения списка фьючерсов
instruments_url = "https://api.bybit.com/v5/market/instruments-info?category=linear"
# URL для получения объемов торгов
tickers_url = "https://api.bybit.com/v5/market/tickers?category=linear"
# Имя файла для сохранения торговых пар
output_file = "bybit_futures_tradingview_symbols.txt"

try:
    # Получение списка инструментов
    response_instruments = requests.get(instruments_url)
    response_instruments.raise_for_status()
    instruments_data = response_instruments.json()

    if instruments_data.get("result") and instruments_data["result"].get("list"):
        instruments = instruments_data["result"]["list"]

        # Фильтрация бессрочных контрактов
        perpetual_instruments = [
            instrument for instrument in instruments
            if instrument.get("contractType") == "LinearPerpetual"
            and instrument.get("settleCoin") == "USDT"
            and "PERP" not in instrument.get("symbol", "").upper()
            and "ETHBTC" not in instrument.get("symbol", "").upper()
        ]

        # Получение данных о торговой активности
        response_tickers = requests.get(tickers_url)
        response_tickers.raise_for_status()
        tickers_data = response_tickers.json()

        if tickers_data.get("result") and tickers_data["result"].get("list"):
            tickers = tickers_data["result"]["list"]

            # Создаем словарь с объемами
            volume_dict = {
                ticker["symbol"]: float(ticker.get("turnover24h", 0)) for ticker in tickers
            }

            # Добавляем объемы к инструментам
            for instrument in perpetual_instruments:
                symbol = instrument["symbol"]
                instrument["volume24h"] = volume_dict.get(symbol, 0)

            # Сортировка по объему
            sorted_instruments = sorted(
                perpetual_instruments,
                key=lambda x: x["volume24h"],
                reverse=True
            )

            # Формирование списка символов для TradingView
            futures_symbols = [
                f"BYBIT:{instrument['symbol']}.P" for instrument in sorted_instruments
            ]

            # Проверка наличия старого файла
            if os.path.exists(output_file):
                with open(output_file, "r") as file:
                    old_symbols = set(file.read().split(","))
            else:
                old_symbols = set()

            # Вычисление новых символов
            new_symbols = set(futures_symbols) - old_symbols

            # Запись нового списка в файл
            with open(output_file, "w") as file:
                file.write(",".join(futures_symbols))

            # Вывод новых символов в терминал
            if new_symbols:
                print("Новые торговые пары:")
                for symbol in new_symbols:
                    print(symbol)
            else:
                print("Новых торговых пар не обнаружено.")
        else:
            print("Не удалось получить данные о торговой активности.")
    else:
        print("Не удалось получить список инструментов.")

except requests.exceptions.RequestException as e:
    print(f"Произошла ошибка при выполнении запроса: {e}")