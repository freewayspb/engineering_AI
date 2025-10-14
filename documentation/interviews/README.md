# PDF Generation Workflow

В этой папке готовим PDF-версии интервью на основе Markdown (`questions.md`). Ниже — краткий чек-лист шагов, чтобы получить итоговый файл с интерактивными чекбоксами.

## 1. Зависимости
- `pandoc` — конвертация Markdown → LaTeX.
- `tectonic` — автономная сборка LaTeX → PDF (скачивает нужные пакеты при первом запуске).

Установка через Homebrew:
```bash
brew install pandoc tectonic
```

## 2. Генерация LaTeX из Markdown
```bash
pandoc -f gfm documentation/interviews/questions.md \
       -t latex -s \
       -o documentation/interviews/questions.tex
```

## 3. Добавление интерактивных чекбоксов
Файл `questions.tex` содержит готовые макросы (`\FormCheckBox`) и подключение `hyperref`/`bookmark`. После перегенерации LaTeX убедитесь, что:
- В шапке файла присутствует блок с `\usepackage{hyperref}`, `\usepackage{bookmark}`, определением `\FormCheckBox` и обёрткой `\begin{Form} … \end{Form}`.
- Текст маркеров `[ ]` заменён на `\FormCheckBox`. Для быстрой подстановки можно выполнить:
```bash
python - <<'PY'
import re
from pathlib import Path
path = Path("documentation/interviews/questions.tex")
text = path.read_text()
text = re.sub(r"\\item\[[^\]]*\\square[^\]]*\]\s*", r"\\item\n  \\FormCheckBox\\ ", text)
path.write_text(text)
PY
```

## 4. Компиляция PDF
```bash
TECTONIC_CACHE_PATH=.tectonic-cache \
tectonic documentation/interviews/questions.tex \
         --outdir documentation/interviews
```

Результат — `documentation/interviews/questions.pdf`. Первые запуски могут занимать больше времени из-за скачивания TeX-пакетов. Готовые PDF не коммитим: `.gitignore` уже содержит исключение `*.pdf`.
