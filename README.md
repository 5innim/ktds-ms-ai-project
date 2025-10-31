# 🚀 PR 영향도 분석 레포트 생성 에이전트

**GitHub Pull Request의 프로젝트 영향도 자동 분석 시스템**
http://20.33.67.16/
https://github.com/dono-organization/dono_backend/pull/33
---

## 💡 1. 핵심 아이디어 (The Idea)

> "GitHub 개발자 PR 시,
기존 프로젝트에 끼치는 영향도를
어떻게 효과적으로 자동 분석할 수 있을까?"
> 
- **Problem:** 코드 리뷰 시, 리뷰어는 PR의 변경 사항이 프로젝트의 다른 부분(Side Effect)에 어떤 영향을 미칠지 모두 파악하기 어렵습니다.
- **Goal:** 이 "영향도"를 분석하여 레포트(Report)를 자동으로 생성하는 에이전트를 개발합니다.

<img width="757" height="486" alt="Image" src="https://github.com/user-attachments/assets/260d665a-3921-4b79-b406-3bf1d9fd1aef" />

---

## 🎯 2. 주요 과제 (The Challenge)

- 단순히 변경된 파일(diff)만 보는 것은 한계가 있습니다.
- **핵심 질문:** 이 변경 사항(e.g., 특정 함수 수정)이 **프로젝트 내 어떤 다른 소스코드**와 연관되어 있을까?
- **어려움:** 이 "연관된 소스코드"를 어떻게 정확하게 식별하고 분석 컨텍스트에 포함시킬 것인가?

---

## 🛠️ 3. 해결 전략: `tree-sitter`

- **선택한 도구:** `tree-sitter` 패키지를 핵심 전략으로 사용합니다.
- **`tree-sitter`란?**
    - 매우 빠르고 증분(incremental) 파싱이 가능한 파서(parser) 생성기입니다.
    - 코드를 단순 텍스트가 아닌, **구문 트리(Syntax Tree) 형태의 자료구조**로 변환해 줍니다.
    - 이를 통해 코드의 구조적 의미(Semantic Structure)를 이해할 수 있습니다.


---
<img width="500" height="410" alt="Image" src="https://github.com/user-attachments/assets/a8dce68d-c878-4873-b0bb-58a36887c7ce" />


## 📊 4. 기대 결과 (The Result)

이 프로세스를 통해 **"PR 영향도 분석 에이전트"**가 다음과 같이 동작합니다.

1. **PR 발생:** 개발자가 새 PR을 제출합니다.
2. **변경 분석:** 에이전트가 `tree-sitter`로 PR의 변경 사항(e.g., `updateUser` 함수 수정)을 분석합니다.
3. **유사도 검색:** 임베딩된 벡터 DB에서 `updateUser` 함수와 의미적/구조적으로 연관된 다른 코드 Chunk(e.g., `updateUser`를 호출하는 `OrderService`, `PaymentService`)를 검색합니다.
4. **레포트 생성:**
    
    > [PR 영향도 분석 레포트]
    > 
    > - **변경 사항:** `UserService`의 `updateUser` 함수 시그니처가 변경되었습니다.
    > - **영향 범위:**
    >     - `OrderService` (line 75)
    >     - `PaymentService` (line 120)
    > - **분석:** 위 2개 서비스에서 `updateUser` 함수를 호출하고 있어 **사이드 이펙트**가 우려됩니다. 리뷰 시 해당 부분의 수정이 필요합니다.

<img width="1512" height="516" alt="Image" src="https://github.com/user-attachments/assets/9256c4b9-6a28-4403-bfca-8d5c70a827d5" />

<img width="524" height="552" alt="Image" src="https://github.com/user-attachments/assets/c9567fb2-a589-4efd-9764-00b384789fdb" />
