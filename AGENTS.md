# AGENTS.md

이 문서는 프로젝트에서 활용되는 MCP 에이전트와 도구를 설명합니다.

## TimeAgent (🕒)

- **역할**: 사용자의 질문에서 현재 시간을 요청하는 의도가 감지되면 `get_current_time` 도구를 호출합니다.
- **도구 이름**: `get_current_time`
- **입력 파라미터**: 없음
- **출력 형식**:
  ```json
  {
    "time": "YYYY-MM-DD HH:MM:SS"
  }
  ```
  반환 값은 서울 시간 기준의 현재 시각 문자열입니다.
