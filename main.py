import os
import time
import requests

class TeraBoxAutoClient:
    def __init__(self, username, password, initial_ndus=None):
        self.username = username
        self.password = password
        self.ndus = initial_ndus or os.getenv("TERABOX_NDUS")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.terabox.com/main"
        })
        self.base_url = "https://www.terabox.com/api"

    def refresh_cookie_if_needed(self):
        """쿠키 만료 검사 및 로그인으로 자동 재발급"""
        if self.ndus:
            self.session.cookies.set("ndus", self.ndus, domain=".terabox.com")
            try:
                res = self.session.get(f"{self.base_url}/quota", params={"checkfree": "1"})
                if res.status_code == 200 and res.json().get("errno") == 0:
                    print("[TeraBox] 기존 쿠키(ndus)가 정상 작동합니다.")
                    return True
            except Exception as e:
                print(f"[TeraBox] 쿠키 확인 중 에러: {e}")

        print("[TeraBox] 쿠키가 만료되어 자동 재로그인을 시도합니다...")
        login_url = "https://www.terabox.com/passport/auth/login"
        payload = {
            "username": self.username,
            "password": self.password,
            "client_type": "web"
        }
        
        try:
            response = self.session.post(login_url, data=payload)
            new_ndus = self.session.cookies.get("ndus")
            if new_ndus:
                self.ndus = new_ndus
                print("[TeraBox] 새 쿠키(ndus) 자동 발급 완료!")
                return True
            else:
                print("[TeraBox ERROR] 자동 로그인 실패 (캡차 요구 또는 계정 오타 가능성)")
                return False
        except Exception as e:
            print(f"[TeraBox ERROR] 로그인 요청 에러: {e}")
            return False

    def upload_and_cleanup(self, file_path, remote_dir="/RenderBackups"):
        """TeraBox 업로드 후 Render 로컬 파일 삭제 (디스크 소모 $0\text{ MB}$ 유지)"""
        if not os.path.exists(file_path):
            return

        if not self.refresh_cookie_if_needed():
            print("[TeraBox ERROR] 인증 실패로 업로드를 취소합니다.")
            return

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        # 1. Precreate (업로드 예약)
        precreate_url = f"{self.base_url}/precreate"
        pre_data = {
            "path": f"{remote_dir.rstrip('/')}/{file_name}",
            "size": file_size,
            "isdir": "0",
            "autoinit": "1"
        }
        pre_res = self.session.post(precreate_url, data=pre_data).json()
        
        if pre_res.get("errno") != 0:
            print(f"[TeraBox ERROR] Precreate 실패: {pre_res}")
            return

        upload_url = pre_res.get("uploadid_url")
        upload_id = pre_res.get("uploadid")

        # 2. 파일 바이트 전송
        print(f"[TeraBox] 업로드 시작: {file_name} ({file_size} bytes)")
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f)}
            self.session.post(upload_url, files=files)

        # 3. Create (업로드 확정)
        create_url = f"{self.base_url}/create"
        confirm_data = {
            "path": f"{remote_dir.rstrip('/')}/{file_name}",
            "size": file_size,
            "isdir": "0",
            "uploadid": upload_id
        }
        final_res = self.session.post(create_url, data=confirm_data).json()

        if final_res.get("errno") == 0:
            print(f"[TeraBox SUCCESS] 업로드 완료: {file_name}")
            # 로컬 파일 즉시 삭제
            os.remove(file_path)
            print(f"[Render Storage Cleanup] 로컬 파일 삭제 완료: {file_path}")
        else:
            print(f"[TeraBox ERROR] 최종 확정 실패: {final_res}")

def watch_folder_and_upload(watch_dir="/tmp/upload_queue"):
    """특정 폴더에 들어오는 파일을 감지하여 TeraBox로 자동 전송하는 데몬"""
    os.makedirs(watch_dir, exist_ok=True)
    TB_USER = os.getenv("TERABOX_USER")
    TB_PASS = os.getenv("TERABOX_PASS")

    if not TB_USER or not TB_PASS:
        print("[WARN] TERABOX_USER 또는 TERABOX_PASS 환경 변수가 설정되지 않았습니다.")
        return

    client = TeraBoxAutoClient(username=TB_USER, password=TB_PASS)

    print(f"[Daemon Started] '{watch_dir}' 폴더 감시 중... (파일 입력 시 TeraBox 자동 업로드)")
    while True:
        try:
            files = os.listdir(watch_dir)
            for f in files:
                full_path = os.path.join(watch_dir, f)
                if os.path.isfile(full_path):
                    client.upload_and_cleanup(full_path)
        except Exception as e:
            print(f"[Daemon Error] {e}")
        time.sleep(10)

if __name__ == "__main__":
    watch_folder_and_upload()
