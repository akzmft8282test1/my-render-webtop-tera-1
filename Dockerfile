FROM lscr.io/linuxserver/webtop:ubuntu-xfce

# 한글 폰트 및 파이썬 환경 설치
RUN apt-get update && apt-get install -y \
    fonts-nanum \
    locales \
    python3 \
    python3-pip \
    && locale-gen ko_KR.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

# 스크립트 실행 권한 부여
RUN chmod +x /app/start.sh

# 한글 및 환경 변수 설정
ENV PUID=1000 \
    PGID=1000 \
    TZ=Asia/Seoul \
    LC_ALL=ko_KR.UTF-8 \
    LANG=ko_KR.UTF-8 \
    PORT=3000

EXPOSE 3000

ENTRYPOINT ["/app/start.sh"]
