FROM python:3.13-slim

WORKDIR /app

# Railway Linux 서버에 한글 Noto CJK 폰트 설치
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
