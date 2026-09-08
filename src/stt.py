import re
import speech_recognition as sr


# [2026-09-07 추가] 음성 인식 실패 시 재시도할 최대 횟수
MAX_RETRIES = 3


def clean_korean_text(text: str) -> str:
    # 1. '장' 오인식 보정 (10장 -> 10잔)
    text = re.sub(
        r'(\d+)\s*장(?=[ 은는이가을를만도.,!?]|$)',
        r'\1잔',
        text,
    )

    korean_numbers = (
        r'(한|두|세|네|다섯|여섯|일곱|여덟|아홉|열|'
        r'열한|열두|열세|열네|열다섯|스무|스물둘|스물두)'
    )

    text = re.sub(
        rf'({korean_numbers})\s*장(?=[ 은는이가을를만도.,!?]|$)',
        r'\1잔',
        text,
    )

    # [2026-09-07 수정]
    # 기존에는 문장 끝의 모든 숫자에 '잔'을 붙였습니다.
    # 예: "햄버거 2 주세요"도 "햄버거 2잔 주세요"가 될 수 있어 제거했습니다.
    # 메뉴 수량 해석은 llm.py가 담당하도록 둡니다.
    #
    # text = re.sub(
    #     r'(\d+)(?=\s*$|\s+(?:주세요|줘|부탁|결제))',
    #     r'\1잔',
    #     text,
    # )

    return text.strip()


def get_user_voice_input() -> str:
    recognizer = sr.Recognizer()

    # 말 사이의 딜레이 1.5초까지 기다려줌
    recognizer.pause_threshold = 1.5

    # [2026-09-07 추가] 주변 소음 변화에 맞춰 인식 기준을 자동 조절
    recognizer.dynamic_energy_threshold = True

    messages = {
        sr.WaitTimeoutError: "말씀이 없어 대기 시간이 초과되었습니다.",
        sr.UnknownValueError: "음성을 정확하게 인식하지 못했습니다.",
    }

    # [2026-09-07 추가] 인식 실패 시 바로 종료하지 않고 최대 3회 재시도
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with sr.Microphone() as source:
                print(f"\n🎙️ 주변 소음 측정 중... ({attempt}/{MAX_RETRIES})")
                recognizer.adjust_for_ambient_noise(source, duration=0.8)

                print("🎧 듣고 있습니다. 주문을 말씀해 주세요! (대기 시간 10초)")

                audio = recognizer.listen(
                    source,
                    timeout=10,
                    phrase_time_limit=15,
                )

                user_input = recognizer.recognize_google(
                    audio,
                    language="ko-KR",
                )

                refined_input = clean_korean_text(user_input)
                print(f"✅ 인식 결과: {refined_input}")
                return refined_input

        except (sr.WaitTimeoutError, sr.UnknownValueError) as e:
            print(f"⚠️ {messages[type(e)]}")

            # [2026-09-07 추가] 마지막 시도가 아니라면 재주문 안내
            if attempt < MAX_RETRIES:
                print("다시 말씀해 주세요.")

        except sr.RequestError as e:
            print(f"❌ STT 서비스 연결 실패: {e}")
            return ""

        # [2026-09-07 추가] 마이크 연결·권한 문제 처리
        except OSError as e:
            print(f"❌ 마이크를 사용할 수 없습니다: {e}")
            return ""

    # [2026-09-07 추가] 모든 재시도 실패 후 빈 문자열 반환
    print("❌ 음성을 여러 번 인식하지 못했습니다.")
    return ""


if __name__ == "__main__":
    result = get_user_voice_input()
    print(f"\n👉 최종 텍스트: '{result}'" if result else "\n❌ 음성 인식 실패")