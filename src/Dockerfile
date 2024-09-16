FROM debian:trixie

# 非rootユーザーの作成
RUN useradd -m appuser

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3.12 python3-pip python3.12-venv libopencv-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Python 環境セットアップ
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip3 install --no-cache-dir poetry
WORKDIR /app
COPY pyproject.toml poetry.lock /app/ 
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

COPY . /app

# 非rootユーザーに切り替え
RUN chown -R appuser:appuser /app
USER appuser

# ヘルスチェックの追加
HEALTHCHECK CMD curl --fail http://localhost:8501 || exit 1

# Streamlit 起動
ENTRYPOINT ["poetry", "run", "streamlit", "run", "app.py"]
EXPOSE 8501
