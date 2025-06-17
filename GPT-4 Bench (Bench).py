import pandas as pd
import time
import openai
import json
from typing import Dict, List, Tuple
import subprocess
import sys
import pkg_resources

class GPT4oBenchmark:
    def __init__(self):
        """Ініціалізація тестування з використанням OpenRouter API"""
        self.client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=""
        )
        
        self.metrics = {
            "Робота з даними": {
                "Загальні знання": ["MMLU", "MMLU-Redux", "MMLU-Pro", "DROP", "IF-Eval"],
                "Спеціалізовані тести": ["GPQA-Diamond", "FRAMES", "LongBench"]
            },
            "Програмування": {
                "Генерація коду": ["HumanEval-Mul", "LiveCodeBench", "LiveCodeBench-COT"],
                "Інженерія": ["Codeforces", "SWE-Verified", "Aider-Edit", "Aider-Polyglot"]
            },
            "Математика": {
                "Базова": ["MATH-500"],
                "Просунута": ["AIME", "CNMO"]
            },
            "Китайська": ["CLUEWSC", "C-Eval", "C-SimpleQA"]
        }
        
        self.test_data = self._load_test_data()
        self.results = {}

    def _load_test_data(self) -> Dict[str, List[Tuple]]:
        """Завантаження тестових даних"""
        test_data = {
            "MMLU": [
                ("Яка столиця Франції?", ["Лондон", "Париж", "Берлін", "Мадрид"], 1),
                ("Яка планета відома як Червона Планета?", ["Венера", "Марс", "Юпітер", "Сатурн"], 1),
                ("Хто написав 'Вбити пересмішника'?", ["Дж.К. Роулінг", "Гарпер Лі", "Стівен Кінг", "Ернест Хемінгуей"], 1),
                ("Який хімічний символ золота?", ["Au", "Ag", "Fe", "Hg"], 0),
                ("У якому році закінчилася Друга світова війна?", ["1943", "1945", "1950", "1939"], 1)
            ],
            "MMLU-Redux": [
                ("Який атомний номер кисню?", ["6", "7", "8", "9"], 2),
                ("Хто відкрив пеніцилін?", ["Марія Кюрі", "Олександр Флемінг", "Луї Пастер", "Роберт Кох"], 1),
                ("Яка столиця Бразилії?", ["Ріо-де-Жанейро", "Сан-Паулу", "Бразиліа", "Буенос-Айрес"], 2),
                ("Яка країна винайла чай?", ["Індія", "Китай", "Японія", "Англія"], 1),
                ("Яка найбільша тварина?", ["Слон", "Синій кит", "Жираф", "Білий ведмідь"], 1)
            ],
            "MMLU-Pro": [
                ("У квантовій теорії поля, що пояснює механізм Хіггса?", 
                 ["Масу елементарних частинок", "Електричний заряд", "Квантову заплутаність", "Чорні діри"], 0),
                ("У теорії обчислювальної складності, що питає проблема P vs NP?",
                 ["Чи перевірка легша за обчислення", "Чи квантові комп'ютери можуть вирішувати NP-проблеми",
                  "Чи всі проблеми можна вирішити за поліноміальний час", "Чи P дорівнює NP"], 3),
                ("Що говорить другий закон термодинаміки про ентропію?",
                 ["Ентропія залишається постійною", "Ентропія зменшується з часом", 
                  "Ентропія зростає в ізольованих системах", "Ентропія не пов'язана з енергією"], 2),
                ("У молекулярній біології, що означає PCR?",
                 ["Полімеразна ланцюгова реакція", "Регіон кодування білка", 
                  "Первинна клітинна відповідь", "Співвідношення концентрації білка"], 0),
                ("Яка теорема стверджує, що немає трьох додатних цілих чисел a, b і c, що задовольняють aⁿ + bⁿ = cⁿ для n > 2?",
                 ["Теорема Піфагора", "Велика теорема Ферма", 
                  "Теорема Геделя про неповноту", "Формула Ейлера"], 1)
            ],
            "DROP": [
                ("На конференції було 300 учасників з 40 країн. Скільки країн було представлено?",
                 "40",
                 "40"),
                ("У Джона 5 яблук. Він дає 2 Марії та 1 Бобу. Скільки яблук у нього залишилося?",
                 "2",
                 "2"),
                ("Потяг проїжджає 120 миль за 2 години. Яка його швидкість у милях на годину?",
                 "60",
                 "60"),
                ("Якщо книга має 450 сторінок, і ви читаєте 30 сторінок щодня, скільки днів знадобиться, щоб її закінчити?",
                 "15",
                 "15"),
                ("Прямокутник має довжину 8 і ширину 5. Яка його площа?",
                 "40",
                 "40")
            ],
            "IF-Eval": [
                ("Виконай ці кроки: 1) Напиши 'привіт' 2) Переверни 3) Велика перша літера",
                 "Тівірп",
                 "Тівірп"),
                ("Інструкції: 1) Візьми першу літеру 'кіт' 2) Візьми останню літеру 'пес' 3) Поєднай їх",
                 "кс",
                 "кс"),
                ("Кроки: 1) Напиши 'Python' 2) Видали першу та останню літери 3) Перетвори на великі літери",
                 "YTHO",
                 "YTHO"),
                ("Напрямки: 1) Напиши '42' 2) Додай '17' 3) Помнож на 2",
                 "118",
                 "118"),
                ("Процедура: 1) Напиши 'банан' 2) Видали всі 'а' 3) Переверни результат",
                 "ннб",
                 "ннб")
            ],
            "GPQA-Diamond": [
                ("Поясни гіпотезу Рімана простою мовою",
                 "Це про розподіл простих чисел",
                 "прості числа"),
                ("Які наслідки, якщо P=NP буде доведено?",
                 "Багато складних проблем стануть легкими для вирішення",
                 "P=NP"),
                ("Опиши квантову заплутаність простою мовою",
                 "Коли частинки залишаються зв'язаними на відстані",
                 "квантова заплутаність"),
                ("Яке значення експерименту Міллера-Юрі?",
                 "Показав, як могло виникнути життя з простих хімічних речовин",
                 "походження життя"),
                ("Поясни поняття ентропії для 5-річної дитини",
                 "Це міра безпорядку в системі",
                 "безпорядок")
            ],
            "FRAMES": [
                ("Діалог: A: 'Мені сподобався цей ресторан!' B: 'Мені теж, паста була чудова'. Визнач настрої",
                 "позитивний",
                 "позитивний"),
                ("Розмова: A: 'Цей продукт жахливий' B: 'Погоджуюсь, найгірша покупка'. Настрої?",
                 "негативний",
                 "негативний"),
                ("Обмін: A: 'Фільм був нормальний' B: 'Я очікував більшого'. Настрої?",
                 "нейтральний",
                 "нейтральний"),
                ("Чат: A: 'Найкращий день у житті!' B: 'Радий за тебе!'. Емоції?",
                 "щасливий",
                 "щасливий"),
                ("Обговорення: A: 'Я так розчарований' B: 'Все буде добре'. Настрій?",
                 "розчарований",
                 "розчарований")
            ],
            "LongBench": [
                ("Резюмуй текст: " + ("Штучний інтелект змінює галузі. " * 10),
                 "ШІ змінює галузі",
                 "ШІ змінює"),
                (("Історія Риму триває понад 2800 років. " * 10) + "Скільки років існує Рим?",
                 "2800 років",
                 "2800"),
                ("Повтори це число: " + "12345 " * 15,
                 "12345",
                 "12345"),
                (("Машинне навчання вимагає великих наборів даних. " * 12) + "Що потрібно для ML?",
                 "великі набори даних",
                 "великі набори даних"),
                (("Зміна клімату впливає на екосистеми в усьому світі. " * 10) + "Що впливає на екосистеми?",
                 "зміна клімату",
                 "зміна клімату")
            ],
            "HumanEval-Mul": [
                ("Напиши функцію для обертання рядка", 
                 "def reverse_string(s):\n    return s[::-1]",
                 "assert reverse_string('привіт') == 'тівирп'"),
                ("Напиши функцію для обчислення факторіалу",
                 "def factorial(n):\n    return 1 if n == 0 else n * factorial(n-1)",
                 "assert factorial(5) == 120"),
                ("Напиши функцію для перевірки, чи число просте",
                 "def is_prime(n):\n    if n <= 1:\n        return False\n    for i in range(2, int(n**0.5)+1):\n        if n % i == 0:\n            return False\n    return True",
                 "assert is_prime(11) == True"),
                ("Напиши функцію для знаходження максимуму в списку",
                 "def find_max(lst):\n    return max(lst)",
                 "assert find_max([1,5,3]) == 5"),
                ("Напиши функцію для підрахунку голосних у рядку",
                 "def count_vowels(s):\n    return sum(1 for c in s.lower() if c in 'аеиіоуяюєї')",
                 "assert count_vowels('привіт') == 2")
            ],
            "LiveCodeBench": [
                ("Напиши функцію для знаходження найдовшого підрядка без повторень",
                 "def longest_substring(s):\n    used = {}\n    max_length = start = 0\n    for i, c in enumerate(s):\n        if c in used and start <= used[c]:\n            start = used[c] + 1\n        else:\n            max_length = max(max_length, i - start + 1)\n        used[c] = i\n    return max_length",
                 "assert longest_substring('abcabcbb') == 3"),
                ("Напиши функцію для перевірки балансу дужок",
                 "def is_balanced(s):\n    stack = []\n    pairs = {'(': ')', '[': ']', '{': '}'}\n    for char in s:\n        if char in pairs:\n            stack.append(char)\n        elif stack and char == pairs[stack[-1]]:\n            stack.pop()\n        else:\n            return False\n    return len(stack) == 0",
                 "assert is_balanced('({[]})') == True"),
                ("Напиши функцію для об'єднання двох відсортованих списків",
                 "def merge_sorted(a, b):\n    return sorted(a + b)",
                 "assert merge_sorted([1,3], [2,4]) == [1,2,3,4]"),
                ("Напиши функцію для видалення дублікатів зі списку",
                 "def remove_duplicates(lst):\n    return list(dict.fromkeys(lst))",
                 "assert remove_duplicates([1,2,2,3]) == [1,2,3]"),
                ("Напиши функцію для обчислення послідовності Фібоначчі до n членів",
                 "def fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        yield a\n        a, b = b, a + b",
                 "assert list(fibonacci(5)) == [0,1,1,2,3]")
            ],
            "LiveCodeBench-COT": [
                ("Поясни, а потім напиши код для знаходження найдовшого підрядка без повторень",
                 "Спочатку використаємо метод ковзного вікна з двома вказівниками...",
                 "def length_of_longest_substring(s):"),
                ("Опиши, а потім реалізуй структуру даних стек",
                 "Стек - це структура LIFO з операціями push/pop...",
                 "class Stack:"),
                ("Поясни алгоритм бінарного пошуку, а потім реалізуй його",
                 "Бінарний пошук працює шляхом поділу інтервалу...",
                 "def binary_search(arr, target):"),
                ("Опиши швидке сортування, а потім напиши код",
                 "Швидке сортування використовує стратегію 'розділяй і володарюй'...",
                 "def quicksort(arr):"),
                ("Поясни алгоритм Дейкстри, а потім реалізуй його",
                 "Алгоритм Дейкстри знаходить найкоротші шляхи...",
                 "def dijkstra(graph, start):")
            ],
            "Codeforces": [
                ("1A: Театральна площа - викласти прямокутну область квадратними плитками", "математика, жадібність", "математика"),
                ("4A: Кавун - поділити кавун на парні частини", "математика, перебір", "математика"),
                ("71A: Занадто довгі слова - скоротити довгі слова", "рядки", "рядки"),
                ("158A: Наступний раунд - пройти учасників у наступний раунд", "сортування", "сортування"),
                ("50A: Укладання доміно - максимізувати кількість доміно на дошці", "математика, жадібність", "математика")
            ],
            "SWE-Verified": [
                ("Виправ помилку нульового вказівника: String s; s.length();", 
                 "Додати перевірку: if (s != null)", 
                 "null check"),
                ("Виправ нескінченний цикл: while(i < 10) { j++; }",
                 "Додати i++ в циклі",
                 "інкремент лічильника"),
                ("Виправ витік пам'яті у коді на C++ з new[]",
                 "Додати виклик delete[]",
                 "управління пам'яттю"),
                ("Виправ вразливість SQL-ін'єкції",
                 "Використати підготовлені запити",
                 "безпека SQL"),
                ("Виправ стан гонки у багатопотоковому коді",
                 "Додати блокування м'ютексів",
                 "безпека потоків")
            ],
            "Aider-Edit": [
                ("Рефактори цей код з використанням спискового включення:\nnumbers = []\nfor i in range(10):\n    numbers.append(i*2)",
                 "numbers = [i*2 for i in range(10)]",
                 "спискове включення"),
                ("Зроби цю функцію обробки None: def foo(x): return x+1",
                 "def foo(x): return None if x is None else x+1",
                 "перевірка на None"),
                ("Оптимізуй цей вкладений цикл O(n²) до O(n)",
                 "Використай хеш-таблицю для O(1) пошуку",
                 "оптимізація"),
                ("Додай підказки типів до цієї функції Python",
                 "def func(x: int) -> str:",
                 "підказки типів"),
                ("Зроби цей код відповідним до PEP 8",
                 "Виправи відступи та імена змінних",
                 "стиль коду")
            ],
            "Aider-Polyglot": [
                ("Перетвори цей Python на JavaScript: def add(a,b): return a+b",
                 "function add(a,b) { return a+b }",
                 "function add"),
                ("Переклади цей Java на Python: public class Hello { public static void main() { System.out.println('Hello'); } }",
                 "def main():\n    print('Hello')",
                 "функція print"),
                ("Перетвори цей C++ вектор на Python: vector<int> v = {1,2,3};",
                 "v = [1, 2, 3]",
                 "список"),
                ("Переклади цей SQL запит на Pandas: SELECT name FROM users WHERE age > 30",
                 "users[users.age > 30]['name']",
                 "запит DataFrame"),
                ("Перетвори цей Bash на Python: for file in *.txt; do echo $file; done",
                 "import glob\nfor file in glob.glob('*.txt'):\n    print(file)",
                 "модуль glob")
            ],
            "MATH-500": [
                ("Розв'яжи: x² - 5x + 6 = 0", "x = 2 або x = 3", "2,3"),
                ("Обчисли площу кола з радіусом 5", "78.5398", "78.5398"),
                ("Знайди похідну x³ + 2x² - x", "3x² + 4x - 1", "3x²+4x-1"),
                ("Розв'яжи: 2x + 3 = 15", "x = 6", "6"),
                ("Обчисли 5! (факторіал)", "120", "120")
            ],
            "AIME": [
                ("Знайди залишок від ділення 7^2023 на 5", "3", "3"),
                ("Обчисли суму перших 100 простих чисел", "24133", "24133"),
                ("Знайди найменше додатне ціле x таке, що 2x ≡ 1 mod 11", "6", "6"),
                ("Обчисли інтеграл e^x від 0 до 1", "e - 1", "e-1"),
                ("Знайди кількість додатних дільників 360", "24", "24")
            ],
            "CNMO": [
                ("Розв'яжи: x³ - 6x² + 11x - 6 = 0", "x = 1, 2, 3", "1,2,3"),
                ("Знайди площу трикутника зі сторонами 7, 24, 25", "84", "84"),
                ("Обчисли суму 1 + 1/2 + 1/4 + 1/8 + ...", "2", "2"),
                ("Знайди НСД чисел 1071 і 462", "21", "21"),
                ("Розв'яжи для x: log₂(x) = 5", "32", "32")
            ],
            "CLUEWSC": [
                ("Переклади на англійську: 今天天气怎么样?", "How's the weather today?", "weather"),
                ("Переклади: 人工智能是什么意思?", "What does artificial intelligence mean?", "AI"),
                ("Переклади: 请打开窗户", "Please open the window", "open window"),
                ("Переклади: 我饿了", "I'm hungry", "hungry"),
                ("Переклади: 这个多少钱?", "How much does this cost?", "price")
            ],
            "C-Eval": [
                ("什么是人工智能?", "Штучний інтелект - це комп'ютерні системи, що імітують людський інтелект", "ШІ"),
                ("中国的首都是哪里?", "Пекін", "Пекін"),
                ("1+1等于几?", "2", "2"),
                ("水的化学式是什么?", "H₂O", "H2O"),
                ("Python是什么?", "Мова програмування", "програмування")
            ],
            "C-SimpleQA": [
                ("谁发明了电话?", "Олександр Грехем Белл", "Белл"),
                ("地球是平的还是圆的?", "Кругла", "кругла"),
                ("太阳系有多少颗行星?", "8", "8"),
                ("中国的面积是多少?", "Приблизно 9.6 млн км²", "9.6 млн"),
                ("谁写了《红楼梦》?", "Цао Сюецінь", "Цао")
            ]
        }
        return test_data

    def _query_gpt4o(self, prompt: str, max_tokens: int = 500) -> str:
        """Запит до GPT-4 через OpenRouter"""
        try:
            completion = self.client.chat.completions.create(
                model="openai/gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
                timeout=30
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"🔴 Помилка API: {str(e)}")
            return None

    def _check_answer(self, metric: str, test_case, response: str) -> bool:
        """Перевірка правильності відповіді"""
        if not response or not response.strip():
            return False
            
        response = response.lower().strip()
        
        # Спеціальна обробка для тестів з ланцюжком міркувань
        if "COT" in metric:
            explanation_keyword = test_case[1].lower().split()[0]
            code_keyword = test_case[2].lower().split('(')[0]
            
            has_explanation = explanation_keyword in response
            has_code = code_keyword in response
            
            return has_explanation and has_code
        
        # Для тестів з варіантами відповідей
        if "MMLU" in metric:
            correct_index = test_case[2]
            correct_answer = test_case[1][correct_index].lower()
            return correct_answer in response
        
        # Для генерації коду
        if "HumanEval" in metric or "LiveCodeBench" in metric:
            expected_keywords = test_case[2].lower().split('assert ')[1].split('(')[0]
            return expected_keywords in response
        
        # Для математичних задач
        if "MATH" in metric or "AIME" in metric or "CNMO" in metric:
            correct_answer = str(test_case[1]).lower()
            return correct_answer in response
        
        # Для китайських тестів
        if metric in ["CLUEWSC", "C-Eval", "C-SimpleQA"]:
            correct_keyword = str(test_case[2]).lower()
            return correct_keyword in response
        
        # Для інших тестів
        if metric in ["DROP", "IF-Eval", "GPQA-Diamond", "FRAMES", "LongBench"]:
            correct_answer = str(test_case[1]).lower()
            return correct_answer in response
        
        return False

    def _evaluate_metric(self, metric: str, num_samples: int):
        """Оцінка конкретної метрики"""
        if metric not in self.test_data or not self.test_data[metric]:
            print(f"⚠️ Немає тестових даних для {metric}")
            return
            
        samples = self.test_data[metric][:num_samples]
        correct = 0
        detailed_results = []
        
        print(f"\n🔎 Тестування {metric} ({len(samples)} прикладів)...")
        
        for i, test_case in enumerate(samples):
            try:
                question = test_case[0]
                print(f"\n📌 Приклад {i+1}: {question[:60]}...")
                
                start_time = time.time()
                response = self._query_gpt4o(question, 
                                          max_tokens=1024 if metric in ["LongBench", "LiveCodeBench-COT"] else 500)
                elapsed = time.time() - start_time
                
                if response is None:
                    raise Exception("Помилка запиту до API")
                
                is_correct = self._check_answer(metric, test_case, response)
                correct += 1 if is_correct else 0
                
                detailed_results.append({
                    "питання": question,
                    "відповідь": response,
                    "правильно": is_correct,
                    "час": elapsed
                })
                
                print(f"   {'✅' if is_correct else '❌'} Час: {elapsed:.2f}с")
                print(f"   Відповідь: {response[:100]}..." if response else "   Немає відповіді")
                
            except Exception as e:
                print(f"   ❗ Помилка: {str(e)}")
                detailed_results.append({
                    "питання": question,
                    "відповідь": f"Помилка: {str(e)}",
                    "правильно": False,
                    "час": 0
                })
        
        accuracy = correct / len(samples) if samples else 0
        avg_time = sum(r['час'] for r in detailed_results) / len(samples) if samples else 0
        
        self.results[metric] = {
            "точність": accuracy,
            "середній_час": avg_time,
            "тестовані_приклади": len(samples),
            "детальні_результати": detailed_results
        }

    def run_benchmark(self, num_samples: int = 5) -> Dict[str, Dict]:
        """Запуск повного тестування"""
        print("🚀 Початок комплексного тестування GPT-4\n")
        
        # Перевірка підключення до API
        test_response = self._query_gpt4o("Скажи 'тест'", max_tokens=10)
        if not test_response:
            print("🔴 Помилка підключення до API, переривання тестування")
            return {}
        
        print("✅ Підключення до API успішне")
        
        for category, subcategories in self.metrics.items():
            print(f"\n🔹 {category.upper()}")
            
            if isinstance(subcategories, dict):
                for subcategory, metrics in subcategories.items():
                    print(f"  ⚙️ {subcategory}")
                    for metric in metrics:
                        self._evaluate_metric(metric, num_samples)
            else:
                for metric in subcategories:
                    self._evaluate_metric(metric, num_samples)
        
        print("\n✅ Тестування завершено!")
        return self.results

    def generate_report(self) -> pd.DataFrame:
        """Генерація звіту"""
        report_data = []
        for metric, result in self.results.items():
            report_data.append({
                "Метрика": metric,
                "Точність (%)": f"{result['точність']*100:.1f}",
                "Середній час (с)": f"{result['середній_час']:.2f}",
                "Приклади": result['тестовані_приклади'],
                "Статус": "✅ Успіх" if result['точність'] >= 0.7 else "⚠️ Частково" if result['точність'] >= 0.4 else "❌ Невдача",
                "Приклад відповіді": result['детальні_результати'][0]['відповідь'][:50] + "..." if result['детальні_результати'] else ""
            })
        return pd.DataFrame(report_data)

    def save_results(self):
        """Збереження результатів у файли"""
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        
        report = self.generate_report()
        csv_file = f"gpt4_benchmark_{timestamp}.csv"
        report.to_csv(csv_file, index=False)
        
        json_file = f"gpt4_benchmark_details_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 Результати збережено:")
        print(f"- Зведений звіт: {csv_file}")
        print(f"- Детальні дані: {json_file}")

def check_dependencies():
    """Перевірка та встановлення залежностей"""
    required = {'requests', 'pandas', 'openai'}
    try:
        installed = {pkg.key for pkg in pkg_resources.working_set}
        missing = required - installed
        if missing:
            print(f"🔧 Встановлення відсутніх пакетів: {', '.join(missing)}")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])
    except:
        try:
            import requests
            import pandas
            import openai
        except ImportError as e:
            print(f"🔴 Відсутня залежність: {str(e)}")
            print("Будь ласка, встановіть необхідні пакети вручну:")
            print("pip install requests pandas openai")
            sys.exit(1)

if __name__ == "__main__":
    check_dependencies()
    
    try:
        print("🔍 Ініціалізація тестування GPT-4...")
        benchmark = GPT4oBenchmark()
        benchmark.run_benchmark(num_samples=5)
        
        print("\n📋 Результати тестування:")
        report = benchmark.generate_report()
        print(report.to_markdown(tablefmt="grid", stralign="left"))
        
        benchmark.save_results()
        
    except Exception as e:
        print(f"🔴 Критична помилка: {str(e)}")