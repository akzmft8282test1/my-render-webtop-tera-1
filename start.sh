#!/bin/bash

# 1. 터미널 편의용 wins 명령어 등록 (~/.bashrc 에 추가)
mkdir -p /config/webtop_data
cat << 'EOF' >> ~/.bashrc

wins() {
  echo "🚀 [wins] Webtop + Wine (한글 지원) 가동 중..."
  echo "✅ Ports 탭 또는 접속 URL로 직접 접근하세요."
}
EOF

# 2. 백그라운드에서 TeraBox 자동 업로드 데몬 실행
python3 /app/main.py &

# 3. Webtop 서비스 메인 실행 (LinuxServer 컨테이너 필수 가동 엔트리포인트)
exec /init
