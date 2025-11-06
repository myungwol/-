# 1. 베이스 이미지 선택 (파이썬 3.10 슬림 버전)
# 가볍고 안정적인 파이썬 환경을 제공합니다.
FROM python:3.10-slim

# 2. 작업 디렉토리 설정
# 컨테이너 내에서 코드가 위치하고 실행될 기본 폴더를 지정합니다.
WORKDIR /app

# 3. 의존성 파일 복사 및 설치
# requirements.txt 파일을 먼저 복사하여 라이브러리를 설치합니다.
# 이렇게 하면 소스 코드가 변경되어도 라이브러리는 다시 설치하지 않아 빌드 속도가 빨라집니다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 프로젝트 소스 코드 복사
# 현재 폴더의 모든 파일(main.py 등)을 컨테이너의 /app 폴더로 복사합니다.
COPY . .

# 5. 봇 실행 명령어
# 컨테이너가 시작될 때 이 명령어를 실행하여 봇을 구동합니다.
CMD ["python", "main.py"]
