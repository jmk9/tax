# Tax Refund Alert Agent

종합소득세 신고 시기를 감지해서 이메일로 알려주는 개인용 에이전트.
삼쩜삼 등 유료 중개서비스 없이 홈택스 직접 신고를 안내한다.

## 설치

```bash
cp config.example.yaml config.yaml   # 이메일 주소 수정
# Gmail 앱 비밀번호는 ~/.config/tax-agent/env 에 저장 (chmod 600):
#   export SMTP_PASSWORD=<16자리>
# .bashrc가 이 파일을 source하므로 새 셸부터 자동 적용.
```

의존성: Python 3.9+, PyYAML. (테스트는 pytest)

## 사용

```bash
# 매일 실행 (cron 진입점) — 트리거 조건 충족 시 이메일 발송
python3 -m tax_agent.cli run

# 발송 대신 내용만 출력
python3 -m tax_agent.cli run --dry-run

# 신고 완료 처리 (해당 연도 추가 알림 중단)
python3 -m tax_agent.cli complete        # 올해
python3 -m tax_agent.cli complete 2026   # 연도 지정

# 연도별 상태 확인
python3 -m tax_agent.cli status
```

## 자동 실행

### 방법 1: GitHub Actions (권장 — 노트북 안 켜도 됨)

`.github/workflows/tax-alert.yml`이 매일 00:00 UTC(09:00 KST)에 실행된다.

repo Settings → Secrets and variables → Actions 에 등록:

| Secret | 값 |
|---|---|
| `SMTP_PASSWORD` | Gmail 앱 비밀번호 |
| `ALERT_EMAIL` | 수신자. 여러 명이면 쉼표로: `a@x.com,b@y.com` |
| `GMAIL_SENDER` | (선택) 발신 Gmail. 생략 시 `ALERT_EMAIL` 첫 번째 주소 사용 |

config.yaml은 개인정보 노출 방지로 커밋하지 않고, workflow가
config.example.yaml + `ALERT_EMAIL`로 매 실행마다 생성한다.
state는 workflow가 repo에 커밋해서 유지한다.

신고 완료 처리:

```bash
git pull
python3 -m tax_agent.cli complete
git add state && git commit -m "filing completed" && git push
```

### 방법 2: 로컬 cron (매일 09:00 KST)

```cron
0 9 * * * . $HOME/.config/tax-agent/env && cd $HOME/tax && python3 -m tax_agent.cli run >> agent.log 2>&1
```

## 신고기간 계산

- 시작일: 5월 1일 고정
- 마감일: 5월 31일 기준, 국세기본법 제5조에 따라 토·일·공휴일이면 다음 영업일로 순연
- 공휴일 데이터: 환경변수 `DATA_GO_KR_KEY` 설정 시 공공데이터포털 특일정보 API 사용,
  미설정 시 내장 테이블(2025~2028) 사용. 2029년 이후는 API 키 등록 필요.

예: 2026년은 5/31이 일요일이라 마감일이 6/1로 계산된다.

## 트리거

| 트리거 | 조건 | 내용 |
|---|---|---|
| filing_open | 신고기간 내, 미발송 | 신고기간 시작 + 홈택스 절차 안내 |
| d7 | 마감 7일 전부터, 미발송 | 마감 임박 알림 |
| d1 | 마감 하루 전부터, 미발송 | 마감 전일 알림 |
| late_filing | 마감 후, 미발송 | 기한후 환급신고 안내 |

`complete` 또는 `not_applicable` 상태면 모든 알림이 중단된다.
날짜를 정확일치가 아니라 창(window)으로 판정하므로 하루 이틀 실행을 놓쳐도
다음 실행에서 발송된다.

## 테스트

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -q
```

(이 환경에 설치된 ROS pytest 플러그인이 수집을 깨뜨려서 autoload 비활성화 필요.)

## 저장하지 않는 것

홈택스 ID/PW, 공동인증서 비밀번호, 주민등록번호. SMTP 비밀번호도 파일이 아니라
환경변수로만 받는다. 자동 로그인·자동 제출 없음 — 신고는 사용자가 홈택스에서
직접 확인 후 제출한다.
