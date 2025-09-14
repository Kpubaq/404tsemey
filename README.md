README — Push Personalization Pipeline (CASE 1)

Полное руководство для жюри: как подготовить, запустить, проверить и принять результаты. Документ рассчитан на Windows (PowerShell) и Linux/macOS (bash). Все шаги даны пошагово — просто следуйте.

Содержание

Требования

Структура репозитория и важные файлы

Подготовка (виртуальное окружение, зависимости)

Настройка API (опционально, AI-парафразирование)

Подготовка данных (обязательные файлы и номенклатура)

Запуск пайплайна (без AI / с AI)

Что будет создано (файлы-результаты и отладка)

Оценка и отчёты (что смотреть жюри)

Как собрать submission (архив для сдачи)

Безопасность и советы по GitHub

Частые ошибки и их исправление

Контрольный чек-лист для жюри

1. Требования

Python 3.10+

~200 MB свободного места (зависит от данных)

Интернет только если вы включаете --use-ai true (AI вызов к OpenRouter)

Пакеты в requirements.txt (см. ниже)

2. Структура репозитория (важное)
project-root/
├── .gitignore
├── .env.example
├── requirements.txt
├── README.md
├── submission_debug.py
├── examples/
│   └── results.csv            # пример результата
├── data/                      # сюда жюри положит свои CSV (см. ниже)
└── src/
    ├── app.py                 # CLI точка входа
    ├── pipeline/
    │   ├── preprocess.py
    │   ├── features.py
    │   ├── scorer.py
    │   └── generator.py
    ├── utils/
    │   └── io.py
    └── eval/
        └── evaluate.py


Файлы, которые обязательны в репозитории: код в src/, requirements.txt, .env.example, .gitignore, README.md, examples/ (опционально с примерами).
Ни в коем случае не добавляйте .env в репозиторий — он в .gitignore.

3. Подготовка (виртуальное окружение и зависимости)

Windows (PowerShell):

python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt


Linux / macOS (bash):

python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt


Проверка версии Python:

python --version
# должен быть 3.10 или выше

4. Настройка API (опционально — только если вы хотите AI-парафразирование)

Скопируйте .env.example → .env
Windows:

copy .env.example .env


Linux/macOS:

cp .env.example .env


Откройте .env и вставьте свой ключ:

OPENROUTER_API_KEY=вставьте_апи_openrouter
OPENROUTER_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=deepseek/deepseek-r1:free


Примечание: URL и MODEL можно оставить одинаковыми с .env.example — главное заполнить OPENROUTER_API_KEY.

Если .env пустой или отсутствует — пайплайн будет работать без AI, используя встроенные шаблоны.

5. Подготовка данных (обязательно — формат и имена файлов)

В папке data/ жюри должны положить свои файлы. Формат и имена строго обязательны.

profiles.csv
столбцы: client_code,name,status,age,city,avg_monthly_balance_KZT
client_code — целое число 1..60

Для каждого клиента i (i = 1..60) — два файла:

client_{i}_transactions_3m.csv
client_{i}_transfers_3m.csv


Итого максимум 120 файлов + profiles.csv.
Если какого-то файла нет — пайплайн пропустит этого клиента и запишет отсутствующие файлы в debug/missing_files.json.

Форматы колонок (важно для корректной работы):

client_{i}_transactions_3m.csv:

date, category, amount, currency, client_code

client_{i}_transfers_3m.csv:

date, type, direction, amount, currency, client_code

6. Запуск пайплайна

Рекомендуемый запуск (модульный запуск обеспечивает корректные импорты):

Без AI:

python -m src.app --data-dir data --use-ai false --output examples/results.csv


С AI (требуется рабочий .env с ключом):

python -m src.app --data-dir data --use-ai true --output examples/results.csv


Аргументы:

--data-dir — путь к папке с CSV (по умолчанию data/)

--use-ai — true или false

--output — путь файла для записи окончательного CSV (рекомендуем examples/results.csv)

Если вы хотите запускать src/app.py напрямую (не через -m), убедитесь, что пакетная структура и импорты соответствуют; проще и безопаснее запускать через python -m src.app.

7. Что создаётся и куда смотреть

После успешного прогона вы получите:

examples/results.csv — финальный CSV с колонками:

client_code,product,push_notification


Каждая строчка — один обработанный клиент.

debug/ — папка с подробными файлами:

client_{i}_scores.json — детальная информация по каждому обработанному клиенту:

raw signals, normalized signals, benefit для каждого продукта, score, top4, chosen

missing_files.json — список недостающих файлов (если есть)

evaluation_summary.json — итог автоматической оценки качества пушей

evaluation_per_client.csv — per-client баллы по чеклисту качества

submission_debug.zip — при запуске submission_debug.py будет создан архив, содержащий examples/results.csv и debug/* (для сдачи жюри).

8. Оценка и отчёты (как проверять жюри)

Пайплайн выполняет автоматическую проверку качества пушей (см. src/eval/evaluate.py) и сохраняет результаты в debug/.

Что смотреть:

debug/evaluation_summary.json — средняя оценка качества пушей и количество обработанных клиентов.

debug/evaluation_per_client.csv — per-client баллы (на основе 4 критериев: персонализация, TOV и длина, CTA, форматирование).

debug/client_{i}_scores.json — подробные данные, которые показывают почему был выбран тот или иной продукт (аудитируемая логика).

Как оценивать вручную:

убедиться, что для каждого клиента в examples/results.csv product — один из перечня:

Карта для путешествий
Премиальная карта
Кредитная карта
Обмен валют
Кредит наличными
Депозит Мультивалютный
Депозит Сберегательный
Депозит Накопительный
Инвестиции
Золотые слитки


открыть debug/client_{i}_scores.json и сверить raw_signals и расчет benefits. Логика детерминирована и прозрачна.

9. Как собрать submission (архив для сдачи)

В корне репозитория выполните:

python submission_debug.py


Это создаст submission_debug.zip, включающее examples/results.csv и содержимое debug/. Этот zip отправляйте жюри.

10. Безопасность и GitHub (как правильно залить код)

Никогда не добавляйте .env в коммит. В репозитории уже есть .gitignore, который исключает .env.

Коммитите .env.example вместо реального .env — так жюри знают, какие переменные окружения заполнить.

Что загружать на GitHub:

весь код (src/)

.env.example

.gitignore

requirements.txt

README.md

examples/ (при желании)

пустую папку data/ (или инструкцию в README) — реальные данные жюри должны положить сами.

Пример шагов:

git init
git add .
git commit -m "Release: Push Personalization Pipeline"
git branch -M main
git remote add origin https://github.com/youruser/yourrepo.git
git push -u origin main

11. Частые ошибки и как их исправить

ModuleNotFoundError: No module named 'src'
Решение: запускать через модуль:

python -m src.app --data-dir data --use-ai false --output examples/results.csv


Или добавить пустой src/__init__.py и/или исправить PYTHONPATH.

Предупреждение pandas о dayfirst=True при парсинге дат
Исправлено: src/pipeline/preprocess.py пробует несколько форматов дат и не вызывает предупреждение.

.env был случайно закоммичен
Удалите из репозитория и добавьте в .gitignore:

git rm --cached .env
echo ".env" >> .gitignore
git commit -m "Remove .env from repo"
git push


AI вызов падает (таймаут/401)
Проверьте:

OPENROUTER_API_KEY корректен

OPENROUTER_URL корректен

Есть интернет

Лимиты API

Некорректные push-тексты (с точки зрения длины / TOV)
Проверяйте debug/client_{i}_scores.json — в нём хранится template, benefit и итоговый текст. По умолчанию при невалидном AI ответе используется template.

12. Контрольный чек-лист для жюри (быстрая проверка)

Клонировали репозиторий.

Создали .venv и установили зависимости: pip install -r requirements.txt.

Скопировали .env.example → .env и заполнили ключ (если нужно AI).

Положили profiles.csv и client_{i}_*.csv в data/.

Запустили:

python -m src.app --data-dir data --use-ai false --output examples/results.csv


Открыли examples/results.csv — убедились в колонках client_code,product,push_notification.

Открыли debug/client_{i}_scores.json для нескольких клиентов и проверили логику выбора продукта.

Запустили python submission_debug.py и отправили submission_debug.zip вместе с examples/results.csv.

Примеры форматов (результат)

examples/results.csv:

client_code,product,push_notification
1,Карта для путешествий,"Алия, в августа 2025 у вас 3 поездки/такси на 45 000 ₸. С картой для путешествий вернулись бы ≈1 800 ₸. Открыть"
2,Премиальная карта,"Аскер, у вас средний остаток 2 400 000 ₸ и траты в ресторанах 75 000 ₸. Премиальная карта даст до 4% на рестораны и бесплатные снятия. Оформить"


debug/client_1_scores.json содержит: raw_signals, normalized_signals, product_scores (benefit, score), top4, chosen.
