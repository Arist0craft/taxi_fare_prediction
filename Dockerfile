###############
# BUILD STAGE #
###############
FROM python:3.11-slim-bookworm AS builder

# Копируем утилиту из официального образа
# https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
# опция `--link` позволяет переиспользовать слой, даже если предыдущие слои изменились.
# https://docs.docker.com/reference/dockerfile/#copy---link
COPY --link --from=ghcr.io/astral-sh/uv:0.5.4 /uv /usr/local/bin/uv

# Задаём переменные окружения.
# UV_COMPILE_BYTECODE — включает компиляцию файлов Python в байт-код после установки.
#   https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
# UV_LINK_MODE — меняет способ установки пакетов из глобального кэша.
#   Вместо создания жёстких ссылок, файлы пакета копируются в директорию  виртуального окружения `site-packages`.
#   Это необходимо для будущего копирования изолированной `/app` директории из  стадии `build` в финальный Docker-образ.
# PYTHONOPTIMIZE — убирает инструкции `assert` и код, зависящий от значения  константы `__debug__`,
#   при компиляции файлов Python в байт-код.
#   https://docs.python.org/3/using/cmdline.html#environment-variables

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONOPTIMIZE=1

# Копируем конфиги зависимостей
COPY pyproject.toml uv.lock /_project/

# Для быстрой локальной установки зависимостей монтируем кэш-директорию, в которой будет храниться глобальный кэш uv.
# Первый вызов `uv sync` создаёт виртуальное окружение и устанавливает зависимости без текущего проекта.
# Опция `--no-dev` устанавливает зависимости только для production среды
# Опция `--frozen` запрещает обновлять `uv.lock` файл.
# Опция `--no-install-project` устанавливает зависимости проекта, но не сам проект.
#   Необходима, когда `uv` используется как менеджер проекта (а не `pdm`, например)
#   https://docs.astral.sh/uv/guides/integration/docker/#non-editable-installs
RUN --mount=type=cache,target=/root/.cache/uv <<EOF
cd /_project
uv sync \
    --no-dev \
    --frozen \
    --no-install-project
EOF

# Копируем исходный код проекта в папку сборки
COPY ./app /_project/app

# Устанавливаем текущий проект.
# Опция `--no-editable` отключает установку проекта в  режиме "editable".
#   Код проекта копируется в директорию виртуального окружения `site-packages`.
#   https://docs.astral.sh/uv/guides/integration/docker/#non-editable-installs
RUN --mount=type=cache,target=/root/.cache/uv <<EOF
cd /_project
uv sync \
    --no-dev \
    --frozen
EOF


###############
# FINAL STAGE #
###############
FROM python:3.11-slim-bookworm AS final

# Задаём переменные окружения.
# PATH — добавляет директорию виртуального окружения `bin` в начало списка директорий с исполняемыми файлами.
#   Это позволяет запускать Python-утилиты из любой директории контейнера без указания полного пути к файлу.
# PYTHONOPTIMIZE — указывает интерпретатору Python, что нужно использовать ранее скомпилированные файлы из  директории `__pycache__` с  суффиксом `opt-1` в имени.
# PYTHONUNBUFFERED — отключает буферизацию для потоков stdout и stderr.
# https://docs.python.org/3/using/cmdline.html#environment-variables
ENV PATH="/project/.venv/bin:$PATH" \
    PYTHONOPTIMIZE=1 \
    PYTHONUNBUFFERED=1

ENV PYTHONPATH="/project/app:$PTHONPATH"

# Копируем директорию с виртуальным окружением из предыдущего этапа.
COPY --link --from=builder /_project /project

# Копируем папку с моделями
COPY --link /models /project/models
COPY --link /logging.yaml /project/logging.yaml


WORKDIR /project

# Выводим информацию о питоне
RUN <<EOF
python --version
python -I -m site
EOF


CMD ["python", "app/main.py"]
